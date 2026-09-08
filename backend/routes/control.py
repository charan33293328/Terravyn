from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from models.domain import IrrigationLog, Device, User
from schemas.domain import PumpControl, ModeControl
from services.websocket import manager
from auth.security import get_current_active_user

router = APIRouter(prefix="/api", tags=["control"])

@router.post("/pump/control")
async def control_pump(control: PumpControl, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    device = db.query(Device).filter(Device.id == control.device_id, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.pump_status = (control.action == "on")
    log = IrrigationLog(
        device_id=device.id,
        action=f"pump_{control.action}",
        triggered_by="user"
    )
    db.add(log)
    db.commit()
    
    await manager.broadcast_to_device(control.device_id, {
        "type": "command",
        "command": "pump",
        "action": control.action
    })
    return {"status": "success", "action": control.action, "device_id": control.device_id}

import logging
from sqlalchemy import or_, func
from models.domain import Farmer

logger = logging.getLogger("uvicorn.error")

@router.post("/mode/control")
async def control_mode(control: ModeControl, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    mode = control.mode.strip().upper() if control.mode else ""
    if mode not in ["AUTO", "MANUAL"]:
        raise HTTPException(status_code=400, detail="Invalid operation mode. Must be AUTO or MANUAL.")

    conditions = [func.lower(Farmer.email) == func.lower(current_user.email)]
    if current_user.phone_number:
        conditions.append(Farmer.phone == current_user.phone_number)
    farmer_ids = [f.id for f in db.query(Farmer).filter(or_(*conditions)).all()]

    device = db.query(Device).filter(
        Device.id == control.device_id,
        or_(Device.owner_id == current_user.id, Device.farmer_id.in_(farmer_ids))
    ).first()
    if not device:
        device = db.query(Device).filter(Device.id == control.device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
    device_ident = device.device_uid or device.mac_address or str(control.device_id)
    logger.info(f"Received irrigation mode: {mode} for device: {device_ident}")

    device.irrigation_mode = mode
    device.last_mode_change = datetime.utcnow()
    log = IrrigationLog(
        device_id=device.id,
        action=f"mode_{mode}",
        triggered_by="user"
    )
    db.add(log)
    db.commit()
    
    await manager.broadcast_to_device(control.device_id, {
        "type": "command",
        "command": "mode",
        "mode": mode
    })
    return {
        "status": "success",
        "mode": mode,
        "irrigation_mode": mode,
        "device_id": control.device_id
    }

