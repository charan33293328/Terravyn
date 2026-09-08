import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import pandas as pd
import io

from database.connection import get_db
from models.domain import Order, AdminNotification, User, RoleEnum
from schemas.domain import OrderAdminResponse, OrderStatusUpdate, PaymentStatusUpdate, OrderDetailsNestedResponse, IdentityVerificationStatusUpdate
from auth.security import get_current_active_user, get_current_user
import os
import mimetypes
from fastapi.responses import FileResponse

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/admin/orders", tags=["admin_orders"])

def check_admin(current_user: User):
    if current_user.role not in [RoleEnum.admin, RoleEnum.super_admin]:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
    return current_user

@router.get("", response_model=dict)
def get_orders(
    skip: int = 0, 
    limit: int = 100, 
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    check_admin(current_user)
    query = db.query(Order)

    if status:
        query = query.filter(Order.order_status == status)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Order.order_id.ilike(search_filter),
                Order.invoice_number.ilike(search_filter),
                Order.customer_name.ilike(search_filter),
                Order.phone_number.ilike(search_filter),
                Order.email.ilike(search_filter)
            )
        )
    
    total = query.count()
    orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    # We serialize manually or use Pydantic
    serialized_orders = [OrderAdminResponse.model_validate(o).model_dump() for o in orders]
    
    return {
        "total": total,
        "items": serialized_orders
    }

@router.get("/export")
def export_orders(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    check_admin(current_user)
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.order_status == status)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Order.order_id.ilike(search_filter),
                Order.invoice_number.ilike(search_filter),
                Order.customer_name.ilike(search_filter),
                Order.phone_number.ilike(search_filter)
            )
        )
        
    orders = query.order_by(desc(Order.created_at)).all()
    
    data = []
    for o in orders:
        data.append({
            "Order ID": o.order_id,
            "Invoice Number": o.invoice_number,
            "Customer Name": o.customer_name,
            "Phone": o.phone_number,
            "Email": o.email,
            "Product": o.product_name,
            "Quantity": o.quantity,
            "Total Amount": o.total_amount,
            "Payment Method": o.payment_method,
            "Payment Status": o.payment_status,
            "Order Status": o.order_status,
            "Created At": o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else ""
        })
        
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Orders')
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="terravyn_orders.xlsx"'
    }
    
    return Response(
        content=output.read(), 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers=headers
    )

@router.get("/{order_id}", response_model=OrderDetailsNestedResponse)
def get_order_details(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return {
        "order_id": order.order_id,
        "invoice_number": order.invoice_number if hasattr(order, 'invoice_number') else None,
        "customer": {
            "name": order.customer_name,
            "phone": order.phone_number,
            "email": order.email
        },
        "shipping_address": {
            "address": order.address,
            "city": getattr(order, 'city', ''),
            "district": getattr(order, 'district', ''),
            "state": getattr(order, 'state', ''),
            "pincode": getattr(order, 'pincode', '')
        },
        "product": {
            "name": order.product_name,
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "subtotal": order.subtotal
        },
        "pricing": {
            "tax": order.tax_amount,
            "shipping": order.shipping_amount if hasattr(order, 'shipping_amount') else 0.0,
            "total": order.total_amount
        },
        "payment": {
            "method": order.payment_method,
            "status": order.payment_status,
            "razorpay_order_id": order.razorpay_order_id,
            "razorpay_payment_id": order.razorpay_payment_id
        },
        "order_status": order.order_status,
        "identity": {
            "status": order.identity_verification_status or "PENDING",
            "verified_at": order.identity_verified_at,
            "aadhaar_number_masked": order.aadhaar_number_masked,
            "aadhaar_document_path": order.aadhaar_document_path
        },
        "timestamps": {
            "created_at": order.created_at,
            "updated_at": getattr(order, 'updated_at', None)
        }
    }

@router.get("/{order_id}/aadhaar-document")
async def get_aadhaar_document(order_id: str, token: str, db: Session = Depends(get_db)):
    current_user = await get_current_user(token=token, db=db)
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    check_admin(current_user)
    
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order or not order.aadhaar_document_path:
        raise HTTPException(status_code=404, detail="Document not found")
        
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "secure_uploads")
    file_path = os.path.join(upload_dir, order.aadhaar_document_path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File does not exist on server")
        
    media_type, _ = mimetypes.guess_type(file_path)
    if not media_type:
        media_type = "application/pdf"
        
    filename = order.aadhaar_document_path.split("/")[-1]
        
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"'
        }
    )

@router.put("/{order_id}/identity-verification", response_model=OrderAdminResponse)
def update_identity_verification(order_id: str, status_update: IdentityVerificationStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.identity_verification_status = status_update.status
    if status_update.status in ["APPROVED", "REJECTED"]:
        order.identity_verified_at = datetime.utcnow()
        
    db.commit()
    db.refresh(order)
    
    # Ideally trigger notification to user here
    return order

@router.put("/{order_id}/status", response_model=OrderAdminResponse)
def update_order_status(order_id: str, status_update: OrderStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.order_status = status_update.order_status
    db.commit()
    db.refresh(order)
    return order

@router.put("/{order_id}/payment-status", response_model=OrderAdminResponse)
def update_payment_status(order_id: str, status_update: PaymentStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.payment_status = status_update.payment_status
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/cancel", response_model=OrderAdminResponse)
def cancel_order(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.order_status = "CANCELLED"
    db.commit()
    db.refresh(order)
    return order
