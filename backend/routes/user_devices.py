from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database.connection import get_db
from models.domain import Device, User
from schemas.domain import DeviceClaim, DeviceResponse, FarmerDeviceResponse
from auth.security import get_current_active_user

router = APIRouter()

@router.post("/api/device/claim", response_model=DeviceResponse)
def claim_device(claim_data: DeviceClaim, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_device = db.query(Device).filter(
        Device.device_uid == claim_data.device_uid,
        Device.activation_code == claim_data.activation_code
    ).first()

    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found or invalid activation code")
    
    if db_device.owner_id is not None:
        raise HTTPException(status_code=400, detail="Device has already been claimed")

    # Claim the device
    db_device.owner_id = current_user.id
    db_device.claimed_at = datetime.utcnow()
    db_device.name = claim_data.name
    db_device.location = claim_data.location

    db.commit()
    db.refresh(db_device)
    
    return db_device

from models.domain import Farm

@router.get("/api/user/devices", response_model=List[FarmerDeviceResponse])
def get_user_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    devices = db.query(Device).filter(Device.owner_id == current_user.id).offset(skip).limit(limit).all()
    
    result = []
    for d in devices:
        # Determine connectivity status
        if d.last_heartbeat is None:
            conn_status = "UNKNOWN"
        elif (datetime.utcnow() - d.last_heartbeat).total_seconds() <= 60:
            conn_status = "ONLINE"
        else:
            conn_status = "OFFLINE"
            
        # Get farm name if farm_id exists
        farm_name = None
        if d.farm_id:
            farm = db.query(Farm).filter(Farm.id == d.farm_id).first()
            if farm:
                farm_name = farm.name
                
        result.append({
            "id": d.id,
            "device_uid": d.device_uid,
            "device_name": d.name,
            "registration_status": d.registration_status,
            "last_heartbeat": d.last_heartbeat,
            "connectivity_status": conn_status,
            "farm_name": farm_name,
            "activation_date": d.activated_at,
            "location": d.location
        })
        
    return result
