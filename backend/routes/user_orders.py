from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from models.domain import Order, User, Invoice
from schemas.domain import OrderResponse
from auth.security import get_current_active_user

router = APIRouter(prefix="/api/user/orders", tags=["user-orders"])

@router.get("")
def get_user_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    orders = db.query(Order).filter(Order.email == current_user.email).order_by(desc(Order.created_at)).all()
    
    results = []
    for o in orders:
        inv = db.query(Invoice).filter(Invoice.order_id == o.order_id).first()
        o_dict = o.__dict__.copy()
        o_dict["invoice_number"] = inv.invoice_number if inv else None
        results.append(o_dict)
        
    return results

@router.get("/{order_id}")
def get_user_order_details(order_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    order = db.query(Order).filter(Order.order_id == order_id, Order.email == current_user.email).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
    
    return {
        "order": order,
        "invoice": invoice
    }
