from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database.connection import get_db
from models.domain import User, Farmer, Device, Farm, Alert
from auth.security import get_current_active_user
from schemas.alerts import AlertResolveRequest, AlertSummary, AlertDetailResponse, PaginatedAlertsResponse

router = APIRouter()

def get_farmer(db: Session, current_user: User):
    farmer = db.query(Farmer).filter(
        (Farmer.email == current_user.email) | 
        (Farmer.phone == current_user.phone_number)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return farmer

def map_alert_to_response(alert: Alert) -> dict:
    data = {
        "id": alert.id,
        "farmer_id": alert.farmer_id,
        "farm_id": alert.farm_id,
        "device_id": alert.device_id,
        "title": alert.title or alert.category,
        "description": alert.description,
        "category": alert.category,
        "severity": alert.severity,
        "status": alert.status,
        "trigger_data": alert.trigger_data,
        "resolution_notes": alert.resolution_notes,
        "resolved_by": alert.resolved_by,
        "resolved_at": alert.resolved_at,
        "created_at": alert.created_at,
        "updated_at": alert.updated_at,
    }
    
    if alert.farm:
        data["farm_name"] = alert.farm.name
        data["crop_type"] = alert.farm.crop_type
        data["farm_status"] = alert.farm.status
        
    if alert.device:
        data["device_name"] = alert.device.name if hasattr(alert.device, 'name') else None
        data["device_uid"] = alert.device.device_uid
        data["connection_status"] = alert.device.connection_status if hasattr(alert.device, 'connection_status') else alert.device.status
        data["last_heartbeat"] = alert.device.last_heartbeat if hasattr(alert.device, 'last_heartbeat') else None
        
    return data

@router.get("/api/farmer/alerts/summary", response_model=AlertSummary)
def get_alerts_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    active_alerts = db.query(Alert).outerjoin(Device, Alert.device_id == Device.id).filter(
        (Alert.farmer_id == farmer.id) | (Device.farmer_id == farmer.id),
        Alert.status.in_(["UNREAD", "READ"])
    ).all()
    
    total_active = len(active_alerts)
    total_critical = sum(1 for a in active_alerts if a.severity == "CRITICAL")
    total_warning = sum(1 for a in active_alerts if a.severity == "WARNING")
    
    # Resolved in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    total_resolved = db.query(Alert).outerjoin(Device, Alert.device_id == Device.id).filter(
        (Alert.farmer_id == farmer.id) | (Device.farmer_id == farmer.id),
        Alert.status == "RESOLVED",
        Alert.resolved_at >= thirty_days_ago
    ).count()
    
    return {
        "total_active": total_active,
        "total_critical": total_critical,
        "total_warning": total_warning,
        "total_resolved": total_resolved
    }

@router.get("/api/farmer/alerts/check-offline")
def check_offline_devices(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Check for offline devices and generate connectivity alerts if missed heartbeats exceed thresholds."""
    farmer = get_farmer(db, current_user)
    devices = db.query(Device).filter(Device.farmer_id == farmer.id, Device.is_active == True).all()
    now = datetime.utcnow()
    
    alerts_created = 0
    
    for device in devices:
        if not device.last_heartbeat:
            continue
            
        minutes_since_heartbeat = (now - device.last_heartbeat).total_seconds() / 60.0
        
        severity = None
        description = None
        if minutes_since_heartbeat > 30:
            severity = "CRITICAL"
            description = f"No heartbeat received for over 30 minutes. Last seen {int(minutes_since_heartbeat)} mins ago."
        elif minutes_since_heartbeat > 10:
            severity = "WARNING"
            description = f"No heartbeat received for over 10 minutes. Last seen {int(minutes_since_heartbeat)} mins ago."
            
        if severity:
            active_alert = db.query(Alert).filter(
                Alert.device_id == device.id,
                Alert.category == "Device Connectivity Alerts",
                Alert.status.in_(["UNREAD", "READ"])
            ).first()
            
            trigger_data = json.dumps({"Last Heartbeat (mins ago)": round(minutes_since_heartbeat, 1)})
            
            if active_alert:
                if active_alert.severity != severity:
                    active_alert.severity = severity
                    active_alert.description = description
                    active_alert.trigger_data = trigger_data
                    active_alert.updated_at = now
            else:
                new_alert = Alert(
                    farmer_id=device.farmer_id,
                    farm_id=device.farm_id,
                    device_id=device.id,
                    title="Device Offline",
                    description=description,
                    category="Device Connectivity Alerts",
                    severity=severity,
                    status="UNREAD",
                    trigger_data=trigger_data,
                    created_at=now,
                    updated_at=now
                )
                db.add(new_alert)
                alerts_created += 1
                
    if alerts_created > 0:
        db.commit()
        
    return {"status": "success", "alerts_generated": alerts_created}

@router.get("/api/farmer/alerts", response_model=PaginatedAlertsResponse)
def get_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    farm_id: Optional[int] = None,
    device_id: Optional[int] = None,
    date_range: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    
    query = db.query(Alert).outerjoin(Device, Alert.device_id == Device.id).filter(
        (Alert.farmer_id == farmer.id) | (Device.farmer_id == farmer.id)
    )
    
    if severity and severity != "All":
        query = query.filter(Alert.severity == severity.upper())
    if status and status != "All":
        query = query.filter(Alert.status == status.upper())
    if farm_id and farm_id > 0:
        query = query.filter(Alert.farm_id == farm_id)
    if device_id and device_id > 0:
        query = query.filter(Alert.device_id == device_id)
        
    if date_range and date_range != "All Time":
        now = datetime.utcnow()
        if date_range == "Today":
            query = query.filter(Alert.created_at >= now.replace(hour=0, minute=0, second=0))
        elif date_range == "Last 7 Days":
            query = query.filter(Alert.created_at >= now - timedelta(days=7))
        elif date_range == "Last 30 Days":
            query = query.filter(Alert.created_at >= now - timedelta(days=30))
            
    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "alerts": [map_alert_to_response(a) for a in alerts]
    }

@router.get("/api/farmer/alerts/{alert_id}", response_model=AlertDetailResponse)
def get_alert_details(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    alert = db.query(Alert).outerjoin(Device, Alert.device_id == Device.id).filter(
        Alert.id == alert_id, 
        (Alert.farmer_id == farmer.id) | (Device.farmer_id == farmer.id)
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    return map_alert_to_response(alert)

@router.put("/api/farmer/alerts/{alert_id}/read")
def mark_alert_read(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    alert = db.query(Alert).outerjoin(Device, Alert.device_id == Device.id).filter(
        Alert.id == alert_id, 
        (Alert.farmer_id == farmer.id) | (Device.farmer_id == farmer.id)
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    if alert.status == "UNREAD":
        alert.status = "READ"
        alert.updated_at = datetime.utcnow()
        db.commit()
        
    return {"success": True, "status": alert.status}

@router.put("/api/farmer/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, resolve_data: AlertResolveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    alert = db.query(Alert).outerjoin(Device, Alert.device_id == Device.id).filter(
        Alert.id == alert_id, 
        (Alert.farmer_id == farmer.id) | (Device.farmer_id == farmer.id)
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    if alert.status == "RESOLVED":
        raise HTTPException(status_code=400, detail="Alert is already resolved")
        
    alert.status = "RESOLVED"
    alert.resolution_notes = resolve_data.resolution_notes
    alert.resolved_by = farmer.full_name
    alert.resolved_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"success": True, "status": alert.status}
