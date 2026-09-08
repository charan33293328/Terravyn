from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import List, Optional
from datetime import datetime, timedelta

from database.connection import get_db
from models.domain import User, Farmer, Device, DeviceTelemetry, Alert, Farm
from schemas.monitoring import (
    MonitoringSummaryResponse, TelemetrySnapshot, 
    TelemetryHistoryResponse, ChartDataResponse, ChartDataPoint
)
from auth.security import get_current_active_user

router = APIRouter()

from sqlalchemy import or_, func

def get_farmer_from_user(db: Session, user: User) -> Farmer:
    conditions = [func.lower(Farmer.email) == func.lower(user.email)]
    if user.phone_number:
        conditions.append(Farmer.phone == user.phone_number)
    return db.query(Farmer).filter(or_(*conditions)).first()

def get_accessible_device_filter(farmer: Farmer, user: User):
    if farmer:
        return or_(
            Device.owner_id == user.id,
            Device.farmer_id == farmer.id,
            Device.farm.has(Farm.farmer_id == farmer.id)
        )
    return Device.owner_id == user.id

def getLightStatus(dark_detected: bool) -> str:
    if dark_detected is None:
        return "UNKNOWN"
    return "NIGHT" if dark_detected else "DAY"

def clean_sensor_health(sensor_health: Optional[dict]) -> Optional[dict]:
    if not sensor_health or not isinstance(sensor_health, dict):
        return sensor_health
    return {k: v for k, v in sensor_health.items() if k not in ("water", "ultrasonic")}

def get_tank_status(water_level: Optional[int], sensor_health: Optional[dict]) -> Optional[str]:
    return None

def get_time_range_filter(time_range: str) -> datetime:
    now = datetime.utcnow()
    if time_range == "Last 1 Hour":
        return now - timedelta(hours=1)
    elif time_range == "Last 6 Hours":
        return now - timedelta(hours=6)
    elif time_range == "Last 24 Hours":
        return now - timedelta(days=1)
    elif time_range == "Last 7 Days":
        return now - timedelta(days=7)
    elif time_range == "Last 30 Days":
        return now - timedelta(days=30)
    return now - timedelta(days=1) # Default Last 24 Hours

@router.get("/api/farmer/monitoring/summary", response_model=MonitoringSummaryResponse)
def get_monitoring_summary(
    farm_id: Optional[int] = None,
    device_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    dev_query = db.query(Device).filter(get_accessible_device_filter(farmer, current_user))
    if farm_id and farm_id != 0:
        dev_query = dev_query.filter(Device.farm_id == farm_id)
    if device_id and device_id != 0:
        dev_query = dev_query.filter(Device.id == device_id)
        
    devices = dev_query.all()
    device_ids = [d.id for d in devices]
    
    total_devices = len(device_ids)
    online_devices = sum(1 for d in devices if (d.status and d.status.upper() == "ONLINE"))
    
    # Active alerts
    alert_query = db.query(Alert).filter(Alert.device_id.in_(device_ids), Alert.status.in_(["UNREAD", "READ"]))
    active_alerts = alert_query.count() if device_ids else 0
    
    # Averages
    avg_soil = None
    avg_temp = None
    
    if device_ids:
        # Get latest telemetry for each device to calculate average
        subq = db.query(
            DeviceTelemetry.device_id,
            func.max(DeviceTelemetry.recorded_at).label("max_date")
        ).filter(DeviceTelemetry.device_id.in_(device_ids)).group_by(DeviceTelemetry.device_id).subquery()
        
        latest_tel = db.query(DeviceTelemetry).join(
            subq, 
            (DeviceTelemetry.device_id == subq.c.device_id) & 
            (DeviceTelemetry.recorded_at == subq.c.max_date)
        ).all()
        
        soil_values = [t.soil_moisture for t in latest_tel if t.soil_moisture is not None]
        temp_values = [t.temperature for t in latest_tel if t.temperature is not None]
        
        if soil_values:
            avg_soil = round(sum(soil_values) / len(soil_values), 1)
        if temp_values:
            avg_temp = round(sum(temp_values) / len(temp_values), 1)

    return MonitoringSummaryResponse(
        total_devices=total_devices,
        online_devices=online_devices,
        avg_soil_moisture=avg_soil,
        avg_temperature=avg_temp,
        active_alerts=active_alerts
    )

@router.get("/api/farmer/monitoring/latest", response_model=List[TelemetrySnapshot])
def get_monitoring_latest(
    farm_id: Optional[int] = None,
    device_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    dev_query = db.query(Device).filter(get_accessible_device_filter(farmer, current_user))
    if farm_id and farm_id != 0:
        dev_query = dev_query.filter(Device.farm_id == farm_id)
    if device_id and device_id != 0:
        dev_query = dev_query.filter(Device.id == device_id)
        
    devices = dev_query.all()
    device_ids = [d.id for d in devices]
    if not device_ids:
        return []

    subq = db.query(
        DeviceTelemetry.device_id,
        func.max(DeviceTelemetry.recorded_at).label("max_date")
    ).filter(DeviceTelemetry.device_id.in_(device_ids)).group_by(DeviceTelemetry.device_id).subquery()
    
    latest_tel = db.query(DeviceTelemetry).join(
        subq, 
        (DeviceTelemetry.device_id == subq.c.device_id) & 
        (DeviceTelemetry.recorded_at == subq.c.max_date)
    ).all()
    
    tel_dict = {t.device_id: t for t in latest_tel}
    
    result = []
    for d in devices:
        t = tel_dict.get(d.id)
        farm_name = d.farm.name if d.farm else None
        
        result.append(TelemetrySnapshot(
            device_id=d.id,
            device_name=d.name or "Unnamed Device",
            device_uid=d.device_uid,
            farm_name=farm_name,
            soil_moisture=t.soil_moisture if t and t.soil_moisture is not None else d.last_soil_moisture,
            temperature=t.temperature if t and t.temperature is not None else d.last_temperature,
            humidity=t.humidity if t and t.humidity is not None else d.last_humidity,
            rain_detected=t.rain_detected if t and t.rain_detected is not None else d.last_rain_detected,
            water_level=t.water_level if t else None,
            pressure=t.pressure if t and t.pressure is not None else d.last_pressure,
            pressure_trend=getattr(t, 'pressure_trend', None) if t else getattr(d, 'last_pressure_trend', None),
            bmp_temperature=t.bmp_temperature if t and t.bmp_temperature is not None else d.last_bmp_temperature,
            pump_status=t.pump_status if t else None,
            signal_quality=t.signal_quality if t and t.signal_quality is not None else d.last_signal_quality,
            weather_prediction=t.weather_prediction if t and t.weather_prediction is not None else d.last_weather_prediction,
            dark_detected=t.dark_detected if t and t.dark_detected is not None else d.last_dark_detected,
            light_status=getLightStatus(t.dark_detected if t and t.dark_detected is not None else d.last_dark_detected),
            obstacle_detected=t.obstacle_detected if t and t.obstacle_detected is not None else d.last_obstacle_detected,
            sensor_health=clean_sensor_health(t.sensor_health if t and t.sensor_health is not None else d.sensor_health),
            ultrasonic_distance=None,
            ultrasonic_water_level=None,
            tank_status=None,
            recorded_at=t.recorded_at if t else d.last_heartbeat,
            connection_status=d.status,
            irrigation_mode=d.irrigation_mode,
            last_mode_change=d.last_mode_change
        ))
        
    return result

@router.get("/api/farmer/monitoring/history", response_model=TelemetryHistoryResponse)
def get_monitoring_history(
    farm_id: Optional[int] = None,
    device_id: Optional[int] = None,
    time_range: str = "Last 24 Hours",
    page: int = 1,
    page_size: int = 25,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    query = db.query(DeviceTelemetry).join(Device, DeviceTelemetry.device_id == Device.id)
    query = query.filter(get_accessible_device_filter(farmer, current_user))
    
    if farm_id and farm_id != 0:
        query = query.filter(Device.farm_id == farm_id)
    if device_id and device_id != 0:
        query = query.filter(DeviceTelemetry.device_id == device_id)
        
    if time_range != "Custom Range":
        cutoff = get_time_range_filter(time_range)
        query = query.filter(DeviceTelemetry.recorded_at >= cutoff)
        
    total = query.count()
    records = query.order_by(desc(DeviceTelemetry.recorded_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    items = []
    for r in records:
        items.append({
            "timestamp": r.recorded_at.isoformat(),
            "device": r.device.name or r.device.device_uid,
            "farm": r.device.farm.name if r.device.farm else "N/A",
            "soil_moisture": r.soil_moisture,
            "temperature": r.temperature,
            "humidity": r.humidity,
            "rain_detected": r.rain_detected,
            "water_level": None,
            "pressure": r.pressure,
            "pressure_trend": getattr(r, 'pressure_trend', None),
            "bmp_temperature": r.bmp_temperature,
            "altitude": r.altitude,
            "weather_prediction": r.weather_prediction,
            "signal_quality": r.signal_quality,
            "operation_mode": r.operation_mode,
            "pump_status": r.pump_status,
            "dark_detected": r.dark_detected,
            "light_status": getLightStatus(r.dark_detected),
            "obstacle_detected": r.obstacle_detected,
            "sensor_health": clean_sensor_health(r.sensor_health),
            "ultrasonic_distance": None,
            "ultrasonic_water_level": None,
            "tank_status": None,
            "firmware_version": r.firmware_version,
            "rssi": r.rssi
        })
        
    return TelemetryHistoryResponse(
        items=items,
        total=total,
        page=page,
        pages=(total + page_size - 1) // page_size
    )

@router.get("/api/farmer/monitoring/charts", response_model=List[ChartDataResponse])
def get_monitoring_charts(
    farm_id: Optional[int] = None,
    device_id: Optional[int] = None,
    time_range: str = "Last 24 Hours",
    metrics: str = "temperature,soil_moisture,humidity,rain_detected,bmp_temperature,pressure,altitude,rssi,dark_detected,obstacle_detected",
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    from datetime import timedelta
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    query = db.query(DeviceTelemetry).join(Device, DeviceTelemetry.device_id == Device.id)
    query = query.filter(get_accessible_device_filter(farmer, current_user))
    
    if farm_id and farm_id != 0:
        query = query.filter(Device.farm_id == farm_id)
    if device_id and device_id != 0:
        query = query.filter(DeviceTelemetry.device_id == device_id)
        
    if time_range != "Custom Range":
        cutoff = get_time_range_filter(time_range)
        query = query.filter(DeviceTelemetry.recorded_at >= cutoff)
        
    records = query.order_by(asc(DeviceTelemetry.recorded_at)).all()
    if not records:
        return []
        
    if time_range in ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours"]:
        delta_minutes = 0
    elif time_range == "Last 7 Days":
        delta_minutes = 60
    elif time_range == "Last 30 Days":
        delta_minutes = 1440
    else:
        duration = records[-1].recorded_at - records[0].recorded_at
        if duration.days <= 1:
            delta_minutes = 0
        elif duration.days <= 7:
            delta_minutes = 60
        else:
            delta_minutes = 1440

    grouped = {}
    for r in records:
        ts = r.recorded_at
        if delta_minutes == 0:
            floored_ts = ts.replace(microsecond=0)
        elif delta_minutes == 5:
            floored_ts = ts.replace(minute=ts.minute - (ts.minute % 5), second=0, microsecond=0)
        elif delta_minutes == 60:
            floored_ts = ts.replace(minute=0, second=0, microsecond=0)
        else:
            floored_ts = ts.replace(hour=0, minute=0, second=0, microsecond=0)
            
        if floored_ts not in grouped:
            grouped[floored_ts] = []
        grouped[floored_ts].append(r)
    
    metric_list = metrics.split(",")
    result = []
    
    for metric in metric_list:
        data = []
        for ts in sorted(grouped.keys()):
            group_records = grouped[ts]
            vals = [getattr(r, metric, None) for r in group_records]
            vals = [v for v in vals if v is not None]
            if vals:
                avg = sum(vals) / len(vals)
                data.append(ChartDataPoint(timestamp=ts, value=round(avg, 2)))
        result.append(ChartDataResponse(metric=metric, data=data))
        
    return result

@router.get("/api/farmer/monitoring/devices/{device_id}")
def get_monitoring_device_detail(
    device_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer_from_user(db, current_user)
    device = db.query(Device).filter(Device.id == device_id, get_accessible_device_filter(farmer, current_user)).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    last_tel = db.query(DeviceTelemetry).filter(DeviceTelemetry.device_id == device.id).order_by(desc(DeviceTelemetry.recorded_at)).first()
    
    alerts_records = db.query(Alert).filter(Alert.device_id == device.id).order_by(desc(Alert.created_at)).limit(5).all()
    alerts = [{"id": a.id, "title": a.title or a.category, "severity": a.severity, "generated_time": a.created_at} for a in alerts_records]
    
    farm_name = device.farm.name if device.farm else None
    
    return {
        "device_info": {
            "id": device.id,
            "name": device.name,
            "uid": device.device_uid,
            "farm_name": farm_name,
            "connection_status": device.status,
            "last_heartbeat": device.last_heartbeat,
            "rssi": last_tel.rssi if last_tel else device.last_rssi
        },
        "latest_telemetry": {
            "soil_moisture": last_tel.soil_moisture if last_tel else None,
            "temperature": last_tel.temperature if last_tel else None,
            "humidity": last_tel.humidity if last_tel else None,
            "rain_detected": last_tel.rain_detected if last_tel else None,
            "water_level": None,
            "pressure": last_tel.pressure if last_tel else None,
            "pressure_trend": getattr(last_tel, 'pressure_trend', None) if last_tel else getattr(device, 'last_pressure_trend', None),
            "bmp_temperature": last_tel.bmp_temperature if last_tel else None,
            "altitude": last_tel.altitude if last_tel else None,
            "weather_prediction": last_tel.weather_prediction if last_tel else None,
            "signal_quality": last_tel.signal_quality if last_tel else None,
            "firmware_version": last_tel.firmware_version if last_tel else None,
            "operation_mode": last_tel.operation_mode if last_tel else None,
            "pump_status": last_tel.pump_status if last_tel else None,
            "uptime_seconds": last_tel.uptime_seconds if last_tel else None,
            "ultrasonic_distance": None,
            "ultrasonic_water_level": None,
            "tank_status": None,
            "obstacle_detected": last_tel.obstacle_detected if last_tel else None,
            "sensor_health": clean_sensor_health(last_tel.sensor_health if last_tel else None),
            "recorded_at": last_tel.recorded_at if last_tel else None
        },
        "recent_alerts": alerts
    }
