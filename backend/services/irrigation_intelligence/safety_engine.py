"""
Terravyn Irrigation Intelligence: Layer B Execution Safety & Authorization Engine
"""
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    Farm,
    Device,
    DeviceTelemetry,
    CropDecisionLog,
    IrrigationControlConfig,
    IrrigationAuthorizationRecord,
    IrrigationLog,
    Alert
)
from services.irrigation_intelligence.sensor_validator import (
    IrrigationSensorValidator,
    SensorQuality
)
from services.irrigation_intelligence.weather_validator import (
    IrrigationWeatherValidator
)


class AuthorizationStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"
    DEFERRED = "DEFERRED"
    FAILED = "FAILED"


class ExecutionSafetyEngine:
    """
    Layer B — Execution Safety Engine.
    Determines whether it is safe and permitted to execute irrigation right now.
    Answers: 'Is it safe and permitted to execute irrigation right now?'
    """

    @classmethod
    def evaluate_authorization(
        cls,
        db: Session,
        farm: Farm,
        device: Optional[Device],
        decision_log: CropDecisionLog,
        config: IrrigationControlConfig,
        current_time: Optional[datetime] = None
    ) -> Tuple[AuthorizationStatus, str, List[str], List[str], Dict[str, Any]]:
        """
        Executes all Layer B safety checks.
        Returns:
            (status: AuthorizationStatus,
             reason: str,
             checks_passed: List[str],
             checks_failed: List[str],
             input_snapshot: Dict[str, Any])
        """
        now = current_time or datetime.utcnow()
        checks_passed: List[str] = []
        checks_failed: List[str] = []

        # Snapshot of all evaluated factors
        input_snapshot = {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "device_id": device.id if device else None,
            "device_uid": device.device_uid if device else None,
            "decision_log_id": decision_log.id,
            "agricultural_decision": decision_log.decision,
            "confidence": decision_log.confidence,
            "intelligence_mode": config.intelligence_mode,
            "automatic_irrigation_enabled": config.automatic_irrigation_enabled,
            "control_mode": device.irrigation_mode if device else config.control_mode,
            "evaluated_at": now.isoformat()
        }

        # -------------------------------------------------------------
        # CHECK 1: MANUAL MODE PRIORITY GUARD (Absolute Priority)
        # -------------------------------------------------------------
        current_control_mode = (device.irrigation_mode if device and device.irrigation_mode else config.control_mode or "AUTO").upper()
        if current_control_mode == "MANUAL":
            checks_failed.append("manual_mode_active")
            reason = "Manual mode is active on device. Automatic irrigation engine is strictly blocked and cannot override manual mode."
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("auto_mode_active")

        # -------------------------------------------------------------
        # CHECK 2: HARDWARE PRESENCE & CONNECTIVITY
        # -------------------------------------------------------------
        if not device:
            checks_failed.append("device_missing")
            reason = "No hardware device is linked to this farm field. Remote actuation impossible."
            return AuthorizationStatus.FAILED, reason, checks_passed, checks_failed, input_snapshot

        device_status = (device.status or "OFFLINE").upper()
        if device_status != "ONLINE":
            checks_failed.append("device_offline")
            reason = f"ESP32 device is {device_status}. Automatic irrigation blocked for offline safety."
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("device_online")

        # -------------------------------------------------------------
        # CHECK 3: SENSOR FRESHNESS & RANGE VALIDITY
        # -------------------------------------------------------------
        latest_telem = db.query(DeviceTelemetry).filter(DeviceTelemetry.device_id == device.id).order_by(desc(DeviceTelemetry.recorded_at)).first()
        sensor_valid, quality, sensor_reason, sensor_meta = IrrigationSensorValidator.validate_sensor_telemetry(
            device=device,
            latest_telem=latest_telem,
            max_age_seconds=config.sensor_freshness_seconds,
            current_time=now
        )
        input_snapshot["sensor_telemetry"] = sensor_meta

        if not sensor_valid:
            checks_failed.append(f"sensor_{quality.value.lower()}")
            reason = f"Sensor validation failed ({quality.value}): {sensor_reason}"
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("sensor_fresh_and_valid")

        # -------------------------------------------------------------
        # CHECK 4: WATER LEVEL SAFETY GUARD (Low Water Protection)
        # -------------------------------------------------------------
        is_low_water = False
        low_water_details = ""

        if getattr(device, "last_low_water_alert", False):
            is_low_water = True
            low_water_details = "Device reported low water hardware alert."
        elif device.last_ultrasonic_water_level is not None:
            if device.last_ultrasonic_water_level < config.min_water_level_pct:
                is_low_water = True
                low_water_details = f"Ultrasonic water level ({device.last_ultrasonic_water_level}%) is below minimum safe threshold ({config.min_water_level_pct}%)."
        elif latest_telem and latest_telem.water_level is not None:
            if str(latest_telem.water_level).upper() in ["LOW", "EMPTY", "CRITICAL"]:
                is_low_water = True
                low_water_details = f"Telemetry water level sensor reported {latest_telem.water_level}."

        if is_low_water:
            checks_failed.append("low_water_detected")
            reason = f"BLOCKED_LOW_WATER: {low_water_details} Pump activation blocked to prevent dry-running and hardware damage."
            # Create Alert in database
            alert = Alert(
                farmer_id=device.farmer_id,
                farm_id=farm.id,
                device_id=device.id,
                title="Low Water Level - Irrigation Blocked",
                description=reason,
                category="Hardware Safety",
                severity="CRITICAL",
                status="UNREAD",
                created_at=now
            )
            db.add(alert)
            db.commit()
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("water_level_adequate")

        # -------------------------------------------------------------
        # CHECK 5: PUMP CURRENT STATE & EMERGENCY STOP
        # -------------------------------------------------------------
        if getattr(device, "pump_status", False):
            checks_failed.append("pump_already_running")
            reason = "Irrigation pump is already actively running. Duplicate start command prevented."
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("pump_idle")

        # Hardware safety check from sensor_health
        if device.sensor_health and isinstance(device.sensor_health, dict):
            pump_health = device.sensor_health.get("pump") or device.sensor_health.get("relay")
            if pump_health and str(pump_health).upper() in ["FAULT", "OVERHEAT", "SHORT"]:
                checks_failed.append("pump_hardware_fault")
                reason = f"Pump hardware fault detected: {pump_health}. Actuation blocked."
                return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("hardware_fault_absent")

        # -------------------------------------------------------------
        # CHECK 6: AGRICULTURAL DECISION MATCH
        # -------------------------------------------------------------
        if decision_log.decision.upper() != "IRRIGATE":
            checks_failed.append("decision_not_irrigate")
            reason = f"Agricultural decision is {decision_log.decision}, not IRRIGATE. Pump actuation not required."
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("agricultural_decision_irrigate")

        # -------------------------------------------------------------
        # CHECK 7: CONFIDENCE THRESHOLD
        # -------------------------------------------------------------
        if decision_log.confidence < config.decision_confidence_min:
            checks_failed.append("confidence_below_minimum")
            reason = f"Decision confidence ({decision_log.confidence}%) is below required minimum ({config.decision_confidence_min}%)."
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("confidence_threshold_met")

        # -------------------------------------------------------------
        # CHECK 8: DECISION EXPIRATION
        # -------------------------------------------------------------
        decision_age = (now - decision_log.timestamp).total_seconds()
        if decision_age > config.decision_validity_seconds:
            checks_failed.append("decision_expired")
            reason = f"Decision has expired ({int(decision_age)}s old, validity window: {config.decision_validity_seconds}s). Re-evaluation required."
            return AuthorizationStatus.FAILED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("decision_fresh")

        # -------------------------------------------------------------
        # CHECK 9: COOLDOWN ENFORCEMENT (Anti-Cycling)
        # -------------------------------------------------------------
        recent_irrigation = (
            db.query(IrrigationLog)
            .filter(IrrigationLog.device_id == device.id, IrrigationLog.action.ilike("%on%"))
            .order_by(desc(IrrigationLog.timestamp))
            .first()
        )
        if recent_irrigation and recent_irrigation.timestamp:
            irrigation_age = (now - recent_irrigation.timestamp).total_seconds()
            if irrigation_age < config.cooldown_seconds:
                time_left = int(config.cooldown_seconds - irrigation_age)
                checks_failed.append("cooldown_active")
                reason = f"Cooldown window active ({time_left}s remaining of {config.cooldown_seconds}s). Deferring execution to allow soil moisture redistribution."
                return AuthorizationStatus.DEFERRED, reason, checks_passed, checks_failed, input_snapshot
        checks_passed.append("cooldown_cleared")

        # -------------------------------------------------------------
        # CHECK 10: INTELLIGENCE DEPLOYMENT MODE
        # -------------------------------------------------------------
        int_mode = config.intelligence_mode.upper()
        if int_mode == "OBSERVATION":
            checks_failed.append("mode_observation_only")
            reason = "Intelligence mode is OBSERVATION. Operating purely in passive data collection mode."
            return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot

        if int_mode == "SHADOW":
            checks_failed.append("mode_shadow_parallel")
            reason = "Intelligence mode is SHADOW. Evaluating parallel decisions with zero physical pump actuation."
            return AuthorizationStatus.DEFERRED, reason, checks_passed, checks_failed, input_snapshot

        if int_mode == "ASSISTED":
            # Assisted mode requires user confirmation
            checks_passed.append("mode_assisted_authorized")
            reason = "Recommendation verified and authorized. Ready for user confirmation (ASSISTED mode)."
            return AuthorizationStatus.AUTHORIZED, reason, checks_passed, checks_failed, input_snapshot

        if int_mode == "AUTOMATIC":
            if not config.automatic_irrigation_enabled:
                checks_failed.append("automatic_execution_feature_flag_off")
                reason = "Automatic irrigation execution feature flag is disabled for this field."
                return AuthorizationStatus.BLOCKED, reason, checks_passed, checks_failed, input_snapshot
            checks_passed.append("automatic_execution_enabled")

        # -------------------------------------------------------------
        # ALL CHECKS SATISFIED: AUTHORIZED
        # -------------------------------------------------------------
        reason = f"All {len(checks_passed)} safety and agronomic authorization checks passed. Execution authorized."
        return AuthorizationStatus.AUTHORIZED, reason, checks_passed, checks_failed, input_snapshot

    @classmethod
    def record_authorization(
        cls,
        db: Session,
        decision_log_id: int,
        farm_id: int,
        device_id: Optional[int],
        status: AuthorizationStatus,
        reason: str,
        checks_passed: List[str],
        checks_failed: List[str],
        input_snapshot: Dict[str, Any]
    ) -> IrrigationAuthorizationRecord:
        """Persists the authorization evaluation audit log."""
        record = IrrigationAuthorizationRecord(
            decision_log_id=decision_log_id,
            farm_id=farm_id,
            device_id=device_id,
            status=status.value,
            failure_reason=reason if status != AuthorizationStatus.AUTHORIZED else None,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            input_snapshot=input_snapshot,
            evaluated_at=datetime.utcnow()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
