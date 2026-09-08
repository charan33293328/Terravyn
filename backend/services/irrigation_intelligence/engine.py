"""
Terravyn Production Irrigation Intelligence Engine V1: Primary Orchestrator
"""
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    Farm,
    Device,
    CropDecisionLog,
    IrrigationControlConfig,
    IrrigationAuthorizationRecord,
    IrrigationCommandRecord,
    IrrigationExecutionRecord
)
from services.crop_engine.engine import GreenGramIrrigationDecisionEngine
from services.irrigation_intelligence.config import (
    IrrigationConfigService,
    IntelligenceMode,
    ControlMode
)
from services.irrigation_intelligence.safety_engine import (
    ExecutionSafetyEngine,
    AuthorizationStatus
)
from services.irrigation_intelligence.execution_controller import (
    IrrigationExecutionController,
    CommandStatus,
    ExecutionStatus
)
from services.validation_engine.calibration_manager import FieldCalibrationManager

logger = logging.getLogger(__name__)


class IrrigationIntelligenceEngine:
    """
    Unified entry point for Prompt 8 Production Irrigation Intelligence.
    Separates Layer A (Agricultural Decision) and Layer B (Execution Safety)
    while enforcing hardware boundaries and safe actuation.
    """

    def __init__(self):
        self.crop_engine = GreenGramIrrigationDecisionEngine()

    def evaluate_farm_pipeline(
        self,
        db: Session,
        farm_id: int,
        auto_dispatch: bool = False
    ) -> Dict[str, Any]:
        """
        Runs the full dual-layer evaluation pipeline:
        1. Layer A: Agricultural Decision
        2. Layer B: Execution Safety & Authorization
        3. Optional Execution Dispatch (if in AUTOMATIC mode with flag enabled)
        """
        now = datetime.utcnow()
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            raise ValueError(f"Farm #{farm_id} not found")

        device = db.query(Device).filter(Device.farm_id == farm.id).first()
        config = IrrigationConfigService.get_or_create_config(db, farm.id)

        # -------------------------------------------------------------
        # STEP 1: LAYER A — AGRICULTURAL DECISION
        # -------------------------------------------------------------
        decision_result = self.crop_engine.evaluate_farm(db=db, farm=farm, current_time=now)

        # Retrieve newly persisted decision log
        decision_log = (
            db.query(CropDecisionLog)
            .filter(CropDecisionLog.farm_id == farm.id)
            .order_by(desc(CropDecisionLog.timestamp))
            .first()
        )

        # -------------------------------------------------------------
        # STEP 2: LAYER B — EXECUTION SAFETY & AUTHORIZATION
        # -------------------------------------------------------------
        auth_status, reason, checks_passed, checks_failed, snapshot = ExecutionSafetyEngine.evaluate_authorization(
            db=db,
            farm=farm,
            device=device,
            decision_log=decision_log,
            config=config,
            current_time=now
        )

        auth_record = ExecutionSafetyEngine.record_authorization(
            db=db,
            decision_log_id=decision_log.id,
            farm_id=farm.id,
            device_id=device.id if device else None,
            status=auth_status,
            reason=reason,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            input_snapshot=snapshot
        )

        # -------------------------------------------------------------
        # STEP 3: EXECUTION DISPATCH (CONDITIONAL)
        # -------------------------------------------------------------
        execution_dispatched = False
        command_record = None
        exec_record = None
        dispatch_message = reason

        # Handle SHADOW mode: evaluate parallel decision without pump actuation
        if config.intelligence_mode == IntelligenceMode.SHADOW.value:
            if decision_log.decision == "IRRIGATE":
                created, shadow_cmd, msg = IrrigationExecutionController.create_command(
                    db=db,
                    authorization=auth_record,
                    farm=farm,
                    device=device,
                    config=config,
                    source="SIMULATION"
                )
                if created and shadow_cmd:
                    # In shadow mode, simulate execution
                    _, dispatch_message, exec_record = None, "Shadow mode parallel evaluation recorded.", None
                    command_record = shadow_cmd

        # Handle AUTOMATIC mode execution if authorized and auto_dispatch requested
        elif config.intelligence_mode == IntelligenceMode.AUTOMATIC.value and config.automatic_irrigation_enabled:
            if auth_status == AuthorizationStatus.AUTHORIZED and auto_dispatch:
                created, cmd, msg = IrrigationExecutionController.create_command(
                    db=db,
                    authorization=auth_record,
                    farm=farm,
                    device=device,
                    config=config,
                    source="TERRAVYN_AUTO"
                )
                if created and cmd:
                    import asyncio
                    # Dispatch command
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Synchronous wrapper for test/background context
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as pool:
                                ok, dispatch_message, exec_record = pool.submit(
                                    asyncio.run,
                                    IrrigationExecutionController.dispatch_command(
                                        db=db,
                                        command=cmd,
                                        device=device,
                                        config=config,
                                        is_simulation=config.dry_run_mode
                                    )
                                ).result()
                        else:
                            ok, dispatch_message, exec_record = loop.run_until_complete(
                                IrrigationExecutionController.dispatch_command(
                                    db=db,
                                    command=cmd,
                                    device=device,
                                    config=config,
                                    is_simulation=config.dry_run_mode
                                )
                            )
                    except Exception:
                        ok, dispatch_message, exec_record = asyncio.run(
                            IrrigationExecutionController.dispatch_command(
                                db=db,
                                command=cmd,
                                device=device,
                                config=config,
                                is_simulation=config.dry_run_mode
                            )
                        )
                    execution_dispatched = True
                    command_record = cmd

        return {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "crop": farm.crop_type or "Green Gram (Moong)",
            "growth_stage": decision_result.factors.get("crop_stage", "Vegetative"),
            "layer_a_decision": {
                "decision_id": decision_log.id,
                "decision": decision_result.decision,
                "confidence": decision_result.confidence,
                "reasons": decision_result.reasons,
                "factors": decision_result.factors,
                "recommended_action": decision_result.recommended_action,
                "engine_version": decision_result.engine_version,
                "generated_at": decision_result.generated_at
            },
            "layer_b_authorization": {
                "authorization_id": auth_record.id,
                "status": auth_record.status,
                "reason": reason,
                "checks_passed": checks_passed,
                "checks_failed": checks_failed,
                "evaluated_at": auth_record.evaluated_at.isoformat()
            },
            "execution": {
                "dispatched": execution_dispatched,
                "command_id": command_record.command_id if command_record else None,
                "command_status": command_record.status if command_record else None,
                "message": dispatch_message,
                "execution_status": exec_record.status if exec_record else None
            },
            "config": {
                "intelligence_mode": config.intelligence_mode,
                "automatic_irrigation_enabled": config.automatic_irrigation_enabled,
                "control_mode": device.irrigation_mode if device else config.control_mode,
                "decision_confidence_min": config.decision_confidence_min,
                "cooldown_seconds": config.cooldown_seconds,
                "default_duration_seconds": config.default_duration_seconds,
                "dry_run_mode": config.dry_run_mode
            }
        }

    def get_intelligence_state(self, db: Session, farm_id: int) -> Dict[str, Any]:
        """Returns comprehensive state for frontend dashboard panels."""
        farm = db.query(Farm).filter(Farm.id == farm_id).first()
        if not farm:
            raise ValueError(f"Farm #{farm_id} not found")

        device = db.query(Device).filter(Device.farm_id == farm.id).first()
        config = IrrigationConfigService.get_or_create_config(db, farm.id)

        # Fetch latest decision
        latest_decision = (
            db.query(CropDecisionLog)
            .filter(CropDecisionLog.farm_id == farm.id)
            .order_by(desc(CropDecisionLog.timestamp))
            .first()
        )

        # Fetch latest authorization
        latest_auth = (
            db.query(IrrigationAuthorizationRecord)
            .filter(IrrigationAuthorizationRecord.farm_id == farm.id)
            .order_by(desc(IrrigationAuthorizationRecord.evaluated_at))
            .first()
        )

        # Fetch latest command / execution
        latest_cmd = (
            db.query(IrrigationCommandRecord)
            .filter(IrrigationCommandRecord.farm_id == farm.id)
            .order_by(desc(IrrigationCommandRecord.created_at))
            .first()
        )

        # Active field calibration if present
        active_cal = FieldCalibrationManager.get_active_calibration(
            db=db,
            field_id=farm.id,
            soil_type=farm.soil_type,
            growth_stage=latest_decision.growth_stage if latest_decision else None,
            crop=farm.crop_type or "Green Gram (Moong)"
        )

        return {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "device": {
                "id": device.id if device else None,
                "uid": device.device_uid if device else None,
                "status": device.status if device else "OFFLINE",
                "pump_status": device.pump_status if device else False,
                "irrigation_mode": device.irrigation_mode if device else "AUTO",
                "last_seen": device.last_seen.isoformat() if device and device.last_seen else None
            },
            "intelligence_mode": config.intelligence_mode,
            "automatic_irrigation_enabled": config.automatic_irrigation_enabled,
            "dry_run_mode": config.dry_run_mode,
            "system_status": "READY" if (device and device.status == "ONLINE") else "DEGRADED",
            "latest_decision": {
                "decision": latest_decision.decision if latest_decision else "MONITOR",
                "confidence": latest_decision.confidence if latest_decision else 0,
                "reasons": latest_decision.reasons if latest_decision else [],
                "timestamp": latest_decision.timestamp.isoformat() if latest_decision else None
            } if latest_decision else None,
            "latest_authorization": {
                "status": latest_auth.status if latest_auth else "BLOCKED",
                "reason": latest_auth.failure_reason if latest_auth else "No authorization evaluated yet",
                "evaluated_at": latest_auth.evaluated_at.isoformat() if latest_auth else None
            } if latest_auth else None,
            "latest_command": {
                "command_id": latest_cmd.command_id if latest_cmd else None,
                "status": latest_cmd.status if latest_cmd else None,
                "duration_seconds": latest_cmd.duration_seconds if latest_cmd else None,
                "sent_at": latest_cmd.sent_at.isoformat() if latest_cmd and latest_cmd.sent_at else None
            } if latest_cmd else None,
            "active_calibration": {
                "version": active_cal.version,
                "parameter": active_cal.parameter,
                "value": active_cal.value,
                "hysteresis_delta": active_cal.hysteresis_delta,
                "scope": active_cal.scope
            } if active_cal else None
        }
