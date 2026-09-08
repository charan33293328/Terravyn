"""
Terravyn Validation Engine: Field Calibration Manager
Manages field-specific, growth-stage-specific parameters with range-based trigger zones,
hysteresis, immutable versioning, shadow mode execution, and non-destructive rollback.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    FieldCalibrationRecord,
    CalibrationVersion,
    ShadowDecisionLog,
    CropDecisionLog,
    Farm,
)


class FieldCalibrationManager:
    """Manages the creation, versioning, shadow testing, activation, and rollback of field calibrations."""

    @classmethod
    def create_calibration(
        cls,
        db: Session,
        parameter: str,
        field_id: Optional[int] = None,
        plot_id: Optional[int] = None,
        device_id: Optional[int] = None,
        crop: str = "Green Gram (Moong)",
        variety: Optional[str] = None,
        soil_type: Optional[str] = "sandy_loam",
        growth_stage: Optional[str] = "Flowering",
        value: Optional[float] = None,
        value_range: Optional[Dict[str, float]] = None,
        hysteresis_delta: Optional[float] = 10.0,
        unit: str = "% volumetric",
        scope: str = "FIELD",
        status: str = "EXPERIMENTAL",
        confidence: int = 60,
        sample_count: int = 0,
        experiment_ids: Optional[List[int]] = None,
        rationale: Optional[str] = None,
        actor_id: Optional[int] = None,
    ) -> FieldCalibrationRecord:
        """Initializes a new candidate or experimental field calibration."""
        # Find latest version for this parameter + scope
        latest = (
            db.query(FieldCalibrationRecord)
            .filter(
                FieldCalibrationRecord.field_id == field_id,
                FieldCalibrationRecord.parameter == parameter,
                FieldCalibrationRecord.growth_stage == growth_stage,
            )
            .order_by(desc(FieldCalibrationRecord.version))
            .first()
        )
        new_version = (latest.version + 1) if latest else 1

        cal = FieldCalibrationRecord(
            field_id=field_id,
            plot_id=plot_id,
            device_id=device_id,
            crop=crop,
            variety=variety,
            soil_type=soil_type,
            growth_stage=growth_stage,
            parameter=parameter,
            value=value,
            value_range=value_range or {"min": (value - 3.0) if value else 32.0, "max": (value + 3.0) if value else 38.0, "stop_threshold": (value + hysteresis_delta) if value else 45.0},
            hysteresis_delta=hysteresis_delta,
            unit=unit,
            scope=scope,
            status=status,
            confidence=confidence,
            sample_count=sample_count,
            experiment_ids=experiment_ids or [],
            version=new_version,
            previous_version_id=latest.id if latest else None,
            rationale=rationale or "Empirical calibration candidate generated from trial observations.",
            created_at=datetime.utcnow(),
        )
        db.add(cal)
        db.commit()
        db.refresh(cal)

        # Log to immutable version audit
        cls._log_version_event(
            db=db,
            calibration=cal,
            action="CREATED",
            actor_id=actor_id,
            notes=f"Created version {cal.version} for parameter '{parameter}'.",
        )
        return cal

    @classmethod
    def enable_shadow_mode(
        cls,
        db: Session,
        calibration_id: int,
        actor_id: Optional[int] = None,
    ) -> FieldCalibrationRecord:
        """Transitions calibration to SHADOW mode to test side-by-side with production."""
        cal = db.query(FieldCalibrationRecord).filter(FieldCalibrationRecord.id == calibration_id).first()
        if not cal:
            raise ValueError(f"Calibration #{calibration_id} not found.")

        cal.status = "SHADOW"
        cal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cal)

        cls._log_version_event(
            db=db,
            calibration=cal,
            action="SHADOW_ENABLED",
            actor_id=actor_id,
            notes="Shadow mode enabled. Decisions will be evaluated in parallel without pump actuation.",
        )
        return cal

    @classmethod
    def activate_calibration(
        cls,
        db: Session,
        calibration_id: int,
        actor_id: Optional[int] = None,
    ) -> FieldCalibrationRecord:
        """
        Explicitly activates a calibration for production decision evaluation.
        Supersedes any previously active calibration for the same scope/field/parameter/stage.
        """
        cal = db.query(FieldCalibrationRecord).filter(FieldCalibrationRecord.id == calibration_id).first()
        if not cal:
            raise ValueError(f"Calibration #{calibration_id} not found.")

        # Supersede old active calibration for this field/parameter/stage
        old_actives = (
            db.query(FieldCalibrationRecord)
            .filter(
                FieldCalibrationRecord.field_id == cal.field_id,
                FieldCalibrationRecord.parameter == cal.parameter,
                FieldCalibrationRecord.growth_stage == cal.growth_stage,
                FieldCalibrationRecord.status == "ACTIVE",
                FieldCalibrationRecord.id != cal.id,
            )
            .all()
        )
        for old in old_actives:
            old.status = "SUPERSEDED"
            cls._log_version_event(
                db=db,
                calibration=old,
                action="SUPERSEDED",
                actor_id=actor_id,
                notes=f"Superseded by newly activated version {cal.version}.",
            )

        cal.status = "ACTIVE"
        cal.activated_at = datetime.utcnow()
        cal.activated_by = actor_id
        cal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cal)

        cls._log_version_event(
            db=db,
            calibration=cal,
            action="ACTIVATED",
            actor_id=actor_id,
            notes=f"Version {cal.version} explicitly activated for field decision evaluation.",
        )
        return cal

    @classmethod
    def rollback_calibration(
        cls,
        db: Session,
        calibration_id: int,
        actor_id: Optional[int] = None,
    ) -> FieldCalibrationRecord:
        """
        Non-destructive rollback: Reverts to the previous version and sets current version to SUPERSEDED.
        """
        current = db.query(FieldCalibrationRecord).filter(FieldCalibrationRecord.id == calibration_id).first()
        if not current:
            raise ValueError(f"Calibration #{calibration_id} not found.")

        if not current.previous_version_id:
            raise ValueError("No previous configuration version exists to rollback to.")

        prev = db.query(FieldCalibrationRecord).filter(FieldCalibrationRecord.id == current.previous_version_id).first()
        if not prev:
            raise ValueError(f"Previous version #{current.previous_version_id} not found in database.")

        current.status = "SUPERSEDED"
        current.updated_at = datetime.utcnow()

        prev.status = "ACTIVE"
        prev.activated_at = datetime.utcnow()
        prev.activated_by = actor_id
        prev.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(current)
        db.refresh(prev)

        cls._log_version_event(
            db=db,
            calibration=current,
            action="ROLLED_BACK",
            actor_id=actor_id,
            notes=f"Rolled back from version {current.version} to version {prev.version}.",
        )
        cls._log_version_event(
            db=db,
            calibration=prev,
            action="ACTIVATED",
            actor_id=actor_id,
            notes=f"Re-activated version {prev.version} via rollback.",
        )
        return prev

    @classmethod
    def run_shadow_evaluation(
        cls,
        db: Session,
        decision_log: CropDecisionLog,
        calibration: FieldCalibrationRecord,
    ) -> ShadowDecisionLog:
        """
        Executes parallel shadow evaluation using the candidate calibration parameters.
        Evaluates hypothetical irrigation trigger without actuating pumps or modifying production logs.
        """
        moisture = decision_log.soil_moisture
        prod_decision = decision_log.decision

        # Get calibrated trigger threshold
        trigger_val = calibration.value
        if trigger_val is None and calibration.value_range:
            trigger_val = calibration.value_range.get("min", 32.0)
        trigger_val = trigger_val or 32.0

        # Simulate shadow decision
        if moisture is not None:
            if moisture < trigger_val:
                # Check weather forecast as usual
                rain_forecast = decision_log.rainfall_forecast_24h or 0.0
                rain_prob = decision_log.rainfall_probability_24h or 0
                if rain_forecast >= 5.0 and rain_prob >= 50:
                    shadow_decision = "WAIT"
                else:
                    shadow_decision = "IRRIGATE"
            else:
                shadow_decision = "MONITOR"
        else:
            shadow_decision = "ALERT"

        divergence = prod_decision != shadow_decision

        simulated_impact = {
            "calibrated_trigger": trigger_val,
            "calibrated_stop": calibration.value_range.get("stop_threshold") if calibration.value_range else None,
            "hysteresis_applied": calibration.hysteresis_delta,
            "moisture_observed": moisture,
            "divergence_flag": divergence,
            "water_impact_estimate": "+1.5 L" if (prod_decision == "WAIT" and shadow_decision == "IRRIGATE") else ("-1.5 L" if (prod_decision == "IRRIGATE" and shadow_decision == "WAIT") else "0.0 L"),
            "risk_assessment": "LOW" if not divergence else "MODERATE",
        }

        shadow_log = ShadowDecisionLog(
            decision_log_id=decision_log.id,
            calibration_id=calibration.id,
            production_decision=prod_decision,
            shadow_decision=shadow_decision,
            production_factors=decision_log.factors,
            shadow_factors={"calibrated_parameter": calibration.parameter, "calibrated_value": trigger_val, "version": calibration.version},
            divergence=divergence,
            simulated_impact=simulated_impact,
        )
        db.add(shadow_log)
        db.commit()
        db.refresh(shadow_log)
        return shadow_log

    @classmethod
    def get_active_calibration(
        cls,
        db: Session,
        field_id: Optional[int],
        soil_type: Optional[str] = None,
        growth_stage: Optional[str] = None,
        crop: str = "Green Gram (Moong)",
    ) -> Optional[FieldCalibrationRecord]:
        """Queries for an active, approved field calibration matching the field and growth stage."""
        query = db.query(FieldCalibrationRecord).filter(
            FieldCalibrationRecord.status == "ACTIVE",
            FieldCalibrationRecord.crop == crop,
        )
        if field_id:
            query = query.filter(FieldCalibrationRecord.field_id == field_id)
        if growth_stage:
            query = query.filter(FieldCalibrationRecord.growth_stage == growth_stage)

        return query.first()

    @classmethod
    def get_shadow_calibrations(
        cls,
        db: Session,
        field_id: Optional[int],
        growth_stage: Optional[str] = None,
    ) -> List[FieldCalibrationRecord]:
        """Queries for calibrations currently running in SHADOW mode."""
        query = db.query(FieldCalibrationRecord).filter(FieldCalibrationRecord.status == "SHADOW")
        if field_id:
            query = query.filter(FieldCalibrationRecord.field_id == field_id)
        if growth_stage:
            query = query.filter(FieldCalibrationRecord.growth_stage == growth_stage)
        return query.all()

    @classmethod
    def _log_version_event(
        cls,
        db: Session,
        calibration: FieldCalibrationRecord,
        action: str,
        actor_id: Optional[int] = None,
        notes: Optional[str] = None,
    ):
        """Appends immutable configuration version record."""
        v = CalibrationVersion(
            calibration_id=calibration.id,
            version=calibration.version,
            action=action,
            config_snapshot={
                "parameter": calibration.parameter,
                "value": calibration.value,
                "value_range": calibration.value_range,
                "hysteresis_delta": calibration.hysteresis_delta,
                "scope": calibration.scope,
                "status": calibration.status,
                "growth_stage": calibration.growth_stage,
                "soil_type": calibration.soil_type,
                "confidence": calibration.confidence,
                "version": calibration.version,
            },
            actor_id=actor_id,
            notes=notes,
        )
        db.add(v)
        db.commit()
