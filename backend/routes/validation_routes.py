"""
Terravyn API Routes: Knowledge Validation & Calibration Engine V1
Endpoints for validating scientific literature, evaluating experimental trial evidence,
managing field-specific calibrations, shadow mode testing, activation, rollback, and decision outcome tracking.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from models.domain import (
    KnowledgeValidationRecord,
    FieldCalibrationRecord,
    CalibrationVersion,
    DecisionOutcomeRecord,
    CropDecisionLog,
)
from schemas.domain import (
    ValidationRunRequest,
    ValidationRecordResponse,
    CalibrationCreate,
    CalibrationResponse,
    CalibrationActivateRequest,
    DecisionOutcomeResponse,
)
from services.validation_engine import (
    KnowledgeValidationAndCalibrationEngine,
    FieldCalibrationManager,
    DecisionOutcomeEvaluator,
    ScientificKnowledgeValidator,
    ExperimentalDataValidator,
)

router = APIRouter(prefix="/api/validation", tags=["Knowledge Validation & Calibration"])


@router.post("/run", response_model=ValidationRecordResponse)
def run_validation(
    payload: ValidationRunRequest,
    db: Session = Depends(get_db),
):
    """
    Executes validation on either an external scientific literature claim (DynamicKnowledgeItem)
    or an empirical trial (Experiment candidate).
    """
    try:
        if payload.target_type == "SCIENTIFIC_KNOWLEDGE":
            rec = KnowledgeValidationAndCalibrationEngine.validate_scientific_item(
                db=db,
                knowledge_item_id=payload.target_id,
                target_field_context={
                    "field_id": payload.field_id,
                    "growth_stage": payload.growth_stage,
                    "soil_type": payload.soil_type,
                },
            )
        elif payload.target_type == "EXPERIMENTAL_CANDIDATE":
            rec = KnowledgeValidationAndCalibrationEngine.validate_experimental_trial(
                db=db,
                experiment_id=payload.target_id,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported target_type '{payload.target_type}'.")

        return rec
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation execution failed: {str(e)}")


@router.get("/records", response_model=List[ValidationRecordResponse])
def list_validation_records(
    target_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Lists validation evaluation audit records."""
    q = db.query(KnowledgeValidationRecord)
    if target_type:
        q = q.filter(KnowledgeValidationRecord.target_type == target_type)
    if status:
        q = q.filter(KnowledgeValidationRecord.status == status)

    return q.order_by(desc(KnowledgeValidationRecord.created_at)).limit(limit).all()


@router.get("/records/{record_id}", response_model=ValidationRecordResponse)
def get_validation_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves full details for a validation record including all 10 dimensional scores."""
    rec = db.query(KnowledgeValidationRecord).filter(KnowledgeValidationRecord.id == record_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Validation record #{record_id} not found.")
    return rec


# --- Calibration Endpoints ---

@router.get("/calibrations", response_model=List[CalibrationResponse])
def list_calibrations(
    field_id: Optional[int] = None,
    status: Optional[str] = None,
    parameter: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Lists field-specific calibrations."""
    q = db.query(FieldCalibrationRecord)
    if field_id:
        q = q.filter(FieldCalibrationRecord.field_id == field_id)
    if status:
        q = q.filter(FieldCalibrationRecord.status == status)
    if parameter:
        q = q.filter(FieldCalibrationRecord.parameter == parameter)

    return q.order_by(desc(FieldCalibrationRecord.created_at)).limit(limit).all()


@router.post("/calibrations", response_model=CalibrationResponse, status_code=status.HTTP_201_CREATED)
def create_field_calibration(
    payload: CalibrationCreate,
    db: Session = Depends(get_db),
):
    """Initializes a new candidate field calibration from empirical trial evidence."""
    cal = FieldCalibrationManager.create_calibration(
        db=db,
        parameter=payload.parameter or "capacitive_soil_moisture_threshold",
        field_id=payload.field_id,
        plot_id=payload.plot_id,
        crop=payload.crop or "Green Gram (Moong)",
        growth_stage=payload.growth_stage or "Flowering",
        soil_type=payload.soil_type or "sandy_loam",
        value=payload.value,
        value_range=payload.value_range,
        hysteresis_delta=payload.hysteresis_delta or 10.0,
        scope=payload.scope or "FIELD",
        status=payload.status or "EXPERIMENTAL",
        rationale=payload.rationale,
        experiment_ids=payload.experiment_ids,
    )
    return cal


@router.post("/calibrations/{calibration_id}/shadow", response_model=CalibrationResponse)
def enable_shadow_mode(
    calibration_id: int,
    db: Session = Depends(get_db),
):
    """Transitions a candidate calibration into SHADOW testing mode."""
    try:
        cal = FieldCalibrationManager.enable_shadow_mode(db=db, calibration_id=calibration_id)
        return cal
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/calibrations/{calibration_id}/activate", response_model=CalibrationResponse)
def activate_calibration(
    calibration_id: int,
    payload: Optional[CalibrationActivateRequest] = None,
    db: Session = Depends(get_db),
):
    """Explicitly activates a calibration version for production decision evaluation."""
    try:
        cal = FieldCalibrationManager.activate_calibration(db=db, calibration_id=calibration_id)
        return cal
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/calibrations/{calibration_id}/rollback", response_model=CalibrationResponse)
def rollback_calibration(
    calibration_id: int,
    db: Session = Depends(get_db),
):
    """Reverts configuration to the previous approved version."""
    try:
        reverted = FieldCalibrationManager.rollback_calibration(db=db, calibration_id=calibration_id)
        return reverted
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/calibrations/{calibration_id}/comparison")
def compare_calibration(
    calibration_id: int,
    db: Session = Depends(get_db),
):
    """
    Compares candidate calibration vs currently active baseline configuration:
    threshold differences, evidence count, confidence, risk score, and expected impact.
    """
    candidate = db.query(FieldCalibrationRecord).filter(FieldCalibrationRecord.id == calibration_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Calibration #{calibration_id} not found.")

    # Find current active calibration or standard baseline
    active = FieldCalibrationManager.get_active_calibration(
        db=db,
        field_id=candidate.field_id,
        soil_type=candidate.soil_type,
        growth_stage=candidate.growth_stage,
        crop=candidate.crop,
    )

    baseline_val = 40.0 if candidate.growth_stage in ("Flowering", "Pod Formation") else 32.0
    active_val = active.value if active else baseline_val
    cand_val = candidate.value or 32.0

    diff = round(cand_val - active_val, 1)

    return {
        "candidate": {
            "id": candidate.id,
            "version": candidate.version,
            "parameter": candidate.parameter,
            "growth_stage": candidate.growth_stage,
            "value": cand_val,
            "range": candidate.value_range,
            "hysteresis_delta": candidate.hysteresis_delta,
            "status": candidate.status,
            "confidence": candidate.confidence,
            "sample_count": candidate.sample_count,
            "rationale": candidate.rationale,
        },
        "current_active": {
            "id": active.id if active else None,
            "version": active.version if active else "Base-Rule-v1",
            "value": active_val,
            "status": active.status if active else "STANDARD_RULE",
        },
        "comparison": {
            "threshold_difference": diff,
            "expected_water_impact": (
                "Lower irrigation frequency (reduced water demand)" if diff < 0 else "Higher irrigation sensitivity (prevent moisture stress)"
            ) if diff != 0 else "Equivalent threshold",
            "risk_assessment": "LOW" if abs(diff) <= 4.0 else "MODERATE",
            "activation_ready": candidate.confidence >= 65 and candidate.sample_count >= 5,
        },
    }


# --- Decision Outcome Endpoints ---

@router.get("/decisions/outcomes")
def get_decision_outcomes(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    """Retrieves decision outcome classifications and historical accuracy rates."""
    stats = DecisionOutcomeEvaluator.get_outcome_statistics(db=db, limit=limit)
    outcomes = (
        db.query(DecisionOutcomeRecord)
        .order_by(desc(DecisionOutcomeRecord.created_at))
        .limit(limit)
        .all()
    )
    return {
        "statistics": stats,
        "recent_outcomes": [
            {
                "id": o.id,
                "decision_log_id": o.decision_log_id,
                "classification": o.classification,
                "hours_to_response": o.hours_to_response,
                "plant_response_summary": o.plant_response_summary,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in outcomes
        ],
    }


@router.post("/decisions/{decision_log_id}/evaluate-outcome", response_model=DecisionOutcomeResponse)
def evaluate_decision_outcome(
    decision_log_id: int,
    db: Session = Depends(get_db),
):
    """Evaluates field outcome for a specific decision log."""
    try:
        outcome = DecisionOutcomeEvaluator.evaluate_decision_outcome(db=db, decision_log_id=decision_log_id)
        return outcome
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
