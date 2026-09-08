from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Union, Dict, Any
from datetime import datetime, timedelta
from database.connection import get_db
from models.domain import Device, DeviceAuditLog, DeviceTelemetry, Alert, IrrigationLog
from schemas.domain import (
    DeviceConfigResponse,
    DynamicIrrigationConfigResponse,
    DeviceConfigAckRequest,
    DeviceConfigAckResponse
)
from services.crop_engine import DeviceConfigSyncService
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/devices", tags=["ESP32 Hardware APIs"])

class DeviceHeartbeatReq(BaseModel):
    mac_address: Optional[str] = None
    device_id: Optional[str] = None
    chip_id: Optional[str] = None
    device_uid: Optional[str] = None
    rssi: Optional[int] = None

    model_config = {
        "extra": "allow"
    }

class TelemetryPayload(BaseModel):
    # Support both flat and nested JSON
    mac_address: Optional[str] = None
    device_id: Optional[str] = None  # v1.0 mapped to mac_address
    chip_id: Optional[str] = None
    device_uid: Optional[str] = None
    
    # Generic catch-all for any other fields
    model_config = {
        "extra": "allow"
    }

def lookup_device(db: Session, identifier: Optional[str] = None, chip_id: Optional[str] = None) -> Optional[Device]:
    query = db.query(Device)
    candidates = [val for val in [identifier, chip_id] if val is not None]
    
    import re
    for val in candidates:
        val_str = str(val).strip()
        if not val_str:
            continue
            
        # 1. Direct match (case-insensitive) on mac_address, device_uid, chip_id
        dev = query.filter(
            (Device.mac_address.ilike(val_str)) |
            (Device.device_uid.ilike(val_str)) |
            (Device.chip_id.ilike(val_str))
        ).first()
        if dev:
            return dev
            
        # 2. If it's a numeric device id
        if val_str.isdigit():
            dev = query.filter(Device.id == int(val_str)).first()
            if dev:
                return dev

        # 3. Normalized alphanumeric matching
        clean_val = re.sub(r'[^A-Za-z0-9]', '', val_str).upper()
        if clean_val:
            all_devices = query.all()
            for d in all_devices:
                d_clean_mac = re.sub(r'[^A-Za-z0-9]', '', d.mac_address or '').upper()
                d_clean_uid = re.sub(r'[^A-Za-z0-9]', '', d.device_uid or '').upper()
                d_clean_chip = re.sub(r'[^A-Za-z0-9]', '', d.chip_id or '').upper()

                if d_clean_mac and clean_val == d_clean_mac:
                    return d
                if d_clean_uid and clean_val == d_clean_uid:
                    return d
                if d_clean_chip and clean_val == d_clean_chip:
                    return d

                # Substring match (e.g. TRV-ESP32-B0CBD8CA2818 or containing MAC)
                if d_clean_mac and len(d_clean_mac) == 12 and d_clean_mac in clean_val:
                    return d
                if clean_val and len(clean_val) == 12 and d_clean_mac and clean_val in d_clean_mac:
                    return d

    # Fallback: If only 1 device exists in the database, match it to prevent hardware rejection
    all_devs = query.all()
    if len(all_devs) == 1:
        return all_devs[0]

    return None

def log_audit(db: Session, device_uid: str, admin_id: int, action: str, old_value: str = None, new_value: str = None):
    final_admin_id = None if admin_id == 0 else admin_id
    log = DeviceAuditLog(
        device_uid=device_uid or "UNKNOWN",
        admin_id=final_admin_id,
        action=action,
        old_value=old_value,
        new_value=new_value
    )
    db.add(log)
    db.commit()

@router.get("/config/{mac_address}", response_model=DeviceConfigResponse)
def get_device_config(mac_address: str, db: Session = Depends(get_db)):
    device = lookup_device(db, identifier=mac_address)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    provisioning_req = bool(device.wifi_provisioning_requested)
    if provisioning_req:
        logger.info(f"Consuming one-time Wi-Fi provisioning request for device {device.device_uid} (MAC: {mac_address})")
        device.wifi_provisioning_requested = False
        db.commit()

    current_mode = (device.irrigation_mode or "AUTO").strip().upper()
    if current_mode not in ["AUTO", "MANUAL"]:
        current_mode = "AUTO"

    # Calculate dynamic crop/variety irrigation thresholds
    dynamic_config = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)

    logger.info(
        f"Returning configuration for device {device.device_uid} (MAC: {mac_address}): "
        f"irrigation_mode={current_mode}, version={dynamic_config.configuration_version}, "
        f"crop={dynamic_config.crop}, start={dynamic_config.start_threshold}%, stop={dynamic_config.stop_threshold}%"
    )

    response_data = DeviceConfigResponse(
        irrigation_mode=current_mode,
        wifi_provisioning_requested=provisioning_req,
        config_version=dynamic_config.configuration_version,
        irrigation_config=dynamic_config
    )
    return response_data

@router.post("/config/ack", response_model=DeviceConfigAckResponse)
@router.post("/devices/config/ack", response_model=DeviceConfigAckResponse)
async def acknowledge_device_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    ESP32 acknowledges or reports status for an applied configuration version.
    """
    payload = {}
    try:
        payload = await request.json()
    except Exception:
        body = await request.body()
        if body:
            try:
                import json
                payload = json.loads(body.decode("utf-8", errors="ignore"))
            except Exception:
                pass
    if not isinstance(payload, dict):
        payload = {}

    req = DeviceConfigAckRequest(**payload)

    ident = req.mac_address or req.device_uid or req.chip_id
    device = lookup_device(db, identifier=ident, chip_id=req.chip_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    res = DeviceConfigSyncService.record_config_ack(db, req, device)
    return DeviceConfigAckResponse(**res)

@router.post("/heartbeat")
async def heartbeat(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = {}
    try:
        payload = await request.json()
    except Exception:
        body = await request.body()
        if body:
            try:
                import json
                payload = json.loads(body.decode("utf-8", errors="ignore"))
            except Exception:
                pass
    if not isinstance(payload, dict):
        payload = {}
        
    logger.info(f"Heartbeat Payload: {payload}")
    mac_address = payload.get("device_id") or payload.get("mac_address") or payload.get("device_uid") or payload.get("chip_id")
    chip_id = payload.get("chip_id")
    rssi = payload.get("rssi")
    
    device = lookup_device(db, identifier=mac_address, chip_id=chip_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not registered")
    
    try:
        now = datetime.utcnow()
        device.last_heartbeat = now
        device.last_seen = now
        if rssi is not None:
            device.rssi = rssi
            device.last_rssi = rssi
        device.status = "ONLINE"
        device.connectivity_status = "ONLINE"
        db.commit()
        
        try:
            from services.websocket import manager
            await manager.broadcast_to_device(device.id, {
                "type": "status_update",
                "status": "ONLINE",
                "device_id": device.id
            })
        except Exception:
            pass
    except Exception as e:
        logger.exception("Heartbeat processing failed")
        raise HTTPException(status_code=500, detail="Internal server error")
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"message": "Heartbeat received", "device_uid": device.device_uid}, headers={"Connection": "close"})

@router.post("/telemetry")
@router.post("/data")
async def submit_telemetry(
    request: Request,
    db: Session = Depends(get_db)
):
    """ESP32 sends sensor telemetry data (v1.0 nested or legacy flat)."""
    req_payload = {}
    try:
        req_payload = await request.json()
    except Exception:
        body = await request.body()
        if body:
            try:
                import json
                req_payload = json.loads(body.decode("utf-8", errors="ignore"))
            except Exception:
                pass
    if not isinstance(req_payload, dict):
        req_payload = {}
    logger.info(f"Raw Telemetry Payload: {req_payload}")
    
    # Extract identifiers
    mac_address = (
        req_payload.get("device_id") or 
        req_payload.get("mac_address") or 
        req_payload.get("device_uid") or 
        req_payload.get("chip_id") or
        req_payload.get("id")
    )
    chip_id = req_payload.get("chip_id")
        
    device = lookup_device(db, identifier=mac_address, chip_id=chip_id)
    if not device:
        logger.warning(f"Device lookup failed for telemetry payload: {req_payload}")
        raise HTTPException(status_code=404, detail="Device not found")
            
    try:
        now = datetime.utcnow()
        
        # Parse fields (handle both v1.0 nested and legacy flat)
        sensors = req_payload.get("sensors", {})
        bmp280 = sensors.get("bmp280", {})
        pump_status_obj = req_payload.get("pump_status", {})
        if isinstance(pump_status_obj, bool):
            pump_is_running = pump_status_obj
            pump_mode = req_payload.get("operation_mode") or "AUTO"
            pump_duration = 0
        else:
            pump_is_running = pump_status_obj.get("is_running", False)
            pump_mode = pump_status_obj.get("mode", req_payload.get("operation_mode", "AUTO"))
            pump_duration = pump_status_obj.get("last_run_duration", 0)

        # Map to unified variables
        p_soil_moisture = sensors.get("soil_moisture", req_payload.get("soil_moisture"))
        p_temperature = sensors.get("temperature", req_payload.get("temperature"))
        p_humidity = sensors.get("humidity", req_payload.get("humidity"))
        p_water_level = sensors.get("water_level", req_payload.get("water_level"))
        p_rain_detected = sensors.get("rain_detected", req_payload.get("rain_detected"))
        p_rainfall = req_payload.get("rainfall")
        p_bmp_temperature = bmp280.get("temperature", req_payload.get("bmp_temperature"))
        p_pressure = bmp280.get("pressure", req_payload.get("pressure"))
        p_altitude = bmp280.get("altitude", req_payload.get("altitude"))
        
        p_rssi = req_payload.get("wifi_rssi", req_payload.get("rssi"))
        p_signal_quality = req_payload.get("signal_quality")
        p_firmware = req_payload.get("firmware_version")
        p_uptime = req_payload.get("uptime_seconds")
        p_weather = req_payload.get("weather_prediction")
        p_pressure_trend = req_payload.get("pressure_trend")
        p_battery = req_payload.get("battery_voltage")
        p_dark_detected = req_payload.get("dark_detected")
        p_obstacle_detected = req_payload.get("obstacle_detected")
        p_sensor_health = req_payload.get("sensor_health")
        if p_sensor_health and isinstance(p_sensor_health, dict):
            p_sensor_health = {k: v for k, v in p_sensor_health.items() if k not in ("water", "ultrasonic")}
        
        p_ultrasonic_distance = req_payload.get("ultrasonic_distance")
        p_ultrasonic_water_level = req_payload.get("ultrasonic_water_level")

        # Dynamic Irrigation Configuration Snapshot fields from ESP32
        p_config_version = req_payload.get("configuration_version") or req_payload.get("config_version")
        p_dynamic_config_valid = req_payload.get("dynamic_threshold_config_valid")
        p_start_thresh = req_payload.get("start_threshold")
        p_stop_thresh = req_payload.get("stop_threshold")
        p_configured_crop = req_payload.get("configured_crop")
        p_configured_variety = req_payload.get("configured_variety")
        p_configured_stage = req_payload.get("configured_growth_stage")
        p_irr_reason = req_payload.get("irrigation_reason") or req_payload.get("irrigation_event_reason")

        # Create Historical Record
        telemetry_record = DeviceTelemetry(
            device_id=device.id,
            farmer_id=device.farmer_id,
            farm_id=device.farm_id,
            soil_moisture=p_soil_moisture,
            temperature=p_temperature,
            humidity=p_humidity,
            rainfall=p_rainfall,
            rain_detected=p_rain_detected,
            water_level=p_water_level,
            pressure=p_pressure,
            pressure_trend=p_pressure_trend,
            light_intensity=req_payload.get("light_intensity"),
            battery_voltage=p_battery,
            rssi=p_rssi,
            bmp_temperature=p_bmp_temperature,
            altitude=p_altitude,
            weather_prediction=p_weather,
            signal_quality=p_signal_quality,
            firmware_version=p_firmware,
            uptime_seconds=p_uptime,
            operation_mode=pump_mode,
            pump_status=pump_is_running,
            dark_detected=p_dark_detected,
            obstacle_detected=p_obstacle_detected,
            sensor_health=p_sensor_health,
            ultrasonic_distance=p_ultrasonic_distance,
            ultrasonic_water_level=p_ultrasonic_water_level,
            configuration_version=p_config_version,
            dynamic_threshold_config_valid=p_dynamic_config_valid,
            start_threshold=p_start_thresh,
            stop_threshold=p_stop_thresh,
            configured_crop=p_configured_crop,
            configured_variety=p_configured_variety,
            configured_growth_stage=p_configured_stage,
            irrigation_event_reason=p_irr_reason,
            recorded_at=now
        )
        db.add(telemetry_record)
        
        # 2. Capture old states & track pump transitions
        old_rain_detected = device.last_rain_detected
        old_pump_status = device.pump_status

        if pump_is_running and not old_pump_status:
            reason_str = p_irr_reason or f"ESP32 Auto: soil moisture ({p_soil_moisture}%) < threshold ({p_start_thresh}%) [v{p_config_version}]"
            irr_log = IrrigationLog(
                device_id=device.id,
                action="pump_on_auto",
                triggered_by="esp32_auto"
            )
            db.add(irr_log)
        elif not pump_is_running and old_pump_status:
            irr_log = IrrigationLog(
                device_id=device.id,
                action="pump_off_auto",
                triggered_by="esp32_auto"
            )
            db.add(irr_log)

        # 3. Update Device Snapshot
        device.last_seen = now
        device.last_heartbeat = now
        if p_config_version is not None:
            device.applied_config_version = p_config_version
            if p_dynamic_config_valid is not None:
                device.config_ack_status = "APPLIED" if p_dynamic_config_valid else "ERROR"
        if p_rssi is not None:
            device.last_rssi = p_rssi
            device.rssi = p_rssi
        if p_temperature is not None:
            device.last_temperature = p_temperature
        if p_humidity is not None:
            device.last_humidity = p_humidity
        if p_soil_moisture is not None:
            device.last_soil_moisture = p_soil_moisture
        if p_rain_detected is not None:
            device.last_rain_detected = p_rain_detected
        if p_bmp_temperature is not None:
            device.last_bmp_temperature = p_bmp_temperature
        if p_pressure is not None:
            device.last_pressure = p_pressure
        if p_altitude is not None:
            device.last_altitude = p_altitude
        if p_weather is not None:
            device.last_weather_prediction = p_weather
            device.last_pressure_trend = p_pressure_trend
        if p_signal_quality is not None:
            device.last_signal_quality = p_signal_quality
        if p_uptime is not None:
            device.last_uptime_seconds = p_uptime
        if p_firmware is not None:
            device.firmware_version = p_firmware
        if p_dark_detected is not None:
            device.last_dark_detected = p_dark_detected
        if p_obstacle_detected is not None:
            device.last_obstacle_detected = p_obstacle_detected
        if p_sensor_health is not None:
            device.sensor_health = p_sensor_health
        if p_ultrasonic_distance is not None:
            device.last_ultrasonic_distance = p_ultrasonic_distance
        if p_ultrasonic_water_level is not None:
            device.last_ultrasonic_water_level = p_ultrasonic_water_level
            
        if pump_is_running is not None:
            device.pump_status = pump_is_running
        # Note: Do not overwrite device.irrigation_mode from telemetry;
        # device.irrigation_mode is the authoritative user-configured mode set via Website/API.
            
        device.status = "ONLINE"
        # 3. Alert Generation Logic
        import json
        def evaluate_alert(category, title, description, severity, trigger_value, metric_name):
            active_alert = db.query(Alert).filter(
                Alert.device_id == device.id,
                Alert.category == category,
                Alert.status.in_(["UNREAD", "READ"])
            ).first()
            
            trigger_data = json.dumps({metric_name: trigger_value})
            
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
                    title=title,
                    description=description,
                    category=category,
                    severity=severity,
                    status="UNREAD",
                    trigger_data=trigger_data,
                    created_at=now,
                    updated_at=now
                )
                db.add(new_alert)

        # Soil Moisture Rules
        if p_soil_moisture is not None:
            if p_soil_moisture < 20:
                evaluate_alert("Soil Moisture Alerts", "Critical Soil Moisture", f"Soil moisture dropped to {p_soil_moisture}%", "CRITICAL", p_soil_moisture, "Soil Moisture")
            elif p_soil_moisture < 30:
                evaluate_alert("Soil Moisture Alerts", "Low Soil Moisture", f"Soil moisture is at {p_soil_moisture}%", "WARNING", p_soil_moisture, "Soil Moisture")

        # Temperature Rules
        if p_temperature is not None:
            if p_temperature > 40:
                evaluate_alert("Temperature Alerts", "High Temperature Warning", f"Temperature is at {p_temperature}°C", "WARNING", p_temperature, "Temperature")

        # Humidity Rules
        if p_humidity is not None:
            if p_humidity > 90:
                evaluate_alert("Humidity Alerts", "High Humidity Warning", f"Humidity is at {p_humidity}%", "WARNING", p_humidity, "Humidity")
            elif p_humidity < 20:
                evaluate_alert("Humidity Alerts", "Low Humidity Warning", f"Humidity is at {p_humidity}%", "WARNING", p_humidity, "Humidity")

        # Rain Rules
        if p_rain_detected is not None:
            if p_rain_detected and not old_rain_detected:
                evaluate_alert("Weather Alerts", "Rain Detected", "Rain detected. Automatic irrigation paused.", "INFO", True, "Rain")
            elif not p_rain_detected and old_rain_detected:
                evaluate_alert("Weather Alerts", "Rain Stopped", "Rain has stopped.", "INFO", False, "Rain")
                
        # IR Obstacle Rules
        if p_obstacle_detected is not None:
            if p_obstacle_detected:
                evaluate_alert("Security Alerts", "Obstacle Detected", "An obstacle was detected near the device.", "WARNING", True, "Obstacle Detection")
                
        # ESP32 v1.0 Specific Alerts
        if pump_duration > 900:  # 15 mins timeout
            evaluate_alert("System Alerts", "Pump Timeout Critical Alert", "Pump exceeded maximum runtime.", "CRITICAL", True, "Pump Timeout")
            
        if p_weather == "Heavy Storm":
            evaluate_alert("Weather Alerts", "Heavy Storm Predicted", "Pressure drop indicates heavy storm.", "WARNING", "Heavy Storm", "Weather Prediction")
            
        if p_signal_quality in ["Weak", "Very Weak"]:
            evaluate_alert("System Alerts", "Weak WiFi Signal", f"Device WiFi signal is {p_signal_quality}.", "WARNING", p_signal_quality, "Signal Quality")
        
        db.commit()
        db.refresh(device)
        logger.info(f"Telemetry stored successfully for {device.device_uid}")
        
        # 3. Update Device Snapshot
        device.last_telemetry = now
        device.last_seen = now
        device.last_heartbeat = now
        device.status = "ONLINE"
        device.connectivity_status = "ONLINE"
        db.commit()

        try:
            from services.websocket import manager
            await manager.broadcast_to_device(device.id, {
                "type": "telemetry_update",
                "device_id": device.id,
                "soil_moisture": device.last_soil_moisture,
                "temperature": device.last_temperature,
                "humidity": device.last_humidity,
                "status": "ONLINE"
            })
        except Exception:
            pass
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content={
                "success": True,
                "message": "Telemetry received",
                "device_uid": device.device_uid,
                "recorded_at": now.isoformat()
            },
            headers={"Connection": "close"}
        )

    except Exception as e:
        logger.exception("Telemetry processing failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{device_uid}/mode")
def get_device_mode(device_uid: str, db: Session = Depends(get_db)):
    """ESP32 polls this endpoint every 15 seconds to fetch the latest irrigation_mode."""
    device = lookup_device(db, identifier=device_uid)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    return {"irrigation_mode": device.irrigation_mode or "AUTO"}

# --- ESP32 Compatibility Router for Alternative URL Schemes ---
compat_router = APIRouter(tags=["ESP32 Hardware APIs (Aliases)"])

@compat_router.post("/devices/telemetry")
@compat_router.post("/devices/data")
@compat_router.post("/device/telemetry")
@compat_router.post("/device/data")
@compat_router.post("/telemetry")
@compat_router.post("/data")
@compat_router.post("/api/device/data")
@compat_router.post("/api/device/telemetry")
@compat_router.post("/api/sensors/data")
@compat_router.post("/api/sensors/telemetry")
@compat_router.post("/sensors/data")
@compat_router.post("/sensors/telemetry")
async def submit_telemetry_compat(
    request: Request,
    db: Session = Depends(get_db)
):
    return await submit_telemetry(request=request, db=db)

@compat_router.post("/devices/heartbeat")
@compat_router.post("/device/heartbeat")
@compat_router.post("/heartbeat")
@compat_router.post("/api/device/heartbeat")
async def heartbeat_compat(
    request: Request,
    db: Session = Depends(get_db)
):
    return await heartbeat(request=request, db=db)

@compat_router.get("/devices/config/{mac_address}")
@compat_router.get("/device/config/{mac_address}")
@compat_router.get("/config/{mac_address}")
@compat_router.get("/api/device/config/{mac_address}")
def get_device_config_compat(mac_address: str, db: Session = Depends(get_db)):
    return get_device_config(mac_address=mac_address, db=db)

@compat_router.get("/devices/{device_uid}/mode")
@compat_router.get("/device/{device_uid}/mode")
@compat_router.get("/{device_uid}/mode")
@compat_router.get("/api/device/{device_uid}/mode")
def get_device_mode_compat(device_uid: str, db: Session = Depends(get_db)):
    return get_device_mode(device_uid=device_uid, db=db)

@compat_router.post("/devices/config/ack")
@compat_router.post("/device/config/ack")
@compat_router.post("/config/ack")
@compat_router.post("/api/device/config/ack")
async def acknowledge_device_config_compat(
    request: Request,
    db: Session = Depends(get_db)
):
    return await acknowledge_device_config(request=request, db=db)


