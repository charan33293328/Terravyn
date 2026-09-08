from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from database.connection import get_db
from models.domain import User, RoleEnum, Device, Order, SupportTicket, AdminNotification
from auth.security import get_current_user
from schemas.admin_analytics import (
    OverviewStats, DeviceStats, OrderStats, CustomerStats, SupportStats,
    TimeSeriesDataPoint, CategoryDataPoint, ActivityEvent
)

router = APIRouter(prefix="/api/admin/analytics", tags=["Admin Analytics"])

def check_admin(user: User):
    if user.role not in [RoleEnum.super_admin, RoleEnum.admin, RoleEnum.operations_manager]:
        raise HTTPException(status_code=403, detail="Not authorized")

def get_date_threshold(range_str: str):
    today = datetime.utcnow()
    if range_str == "today":
        return today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_str == "7d":
        return today - timedelta(days=7)
    elif range_str == "30d":
        return today - timedelta(days=30)
    elif range_str == "90d":
        return today - timedelta(days=90)
    return today - timedelta(days=30)

@router.get("/overview", response_model=OverviewStats)
def get_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    total_rev = db.query(func.sum(Order.total_amount)).filter(Order.order_status == "DELIVERED").scalar() or 0.0
    total_orders = db.query(Order).count()
    total_devices = db.query(Device).count()
    total_customers = db.query(User).filter(User.role == RoleEnum.user).count()
    
    return OverviewStats(
        total_revenue=total_rev,
        total_orders=total_orders,
        total_devices=total_devices,
        total_customers=total_customers
    )

@router.get("/devices", response_model=DeviceStats)
def get_devices_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total = db.query(Device).count()
    online = db.query(Device).filter(Device.status == "ONLINE").count()
    offline = total - online
    provisioned = db.query(Device).filter(Device.nvs_written == True).count()
    unprovisioned = total - provisioned
    assigned = db.query(Device).filter(Device.owner_id != None).count()
    unassigned = total - assigned
    added_today = db.query(Device).filter(Device.created_at >= today).count()
    
    return DeviceStats(
        total=total,
        online=online,
        offline=offline,
        provisioned=provisioned,
        unprovisioned=unprovisioned,
        assigned=assigned,
        unassigned=unassigned,
        added_today=added_today
    )

@router.get("/orders", response_model=OrderStats)
def get_orders_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    this_month = today.replace(day=1)
    
    total = db.query(Order).count()
    orders_today = db.query(Order).filter(Order.created_at >= today).count()
    
    rev_today = db.query(func.sum(Order.total_amount)).filter(Order.created_at >= today, Order.order_status == "DELIVERED").scalar() or 0.0
    rev_month = db.query(func.sum(Order.total_amount)).filter(Order.created_at >= this_month, Order.order_status == "DELIVERED").scalar() or 0.0
    
    pending = db.query(Order).filter(Order.order_status == "PENDING").count()
    processing = db.query(Order).filter(Order.order_status == "PROCESSING").count()
    delivered = db.query(Order).filter(Order.order_status == "DELIVERED").count()
    cancelled = db.query(Order).filter(Order.order_status == "CANCELLED").count()
    
    return OrderStats(
        total=total,
        today=orders_today,
        revenue_today=rev_today,
        revenue_this_month=rev_month,
        pending=pending,
        processing=processing,
        delivered=delivered,
        cancelled=cancelled
    )

@router.get("/customers", response_model=CustomerStats)
def get_customers_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    base_query = db.query(User).filter(User.role == RoleEnum.user)
    total = base_query.count()
    new_today = base_query.filter(User.created_at >= today).count()
    
    # Subquery logic for ownership
    users_with_devices = db.query(Device.owner_id).filter(Device.owner_id != None).distinct().count()
    users_with_orders = db.query(Order.email).distinct().count()
    
    return CustomerStats(
        total=total,
        new_today=new_today,
        with_devices=users_with_devices,
        without_devices=total - users_with_devices,
        with_orders=users_with_orders
    )

@router.get("/support", response_model=SupportStats)
def get_support_analytics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total = db.query(SupportTicket).count()
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "OPEN").count()
    in_progress = db.query(SupportTicket).filter(SupportTicket.status == "IN_PROGRESS").count()
    resolved = db.query(SupportTicket).filter(SupportTicket.status == "RESOLVED").count()
    critical = db.query(SupportTicket).filter(SupportTicket.priority == "CRITICAL").count()
    created_today = db.query(SupportTicket).filter(SupportTicket.created_at >= today).count()
    
    return SupportStats(
        total=total,
        open=open_tickets,
        in_progress=in_progress,
        resolved=resolved,
        critical=critical,
        created_today=created_today
    )

@router.get("/charts/orders_trend", response_model=List[TimeSeriesDataPoint])
def get_orders_trend(time_range: str = Query("30d"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    threshold = get_date_threshold(time_range)
    
    orders = db.query(Order).filter(Order.created_at >= threshold).all()
    
    # Bin by date
    bins = {}
    curr = threshold
    now = datetime.utcnow()
    while curr <= now:
        bins[curr.strftime('%Y-%m-%d')] = 0
        curr += timedelta(days=1)
        
    for o in orders:
        date_str = o.created_at.strftime('%Y-%m-%d')
        if date_str in bins:
            bins[date_str] += 1
            
    return [TimeSeriesDataPoint(date=k, value=v) for k, v in bins.items()]

@router.get("/charts/revenue_trend", response_model=List[TimeSeriesDataPoint])
def get_revenue_trend(time_range: str = Query("30d"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    threshold = get_date_threshold(time_range)
    
    orders = db.query(Order).filter(Order.created_at >= threshold, Order.order_status == "DELIVERED").all()
    
    bins = {}
    curr = threshold
    now = datetime.utcnow()
    while curr <= now:
        bins[curr.strftime('%Y-%m-%d')] = 0.0
        curr += timedelta(days=1)
        
    for o in orders:
        date_str = o.created_at.strftime('%Y-%m-%d')
        if date_str in bins:
            bins[date_str] += o.total_amount
            
    return [TimeSeriesDataPoint(date=k, value=v) for k, v in bins.items()]

@router.get("/charts/support_distribution", response_model=List[CategoryDataPoint])
def get_support_distribution(time_range: str = Query("30d"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    threshold = get_date_threshold(time_range)
    
    tickets = db.query(SupportTicket).filter(SupportTicket.created_at >= threshold).all()
    
    dist = {}
    for t in tickets:
        cat = t.category or "GENERAL_INQUIRY"
        dist[cat] = dist.get(cat, 0) + 1
        
    return [CategoryDataPoint(name=k, value=v) for k, v in dist.items()]

@router.get("/activity", response_model=List[ActivityEvent])
def get_activity_feed(limit: int = 20, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin(current_user)
    
    notifications = db.query(AdminNotification).order_by(AdminNotification.created_at.desc()).limit(limit).all()
    
    return [
        ActivityEvent(
            id=n.id,
            type=n.type,
            message=n.message,
            created_at=n.created_at,
            reference_id=n.reference_id
        ) for n in notifications
    ]
