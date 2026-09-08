"""
Terravyn Irrigation Intelligence: Sensor Validation & Freshness
"""
from enum import Enum
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from models.domain import Device, DeviceTelemetry


class SensorQuality(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    INVALID = "INVALID"
    SUSPECT = "SUSPECT"
    MISSING = "MISSING"


class IrrigationSensorValidator:
    """
    Validates sensor telemetry for automatic irrigation decisions.
    Enforces freshness window, valid ranges, direction (4095=dry, 0=wet),
    and jump detection.
    """

    RAW_DRY_ADC = 4095.0
    RAW_WET_ADC = 1400.0

    @classmethod
    def convert_raw_adc_to_moisture_pct(cls, raw_adc: float) -> float:
        """
        Converts capacitive soil moisture ADC reading to volumetric moisture percentage.
        Strictly preserves standard: 4095 = Air / Dry (0%), ~1400 = Water / Wet (100%).
        """
        if raw_adc is None:
            return 0.0
        # Clamp to expected bounds
        clamped = max(cls.RAW_WET_ADC, min(cls.RAW_DRY_ADC, float(raw_adc)))
        moisture = ((cls.RAW_DRY_ADC - clamped) / (cls.RAW_DRY_ADC - cls.RAW_WET_ADC)) * 100.0
        return round(moisture, 1)

    @classmethod
    def validate_sensor_telemetry(
        cls,
        device: Optional[Device],
        latest_telem: Optional[DeviceTelemetry],
        max_age_seconds: int = 600,
        prev_moisture: Optional[float] = None,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, SensorQuality, str, Dict[str, Any]]:
        """
        Comprehensive validation of in-situ sensor telemetry.
        Returns:
            (is_usable_for_irrigation: bool, quality: SensorQuality, reason: str, metadata: dict)
        """
        now = current_time or datetime.utcnow()

        if not device:
            return False, SensorQuality.MISSING, "No device linked to this field.", {}

        # 1. Device Communication Health
        device_status = (device.status or "OFFLINE").upper()
        if device_status != "ONLINE":
            return False, SensorQuality.INVALID, f"ESP32 device is {device_status}.", {
                "device_id": device.id,
                "device_uid": device.device_uid,
                "status": device_status
            }

        # 2. Reading Timestamp & Freshness
        reading_time = None
        if latest_telem and latest_telem.recorded_at:
            reading_time = latest_telem.recorded_at
        elif device.last_seen:
            reading_time = device.last_seen
        elif device.last_heartbeat:
            reading_time = device.last_heartbeat

        if not reading_time:
            return False, SensorQuality.MISSING, "No telemetry or heartbeat recorded for device.", {
                "device_id": device.id
            }

        age_seconds = (now - reading_time).total_seconds()
        if age_seconds > max_age_seconds:
            return False, SensorQuality.STALE, (
                f"Sensor reading is stale (age: {int(age_seconds)}s, max allowed: {max_age_seconds}s). "
                "Automatic irrigation blocked to prevent operating on outdated field state."
            ), {
                "age_seconds": round(age_seconds, 1),
                "max_age_seconds": max_age_seconds,
                "reading_time": reading_time.isoformat()
            }

        # 3. Moisture Value Presence & Range
        moisture = None
        if latest_telem and latest_telem.soil_moisture is not None:
            moisture = latest_telem.soil_moisture
        elif device.last_soil_moisture is not None:
            moisture = device.last_soil_moisture

        if moisture is None:
            return False, SensorQuality.MISSING, "Soil moisture reading is missing.", {
                "device_id": device.id
            }

        # Range Check: Volumetric moisture percentage must be 0.0% to 100.0%
        if moisture < 0.0 or moisture > 100.0:
            return False, SensorQuality.INVALID, (
                f"Impossible soil moisture reading: {moisture}%. Expected range is 0.0% to 100.0%."
            ), {
                "reported_moisture": moisture
            }

        # 4. Sudden Jump Detection
        if prev_moisture is not None:
            delta = abs(moisture - prev_moisture)
            # A sudden >50% jump in a single interval without active irrigation is suspect
            if delta > 50.0:
                return False, SensorQuality.SUSPECT, (
                    f"Unrealistic moisture jump detected ({prev_moisture}% -> {moisture}%, delta: {delta}%). "
                    "Sensor reading flagged as SUSPECT."
                ), {
                    "prev_moisture": prev_moisture,
                    "current_moisture": moisture,
                    "delta": delta
                }

        # 5. Hardware Sensor Health
        if device.sensor_health and isinstance(device.sensor_health, dict):
            soil_health = device.sensor_health.get("soil_moisture") or device.sensor_health.get("soil")
            if soil_health and str(soil_health).upper() in ["FAULT", "DISCONNECTED", "ERROR"]:
                return False, SensorQuality.INVALID, f"Hardware sensor health reported fault: {soil_health}.", {
                    "sensor_health": device.sensor_health
                }

        return True, SensorQuality.VALID, "Sensor reading verified valid and fresh.", {
            "moisture": moisture,
            "age_seconds": round(age_seconds, 1),
            "reading_time": reading_time.isoformat(),
            "device_status": device_status
        }
