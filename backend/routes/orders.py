from database.connection import get_db, settings
from models.domain import Order, Invoice, Product
from schemas.domain import OrderCreate, OrderResponse, PaymentVerify, CartItemSchema
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
import hmac
import hashlib
import logging
import uuid
from datetime import datetime
import razorpay
from sqlalchemy.orm import Session
from sqlalchemy import func

from services.invoice_generator import generate_invoice_pdf
from services.email_service import send_invoice_email
from models.domain import AdminNotification

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/orders", tags=["orders"])

def get_razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        logger.error("Configuration Failure: Razorpay keys are missing.")
        raise HTTPException(
            status_code=500,
            detail="Payment gateway configuration error. Please contact support."
        )
    try:
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    except Exception as e:
        logger.error(f"Razorpay Client Initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Payment gateway initialization error. Please contact support."
        )

def generate_terravyn_order_id() -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = str(uuid.uuid4().hex)[:4].upper()
    return f"TRV-{date_str}-{unique_suffix}"

def generate_invoice_number(db: Session) -> str:
    date_str = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"TRV-INV-{date_str}-"
    # Find the latest invoice for today
    latest_invoice = db.query(Invoice).filter(Invoice.invoice_number.like(f"{prefix}%")).order_by(Invoice.id.desc()).first()
    if latest_invoice:
        last_seq = int(latest_invoice.invoice_number.split("-")[-1])
        new_seq = last_seq + 1
    else:
        new_seq = 1
    return f"{prefix}{new_seq:04d}"

def process_invoice_and_email(db: Session, order: Order, background_tasks: BackgroundTasks):
    invoice_number = generate_invoice_number(db)
    
    # Calculate GST (assuming 18%)
    gst_percentage = 18.0
    subtotal = order.total_amount / (1 + (gst_percentage / 100.0))
    gst_amount = order.total_amount - subtotal
    
    invoice = Invoice(
        invoice_number=invoice_number,
        order_id=order.order_id,
        customer_name=order.customer_name,
        email=order.email,
        phone=order.phone_number,
        billing_address=f"{order.address}, {order.street}, {order.city}, {order.district}, {order.state} - {order.pincode}",
        product_name=order.product_name,
        quantity=order.quantity,
        unit_price=order.unit_price,
        subtotal=order.subtotal,
        gst_percentage=gst_percentage,
        gst_amount=order.tax_amount,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
        payment_status="PAID" if order.payment_status == "SUCCESS" else "PAYMENT PENDING"
    )
    
    try:
        pdf_path = generate_invoice_pdf(invoice)
        invoice.invoice_pdf_path = pdf_path
    except Exception as e:
        logger.error(f"Failed to generate PDF for order {order.order_id}: {str(e)}")
        # We continue to save the invoice record even if PDF fails
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    background_tasks.add_task(
        send_invoice_email,
        customer_email=invoice.email,
        customer_name=invoice.customer_name,
        order_id=invoice.order_id,
        invoice_number=invoice.invoice_number,
        payment_status=invoice.payment_status,
        pdf_path=invoice.invoice_pdf_path
    )
    
    return invoice

@router.post("/create-order", response_model=OrderResponse)
def create_razorpay_order(order_req: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if order_req.paymentMethod != "ONLINE":
        logger.error(f"Invalid payment method for /create-order: {order_req.paymentMethod}")
        raise HTTPException(status_code=400, detail="Use /place-cod-order for Cash on Delivery.")

    if not order_req.customerDetails.consent_accepted:
        raise HTTPException(status_code=400, detail="Consent for identity verification is required.")
        
    aadhaar = order_req.customerDetails.aadhaar_number.replace(" ", "")
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        raise HTTPException(status_code=400, detail="Invalid Aadhaar number.")
        
    if not order_req.customerDetails.aadhaar_document_path:
        raise HTTPException(status_code=400, detail="Identity verification information is incomplete.")
    
    masked_aadhaar = f"XXXX XXXX {aadhaar[-4:]}"

    if order_req.items:
        items = order_req.items
    else:
        # Fallback for old single product format
        items = [CartItemSchema(productId=order_req.productId, quantity=order_req.quantity or 1)]

    product_names = []
    total_quantity = 0
    total_subtotal = 0.0
    total_tax = 0.0
    total_shipping = 0.0
    first_product_id = None
    first_product_price = 0.0

    for item in items:
        product = db.query(Product).filter(Product.id == item.productId).first()
        if not product or not product.is_active or product.stock_status != "IN_STOCK":
            raise HTTPException(status_code=400, detail=f"Product {item.productId} is unavailable or out of stock")
        
        if first_product_id is None:
            first_product_id = product.id
            first_product_price = product.current_price

        product_names.append(f"{product.name} (x{item.quantity})")
        total_quantity += item.quantity
        sub = product.current_price * item.quantity
        total_subtotal += sub
        total_tax += round(sub * (product.tax_percentage / 100.0), 2)
        total_shipping += product.shipping_charges

    amount_in_rupees = round(total_subtotal + total_tax + total_shipping, 2)
    amount_in_paise = int(amount_in_rupees * 100)

    # 1. Generate Order ID
    trv_order_id = generate_terravyn_order_id()

    # 2. Setup Razorpay Order
    client = get_razorpay_client()
    logger.info(f"Order Creation Attempt: Generating Razorpay order for {trv_order_id} (Amount: {amount_in_paise})")
    try:
        rzp_order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": trv_order_id,
            "payment_capture": 1
        })
        razorpay_order_id = rzp_order.get("id")
        logger.info(f"Razorpay API Response: Successfully created Razorpay order {razorpay_order_id}")
    except Exception as e:
        logger.error(f"Failed to create Razorpay Order for {trv_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create Razorpay Order. Please try again.")

    # 3. Create DB Record
    try:
        db_order = Order(
            order_id=trv_order_id,
            razorpay_order_id=razorpay_order_id,
            customer_name=order_req.customerDetails.name,
            phone_number=order_req.customerDetails.phone,
            email=order_req.customerDetails.email,
            address=order_req.customerDetails.address,
            street=order_req.customerDetails.street,
            city=order_req.customerDetails.city,
            district=order_req.customerDetails.district,
            state=order_req.customerDetails.state,
            pincode=order_req.customerDetails.pincode,
            landmark=order_req.customerDetails.landmark,
            product_id=first_product_id if len(items) == 1 else None,
            product_name=", ".join(product_names),
            quantity=total_quantity,
            unit_price=first_product_price if len(items) == 1 else 0.0,
            subtotal=total_subtotal,
            tax_amount=total_tax,
            shipping_amount=total_shipping,
            total_amount=amount_in_rupees,
            payment_method=order_req.paymentMethod,
            payment_status="PENDING",
            order_status="PENDING",
            aadhaar_number_masked=masked_aadhaar,
            aadhaar_document_path=order_req.customerDetails.aadhaar_document_path,
            identity_verification_status="PENDING"
        )

        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        logger.info(f"Successfully saved ONLINE order {trv_order_id} to database.")
        
        # Add notification
        notif = AdminNotification(
            message=f"New ONLINE order received from {order_req.customerDetails.name} ({trv_order_id}).",
            type="ORDER",
            reference_id=trv_order_id
        )
        db.add(notif)
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Database error while saving order {trv_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save order to database.")

    return db_order

@router.post("/place-cod-order", response_model=OrderResponse)
def place_cod_order(order_req: OrderCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if order_req.paymentMethod != "COD":
        logger.error(f"Invalid payment method for /place-cod-order: {order_req.paymentMethod}")
        raise HTTPException(status_code=400, detail="Use /create-order for Online payments.")

    if not order_req.customerDetails.consent_accepted:
        raise HTTPException(status_code=400, detail="Consent for identity verification is required.")
        
    aadhaar = order_req.customerDetails.aadhaar_number.replace(" ", "")
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        raise HTTPException(status_code=400, detail="Invalid Aadhaar number.")
        
    if not order_req.customerDetails.aadhaar_document_path:
        raise HTTPException(status_code=400, detail="Identity verification information is incomplete.")
    
    masked_aadhaar = f"XXXX XXXX {aadhaar[-4:]}"

    if order_req.items:
        items = order_req.items
    else:
        # Fallback for old single product format
        items = [CartItemSchema(productId=order_req.productId, quantity=order_req.quantity or 1)]

    product_names = []
    total_quantity = 0
    total_subtotal = 0.0
    total_tax = 0.0
    total_shipping = 0.0
    first_product_id = None
    first_product_price = 0.0

    for item in items:
        product = db.query(Product).filter(Product.id == item.productId).first()
        if not product or not product.is_active or product.stock_status != "IN_STOCK":
            raise HTTPException(status_code=400, detail=f"Product {item.productId} is unavailable or out of stock")
        
        if first_product_id is None:
            first_product_id = product.id
            first_product_price = product.current_price

        product_names.append(f"{product.name} (x{item.quantity})")
        total_quantity += item.quantity
        sub = product.current_price * item.quantity
        total_subtotal += sub
        total_tax += round(sub * (product.tax_percentage / 100.0), 2)
        total_shipping += product.shipping_charges

    amount_in_rupees = round(total_subtotal + total_tax + total_shipping, 2)

    # 1. Generate Order ID
    trv_order_id = generate_terravyn_order_id()
    logger.info(f"COD Order Attempt: Creating COD order {trv_order_id} for {order_req.customerDetails.email}")

    # 2. Create DB Record
    try:
        db_order = Order(
            order_id=trv_order_id,
            razorpay_order_id=None,
            customer_name=order_req.customerDetails.name,
            phone_number=order_req.customerDetails.phone,
            email=order_req.customerDetails.email,
            address=order_req.customerDetails.address,
            street=order_req.customerDetails.street,
            city=order_req.customerDetails.city,
            district=order_req.customerDetails.district,
            state=order_req.customerDetails.state,
            pincode=order_req.customerDetails.pincode,
            landmark=order_req.customerDetails.landmark,
            product_id=first_product_id if len(items) == 1 else None,
            product_name=", ".join(product_names),
            quantity=total_quantity,
            unit_price=first_product_price if len(items) == 1 else 0.0,
            subtotal=total_subtotal,
            tax_amount=total_tax,
            shipping_amount=total_shipping,
            total_amount=amount_in_rupees,
            payment_method=order_req.paymentMethod,
            payment_status="PENDING",
            order_status="PENDING",
            aadhaar_number_masked=masked_aadhaar,
            aadhaar_document_path=order_req.customerDetails.aadhaar_document_path,
            identity_verification_status="PENDING"
        )

        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        logger.info(f"Successfully saved COD order {trv_order_id} to database.")
        
        # Add notification
        notif = AdminNotification(
            message=f"New COD order received from {order_req.customerDetails.name} ({trv_order_id}).",
            type="ORDER",
            reference_id=trv_order_id
        )
        db.add(notif)
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Database error while saving COD order {trv_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save COD order to database: {str(e)}")

    # 3. Generate Invoice and trigger email for COD
    try:
        process_invoice_and_email(db, db_order, background_tasks)
        logger.info(f"Successfully processed invoice and email tasks for COD order {trv_order_id}.")
    except Exception as e:
        logger.error(f"Failed to process invoice for COD order {trv_order_id}: {str(e)}")
        # Don't fail the order if invoice fails, but log it

    return db_order

@router.post("/verify-payment")
def verify_payment(payload: PaymentVerify, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Verify Signature
    client = get_razorpay_client()

    try:
        # Razorpay's utility verifies the signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': payload.razorpay_order_id,
            'razorpay_payment_id': payload.razorpay_payment_id,
            'razorpay_signature': payload.razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"Signature Verification Failed for order {payload.razorpay_order_id}: {str(e)}")
        # If verification fails, update DB
        order = db.query(Order).filter(Order.razorpay_order_id == payload.razorpay_order_id).first()
        if order:
            order.payment_status = "FAILED"
            order.order_status = "PENDING"
            db.commit()
        raise HTTPException(status_code=400, detail="Signature Verification Failed")

    # If verification succeeds, update DB
    order = db.query(Order).filter(Order.razorpay_order_id == payload.razorpay_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.payment_status = "SUCCESS"
    order.order_status = "PROCESSING"
    order.razorpay_payment_id = payload.razorpay_payment_id
    db.commit()

    # Generate Invoice and send Email for ONLINE payment success
    process_invoice_and_email(db, order, background_tasks)

    return {"status": "success", "message": "Payment verified successfully", "order_id": order.order_id}
