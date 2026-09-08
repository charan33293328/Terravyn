"""
Terravyn Learning Engine: Sensor Behavior Analyzer
Detects anomalies, sudden jumps, and long-term drift. Never auto-recalibrates.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    DeviceTelemetry,
    Device,
    LearningCandidate,
)

logger = logging.getLogger(__name__)


class SensorBehaviorAnalyzer:
    """Detects sensor anomalies and drift without automatic recalibration."""

    @classmethod
    def detect_anomalies(
        cls,
        db: Session,
        device_id: int,
        lookback_hours: int = 168,
        jump_threshold_pct: float = 30.0,
    ) -> List[Dict[str, Any]]:
        """Detect sudden sensor jumps while environmental conditions remain stable."""
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)

        readings = (
            db.query(DeviceTelemetry)
            .filter(
                DeviceTelemetry.device_id == device_id,
                DeviceTelemetry.recorded_at >= cutoff,
                DeviceTelemetry.soil_moisture.isnot(None),
            )
            .order_by(DeviceTelemetry.recorded_at)
            .all()
        )

        anomalies = []
        for i in range(1, len(readings)):
            prev = readings[i - 1]
            curr = readings[i]

            if prev.soil_moisture is None or curr.soil_moisture is None:
                continue

            delta = abs(curr.soil_moisture - prev.soil_moisture)
            delta_pct = (delta / max(prev.soil_moisture, 1.0)) * 100.0

            # Check if environment was stable (temp and humidity didn't change much)
            env_stable = True
            if prev.temperature and curr.temperature:
                if abs(curr.temperature - prev.temperature) > 5.0:
                    env_stable = False
            if prev.humidity and curr.humidity:
                if abs(curr.humidity - prev.humidity) > 20.0:
                    env_stable = False

            if delta_pct > jump_threshold_pct and env_stable:
                anomalies.append({
                    "timestamp": curr.recorded_at.isoformat(),
                    "prev_moisture": prev.soil_moisture,
                    "curr_moisture": curr.soil_moisture,
                    "delta_pct": round(delta_pct, 1),
                    "env_stable": True,
                    "type": "SUDDEN_JUMP",
                })

        return anomalies

    @classmethod
    def detect_drift(
        cls,
        db: Session,
        device_id: int,
        lookback_days: int = 30,
        min_readings: int = 20,
    ) -> Optional[Dict[str, Any]]:
        """Analyze long-term sensor reading trends for potential drift."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        readings = (
            db.query(DeviceTelemetry)
            .filter(
                DeviceTelemetry.device_id == device_id,
                DeviceTelemetry.recorded_at >= cutoff,
                DeviceTelemetry.soil_moisture.isnot(None),
            )
            .order_by(DeviceTelemetry.recorded_at)
            .all()
        )

        if len(readings) < min_readings:
            return None

        # Simple linear regression on moisture readings over time
        values = [r.soil_moisture for r in readings]
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return None

        slope = numerator / denominator
        # Significant drift: slope changes by >0.1% per reading consistently
        if abs(slope) < 0.1:
            return None

        direction = "INCREASING" if slope > 0 else "DECREASING"
        return {
            "device_id": device_id,
            "readings_analyzed": n,
            "slope_per_reading": round(slope, 4),
            "direction": direction,
            "first_value": values[0],
            "last_value": values[-1],
            "total_change": round(values[-1] - values[0], 2),
            "period_days": lookback_days,
            "type": "POTENTIAL_DRIFT",
        }

    @classmethod
    def create_sensor_candidate(
        cls,
        db: Session,
        device_id: int,
        farm_id: int,
        anomaly_type: str,
        evidence: Dict[str, Any],
    ) -> Optional[LearningCandidate]:
        """Create a SENSOR_PATTERN learning candidate from anomaly/drift detection."""
        candidate_type = "SENSOR_PATTERN"
        idemp = f"sensor:{device_id}:{anomaly_type}"

        existing = db.query(LearningCandidate).filter(
            LearningCandidate.idempotency_key == idemp
        ).first()
        if existing:
            existing.observation_count += 1
            existing.updated_at = datetime.utcnow()
            db.commit()
            return existing

        description = f"Sensor {anomaly_type} detected on device #{device_id}."
        if anomaly_type == "POTENTIAL_DRIFT":
            description += f" Direction: {evidence.get('direction', 'UNKNOWN')}, change: {evidence.get('total_change', 0)}%."
            candidate_type = "CALIBRATION_PATTERN"
        elif anomaly_type == "SUDDEN_JUMP":
            description += f" Jump of {evidence.get('delta_pct', 0):.1f}% while environment stable."

        candidate = LearningCandidate(
            candidate_type=candidate_type,
            farm_id=farm_id,
            pattern_description=description,
            pattern_data=evidence,
            observation_count=1,
            event_count=1,
            field_count=1,
            data_quality="MEDIUM",
            confidence=30,
            priority="LOW" if anomaly_type == "SUDDEN_JUMP" else "MEDIUM",
            impact="MEDIUM",
            risk_level="LOW",
            status="EXPERIMENTAL",
            idempotency_key=idemp,
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        logger.info(f"[SensorAnalyzer] Created {candidate_type} candidate #{candidate.id} for device #{device_id}")
        return candidate
