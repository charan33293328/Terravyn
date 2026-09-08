import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, or_

from database.connection import get_db
from models.domain import (
    Order, User, RoleEnum, Device, Product, SupportTicket, 
    OrderAuditLog, DeviceAuditLog
)
from auth.security import get_current_active_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/admin/dashboard", tags=["admin_dashboard"])

def check_admin(current_user: User):
    if current_user.role not in [RoleEnum.admin, RoleEnum.super_admin]:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
    return current_user

@router.get("/revenue")
def get_revenue_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().date()
    start_of_today = datetime(today.year, today.month, today.day)
    start_of_week = start_of_today - timedelta(days=today.weekday())
    start_of_month = datetime(today.year, today.month, 1)
    start_of_year = datetime(today.year, 1, 1)
    
    valid_payment_statuses = ["SUCCESS", "PAID", "COD_COLLECTED"]
    
    def get_revenue(start_date):
        return db.query(func.sum(Order.total_amount)).filter(
            Order.created_at >= start_date,
            Order.payment_status.in_(valid_payment_statuses),
            Order.order_status != "CANCELLED"
        ).scalar() or 0.0

    return {
        "revenue_today": get_revenue(start_of_today),
        "revenue_this_week": get_revenue(start_of_week),
        "revenue_this_month": get_revenue(start_of_month),
        "revenue_this_year": get_revenue(start_of_year)
    }

@router.get("/orders")
def get_orders_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().date()
    start_of_today = datetime(today.year, today.month, today.day)
    
    new_orders_today = db.query(Order).filter(Order.created_at >= start_of_today).count()
    pending_orders = db.query(Order).filter(Order.order_status == "PENDING").count()
    processing_orders = db.query(Order).filter(Order.order_status == "PROCESSING").count()
    delivered_orders = db.query(Order).filter(Order.order_status == "DELIVERED").count()
    cancelled_orders = db.query(Order).filter(Order.order_status == "CANCELLED").count()
    
    return {
        "new_orders_today": new_orders_today,
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "delivered_orders": delivered_orders,
        "cancelled_orders": cancelled_orders
    }

@router.get("/products")
def get_products_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    published_products = db.query(Product).filter(Product.status == "PUBLISHED").count()
    draft_products = db.query(Product).filter(Product.status == "DRAFT").count()
    archived_products = db.query(Product).filter(Product.status == "ARCHIVED").count()
    
    # Top Selling Products (grouped by product_id)
    top_selling = db.query(
        Order.product_name,
        func.sum(Order.quantity).label("total_sold")
    ).filter(
        Order.order_status != "CANCELLED",
        Order.payment_status.in_(["SUCCESS", "PAID", "COD_COLLECTED"])
    ).group_by(Order.product_name).order_by(desc("total_sold")).limit(5).all()
    
    # Products with no sales
    sold_product_names = [item[0] for item in db.query(Order.product_name).filter(
        Order.order_status != "CANCELLED",
        Order.payment_status.in_(["SUCCESS", "PAID", "COD_COLLECTED"])
    ).distinct()]
    
    products_no_sales = db.query(Product.name).filter(
        Product.name.notin_(sold_product_names) if sold_product_names else True,
        Product.status == "PUBLISHED"
    ).limit(5).all()
    
    return {
        "published_products": published_products,
        "draft_products": draft_products,
        "archived_products": archived_products,
        "top_selling_products": [{"name": row[0], "total_sold": row[1]} for row in top_selling],
        "products_with_no_sales": [row[0] for row in products_no_sales]
    }

@router.get("/customers")
def get_customers_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    today = datetime.utcnow().date()
    start_of_month = datetime(today.year, today.month, 1)
    
    new_customers_month = db.query(User).filter(
        User.role == RoleEnum.user,
        User.created_at >= start_of_month
    ).count()
    
    active_customers = db.query(User).filter(
        User.role == RoleEnum.user,
        User.is_active == True
    ).count()
    
    customers_with_devices = db.query(Device.owner_id).filter(Device.owner_id != None).distinct().count()
    
    customers_awaiting_verification = db.query(Order.email).filter(
        Order.identity_verification_status.in_(["PENDING", "UNDER_REVIEW"])
    ).distinct().count()
    
    repeat_customers_query = db.query(Order.email).filter(
        Order.payment_status.in_(["SUCCESS", "PAID", "COD_COLLECTED"]),
        Order.order_status != "CANCELLED"
    ).group_by(Order.email).having(func.count(Order.id) > 1).count()
    
    return {
        "new_customers_this_month": new_customers_month,
        "active_customers": active_customers,
        "customers_with_devices": customers_with_devices,
        "customers_awaiting_verification": customers_awaiting_verification,
        "repeat_customers": repeat_customers_query
    }

@router.get("/devices")
def get_devices_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    registered_devices = db.query(Device).count()
    provisioned_devices = db.query(Device).filter(
        or_(Device.registration_status == "PROVISIONED", Device.provision_status == "PROVISIONED")
    ).count()
    
    assigned_devices = db.query(Device).filter(
        or_(Device.claim_status == "ASSIGNED", Device.device_status == "ASSIGNED")
    ).count()
    
    devices_awaiting_provisioning = db.query(Device).filter(
        or_(Device.registration_status == "WAITING_FOR_PROVISIONING", Device.provision_status == "NOT_PROVISIONED")
    ).count()
    
    # Online/Offline based on 5 minute threshold
    threshold = datetime.utcnow() - timedelta(minutes=5)
    online_devices = db.query(Device).filter(Device.last_heartbeat >= threshold).count()
    offline_devices = db.query(Device).filter(
        or_(Device.last_heartbeat < threshold, Device.last_heartbeat == None)
    ).count()
    
    return {
        "registered_devices": registered_devices,
        "provisioned_devices": provisioned_devices,
        "assigned_devices": assigned_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "devices_awaiting_provisioning": devices_awaiting_provisioning
    }

@router.get("/support")
def get_support_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status == "OPEN").count()
    
    high_priority_tickets = db.query(SupportTicket).filter(
        SupportTicket.status.notin_(["RESOLVED", "CLOSED"]),
        SupportTicket.priority.in_(["HIGH", "CRITICAL"])
    ).count()
    
    # We use 'WAITING_FOR_CUSTOMER' if available, otherwise just use a placeholder 0 for now
    tickets_awaiting_customer = db.query(SupportTicket).filter(SupportTicket.status == "WAITING_FOR_CUSTOMER").count()
    
    today = datetime.utcnow().date()
    start_of_today = datetime(today.year, today.month, today.day)
    resolved_tickets_today = db.query(SupportTicket).filter(
        SupportTicket.status == "RESOLVED",
        SupportTicket.updated_at >= start_of_today
    ).count()
    
    return {
        "open_tickets": open_tickets,
        "high_priority_tickets": high_priority_tickets,
        "tickets_awaiting_customer_response": tickets_awaiting_customer,
        "resolved_tickets_today": resolved_tickets_today
    }

@router.get("/verifications")
def get_verifications_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    pending_reviews = db.query(Order).filter(Order.identity_verification_status == "PENDING").count()
    approved_verifications = db.query(Order).filter(Order.identity_verification_status == "APPROVED").count()
    rejected_verifications = db.query(Order).filter(Order.identity_verification_status == "REJECTED").count()
    additional_info_requested = db.query(Order).filter(Order.identity_verification_status == "UNDER_REVIEW").count()
    
    return {
        "pending_aadhaar_reviews": pending_reviews,
        "approved_verifications": approved_verifications,
        "rejected_verifications": rejected_verifications,
        "additional_information_requested": additional_info_requested
    }

@router.get("/alerts")
def get_operational_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    alerts = []
    
    # Orders awaiting processing
    pending_orders = db.query(Order).filter(Order.order_status == "PENDING").count()
    if pending_orders > 0:
        alerts.append({
            "type": "ORDER",
            "message": f"{pending_orders} order(s) awaiting processing.",
            "link": "/admin/orders?status=PENDING"
        })
        
    # Devices offline for more than 24 hours
    threshold_24h = datetime.utcnow() - timedelta(hours=24)
    offline_24h = db.query(Device).filter(
        Device.last_heartbeat < threshold_24h,
        or_(Device.claim_status == "ASSIGNED", Device.device_status == "ASSIGNED")
    ).count()
    if offline_24h > 0:
        alerts.append({
            "type": "DEVICE",
            "message": f"{offline_24h} assigned device(s) offline for more than 24 hours.",
            "link": "/admin/devices?status=OFFLINE"
        })
        
    # High-priority support tickets
    high_priority = db.query(SupportTicket).filter(
        SupportTicket.status.notin_(["RESOLVED", "CLOSED"]),
        SupportTicket.priority.in_(["HIGH", "CRITICAL"])
    ).count()
    if high_priority > 0:
        alerts.append({
            "type": "SUPPORT",
            "message": f"{high_priority} high-priority support ticket(s) require attention.",
            "link": "/admin/support?priority=HIGH"
        })
        
    # Customers awaiting identity verification
    pending_verification = db.query(Order).filter(Order.identity_verification_status == "PENDING").count()
    if pending_verification > 0:
        alerts.append({
            "type": "VERIFICATION",
            "message": f"{pending_verification} customer(s) awaiting identity verification.",
            "link": "/admin/orders"
        })
        
    # Failed payment attempts
    today = datetime.utcnow().date()
    start_of_today = datetime(today.year, today.month, today.day)
    failed_payments = db.query(Order).filter(
        Order.payment_status == "FAILED",
        Order.created_at >= start_of_today
    ).count()
    if failed_payments > 0:
        alerts.append({
            "type": "PAYMENT",
            "message": f"{failed_payments} payment(s) failed today.",
            "link": "/admin/orders?payment_status=FAILED"
        })
        
    return alerts

@router.get("/activity")
def get_recent_activity(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    activities = []
    
    # Recent Orders
    recent_orders = db.query(Order).order_by(desc(Order.created_at)).limit(10).all()
    for o in recent_orders:
        activities.append({
            "timestamp": o.created_at.isoformat(),
            "message": f"Customer placed a new order ({o.order_id}).",
            "type": "ORDER_CREATED"
        })
        if o.identity_verified_at:
            activities.append({
                "timestamp": o.identity_verified_at.isoformat(),
                "message": f"Identity verification approved for order {o.order_id}.",
                "type": "VERIFICATION_APPROVED"
            })
            
    # Recent Device Provisioning
    recent_devices = db.query(Device).filter(Device.provisioned_at != None).order_by(desc(Device.provisioned_at)).limit(10).all()
    for d in recent_devices:
        activities.append({
            "timestamp": d.provisioned_at.isoformat(),
            "message": f"Admin provisioned a device ({d.device_uid}).",
            "type": "DEVICE_PROVISIONED"
        })
        
    # Recent Tickets
    recent_tickets = db.query(SupportTicket).order_by(desc(SupportTicket.updated_at)).limit(10).all()
    for t in recent_tickets:
        if t.status == "RESOLVED":
            activities.append({
                "timestamp": t.updated_at.isoformat(),
                "message": f"Support ticket {t.ticket_number or t.id} resolved.",
                "type": "TICKET_RESOLVED"
            })
        elif t.status == "OPEN" and t.created_at == t.updated_at:
            activities.append({
                "timestamp": t.created_at.isoformat(),
                "message": f"New support ticket {t.ticket_number or t.id} opened.",
                "type": "TICKET_CREATED"
            })
            
    # Recent Product Updates
    recent_products = db.query(Product).order_by(desc(Product.updated_at)).limit(10).all()
    for p in recent_products:
        if p.updated_at > p.created_at:
             activities.append({
                "timestamp": p.updated_at.isoformat(),
                "message": f"Product '{p.name}' was updated.",
                "type": "PRODUCT_UPDATED"
            })
            
    # Sort by timestamp desc and take top 20
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities[:20]

@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    return {
        "revenue": get_revenue_overview(db, current_user),
        "orders": get_orders_overview(db, current_user),
        "products": get_products_overview(db, current_user),
        "customers": get_customers_overview(db, current_user),
        "devices": get_devices_overview(db, current_user),
        "support": get_support_overview(db, current_user),
        "verifications": get_verifications_overview(db, current_user),
        "alerts": get_operational_alerts(db, current_user),
        "activities": get_recent_activity(db, current_user)
    }

