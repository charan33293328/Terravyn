from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from database.connection import get_db
from models.domain import SensorData, Device
from schemas.domain import SensorDataCreate, SensorDataResponse
from services.websocket import manager
from auth.security import get_current_active_user
from models.domain import User

router = APIRouter(prefix="/api/device", tags=["sensors"])

@router.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: int):
    await manager.connect(websocket, device_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from WS client for device {device_id}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket, device_id)

@router.post("/heartbeat")
async def device_heartbeat(heartbeat: dict, db: Session = Depends(get_db)):
    # The ESP32 sends {"mac_address": "...", "chip_id": "...", "rssi": ...}
    mac_address = heartbeat.get("mac_address")
    chip_id = heartbeat.get("chip_id")
    device_uid = heartbeat.get("device_uid")

    query = db.query(Device)
    if device_uid:
        device = query.filter(Device.device_uid == device_uid).first()
    elif mac_address:
        device = query.filter(Device.mac_address == mac_address).first()
    elif chip_id:
        device = query.filter(Device.chip_id == chip_id).first()
    else:
        raise HTTPException(status_code=400, detail="Missing device identifiers")

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.last_heartbeat = datetime.utcnow()
    device.status = "online"
    device.connectivity_status = "ONLINE"
    if "rssi" in heartbeat:
        device.last_rssi = heartbeat["rssi"]
        device.rssi = heartbeat["rssi"]
        
    db.commit()
    
    await manager.broadcast_to_device(device.id, {
        "type": "status_update",
        "status": "online",
        "device_id": device.id
    })
    return {"status": "ok"}

@router.post("/data", response_model=SensorDataResponse)
async def create_sensor_data(sensor_data: SensorDataCreate, db: Session = Depends(get_db)):
    # ESP32 uses device_uid to post data
    device = db.query(Device).filter(Device.device_uid == sensor_data.device_uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    data_dict = sensor_data.model_dump()
    
    db_sensor_data = SensorData(
        device_id=device.id,
        soil_moisture=data_dict["soil_moisture"],
        water_level=data_dict.get("water_level"),
        temperature=data_dict["temperature"],
        humidity=data_dict["humidity"],
        rain_status=data_dict["rain_status"],
        light_intensity=data_dict["light_intensity"],
        pump_status=data_dict["pump_status"],
        mode_status=data_dict["mode_status"],
        created_at=datetime.utcnow()
    )
    
    # Update device heartbeat and status
    device.last_heartbeat = db_sensor_data.created_at
    device.status = "online"
    device.pump_status = data_dict["pump_status"]
    device.irrigation_mode = data_dict["mode_status"]
    
    db.add(db_sensor_data)
    db.commit()
    db.refresh(db_sensor_data)
    
    # Build complete data dict for WebSocket
    ws_data = SensorDataResponse.model_validate(db_sensor_data).model_dump(mode="json")
    
    await manager.broadcast_to_device(device.id, {
        "type": "sensor_update",
        "data": ws_data
    })
    
    return db_sensor_data

@router.get("/latest", response_model=SensorDataResponse)
def get_latest_sensor_data(
    device_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    # Verify ownership
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    if current_user.role != 'admin' and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this device")

    data = db.query(SensorData).filter(SensorData.device_id == device_id).order_by(SensorData.created_at.desc()).first()
    if not data:
        raise HTTPException(status_code=404, detail="No sensor data found")
    return data

@router.get("/history", response_model=List[SensorDataResponse])
def get_sensor_data_history(
    device_id: int, 
    days: Optional[int] = Query(7, description="Number of days of history to retrieve"),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    # Verify ownership
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    if current_user.role != 'admin' and device.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this device")

    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all records for the requested period
    # For large datasets, we would typically downsample this in SQL or aggregate
    data = db.query(SensorData).filter(
        SensorData.device_id == device_id,
        SensorData.created_at >= cutoff_date
    ).order_by(SensorData.created_at.asc()).all()
    
    return data
