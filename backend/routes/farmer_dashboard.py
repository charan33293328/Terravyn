from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from datetime import datetime, timedelta
from database.connection import get_db
from models.domain import User, Farmer, Device, DeviceTelemetry, Farm, Alert, Order, SupportTicket
from auth.security import get_current_active_user

router = APIRouter()

def get_farmer(db: Session, current_user: User):
    conditions = [func.lower(Farmer.email) == func.lower(current_user.email)]
    if current_user.phone_number:
        conditions.append(Farmer.phone == current_user.phone_number)
    farmer = db.query(Farmer).filter(or_(*conditions)).first()
    if not farmer:
        farmer = Farmer(
            full_name=current_user.full_name or "Farmer",
            email=current_user.email,
            phone=current_user.phone_number or "N/A",
            address="N/A"
        )
        db.add(farmer)
        db.commit()
        db.refresh(farmer)
    return farmer

@router.get("/api/farmer/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    # Total Devices
    total_devices = db.query(Device).filter(or_(Device.farmer_id == farmer.id, Device.owner_id == current_user.id)).count()
    
    # Online/Offline Devices (threshold 5 minutes)
    five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
    
    devices = db.query(Device).filter(or_(Device.farmer_id == farmer.id, Device.owner_id == current_user.id)).all()
    online_devices = 0
    offline_devices = 0
    for device in devices:
        if device.last_heartbeat and (datetime.utcnow() - device.last_heartbeat).total_seconds() <= 60:
            online_devices += 1
        else:
            offline_devices += 1
            
    # Total Farms
    total_farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).count()
    
    # Active Alerts
    active_alerts = db.query(Alert).join(Device).filter(
        or_(Device.farmer_id == farmer.id, Device.owner_id == current_user.id),
        Alert.status.in_(["UNREAD", "READ"])
    ).count()
    
    # Pending Orders
    pending_orders = db.query(Order).filter(
        Order.email == current_user.email,
        Order.order_status.in_(["PENDING", "PROCESSING", "SHIPPED", "OUT_FOR_DELIVERY"])
    ).count()

    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "total_farms": total_farms,
        "active_alerts": active_alerts,
        "pending_orders": pending_orders
    }

@router.get("/api/farmer/dashboard/devices")
def get_dashboard_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    five_mins_ago = datetime.utcnow() - timedelta(minutes=5)
    
    devices = db.query(Device).filter(
        or_(Device.farmer_id == farmer.id, Device.owner_id == current_user.id)
    ).order_by(Device.created_at.desc()).limit(5).all()
    result = []
    for device in devices:
        farm_name = device.farm.name if device.farm else "Unassigned"
        
        if device.is_active is False:
            status = "Maintenance"
        else:
            if device.last_heartbeat and (datetime.utcnow() - device.last_heartbeat).total_seconds() <= 60:
                status = "Online"
            else:
                status = "Offline"
            
        result.append({
            "id": device.id,
            "device_name": device.name,
            "device_uid": device.device_uid,
            "farm_name": farm_name,
            "connection_status": status,
            "last_seen": device.last_heartbeat,
            "irrigation_mode": device.irrigation_mode,
            "last_mode_change": device.last_mode_change
        })
    return result

@router.get("/api/farmer/dashboard/farms")
def get_dashboard_farms(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).order_by(Farm.created_at.desc()).limit(3).all()
    result = []
    for farm in farms:
        device_count = db.query(Device).filter(Device.farm_id == farm.id).count()
        result.append({
            "id": farm.id,
            "name": farm.name,
            "crop_type": getattr(farm, 'crop_type', 'N/A'),
            "area": getattr(farm, 'area', 'N/A'),
            "number_of_devices": device_count
        })
    return result

@router.get("/api/farmer/dashboard/alerts")
def get_dashboard_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    alerts = db.query(Alert).join(Device).filter(
        or_(Device.farmer_id == farmer.id, Device.owner_id == current_user.id),
        Alert.status.in_(["UNREAD", "READ"])
    ).order_by(Alert.created_at.desc()).limit(5).all()
    
    result = []
    for alert in alerts:
        result.append({
            "id": alert.id,
            "title": alert.title or alert.category,
            "severity": alert.severity,
            "device_name": alert.device.name if alert.device else "Unknown Device",
            "generated_time": alert.created_at
        })
    return result

@router.get("/api/farmer/dashboard/activities")
def get_dashboard_activities(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    activities = []
    
    # 1. Devices claimed
    devices = db.query(Device).filter(Device.farmer_id == farmer.id).order_by(Device.created_at.desc()).limit(10).all()
    for d in devices:
        activities.append({"description": f"Device Claimed: {d.name or d.device_uid}", "timestamp": d.created_at, "type": "device"})
        
    # 2. Farms created
    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).order_by(Farm.created_at.desc()).limit(10).all()
    for f in farms:
        activities.append({"description": f"Farm Created: {f.name}", "timestamp": f.created_at, "type": "farm"})
        
    # 3. Orders placed
    orders = db.query(Order).filter(Order.email == current_user.email).order_by(Order.id.desc()).limit(10).all()
    for o in orders:
        activities.append({"description": f"Order Placed: {o.order_id}", "timestamp": getattr(o, 'created_at', None) or datetime.utcnow(), "type": "order"})
        
    # 4. Support Tickets
    tickets = db.query(SupportTicket).filter(SupportTicket.customer_id == current_user.id).order_by(SupportTicket.created_at.desc()).limit(10).all()
    for t in tickets:
        activities.append({"description": f"Support Ticket Created: {t.subject}", "timestamp": t.created_at, "type": "support"})
        
    # Filter out missing timestamps
    activities = [a for a in activities if a["timestamp"] is not None]
    
    # Sort and take latest 10
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:10]
