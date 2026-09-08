from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_
from typing import List, Optional
from datetime import datetime, timedelta
import io

from database.connection import get_db
from models.domain import Farmer, Order, OrderItem, ReturnRequest, User
from schemas.domain import FarmerOrderResponse, FarmerOrdersSummary, ReturnRequestCreate, ReturnRequestSchema
from auth.security import get_current_active_user

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from fastapi.responses import StreamingResponse
    REPORTLAB_INSTALLED = True
except ImportError:
    REPORTLAB_INSTALLED = False

router = APIRouter()

def get_farmer(db: Session, current_user: User):
    farmer = db.query(Farmer).filter(
        (Farmer.email == current_user.email) | 
        (Farmer.phone == current_user.phone_number)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found for this user.")
    return farmer

@router.get("/summary", response_model=FarmerOrdersSummary)
def get_orders_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    orders = db.query(Order).filter(
        (Order.farmer_id == farmer.id) | 
        (Order.email == current_user.email) | 
        (Order.phone_number == current_user.phone_number)
    )
    
    total = orders.count()
    active = orders.filter(Order.order_status.in_(["PENDING", "PROCESSING", "PACKED", "SHIPPED", "OUT FOR DELIVERY"])).count()
    delivered = orders.filter(Order.order_status == "DELIVERED").count()
    returned = orders.filter(Order.order_status == "RETURNED").count()
    
    return FarmerOrdersSummary(
        total_orders=total,
        active_orders=active,
        delivered_orders=delivered,
        returned_orders=returned
    )

@router.get("", response_model=dict)
def get_farmer_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    date_range: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|total_amount|estimated_delivery_date|order_status)$"),
    sort_desc: bool = True
):
    farmer = get_farmer(db, current_user)
    
    query = db.query(Order).filter(
        (Order.farmer_id == farmer.id) | 
        (Order.email == current_user.email) | 
        (Order.phone_number == current_user.phone_number)
    )
    
    if status and status.upper() != "ALL":
        query = query.filter(Order.order_status == status.upper())
        
    if payment_status and payment_status.upper() != "ALL":
        query = query.filter(Order.payment_status == payment_status.upper())
        
    if search:
        search_term = f"%{search}%"
        query = query.join(OrderItem, isouter=True).filter(
            or_(
                Order.order_id.ilike(search_term),
                Order.invoice_number.ilike(search_term),
                OrderItem.product_name.ilike(search_term)
            )
        )
        
    if date_range:
        now = datetime.utcnow()
        if date_range == "Last 30 Days":
            query = query.filter(Order.created_at >= now - timedelta(days=30))
        elif date_range == "Last 90 Days":
            query = query.filter(Order.created_at >= now - timedelta(days=90))
        elif date_range == "This Year":
            query = query.filter(Order.created_at >= datetime(now.year, 1, 1))

    # Apply sorting
    sort_column = getattr(Order, sort_by)
    if sort_desc:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
        
    total_count = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    orders = query.offset(skip).limit(page_size).all()
    
    return {
        "items": [FarmerOrderResponse.model_validate(order) for order in orders],
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }

@router.get("/{order_id}", response_model=FarmerOrderResponse)
def get_order_details(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    order = db.query(Order).filter(
        Order.order_id == order_id, 
        (Order.farmer_id == farmer.id) | 
        (Order.email == current_user.email) | 
        (Order.phone_number == current_user.phone_number)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return order

@router.get("/{order_id}/tracking")
def get_order_tracking(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    order = db.query(Order).filter(
        Order.order_id == order_id, 
        (Order.farmer_id == farmer.id) | 
        (Order.email == current_user.email) | 
        (Order.phone_number == current_user.phone_number)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Standard static timeline mapped from order_status
    status_flow = ["PENDING", "PROCESSING", "PACKED", "SHIPPED", "OUT FOR DELIVERY", "DELIVERED"]
    
    timeline = []
    current_status = order.order_status.upper()
    
    current_index = -1
    if current_status in status_flow:
        current_index = status_flow.index(current_status)
    elif current_status == "RETURNED":
        current_index = len(status_flow) - 1 # Treated as past delivered
    elif current_status == "CANCELLED":
        current_index = 0 # Cancelled early
        
    for i, st in enumerate(status_flow):
        status_info = {
            "status": st,
            "completed": i <= current_index,
            "current": i == current_index,
            "timestamp": order.updated_at if i == current_index else None
        }
        # Hardcode first step to created_at
        if i == 0 and status_info["completed"]:
            status_info["timestamp"] = order.created_at
        timeline.append(status_info)
        
    return {
        "tracking_number": order.tracking_number,
        "courier_partner": order.courier_name,
        "tracking_url": order.tracking_url,
        "estimated_delivery_date": order.estimated_delivery_date,
        "timeline": timeline
    }

@router.post("/{order_id}/return", response_model=ReturnRequestSchema)
def request_return(order_id: str, return_request: ReturnRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    order = db.query(Order).filter(
        Order.order_id == order_id, 
        (Order.farmer_id == farmer.id) | 
        (Order.email == current_user.email) | 
        (Order.phone_number == current_user.phone_number)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.order_status.upper() != "DELIVERED":
        raise HTTPException(status_code=400, detail="Only delivered orders can be returned.")
        
    # Check return window (7 days)
    if order.updated_at and datetime.utcnow() > order.updated_at + timedelta(days=7):
        raise HTTPException(status_code=400, detail="Return window (7 days) has expired.")
        
    # Check if already requested
    existing = db.query(ReturnRequest).filter(ReturnRequest.order_id == order.order_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="A return request already exists for this order.")
        
    new_request = ReturnRequest(
        order_id=order.order_id,
        farmer_id=farmer.id,
        reason=return_request.reason,
        status="Pending"
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/{order_id}/invoice")
def download_invoice(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not REPORTLAB_INSTALLED:
        raise HTTPException(status_code=500, detail="PDF generation library not installed.")
        
    farmer = get_farmer(db, current_user)
    
    order = db.query(Order).filter(
        Order.order_id == order_id, 
        (Order.farmer_id == farmer.id) | 
        (Order.email == current_user.email) | 
        (Order.phone_number == current_user.phone_number)
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Simple PDF generation
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "TERRAVYN")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, "Invoice for Order: " + order.order_id)
    p.drawString(50, height - 90, "Date: " + order.created_at.strftime("%Y-%m-%d"))
    
    p.drawString(50, height - 130, "Customer: " + order.customer_name)
    p.drawString(50, height - 150, "Email: " + order.email)
    p.drawString(50, height - 170, "Shipping Address:")
    p.drawString(50, height - 190, f"{order.address}, {order.city}")
    p.drawString(50, height - 210, f"{order.state}, {order.pincode}")
    
    y = height - 260
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Item")
    p.drawString(300, y, "Qty")
    p.drawString(400, y, "Price")
    p.drawString(500, y, "Subtotal")
    
    y -= 20
    p.setFont("Helvetica", 12)
    for item in order.items:
        p.drawString(50, y, str(item.product_name)[:30])
        p.drawString(300, y, str(item.quantity))
        p.drawString(400, y, f"Rs.{item.unit_price:,.2f}")
        p.drawString(500, y, f"Rs.{item.subtotal:,.2f}")
        y -= 20
        
    y -= 20
    p.line(50, y, 550, y)
    y -= 20
    
    p.drawString(400, y, "Subtotal:")
    p.drawString(500, y, f"Rs.{order.subtotal:,.2f}")
    y -= 20
    p.drawString(400, y, "Tax:")
    p.drawString(500, y, f"Rs.{order.tax_amount:,.2f}")
    y -= 20
    p.drawString(400, y, "Shipping:")
    p.drawString(500, y, f"Rs.{order.shipping_amount:,.2f}")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(400, y, "Grand Total:")
    p.drawString(500, y, f"Rs.{order.total_amount:,.2f}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return StreamingResponse(
        buffer, 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order.order_id}.pdf"}
    )
