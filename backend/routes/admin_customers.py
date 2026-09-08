import logging
from typing import List, Optional
import io
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from database.connection import get_db
from models.domain import User, RoleEnum, Device, Order, SupportTicket
from schemas.admin_customers import CustomerListResponse, CustomerDetailsResponse
from auth.security import get_current_active_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/admin/customers", tags=["admin_customers"])

def check_admin(current_user: User):
    if current_user.role not in [RoleEnum.admin, RoleEnum.super_admin]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

@router.get("", response_model=List[CustomerListResponse])
def get_all_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)

    # Return all registered app users (role = user) — these are dashboard users / farmers
    users = db.query(User).filter(User.role == RoleEnum.user).order_by(desc(User.created_at)).all()

    result = []
    for user in users:
        latest_order = db.query(Order).filter(Order.email == user.email).order_by(desc(Order.created_at)).first()
        phone_number = latest_order.phone_number if latest_order else "N/A"
        total_orders = db.query(Order).filter(Order.email == user.email).count()
        total_devices = db.query(Device).filter(Device.owner_id == user.id).count()

        result.append({
            "id": user.id,
            "full_name": user.full_name or "Unknown",
            "phone_number": phone_number,
            "email": user.email,
            "is_active": user.is_active,
            "total_orders": total_orders,
            "total_devices": total_devices,
            "created_at": user.created_at,
            "last_login": None
        })

    return result


@router.get("/export")
def export_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)

    users = db.query(User).filter(User.role == RoleEnum.user).all()

    data = []
    for user in users:
        latest_order = db.query(Order).filter(Order.email == user.email).order_by(desc(Order.created_at)).first()
        phone_number = latest_order.phone_number if latest_order else "N/A"
        total_orders = db.query(Order).filter(Order.email == user.email).count()
        total_devices = db.query(Device).filter(Device.owner_id == user.id).count()

        data.append({
            "Full Name": user.full_name or "Unknown",
            "Email": user.email,
            "Phone Number": phone_number,
            "Account Status": "Active" if user.is_active else "Inactive",
            "Total Orders": total_orders,
            "Total Devices": total_devices,
            "Registered Date": user.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    df = pd.DataFrame(data)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Farmers')

    response = Response(content=stream.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response.headers["Content-Disposition"] = "attachment; filename=farmers_export.xlsx"
    return response


@router.get("/{customer_id}", response_model=CustomerDetailsResponse)
def get_customer_details(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)

    user = db.query(User).filter(User.id == customer_id, User.role == RoleEnum.user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    orders = db.query(Order).filter(Order.email == user.email).order_by(desc(Order.created_at)).all()
    phone_number = orders[0].phone_number if orders else "N/A"

    if orders:
        latest = orders[0]
        addr_parts = [latest.address, latest.city, latest.district, latest.state, getattr(latest, 'pincode', '')]
        address = ", ".join([p for p in addr_parts if p])
    else:
        address = "N/A"

    order_history = [{
        "order_id": o.order_id,
        "invoice_number": getattr(o, 'invoice_number', None),
        "created_at": o.created_at,
        "payment_status": o.payment_status,
        "order_status": o.order_status,
        "total_amount": o.total_amount
    } for o in orders]

    devices = db.query(Device).filter(Device.owner_id == user.id).all()
    device_ownership = [{
        "device_uid": d.device_uid,
        "status": d.status,
        "claimed_at": d.claimed_at,
        "is_active": d.status in ["ONLINE", "OFFLINE"]
    } for d in devices]

    total_tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == user.id).count()

    return {
        "id": user.id,
        "is_active": user.is_active,
        "personal_information": {
            "full_name": user.full_name or "Unknown",
            "phone_number": phone_number,
            "email": user.email,
            "address": address
        },
        "order_history": order_history,
        "device_ownership": device_ownership,
        "activity_information": {
            "registration_date": user.created_at,
            "last_login": None,
            "total_support_tickets": total_tickets
        }
    }


@router.put("/{customer_id}/disable")
def disable_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    user = db.query(User).filter(User.id == customer_id, User.role == RoleEnum.user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"message": "User disabled successfully"}


@router.put("/{customer_id}/activate")
def activate_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    user = db.query(User).filter(User.id == customer_id, User.role == RoleEnum.user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return {"message": "User activated successfully"}
