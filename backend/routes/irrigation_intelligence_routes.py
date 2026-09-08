"""
Terravyn Irrigation Intelligence & Safe Automatic Control Routes (Prompt 8)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any

from database.connection import get_db
from models.domain import (
    Farm,
    Device,
    CropDecisionLog,
    IrrigationAuthorizationRecord,
    IrrigationCommandRecord,
    IrrigationExecutionRecord
)
from schemas.domain import (
    IrrigationControlConfigResponse,
    IrrigationControlConfigUpdate,
    IrrigationAuthorizationResponse,
    IrrigationCommandResponse,
    IrrigationCommandAckRequest,
    IrrigationCommandCompleteRequest,
    IrrigationExecutionResponse
)
from services.irrigation_intelligence import (
    IrrigationIntelligenceEngine,
    IrrigationConfigService,
    IrrigationExecutionController,
    AuthorizationStatus,
    IntelligenceMode
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/irrigation", tags=["Irrigation Intelligence & Safe Automatic Control"])
engine = IrrigationIntelligenceEngine()


@router.get("/intelligence/{farm_id}")
def get_intelligence_state(farm_id: int, db: Session = Depends(get_db)):
    """Returns the complete intelligence and authorization state for a farm field."""
    try:
        return engine.get_intelligence_state(db=db, farm_id=farm_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Failed to retrieve intelligence state")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate/{farm_id}")
def evaluate_irrigation_intelligence(
    farm_id: int,
    auto_dispatch: bool = Query(False, description="Attempt dispatch if in AUTOMATIC mode and authorized"),
    db: Session = Depends(get_db)
):
    """
    Executes full dual-layer evaluation:
    Layer A: Agricultural Decision (Green Gram Agronomy + Validated KB + Active Calibration)
    Layer B: Execution Safety & Authorization (Hardware health, low water guard, manual mode guard, cooldown)
    """
    try:
        return engine.evaluate_farm_pipeline(db=db, farm_id=farm_id, auto_dispatch=auto_dispatch)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Irrigation intelligence evaluation failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dry-run/{farm_id}")
def dry_run_irrigation_intelligence(farm_id: int, db: Session = Depends(get_db)):
    """
    Runs complete decision and authorization pipeline, but strictly enforces dry-run mode
    with zero physical relay actuation.
    """
    try:
        config = IrrigationConfigService.get_or_create_config(db, farm_id)
        original_dry_run = config.dry_run_mode
        config.dry_run_mode = True
        db.commit()

        result = engine.evaluate_farm_pipeline(db=db, farm_id=farm_id, auto_dispatch=True)

        config.dry_run_mode = original_dry_run
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("Dry run failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{farm_id}", response_model=IrrigationControlConfigResponse)
def get_irrigation_config(farm_id: int, db: Session = Depends(get_db)):
    """Gets field irrigation intelligence configuration."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm #{farm_id} not found")
    return IrrigationConfigService.get_or_create_config(db, farm_id)


@router.put("/config/{farm_id}", response_model=IrrigationControlConfigResponse)
def update_irrigation_config(
    farm_id: int,
    updates: IrrigationControlConfigUpdate,
    db: Session = Depends(get_db)
):
    """Updates field irrigation intelligence configuration."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm #{farm_id} not found")
    
    update_data = updates.model_dump(exclude_unset=True)
    return IrrigationConfigService.update_config(db, farm_id, update_data)


@router.post("/execute/{authorization_id}")
async def execute_authorized_irrigation(
    authorization_id: int,
    duration_seconds: Optional[int] = Query(None, description="Optional custom duration in seconds"),
    db: Session = Depends(get_db)
):
    """
    Executes an authorized irrigation decision (used in ASSISTED mode after farmer confirmation,
    or manual operator trigger).
    """
    auth = db.query(IrrigationAuthorizationRecord).filter(
        IrrigationAuthorizationRecord.id == authorization_id
    ).first()
    if not auth:
        raise HTTPException(status_code=404, detail="Authorization record not found")

    if auth.status != AuthorizationStatus.AUTHORIZED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute: Authorization status is {auth.status}. Reason: {auth.failure_reason}"
        )

    farm = db.query(Farm).filter(Farm.id == auth.farm_id).first()
    device = db.query(Device).filter(Device.id == auth.device_id).first() if auth.device_id else None
    if not device:
        raise HTTPException(status_code=400, detail="No device associated with this authorization")

    config = IrrigationConfigService.get_or_create_config(db, auth.farm_id)

    # Double check manual mode priority
    if device.irrigation_mode == "MANUAL":
        raise HTTPException(
            status_code=400,
            detail="Device is currently in MANUAL mode. Cannot dispatch automatic/assisted irrigation command."
        )

    created, cmd, msg = IrrigationExecutionController.create_command(
        db=db,
        authorization=auth,
        farm=farm,
        device=device,
        config=config,
        source="USER_ASSISTED" if config.intelligence_mode == IntelligenceMode.ASSISTED.value else "TERRAVYN_AUTO",
        duration_seconds=duration_seconds
    )
    if not created:
        raise HTTPException(status_code=409, detail=msg)

    ok, dispatch_msg, exec_record = await IrrigationExecutionController.dispatch_command(
        db=db,
        command=cmd,
        device=device,
        config=config,
        is_simulation=config.dry_run_mode
    )

    return {
        "success": ok,
        "message": dispatch_msg,
        "command_id": cmd.command_id,
        "status": cmd.status,
        "duration_seconds": cmd.duration_seconds
    }


@router.post("/commands/{command_id}/ack")
def acknowledge_command(
    command_id: str,
    ack: IrrigationCommandAckRequest,
    db: Session = Depends(get_db)
):
    """ESP32 calls this endpoint to acknowledge command receipt."""
    success = IrrigationExecutionController.process_ack(
        db=db,
        command_id=command_id,
        reported_status=ack.status
    )
    if not success:
        raise HTTPException(status_code=404, detail="Command not found")
    return {"status": "success", "command_id": command_id, "ack_status": ack.status}


@router.post("/commands/{command_id}/complete")
async def complete_command(
    command_id: str,
    req: IrrigationCommandCompleteRequest,
    db: Session = Depends(get_db)
):
    """ESP32 calls this endpoint when physical irrigation cycle finishes."""
    success = await IrrigationExecutionController.complete_execution(
        db=db,
        command_id=command_id,
        actual_duration=req.actual_duration_seconds,
        water_volume_liters=req.water_volume_liters
    )
    if not success:
        raise HTTPException(status_code=404, detail="Command not found")
    return {"status": "success", "command_id": command_id, "cycle_state": "COMPLETED"}


@router.get("/history/{farm_id}")
def get_irrigation_history(
    farm_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Returns execution, command, and authorization history for a farm."""
    authorizations = (
        db.query(IrrigationAuthorizationRecord)
        .filter(IrrigationAuthorizationRecord.farm_id == farm_id)
        .order_by(desc(IrrigationAuthorizationRecord.evaluated_at))
        .limit(limit)
        .all()
    )

    commands = (
        db.query(IrrigationCommandRecord)
        .filter(IrrigationCommandRecord.farm_id == farm_id)
        .order_by(desc(IrrigationCommandRecord.created_at))
        .limit(limit)
        .all()
    )

    executions = (
        db.query(IrrigationExecutionRecord)
        .filter(IrrigationExecutionRecord.farm_id == farm_id)
        .order_by(desc(IrrigationExecutionRecord.created_at))
        .limit(limit)
        .all()
    )

    return {
        "farm_id": farm_id,
        "authorizations": [
            {
                "id": a.id,
                "status": a.status,
                "reason": a.failure_reason,
                "evaluated_at": a.evaluated_at.isoformat()
            } for a in authorizations
        ],
        "commands": [
            {
                "id": c.id,
                "command_id": c.command_id,
                "command_type": c.command_type,
                "source": c.source,
                "duration_seconds": c.duration_seconds,
                "status": c.status,
                "created_at": c.created_at.isoformat()
            } for c in commands
        ],
        "executions": [
            {
                "id": e.id,
                "status": e.status,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "actual_duration_seconds": e.actual_duration_seconds,
                "water_volume_liters": e.water_volume_liters,
                "state_reconciled": e.state_reconciled
            } for e in executions
        ]
    }
