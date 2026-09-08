from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import io

from database.connection import get_db
from models.domain import Device, User, Farmer, Farm, RoleEnum, Alert, IrrigationLog, DeviceTelemetry
from schemas.domain import (
    DeviceResponse, FarmerDeviceResponse, DeviceRenameRequest, 
    DeviceFarmAssignmentRequest, FarmerDeviceDetailResponse
)
from auth.security import get_current_active_user

router = APIRouter()

def get_user_farmer_ids(db: Session, current_user: User) -> List[int]:
    conditions = [func.lower(Farmer.email) == func.lower(current_user.email)]
    if current_user.phone_number:
        conditions.append(Farmer.phone == current_user.phone_number)
    farmers = db.query(Farmer).filter(or_(*conditions)).all()
    return [f.id for f in farmers]

class ActivationRequest(BaseModel):
    device_uid: str
    activation_code: str
    device_name: str
    farm_id: int
    installation_location: Optional[str] = None
    installation_date: Optional[datetime] = None
    activation_method: Optional[str] = "QR" # "QR" or "MANUAL"

@router.post("/api/farmer/devices/activate")
@router.post("/api/farmer/devices/link") # alias for the new flow
def activate_device(request: ActivationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_device = db.query(Device).filter(Device.device_uid == request.device_uid).first()
    
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found.")
        
    if db_device.activation_code != request.activation_code:
        raise HTTPException(status_code=400, detail="Invalid activation code.")
        
    if db_device.owner_id is not None or db_device.status == "ACTIVE" or db_device.device_status == "ASSIGNED":
        raise HTTPException(status_code=400, detail="This device has already been linked.")
        
    if db_device.registration_status not in ["MANUFACTURED", "PROVISIONED", "READY_FOR_ACTIVATION"]:
        raise HTTPException(status_code=400, detail="Device is not ready for activation.")

    # Find or create Farmer record
    conditions = [func.lower(Farmer.email) == func.lower(current_user.email)]
    if current_user.phone_number:
        conditions.append(Farmer.phone == current_user.phone_number)
    farmer = db.query(Farmer).filter(or_(*conditions)).first()

    if not farmer:
        farmer = Farmer(
            full_name=current_user.full_name or "Unknown Farmer",
            email=current_user.email,
            phone=current_user.phone_number or "N/A",
            address="N/A"
        )
        db.add(farmer)
        db.flush() # flush to get farmer.id

    # Verify that the provided farm_id belongs to this farmer
    farm = db.query(Farm).filter(Farm.id == request.farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=400, detail="Invalid farm selected.")

    # Assign metadata
    db_device.name = request.device_name
    db_device.farm_id = request.farm_id
    db_device.location = request.installation_location
    db_device.installation_date = request.installation_date

    # Assign to farmer and user
    db_device.owner_id = current_user.id
    db_device.farmer_id = farmer.id
    db_device.activated_at = datetime.utcnow()
    db_device.activation_method = request.activation_method
    
    # Update statuses
    db_device.registration_status = "ACTIVE"
    db_device.status = "online" # Mark as online/active for dashboard
    db_device.device_status = "ASSIGNED"
    db_device.claim_status = "CLAIMED"
    db_device.claimed_at = datetime.utcnow()

    db.commit()
    db.refresh(db_device)

    return {"status": "success", "message": "Device activated successfully."}

def apply_device_filters(query, search: Optional[str] = None, connection_status: Optional[str] = None, device_status: Optional[str] = None, product_category: Optional[str] = None, farm_id: Optional[int] = None):
    if search:
        search_filter = f"%{search}%"
        query = query.join(Farm, Device.farm_id == Farm.id, isouter=True).filter(
            or_(
                Device.name.ilike(search_filter),
                Device.device_uid.ilike(search_filter),
                Farm.name.ilike(search_filter)
            )
        )
    if connection_status:
        cutoff = datetime.utcnow() - timedelta(seconds=120)
        if connection_status.upper() == "ONLINE":
            query = query.filter(
                or_(
                    and_(Device.last_heartbeat != None, Device.last_heartbeat >= cutoff),
                    and_(Device.last_seen != None, Device.last_seen >= cutoff)
                )
            )
        elif connection_status.upper() == "OFFLINE":
            query = query.filter(
                and_(
                    or_(Device.last_heartbeat == None, Device.last_heartbeat < cutoff),
                    or_(Device.last_seen == None, Device.last_seen < cutoff)
                )
            )
    if device_status and device_status.upper() != "ALL":
        query = query.filter(Device.device_status == device_status.upper())
    if product_category and product_category.upper() != "ALL":
        if product_category.upper() == "CUSTOM":
            query = query.filter(Device.product_category_name == None)
        else:
            query = query.filter(Device.product_category_name == product_category)
    if farm_id:
        query = query.filter(Device.farm_id == farm_id)
    return query

def apply_device_sorting(query, sort_by: str, sort_order: str):
    if sort_by == "name":
        order_col = Device.name
    elif sort_by == "claimed_at":
        order_col = Device.claimed_at
    elif sort_by == "last_heartbeat":
        order_col = Device.last_heartbeat
    elif sort_by == "device_status":
        order_col = Device.device_status
    elif sort_by == "farm_name":
        order_col = Device.farm_id
    else:
        order_col = Device.created_at
        
    if sort_order == "desc":
        query = query.order_by(desc(order_col))
    else:
        query = query.order_by(asc(order_col))
    return query

def _build_device_dict(d: Device, db: Session) -> dict:
    farm_name = d.farm.name if d.farm else None
    
    # Real hardware activity: latest timestamp between last_heartbeat and last_seen
    latest_ts = None
    if d.last_heartbeat and d.last_seen:
        latest_ts = max(d.last_heartbeat, d.last_seen)
    else:
        latest_ts = d.last_heartbeat or d.last_seen
        
    if latest_ts is None:
        conn_status = "OFFLINE"
    elif (datetime.utcnow() - latest_ts).total_seconds() <= 120: # 2 minutes threshold for real-time ESP32
        conn_status = "ONLINE"
    else:
        conn_status = "OFFLINE"
        
    return {
        "id": d.id,
        "device_uid": d.device_uid,
        "device_name": d.name,
        "registration_status": d.registration_status,
        "device_status": d.device_status or "UNASSIGNED",
        "product_category_name": d.product_category_name or d.custom_category,
        "firmware_version": d.firmware_version,
        "hardware_version": d.hardware_version,
        "rssi": d.last_rssi or d.rssi,
        "last_heartbeat": latest_ts,
        "connectivity_status": conn_status,
        "status": "online" if conn_status == "ONLINE" else "offline",
        "farm_id": d.farm_id,
        "farm_name": farm_name,
        "irrigation_mode": d.irrigation_mode,
        "last_mode_change": d.last_mode_change,
        "activation_date": d.activated_at,
        "location": d.location,
        "pump_status": d.pump_status,
        "chip_id": d.chip_id,
        "mac_address": d.mac_address,
        "wifi_provisioning_requested": bool(d.wifi_provisioning_requested)
    }

@router.get("/api/farmer/devices/export")
def export_farmer_devices(
    format: str = "csv",
    search: Optional[str] = None,
    connection_status: Optional[str] = None,
    device_status: Optional[str] = None,
    product_category: Optional[str] = None,
    farm_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == RoleEnum.super_admin:
        query = db.query(Device)
    else:
        farmer_ids = get_user_farmer_ids(db, current_user)
        if farmer_ids:
            query = db.query(Device).filter(
                or_(
                    Device.owner_id == current_user.id,
                    Device.farmer_id.in_(farmer_ids),
                    Device.farm.has(Farm.farmer_id.in_(farmer_ids))
                )
            )
        else:
            query = db.query(Device).filter(Device.owner_id == current_user.id)
    query = apply_device_filters(query, search, connection_status, device_status, product_category, farm_id)
    devices = query.order_by(Device.name.asc()).all()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"terravyn_devices_{timestamp}"

    headers = [
        "Device Name", "Device UID", "Product Category", "Assigned Farm",
        "Device Status", "Connection Status", "Light Status", "Last Heartbeat", "Claim Date",
        "Firmware Version", "Hardware Version"
    ]

    rows = []
    for d in devices:
        latest_ts = max(d.last_heartbeat, d.last_seen) if (d.last_heartbeat and d.last_seen) else (d.last_heartbeat or d.last_seen)
        conn_status = "OFFLINE"
        if latest_ts and (datetime.utcnow() - latest_ts).total_seconds() <= 120:
            conn_status = "ONLINE"
            
        light_status = "UNKNOWN"
        if d.last_dark_detected is not None:
            light_status = "NIGHT" if d.last_dark_detected else "DAY"

        rows.append([
            d.name or "N/A",
            d.device_uid,
            d.product_category_name or d.custom_category or "Standard",
            d.farm.name if d.farm else "Unassigned",
            d.device_status or "UNASSIGNED",
            conn_status,
            light_status,
            latest_ts.strftime("%Y-%m-%d %H:%M:%S") if latest_ts else "Never",
            d.activated_at.strftime("%Y-%m-%d %H:%M:%S") if d.activated_at else "Never",
            d.firmware_version or "N/A",
            d.hardware_version or "N/A"
        ])

    if format == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Devices"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return Response(
            content=stream.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    else:
        import csv
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
        return Response(
            content=stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )

@router.get("/api/farmer/devices")
def get_farmer_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    connection_status: Optional[str] = None,
    device_status: Optional[str] = None,
    product_category: Optional[str] = None,
    farm_id: Optional[int] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role == RoleEnum.super_admin:
        query = db.query(Device)
    else:
        farmer_ids = get_user_farmer_ids(db, current_user)
        if farmer_ids:
            query = db.query(Device).filter(
                or_(
                    Device.owner_id == current_user.id,
                    Device.farmer_id.in_(farmer_ids),
                    Device.farm.has(Farm.farmer_id.in_(farmer_ids))
                )
            )
        else:
            query = db.query(Device).filter(Device.owner_id == current_user.id)
    
    query = apply_device_filters(query, search, connection_status, device_status, product_category, farm_id)
    total_count = query.count()
    query = apply_device_sorting(query, sort_by, sort_order)
    
    devices = query.offset(skip).limit(limit).all()
    
    result = [_build_device_dict(d, db) for d in devices]
        
    return {"total": total_count, "devices": result}

@router.get("/api/farmer/devices/{device_id}", response_model=FarmerDeviceDetailResponse)
def get_farmer_device_detail(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role == RoleEnum.super_admin:
        device = db.query(Device).filter(Device.id == device_id).first()
    else:
        farmer_ids = get_user_farmer_ids(db, current_user)
        if farmer_ids:
            device = db.query(Device).filter(
                Device.id == device_id,
                or_(
                    Device.owner_id == current_user.id,
                    Device.farmer_id.in_(farmer_ids),
                    Device.farm.has(Farm.farmer_id.in_(farmer_ids))
                )
            ).first()
        else:
            device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id).first()
        
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or access denied")
        
    base_info = _build_device_dict(device, db)
    
    # Alerts
    alerts_records = db.query(Alert).filter(Alert.device_id == device.id).order_by(desc(Alert.created_at)).limit(5).all()
    alerts = [{"id": a.id, "title": a.title or a.category, "severity": a.severity, "generated_time": a.created_at} for a in alerts_records]
    
    # Telemetry Snapshot
    telemetry = None
    last_tel = db.query(DeviceTelemetry).filter(DeviceTelemetry.device_id == device.id).order_by(desc(DeviceTelemetry.recorded_at)).first()
    if last_tel:
        telemetry = {
            "soil_moisture": last_tel.soil_moisture,
            "temperature": last_tel.temperature,
            "humidity": last_tel.humidity,
            "rainfall": last_tel.rainfall,
            "rain_detected": last_tel.rain_detected,
            "pressure": last_tel.pressure,
            "pressure_trend": getattr(last_tel, "pressure_trend", None),
            "weather_prediction": getattr(last_tel, "weather_prediction", None),
            "pump_status": last_tel.pump_status,
            "obstacle_detected": last_tel.obstacle_detected,
            "recorded_at": last_tel.recorded_at
        }
        
    # Activities (Combined claim, farm, alerts)
    activities = []
    if device.claimed_at:
        activities.append({"type": "CLAIM", "description": "Device claimed and linked to your account.", "timestamp": device.claimed_at})
    if device.assigned_at and device.farm:
        activities.append({"type": "ASSIGNMENT", "description": f"Assigned to farm: {device.farm.name}", "timestamp": device.assigned_at})
        
    for a in alerts_records:
        activities.append({"type": "ALERT", "description": f"Alert generated: {a.category}", "timestamp": a.created_at})
        
    activities = sorted(activities, key=lambda x: x["timestamp"], reverse=True)[:10]
    
    return {
        **base_info,
        "mac_address": device.mac_address or "N/A",
        "chip_id": device.chip_id or "N/A",
        "crop_type": device.farm.crop_type if device.farm and hasattr(device.farm, 'crop_type') else "N/A",
        "manufacturing_date": device.manufactured_at,
        "telemetry": telemetry,
        "alerts": alerts,
        "activities": activities
    }

@router.put("/api/farmer/devices/{device_id}/rename")
def rename_device(device_id: int, payload: DeviceRenameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role == RoleEnum.super_admin:
        device = db.query(Device).filter(Device.id == device_id).first()
    else:
        farmer_ids = get_user_farmer_ids(db, current_user)
        conditions = [Device.owner_id == current_user.id]
        if farmer_ids:
            conditions.append(Device.farmer_id.in_(farmer_ids))
            conditions.append(Device.farm.has(Farm.farmer_id.in_(farmer_ids)))
        device = db.query(Device).filter(Device.id == device_id, or_(*conditions)).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    device.name = payload.device_name[:50]
    db.commit()
    return {"status": "success", "message": "Device renamed successfully"}

@router.put("/api/farmer/devices/{device_id}/farm")
def assign_device_farm(device_id: int, payload: DeviceFarmAssignmentRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.role == RoleEnum.super_admin:
        device = db.query(Device).filter(Device.id == device_id).first()
    else:
        farmer_ids = get_user_farmer_ids(db, current_user)
        conditions = [Device.owner_id == current_user.id]
        if farmer_ids:
            conditions.append(Device.farmer_id.in_(farmer_ids))
            conditions.append(Device.farm.has(Farm.farmer_id.in_(farmer_ids)))
        device = db.query(Device).filter(Device.id == device_id, or_(*conditions)).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    if payload.farm_id is not None:
        farmer_ids = get_user_farmer_ids(db, current_user)
        farm = db.query(Farm).filter(Farm.id == payload.farm_id, Farm.farmer_id.in_(farmer_ids)).first()
        if not farm and current_user.role != RoleEnum.super_admin:
            raise HTTPException(status_code=403, detail="Invalid farm selection")
            
    device.farm_id = payload.farm_id
    device.assigned_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Device assigned to farm successfully"}

@router.post("/api/farmer/devices/{device_id}/wifi-provisioning")
@router.post("/api/devices/{device_id}/wifi-provisioning")
def request_wifi_provisioning(
    device_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    """
    Triggers remote Wi-Fi provisioning for a specific device.
    Zero-credential security rule:
    Never receives, asks for, transmits, logs, or stores Wi-Fi SSID or password.
    Only sets the one-time provisioning flag for the ESP32.
    """
    if current_user.role == RoleEnum.super_admin:
        device = db.query(Device).filter(Device.id == device_id).first()
    else:
        farmer_ids = get_user_farmer_ids(db, current_user)
        if farmer_ids:
            device = db.query(Device).filter(
                Device.id == device_id,
                or_(
                    Device.owner_id == current_user.id,
                    Device.farmer_id.in_(farmer_ids),
                    Device.farm.has(Farm.farmer_id.in_(farmer_ids))
                )
            ).first()
        else:
            device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found or access denied")

    # Verify device is connected with the website (heartbeat or telemetry within 2 minutes)
    cutoff = datetime.utcnow() - timedelta(seconds=120)
    latest_ts = None
    if device.last_heartbeat and device.last_seen:
        latest_ts = max(device.last_heartbeat, device.last_seen)
    else:
        latest_ts = device.last_heartbeat or device.last_seen

    is_connected = (latest_ts is not None and latest_ts >= cutoff)
    if not is_connected:
        raise HTTPException(
            status_code=400, 
            detail="Device is currently offline. The device must be connected to the website to change Wi-Fi."
        )

    device.wifi_provisioning_requested = True
    db.commit()

    # Determine AP name: ESP32 creates TERRAVYN-XXXXXX
    ap_name = "TERRAVYN-XXXXXX"
    if device.chip_id and device.chip_id not in ("N/A", "UNKNOWN", ""):
        clean_chip = device.chip_id.replace(":", "").replace("-", "").upper()
        suffix = clean_chip[-6:] if len(clean_chip) >= 6 else clean_chip
        ap_name = f"TERRAVYN-{suffix}"
    elif device.mac_address and device.mac_address not in ("N/A", "UNKNOWN", ""):
        clean_mac = device.mac_address.replace(":", "").replace("-", "").upper()
        suffix = clean_mac[-6:] if len(clean_mac) >= 6 else clean_mac
        ap_name = f"TERRAVYN-{suffix}"

    return {
        "status": "success",
        "message": "Wi-Fi setup initiated. Device marked for provisioning.",
        "wifi_provisioning_requested": True,
        "ap_name": ap_name
    }
