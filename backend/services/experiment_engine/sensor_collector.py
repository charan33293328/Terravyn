"""
Terravyn Experiment Engine: Sensor Collector & Calibration
Enforces raw ADC direction (4095=dry, 0=wet) and sensor quality tagging.
"""
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.domain import SensorCalibrationRecord, DeviceTelemetry, Device


class SensorQuality:
    VALID = "VALID"
    SUSPECT = "SUSPECT"
    INVALID = "INVALID"
    MISSING = "MISSING"


class ExperimentSensorCollector:
    # Terravyn Hardware Standard Convention: 4095 is Air/Dry, 0 is Saturated Wet
    DEFAULT_DRY_ADC = 4095.0
    DEFAULT_WET_ADC = 1400.0

    @classmethod
    def raw_to_volumetric_moisture(
        cls,
        raw_adc: Optional[float],
        dry_ref: float = DEFAULT_DRY_ADC,
        wet_ref: float = DEFAULT_WET_ADC,
        soil_type: Optional[str] = "sandy_loam"
    ) -> Optional[float]:
        """
        Converts raw ADC capacitive sensor value into volumetric moisture %.
        Strictly enforces: 4095 = Air / Dry (0% moisture), 0 or wet_ref = Wet (100% moisture).
        """
        if raw_adc is None:
            return None

        # Clamp raw_adc to physical limits
        clamped_adc = max(0.0, min(4095.0, float(raw_adc)))
        span = dry_ref - wet_ref
        if span <= 0:
            span = 2695.0  # Safe fallback 4095 - 1400

        # Percentage: higher raw_adc means drier, lower raw_adc means wetter
        percentage = ((dry_ref - clamped_adc) / span) * 100.0
        return round(max(0.0, min(100.0, percentage)), 2)

    @classmethod
    def evaluate_sensor_quality(
        cls,
        raw_value: Optional[float],
        last_recorded_at: Optional[datetime],
        prev_value: Optional[float] = None,
        now: Optional[datetime] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Evaluates sensor reading validity:
        - None -> MISSING
        - Out of 0..4095 bounds -> INVALID
        - Stale (> 2h) or sudden unnatural jump (> 2500 ADC) -> SUSPECT
        - Normal -> VALID
        """
        curr_time = now or datetime.utcnow()

        if raw_value is None:
            return SensorQuality.MISSING, "No telemetry signal received from probe."

        if raw_value < 0 or raw_value > 4095:
            return SensorQuality.INVALID, f"ADC value {raw_value} outside physical ESP32 12-bit range (0-4095)."

        if last_recorded_at and (curr_time - last_recorded_at) > timedelta(hours=2):
            return SensorQuality.SUSPECT, f"Telemetry is stale (last seen {(curr_time - last_recorded_at).total_seconds()/60:.0f} mins ago)."

        if prev_value is not None:
            jump = abs(raw_value - prev_value)
            if jump > 2500.0:
                return SensorQuality.SUSPECT, f"Unnatural jump of {jump:.0f} ADC units detected within consecutive readings."

        return SensorQuality.VALID, "Sensor reading within nominal calibrated bounds."

    @classmethod
    def record_sensor_calibration(
        cls,
        db: Session,
        device_id: Optional[int],
        dry_reference: float = DEFAULT_DRY_ADC,
        wet_reference: float = DEFAULT_WET_ADC,
        soil_type: str = "sandy_loam",
        notes: Optional[str] = None
    ) -> SensorCalibrationRecord:
        """Stores sensor calibration record in the database."""
        rec = SensorCalibrationRecord(
            device_id=device_id,
            sensor_type="capacitive_soil_moisture",
            calibration_date=datetime.utcnow(),
            calibration_method="two_point_air_water",
            dry_reference=dry_reference,
            wet_reference=wet_reference,
            direction="4095_DRY_0_WET",
            soil_type=soil_type,
            calibration_version="v1.0",
            notes=notes or "Standard 2-point air/water calibration"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
