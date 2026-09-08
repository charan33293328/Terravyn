"""
ESP32 Sensor Telemetry Validation Module.
Prevents ungrounded decisions on faulty, disconnected, or stale sensor inputs.
"""

from typing import Tuple, List, Optional
from datetime import datetime, timedelta

def validate_sensor_telemetry(
    soil_moisture: Optional[float],
    temperature: Optional[float],
    humidity: Optional[float],
    last_telemetry_at: Optional[datetime],
    current_time: Optional[datetime] = None,
    max_stale_minutes: int = 60
) -> Tuple[bool, List[str]]:
    """
    Validate in-situ ESP32 sensor readings.
    Returns (is_valid: bool, issues: List[str])
    """
    issues = []
    now = current_time or datetime.utcnow()

    # 1. Check timestamp and staleness
    if not last_telemetry_at:
        issues.append("No telemetry heartbeat has been recorded for this device.")
    else:
        age_minutes = (now - last_telemetry_at).total_seconds() / 60.0
        if age_minutes < -5: # Clock skew > 5 mins in future
            issues.append("Sensor timestamp is set in the future. Check ESP32 NTP synchronization.")
        elif age_minutes > max_stale_minutes:
            issues.append(f"Sensor data is stale ({int(age_minutes)} minutes old). Device may be offline or in sleep mode.")

    # 2. Validate Soil Moisture
    if soil_moisture is None:
        issues.append("Soil moisture reading is missing from device payload.")
    else:
        if soil_moisture < 0.0 or soil_moisture > 100.0:
            issues.append(f"Soil moisture value ({soil_moisture}%) is outside plausible physical range (0–100%).")
        elif soil_moisture == 0.0:
            # Often indicates disconnected sensor wire / open circuit in capacitive probe
            issues.append("Soil moisture read exactly 0.0%. Possible sensor probe disconnection or dry air reading.")

    # 3. Validate Temperature
    if temperature is not None:
        if temperature < -10.0 or temperature > 65.0:
            issues.append(f"Ambient temperature ({temperature}°C) is outside realistic agricultural bounds (-10°C to 65°C).")

    # 4. Validate Humidity
    if humidity is not None:
        if humidity < 0.0 or humidity > 100.0:
            issues.append(f"Relative humidity ({humidity}%) is outside physical range (0–100%).")

    is_valid = len(issues) == 0
    return is_valid, issues
