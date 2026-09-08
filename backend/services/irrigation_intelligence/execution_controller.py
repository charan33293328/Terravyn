"""
Terravyn Irrigation Intelligence: Execution Controller, Command Lifecycle, & ACK Protocol
"""
import uuid
import logging
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    Device,
    Farm,
    IrrigationCommandRecord,
    IrrigationExecutionRecord,
    IrrigationAuthorizationRecord,
    IrrigationControlConfig,
    IrrigationLog,
    Alert
)

logger = logging.getLogger(__name__)


class CommandStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    SIMULATED = "SIMULATED"
    SKIPPED_DRY_RUN = "SKIPPED_DRY_RUN"


class ExecutionStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    ABORTED_SAFETY = "ABORTED_SAFETY"
    TIMEOUT = "TIMEOUT"
    FAILED = "FAILED"
    SIMULATED = "SIMULATED"


class IrrigationExecutionController:
    """
    Handles safe command generation, idempotency checks, pre-execution race condition
    guards, hardware dispatch, ACK tracking, state reconciliation, and max runtime limits.
    """

    @classmethod
    def create_command(
        cls,
        db: Session,
        authorization: IrrigationAuthorizationRecord,
        farm: Farm,
        device: Device,
        config: IrrigationControlConfig,
        command_type: str = "IRRIGATION_ON",
        source: str = "TERRAVYN_AUTO",
        duration_seconds: Optional[int] = None
    ) -> Tuple[bool, Optional[IrrigationCommandRecord], str]:
        """
        Generates an idempotent irrigation command record.
        Enforces idempotency and pre-execution race condition guards.
        """
        now = datetime.utcnow()
        duration = duration_seconds or config.default_duration_seconds

        # -------------------------------------------------------------
        # 1. PRE-EXECUTION RACE CONDITION GUARD
        # -------------------------------------------------------------
        # Check if rain began between decision calculation and execution command
        if getattr(device, "last_rain_detected", False):
            msg = "Pre-execution race condition guard: Rain detected on field sensor immediately prior to command dispatch. Actuation cancelled."
            logger.warning(f"[ExecutionController] {msg}")
            return False, None, msg

        # Check if water level dropped critically in the interim
        if getattr(device, "last_low_water_alert", False):
            msg = "Pre-execution race condition guard: Low water alert reported immediately prior to command dispatch. Actuation cancelled."
            logger.warning(f"[ExecutionController] {msg}")
            return False, None, msg

        # -------------------------------------------------------------
        # 2. COMMAND IDEMPOTENCY GUARD
        # -------------------------------------------------------------
        # Generate stable idempotency key combining authorization, device, and 60-second window
        time_slot = now.strftime("%Y%m%d%H%M")
        idempotency_key = f"CMD-{device.id}-{authorization.id}-{time_slot}"

        existing_cmd = db.query(IrrigationCommandRecord).filter(
            IrrigationCommandRecord.idempotency_key == idempotency_key
        ).first()

        if existing_cmd:
            msg = f"Duplicate command prevented by idempotency guard ({idempotency_key}). Active command status: {existing_cmd.status}."
            logger.info(f"[ExecutionController] {msg}")
            return False, existing_cmd, msg

        command_id = f"cmd-{uuid.uuid4().hex[:12]}"

        command = IrrigationCommandRecord(
            command_id=command_id,
            idempotency_key=idempotency_key,
            authorization_id=authorization.id,
            farm_id=farm.id,
            device_id=device.id,
            command_type=command_type,
            source=source,
            duration_seconds=duration,
            max_runtime_seconds=config.max_pump_runtime_seconds,
            status=CommandStatus.PENDING.value,
            created_at=now
        )
        db.add(command)
        db.commit()
        db.refresh(command)
        return True, command, "Command created and ready for dispatch."

    @classmethod
    async def dispatch_command(
        cls,
        db: Session,
        command: IrrigationCommandRecord,
        device: Device,
        config: IrrigationControlConfig,
        is_simulation: bool = False
    ) -> Tuple[bool, str, Optional[IrrigationExecutionRecord]]:
        """
        Dispatches the command. Supports SIMULATION mode, DRY_RUN mode, and LIVE actuation.
        """
        now = datetime.utcnow()

        # -------------------------------------------------------------
        # SIMULATION / DRY RUN PATH (ZERO PHYSICAL RELAY ACTUATION)
        # -------------------------------------------------------------
        if is_simulation or command.source == "SIMULATION" or config.intelligence_mode == "SHADOW":
            command.status = CommandStatus.SIMULATED.value
            command.sent_at = now
            command.ack_at = now
            command.executed_at = now

            exec_record = IrrigationExecutionRecord(
                command_id=command.id,
                device_id=device.id,
                farm_id=command.farm_id,
                decision_log_id=command.authorization.decision_log_id if command.authorization else None,
                start_time=now,
                end_time=now + timedelta(seconds=command.duration_seconds),
                actual_duration_seconds=float(command.duration_seconds),
                water_volume_liters=None,  # Not fabricated
                status=ExecutionStatus.SIMULATED.value,
                desired_pump_state=True,
                reported_pump_state=False,  # Physical pump remained off
                state_reconciled=True,
                notes="Simulated execution record for shadow testing. Physical pump remained untouched.",
                created_at=now
            )
            db.add(exec_record)
            db.commit()
            db.refresh(command)
            db.refresh(exec_record)
            return True, "Simulated command logged successfully without hardware actuation.", exec_record

        if config.dry_run_mode:
            command.status = CommandStatus.SKIPPED_DRY_RUN.value
            command.sent_at = now
            db.commit()
            return True, "Dry-run mode active. Command authorized but physical execution skipped.", None

        # -------------------------------------------------------------
        # LIVE HARDWARE ACTUATION PATH
        # -------------------------------------------------------------
        # 1. Update command status
        command.status = CommandStatus.SENT.value
        command.sent_at = now
        command.timeout_at = now + timedelta(seconds=config.max_pump_runtime_seconds + 30)

        # 2. Update device desired pump status and audit log
        device.pump_status = True
        log = IrrigationLog(
            device_id=device.id,
            action="pump_on",
            triggered_by=command.source.lower()
        )
        db.add(log)

        # 3. Create active execution record
        exec_record = IrrigationExecutionRecord(
            command_id=command.id,
            device_id=device.id,
            farm_id=command.farm_id,
            decision_log_id=command.authorization.decision_log_id if command.authorization else None,
            start_time=now,
            actual_duration_seconds=None,
            water_volume_liters=None,
            status=ExecutionStatus.RUNNING.value,
            desired_pump_state=True,
            reported_pump_state=None,  # Awaiting ESP32 telemetry confirmation
            state_reconciled=False,
            notes=f"Dispatched command {command.command_id} (duration: {command.duration_seconds}s)",
            created_at=now
        )
        db.add(exec_record)
        db.commit()

        # 4. Broadcast to ESP32 via WebSocket if connected
        try:
            from services.websocket import manager
            await manager.broadcast_to_device(device.id, {
                "type": "command",
                "command": "pump",
                "action": "on",
                "command_id": command.command_id,
                "duration": command.duration_seconds,
                "max_runtime": command.max_runtime_seconds,
                "timestamp": now.isoformat()
            })
            logger.info(f"[ExecutionController] Broadcasted pump ON command {command.command_id} to device {device.device_uid}")
        except Exception as e:
            logger.warning(f"[ExecutionController] WebSocket broadcast non-fatal exception: {e}")

        return True, f"Command {command.command_id} successfully dispatched to ESP32.", exec_record

    @classmethod
    def process_ack(cls, db: Session, command_id: str, reported_status: str = "ACKNOWLEDGED") -> bool:
        """Processes command acknowledgement from ESP32."""
        now = datetime.utcnow()
        command = db.query(IrrigationCommandRecord).filter(IrrigationCommandRecord.command_id == command_id).first()
        if not command:
            return False

        command.status = CommandStatus.ACKNOWLEDGED.value
        command.ack_at = now
        db.commit()
        return True

    @classmethod
    async def complete_execution(
        cls,
        db: Session,
        command_id: str,
        actual_duration: Optional[float] = None,
        water_volume_liters: Optional[float] = None
    ) -> bool:
        """
        Marks an execution complete, shuts off the pump safely, and logs completion.
        """
        now = datetime.utcnow()
        command = db.query(IrrigationCommandRecord).filter(IrrigationCommandRecord.command_id == command_id).first()
        if not command:
            return False

        device = db.query(Device).filter(Device.id == command.device_id).first()
        if device:
            device.pump_status = False

        command.status = CommandStatus.EXECUTED.value
        command.executed_at = now

        exec_record = db.query(IrrigationExecutionRecord).filter(
            IrrigationExecutionRecord.command_id == command.id
        ).first()

        if exec_record:
            exec_record.status = ExecutionStatus.COMPLETED.value
            exec_record.end_time = now
            if actual_duration is not None:
                exec_record.actual_duration_seconds = actual_duration
            elif exec_record.start_time:
                exec_record.actual_duration_seconds = (now - exec_record.start_time).total_seconds()
            exec_record.water_volume_liters = water_volume_liters  # null if not measured
            exec_record.desired_pump_state = False
            exec_record.reported_pump_state = False
            exec_record.state_reconciled = True

        log = IrrigationLog(
            device_id=command.device_id,
            action="pump_off",
            triggered_by=command.source.lower()
        )
        db.add(log)
        db.commit()

        # Broadcast pump OFF command to hardware
        try:
            from services.websocket import manager
            if device:
                await manager.broadcast_to_device(device.id, {
                    "type": "command",
                    "command": "pump",
                    "action": "off",
                    "command_id": command.command_id,
                    "timestamp": now.isoformat()
                })
        except Exception:
            pass

        return True

    @classmethod
    async def enforce_max_runtime(cls, db: Session, device_id: int) -> bool:
        """
        Enforces hard maximum pump runtime to prevent runaway irrigation.
        """
        now = datetime.utcnow()
        active_exec = (
            db.query(IrrigationExecutionRecord)
            .filter(
                IrrigationExecutionRecord.device_id == device_id,
                IrrigationExecutionRecord.status == ExecutionStatus.RUNNING.value
            )
            .order_by(desc(IrrigationExecutionRecord.start_time))
            .first()
        )
        if not active_exec or not active_exec.start_time:
            return False

        duration = (now - active_exec.start_time).total_seconds()
        command = db.query(IrrigationCommandRecord).filter(IrrigationCommandRecord.id == active_exec.command_id).first()
        max_limit = command.max_runtime_seconds if command else 300

        if duration >= max_limit:
            logger.warning(f"[ExecutionController] Pump on device {device_id} exceeded maximum runtime ({duration}s >= {max_limit}s). Forcing OFF.")
            active_exec.status = ExecutionStatus.ABORTED_SAFETY.value
            active_exec.end_time = now
            active_exec.actual_duration_seconds = duration
            active_exec.notes = f"MAX_RUNTIME_REACHED: Hard safety cutoff triggered after {int(duration)}s."

            device = db.query(Device).filter(Device.id == device_id).first()
            if device:
                device.pump_status = False

            # Create Alert
            alert = Alert(
                farmer_id=device.farmer_id if device else None,
                farm_id=active_exec.farm_id,
                device_id=device_id,
                title="Max Pump Runtime Safety Cutoff",
                description=f"Pump exceeded maximum continuous runtime ({int(duration)}s >= {max_limit}s). Forced OFF.",
                category="Hardware Safety",
                severity="CRITICAL",
                status="UNREAD",
                created_at=now
            )
            db.add(alert)
            db.commit()

            # Broadcast force off
            try:
                from services.websocket import manager
                await manager.broadcast_to_device(device_id, {
                    "type": "command",
                    "command": "pump",
                    "action": "off",
                    "reason": "MAX_RUNTIME_REACHED"
                })
            except Exception:
                pass
            return True

        return False
