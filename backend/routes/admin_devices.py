from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from typing import List, Optional
import qrcode
import os
import random
import string
from datetime import datetime
from database.connection import get_db
from models.domain import Device, User, Farmer, DeviceAuditLog
from auth.rbac import require_admin_role, require_super_admin_role
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin/devices", tags=["Admin Devices"])

# -----------------
# Pydantic Schemas
# -----------------
class DeviceResponse(BaseModel):
    id: int
    device_uid: Optional[str] = None
    activation_code: Optional[str] = None
    mac_address: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    device_status: str
    provision_status: str
    owner_id: Optional[int] = None
    farmer_id: Optional[int] = None
    claim_status: Optional[str] = None
    is_active: Optional[bool] = None
    assigned_at: Optional[datetime] = None
    qr_code_path: Optional[str] = None
    product_category_name: Optional[str] = None
    custom_category: Optional[str] = None
    manufactured_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class DeviceCreate(BaseModel):
    mac_address: Optional[str] = None

class DeviceAssign(BaseModel):
    farmer_id: int

class DeviceStatusUpdate(BaseModel):
    device_status: str

class FirmwareUpdate(BaseModel):
    firmware_version: str

class DeviceManufactureReq(BaseModel):
    mac_address: str
    chip_id: str
    product_category_id: int
    product_category_name: str
    custom_category: Optional[str] = None
    device_name: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    manufacturing_notes: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    is_active: bool


# -----------------
# Helper Functions
# -----------------
def generate_activation_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_device_uid():
    date_str = datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"TRV-DEV-{date_str}-{random_str}"

def log_audit(db: Session, device_uid: str, admin_id: int, action: str, old_value: str = None, new_value: str = None):
    log = DeviceAuditLog(
        device_uid=device_uid,
        admin_id=admin_id,
        action=action,
        old_value=old_value,
        new_value=new_value
    )
    db.add(log)
    db.commit()

# -----------------
# Endpoints
# -----------------

@router.get("/", response_model=dict)
def get_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    device_status: Optional[str] = None,
    provision_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    query = db.query(Device)
    
    if search:
        query = query.outerjoin(User, Device.owner_id == User.id).filter(
            or_(
                Device.device_uid.ilike(f"%{search}%"),
                Device.activation_code.ilike(f"%{search}%"),
                Device.mac_address.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )
        
    if device_status:
        query = query.filter(Device.device_status == device_status)
    if provision_status:
        query = query.filter(Device.provision_status == provision_status)
        
    total = query.count()
    devices = query.options(
        joinedload(Device.owner),
        joinedload(Device.farmer)
    ).order_by(desc(Device.created_at)).offset(skip).limit(limit).all()
    
    # We include owner details in response
    results = []
    for d in devices:
        owner_name = d.owner.full_name if d.owner else None
        owner_email = d.owner.email if d.owner else None
        farmer_name = d.farmer.full_name if d.farmer else None
        farmer_phone = d.farmer.phone if d.farmer else None
        results.append({
            "id": d.id,
            "device_uid": d.device_uid,
            "activation_code": d.activation_code,
            "mac_address": d.mac_address,
            "firmware_version": d.firmware_version,
            "hardware_version": d.hardware_version,
            "device_status": d.device_status,
            "provision_status": d.provision_status,
            "owner_id": d.owner_id,
            "owner_name": owner_name,
            "owner_email": owner_email,
            "farmer_id": d.farmer_id,
            "farmer_name": farmer_name,
            "farmer_phone": farmer_phone,
            "claim_status": d.claim_status,
            "is_active": d.is_active,
            "assigned_at": d.assigned_at,
            "qr_code_path": d.qr_code_path,
            "product_category_name": d.product_category_name,
            "custom_category": d.custom_category,
            "manufactured_at": d.manufactured_at,
            "registration_status": d.registration_status,
            "nvs_written": d.nvs_written,
            "last_heartbeat": d.last_heartbeat,
            "chip_id": d.chip_id,
            "created_at": d.created_at
        })
        
    return {
        "items": results,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit
    }

import secrets

from models.domain import ProductCategory

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    categories = db.query(ProductCategory).filter(ProductCategory.is_active == True).all()
    return [{"id": c.id, "name": c.name, "is_active": c.is_active} for c in categories]

@router.post("/manufacture", response_model=DeviceResponse)
def manufacture_device(
    payload: DeviceManufactureReq,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    # Validations
    if db.query(Device).filter(Device.mac_address == payload.mac_address).first():
        raise HTTPException(status_code=400, detail="MAC Address already registered.")
        
    if db.query(Device).filter(Device.chip_id == payload.chip_id).first():
        raise HTTPException(status_code=400, detail="Chip ID already registered.")
        
    # Generate Identity
    device_uid = generate_device_uid()
    activation_code = generate_activation_code()
    secret_code = secrets.token_hex(16)
    
    # Create Device
    new_device = Device(
        mac_address=payload.mac_address.upper(),
        chip_id=payload.chip_id,
        device_uid=device_uid,
        activation_code=activation_code,
        secret_code=secret_code,
        name=payload.device_name,
        product_category_id=payload.product_category_id,
        product_category_name=payload.product_category_name,
        custom_category=payload.custom_category,
        firmware_version=payload.firmware_version,
        hardware_version=payload.hardware_version,
        manufacturing_notes=payload.manufacturing_notes,
        manufactured_at=datetime.utcnow(),
        device_status="READY_FOR_SALE",
        provision_status="PROVISIONED",
        registration_status="MANUFACTURED"
    )
    
    db.add(new_device)
    db.flush()
    
    # Generate QR Code
    qr_data = f"UID:{device_uid}|CODE:{activation_code}"
    qr = qrcode.make(qr_data)
    
    qr_filename = f"{device_uid}.png"
    qr_dir = os.path.join("uploads", "qrcodes")
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = os.path.join(qr_dir, qr_filename)
    qr.save(qr_path)
    
    new_device.qr_code_path = f"/uploads/qrcodes/{qr_filename}"
    db.commit()
    db.refresh(new_device)
    
    log_audit(db, device_uid, current_admin.id, "Device Manufactured", new_value=f"MAC: {new_device.mac_address}")
    
    return new_device

@router.get("/{device_uid}")
def get_device_details(
    device_uid: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    audit_logs = db.query(DeviceAuditLog).filter(DeviceAuditLog.device_uid == device_uid).order_by(desc(DeviceAuditLog.created_at)).all()
    
    # fetch admin names for logs
    log_data = []
    for log in audit_logs:
        admin = db.query(User).filter(User.id == log.admin_id).first()
        log_data.append({
            "action": log.action,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "created_at": log.created_at,
            "admin_name": admin.full_name if admin else "System"
        })
        
    owner = db.query(User).filter(User.id == device.owner_id).first() if device.owner_id else None
    farmer = db.query(Farmer).filter(Farmer.id == device.farmer_id).first() if device.farmer_id else None
        
    return {
        "device": {
            "id": device.id,
            "device_uid": device.device_uid,
            "activation_code": device.activation_code,
            "secret_code": device.secret_code,
            "mac_address": device.mac_address,
            "firmware_version": device.firmware_version,
            "hardware_version": device.hardware_version,
            "device_status": device.device_status,
            "provision_status": device.provision_status,
            "claim_status": device.claim_status,
            "is_active": device.is_active,
            "registration_status": device.registration_status,
            "last_heartbeat": device.last_heartbeat,
            "last_seen": device.last_seen,
            "last_rssi": device.last_rssi,
            "last_temperature": device.last_temperature,
            "last_humidity": device.last_humidity,
            "last_soil_moisture": device.last_soil_moisture,
            "provisioned_at": device.provisioned_at,
            "assigned_at": device.assigned_at,
            "product_category_name": device.product_category_name,
            "custom_category": device.custom_category,
            "manufactured_at": device.manufactured_at,
            "manufacturing_notes": device.manufacturing_notes,
            "owner": {"id": owner.id, "name": owner.full_name, "email": owner.email} if owner else None,
            "farmer": {"id": farmer.id, "name": farmer.full_name, "phone": farmer.phone, "email": farmer.email} if farmer else None,
            "qr_code_path": device.qr_code_path,
            "created_at": device.created_at,
            "updated_at": device.updated_at
        },
        "timeline": log_data
    }

@router.put("/{device_uid}/assign")
def assign_device(
    device_uid: str,
    payload: DeviceAssign,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    farmer = db.query(Farmer).filter(Farmer.id == payload.farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
        
    old_farmer = device.farmer_id
    device.farmer_id = farmer.id
    device.assigned_at = datetime.utcnow()
    device.claim_status = "ASSIGNED"
    device.device_status = "ASSIGNED"
    db.commit()
    
    log_audit(db, device_uid, current_admin.id, "Assigned to Farmer", old_value=str(old_farmer), new_value=str(farmer.id))
    return {"status": "success", "message": "Device assigned"}

@router.put("/{device_uid}/disable")
def disable_device(
    device_uid: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    device.is_active = False
    db.commit()
    
    log_audit(db, device_uid, current_admin.id, "Device Disabled", old_value="True", new_value="False")
    return {"status": "success", "message": "Device disabled"}

@router.put("/{device_uid}/activate")
def activate_device(
    device_uid: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    device.is_active = True
    db.commit()
    
    log_audit(db, device_uid, current_admin.id, "Device Activated", old_value="False", new_value="True")
    return {"status": "success", "message": "Device activated"}

@router.put("/{device_uid}/status")
def update_device_status(
    device_uid: str,
    payload: DeviceStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    old_status = device.device_status
    device.device_status = payload.device_status
    db.commit()
    
    log_audit(db, device_uid, current_admin.id, "Status Updated", old_value=old_status, new_value=payload.device_status)
    return {"status": "success", "message": "Status updated"}

@router.put("/{device_uid}/firmware")
def update_device_firmware(
    device_uid: str,
    payload: FirmwareUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    old_fw = device.firmware_version
    device.firmware_version = payload.firmware_version
    db.commit()
    
    log_audit(db, device_uid, current_admin.id, "Firmware Updated", old_value=old_fw, new_value=payload.firmware_version)
    return {"status": "success", "message": "Firmware updated"}

from fastapi.responses import FileResponse
import logging

logger = logging.getLogger(__name__)

@router.delete("/{identifier}")
def delete_device(
    identifier: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_super_admin_role)  # SUPER ADMIN ONLY
):
    device = db.query(Device).filter(Device.device_uid == identifier).first()
    if not device:
        device = db.query(Device).filter(Device.mac_address == identifier).first()
        
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    db.delete(device)
    db.commit()
    return {"status": "success", "message": "Device deleted"}

@router.get("/{device_uid}/download-qr")
def download_qr(
    device_uid: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    logger.info(f"QR Download Requested for UID: {device_uid}")
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")
        
    db_path = device.qr_code_path
    logger.info(f"QR Path from Database: {db_path}")
    
    # We resolve the absolute path based on the working directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # If the path starts with a slash like "/uploads/...", remove the slash
    relative_path = db_path.lstrip('/') if db_path else None
    
    resolved_path = os.path.join(base_dir, relative_path) if relative_path else None
    logger.info(f"Resolved Absolute Path: {resolved_path}")
    
    file_exists = os.path.exists(resolved_path) if resolved_path else False
    logger.info(f"File Exists Status: {file_exists}")
    
    if not db_path or not file_exists:
        logger.info("QR file missing or NULL. Regenerating...")
        try:
            qr_data = f"UID:{device_uid}|CODE:{device.activation_code}"
            qr = qrcode.make(qr_data)
            
            qr_filename = f"{device_uid}.png"
            qr_dir = os.path.join(base_dir, "uploads", "qrcodes")
            os.makedirs(qr_dir, exist_ok=True)
            
            new_resolved_path = os.path.join(qr_dir, qr_filename)
            qr.save(new_resolved_path)
            
            device.qr_code_path = f"/uploads/qrcodes/{qr_filename}"
            db.commit()
            
            resolved_path = new_resolved_path
            logger.info("QR code successfully regenerated and saved.")
        except Exception as e:
            logger.error(f"Error regenerating QR code: {str(e)}")
            raise HTTPException(status_code=500, detail="Unable to generate QR code.")
            
    # Audit log
    log_audit(db, device_uid, current_admin.id, "QR Download")
            
    return FileResponse(
        path=resolved_path,
        media_type="image/png",
        filename=f"{device_uid}.png",
        headers={"Content-Disposition": f"attachment; filename={device_uid}.png"}
    )
