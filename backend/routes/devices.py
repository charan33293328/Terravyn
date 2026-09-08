from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List
import logging

from database.connection import get_db
from models.domain import Device, User, Farmer
from schemas.domain import DeviceCreate, DeviceUpdate, DeviceResponse, DeviceModeRequest
from auth.security import get_current_active_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/devices", tags=["devices"])

def get_user_farmer_ids(db: Session, current_user: User) -> List[int]:
    conditions = [func.lower(Farmer.email) == func.lower(current_user.email)]
    if current_user.phone_number:
        conditions.append(Farmer.phone == current_user.phone_number)
    farmers = db.query(Farmer).filter(or_(*conditions)).all()
    return [f.id for f in farmers]


@router.get("/", response_model=List[DeviceResponse])
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    devices = db.query(Device).filter(Device.owner_id == current_user.id).offset(skip).limit(limit).all()
    return devices

@router.post("/", response_model=DeviceResponse)
def create_device(device: DeviceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_device = Device(**device.model_dump(exclude={"owner_id"}), owner_id=current_user.id)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@router.put("/{device_id}", response_model=DeviceResponse)
def update_device(device_id: int, device: DeviceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_device, key, value)
    
    db.commit()
    db.refresh(db_device)
    return db_device

@router.delete("/{device_id}")
def delete_device(device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    db_device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id).first()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    db.delete(db_device)
    db.commit()
    return {"ok": True}

from pydantic import BaseModel
from datetime import datetime

class DeviceModeUpdate(BaseModel):
    irrigation_mode: str

@router.put("/{device_id}/mode", response_model=DeviceResponse)
def update_device_mode(device_id: int, mode_update: DeviceModeUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    mode = mode_update.irrigation_mode.strip().upper() if mode_update.irrigation_mode else ""
    if mode not in ["AUTO", "MANUAL"]:
        raise HTTPException(status_code=400, detail="Invalid operation mode. Must be AUTO or MANUAL.")

    farmer_ids = get_user_farmer_ids(db, current_user)
    db_device = db.query(Device).filter(
        Device.id == device_id,
        or_(Device.owner_id == current_user.id, Device.farmer_id.in_(farmer_ids))
    ).first()
    if not db_device:
        db_device = db.query(Device).filter(Device.id == device_id).first()
        if not db_device:
            raise HTTPException(status_code=404, detail="Device not found")

    device_ident = db_device.device_uid or db_device.mac_address or str(device_id)
    logger.info(f"Received irrigation mode: {mode} for device: {device_ident}")
    
    db_device.irrigation_mode = mode
    db_device.last_mode_change = datetime.utcnow()
    db.commit()
    db.refresh(db_device)
    
    from services.websocket import manager
    import asyncio
    
    # Broadcast mode change to the device via websocket if connected
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast_to_device(device_id, {
            "type": "command",
            "command": "mode",
            "mode": mode
        }))
    except Exception as e:
        logger.error(f"Failed to broadcast mode change: {e}")

    return db_device

@router.post("/mode", response_model=DeviceResponse)
def set_device_mode(payload: DeviceModeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    mode = payload.irrigation_mode.strip().upper() if payload.irrigation_mode else ""
    if mode not in ["AUTO", "MANUAL"]:
        raise HTTPException(status_code=400, detail="Invalid operation mode. Must be AUTO or MANUAL.")

    farmer_ids = get_user_farmer_ids(db, current_user)
    db_device = db.query(Device).filter(
        Device.id == payload.device_id,
        or_(Device.owner_id == current_user.id, Device.farmer_id.in_(farmer_ids))
    ).first()
    if not db_device:
        db_device = db.query(Device).filter(Device.id == payload.device_id).first()
        if not db_device:
            raise HTTPException(status_code=404, detail="Device not found or access denied")
    
    device_ident = db_device.device_uid or db_device.mac_address or str(payload.device_id)
    logger.info(f"Received irrigation mode: {mode} for device: {device_ident}")
    
    db_device.irrigation_mode = mode
    db_device.last_mode_change = datetime.utcnow()
    db.commit()
    db.refresh(db_device)
    
    from services.websocket import manager
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(manager.broadcast_to_device(payload.device_id, {
            "type": "command",
            "command": "mode",
            "mode": mode
        }))
    except Exception as e:
        pass
        
    return db_device

