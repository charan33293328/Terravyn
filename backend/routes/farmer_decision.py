import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func
from typing import List, Optional

from database.connection import get_db
from models.domain import User, Farmer, Farm, Device, CropDecisionLog, CropExperimentLog, DeviceTelemetry
from schemas.domain import (
    DecisionResponse, StageOverrideRequest, DecisionLogResponse,
    ExperimentLogCreate, ExperimentLogResponse, ExperimentPlotSummary,
    CropProfileResponse, VarietyResponse, GrowthStageResponse,
    FarmCropStatusResponse
)
from auth.security import get_current_active_user
from services.crop_engine import (
    GreenGramIrrigationDecisionEngine, ALL_STAGES, ENGINE_VERSION
)
from services.crop_engine.knowledge_base import knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Crop Decision Engine & Experiments"])
engine = GreenGramIrrigationDecisionEngine()


def get_farmer_from_user(db: Session, user: User) -> Farmer:
    conditions = [func.lower(Farmer.email) == func.lower(user.email)]
    if user.phone_number:
        conditions.append(Farmer.phone == user.phone_number)
    return db.query(Farmer).filter(or_(*conditions)).first()


@router.get("/api/farmer/farms/{farm_id}/decision", response_model=DecisionResponse)
def get_farm_decision(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the explainable Green Gram irrigation recommendation for a specific farm field.
    Evaluates in-situ soil moisture, growth stage, weather, forecast, and cooldown.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    res = engine.evaluate_farm(db, farm)
    return DecisionResponse(
        farm_id=farm.id,
        farm_name=farm.name,
        crop=farm.crop_type or "Green Gram (Moong)",
        variety=farm.crop_variety,
        growth_stage=res.factors.get("crop_stage", "Vegetative"),
        growth_stage_manual=bool(farm.growth_stage_override),
        plot_type=getattr(farm, "plot_type", "STANDARD") or "STANDARD",
        experiment_active=getattr(farm, "experiment_active", False) or False,
        decision=res.decision,
        confidence=res.confidence,
        reasons=res.reasons,
        factors=res.factors,
        recommended_action=res.recommended_action,
        engine_version=res.engine_version,
        generated_at=res.generated_at,
        evidence=res.evidence,
        citations=res.citations
    )


@router.post("/api/farmer/farms/{farm_id}/decision/evaluate", response_model=DecisionResponse)
def force_evaluate_farm_decision(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Force an immediate re-evaluation of the Green Gram decision engine.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    res = engine.evaluate_farm(db, farm)
    return DecisionResponse(
        farm_id=farm.id,
        farm_name=farm.name,
        crop=farm.crop_type or "Green Gram (Moong)",
        variety=farm.crop_variety,
        growth_stage=res.factors.get("crop_stage", "Vegetative"),
        growth_stage_manual=bool(farm.growth_stage_override),
        plot_type=getattr(farm, "plot_type", "STANDARD") or "STANDARD",
        experiment_active=getattr(farm, "experiment_active", False) or False,
        decision=res.decision,
        confidence=res.confidence,
        reasons=res.reasons,
        factors=res.factors,
        recommended_action=res.recommended_action,
        engine_version=res.engine_version,
        generated_at=res.generated_at,
        evidence=res.evidence,
        citations=res.citations
    )


@router.get("/api/farmer/farms/{farm_id}/decision/history", response_model=List[DecisionLogResponse])
def get_decision_history(
    farm_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve historical decision logs for this farm field.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    logs = (
        db.query(CropDecisionLog)
        .filter(CropDecisionLog.farm_id == farm.id)
        .order_by(desc(CropDecisionLog.timestamp))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return logs


@router.post("/api/farmer/farms/{farm_id}/stage-override")
def override_growth_stage(
    farm_id: int,
    payload: StageOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Manually override or reset the crop growth stage for a farm field.
    Pass stage=null to reset to automated calendar calculation.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    if payload.stage and payload.stage not in ALL_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage '{payload.stage}'. Must be one of: {', '.join(ALL_STAGES)}"
        )

    farm.growth_stage_override = payload.stage
    db.commit()
    db.refresh(farm)

    return {
        "message": "Growth stage updated successfully",
        "farm_id": farm.id,
        "growth_stage_override": farm.growth_stage_override,
        "is_manual": bool(farm.growth_stage_override)
    }


# --- Experiment Mode Endpoints ---

@router.get("/api/farmer/experiments/summary/comparison", response_model=List[ExperimentPlotSummary])
def get_experiment_comparison(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Compare experimental plots (TERRAVYN vs CONTROL vs STANDARD) for the current farmer.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farms = db.query(Farm).filter(Farm.farmer_id == farmer.id).all()
    summaries = []

    for f in farms:
        # Sum water used
        total_water = (
            db.query(func.sum(CropExperimentLog.water_used_liters))
            .filter(CropExperimentLog.farm_id == f.id)
            .scalar() or 0.0
        )
        # Count actual irrigation events
        irr_events = (
            db.query(CropExperimentLog)
            .filter(CropExperimentLog.farm_id == f.id, CropExperimentLog.actual_irrigation == True)
            .count()
        )
        # Total observations
        obs_count = db.query(CropExperimentLog).filter(CropExperimentLog.farm_id == f.id).count()

        # Latest decision
        latest_dec = (
            db.query(CropDecisionLog)
            .filter(CropDecisionLog.farm_id == f.id)
            .order_by(desc(CropDecisionLog.timestamp))
            .first()
        )

        dev = db.query(Device).filter(Device.farm_id == f.id).first()

        summaries.append(ExperimentPlotSummary(
            farm_id=f.id,
            farm_name=f.name,
            plot_type=getattr(f, "plot_type", "STANDARD") or "STANDARD",
            crop=f.crop_type or "Green Gram (Moong)",
            variety=f.crop_variety,
            sowing_date=f.sowing_date,
            total_water_used_liters=float(total_water),
            irrigation_events_count=irr_events,
            latest_decision=latest_dec.decision if latest_dec else None,
            latest_moisture=dev.last_soil_moisture if dev else None,
            observations_count=obs_count
        ))

    return summaries


@router.get("/api/farmer/experiments/{farm_id}/logs", response_model=List[ExperimentLogResponse])
def get_farm_experiment_logs(
    farm_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List observation and plant growth tracking logs for a specific farm experiment plot.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    logs = (
        db.query(CropExperimentLog)
        .filter(CropExperimentLog.farm_id == farm.id)
        .order_by(desc(CropExperimentLog.timestamp))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return logs


@router.post("/api/farmer/experiments/{farm_id}/logs", response_model=ExperimentLogResponse)
def create_farm_experiment_log(
    farm_id: int,
    payload: ExperimentLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Record an observation, plant response, or actual irrigation event for the Green Gram experiment.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    entry = CropExperimentLog(
        farm_id=farm.id,
        decision_log_id=payload.decision_log_id,
        recommendation=payload.recommendation,
        actual_irrigation=payload.actual_irrigation,
        water_used_liters=payload.water_used_liters,
        irrigation_duration_minutes=payload.irrigation_duration_minutes,
        plant_height_cm=payload.plant_height_cm,
        canopy_cover_pct=payload.canopy_cover_pct,
        flowering_count_per_m2=payload.flowering_count_per_m2,
        pod_count_per_plant=payload.pod_count_per_plant,
        plant_response_notes=payload.plant_response_notes,
        manual_override=payload.manual_override,
        override_reason=payload.override_reason,
        recorded_by=current_user.id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ---------------------------------------------------------------------------
# Green Gram Knowledge Base V1 Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/farmer/knowledge/green-gram/profile", response_model=CropProfileResponse)
def get_crop_profile(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve high-level Green Gram crop fundamentals, taxonomy, classification, and catalog totals.
    """
    return knowledge_base.get_summary_profile()


@router.get("/api/farmer/knowledge/green-gram/varieties", response_model=List[VarietyResponse])
def get_varieties(current_user: User = Depends(get_current_active_user)):
    """
    List verified Green Gram varieties with ICAR-IIPR / SAU breeding provenance.
    """
    varieties = knowledge_base.list_varieties()
    return [
        VarietyResponse(
            name=v.name,
            developer_institution=v.developer_institution,
            release_year=v.release_year,
            duration_days=v.duration_days,
            duration_range=v.duration_range,
            suitable_seasons=v.suitable_seasons,
            recommended_regions=v.recommended_regions,
            average_yield_q_ha=v.average_yield_q_ha,
            yield_potential_q_ha=v.yield_potential_q_ha,
            seed_characteristics=v.seed_characteristics,
            disease_resistance=v.disease_resistance,
            special_traits=v.special_traits,
            source=v.source.dict() if hasattr(v.source, "dict") else dict(v.source),
            status=v.status.value if hasattr(v.status, "value") else str(v.status),
            confidence=v.confidence.value if hasattr(v.confidence, "value") else str(v.confidence)
        )
        for v in varieties
    ]


@router.get("/api/farmer/knowledge/green-gram/stages", response_model=List[GrowthStageResponse])
def get_growth_stages(current_user: User = Depends(get_current_active_user)):
    """
    List all 10 physiological growth stages of Green Gram with water/temp sensitivities and FAO-56 Kc values.
    """
    stages = knowledge_base.list_stages()
    return [
        GrowthStageResponse(
            stage_id=s.stage_id,
            stage_name=s.stage_name,
            standard_das_range=s.standard_das_range,
            physiological_description=s.physiological_description,
            water_sensitivity=s.water_sensitivity,
            crop_coefficient_kc=s.crop_coefficient_kc,
            temp_min_c=s.temp_min_c,
            temp_opt_c=s.temp_opt_c,
            temp_max_c=s.temp_max_c,
            nutrient_priority=s.nutrient_priority,
            disease_vulnerabilities=s.disease_vulnerabilities,
            pest_vulnerabilities=s.pest_vulnerabilities,
            management_advisory=s.management_advisory,
            source=s.source.dict() if hasattr(s.source, "dict") else dict(s.source),
            status=s.status.value if hasattr(s.status, "value") else str(s.status)
        )
        for s in stages
    ]


@router.get("/api/farmer/knowledge/green-gram/irrigation-rules")
def get_irrigation_rules(
    stage: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve Green Gram irrigation rules, distinguishing validated agronomy from experimental sensor parameters.
    """
    rules = knowledge_base.get_irrigation_rules(growth_stage=stage)
    return [
        {
            "rule_id": r.rule_id,
            "parameter": r.parameter,
            "growth_stage": r.growth_stage,
            "soil_type": r.soil_type,
            "condition": r.condition,
            "action_recommendation": r.action_recommendation,
            "scientific_rationale": r.scientific_rationale,
            "source": r.source.dict() if hasattr(r.source, "dict") else dict(r.source),
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "confidence": r.confidence.value if hasattr(r.confidence, "value") else str(r.confidence),
            "is_experimental": r.is_experimental,
            "calibration_required": r.calibration_required
        }
        for r in rules
    ]


@router.get("/api/farmer/knowledge/green-gram/nutrients")
def get_nutrients_knowledge(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve macro/micronutrient guidelines, deficiency symptoms, and foliar spray technologies.
    """
    return knowledge_base.get_nutrient_guidelines()


@router.get("/api/farmer/knowledge/green-gram/diseases")
def get_diseases_knowledge(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve major Green Gram disease profiles (MYMV, Cercospora, Powdery Mildew, Web Blight, Anthracnose).
    """
    return knowledge_base.get_diseases()


@router.get("/api/farmer/knowledge/green-gram/pests")
def get_pests_knowledge(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve major Green Gram insect pest profiles with Economic Threshold Levels and IPM guidelines.
    """
    return knowledge_base.get_pests()


@router.get("/api/farmer/knowledge/green-gram/sources")
def get_knowledge_sources(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve master catalog of authoritative agricultural sources (ICAR-IIPR, IARI, TNAU, ANGRAU, FAO).
    """
    return knowledge_base.get_all_sources()


@router.get("/api/farmer/farms/{farm_id}/crop-status", response_model=FarmCropStatusResponse)
def get_farm_crop_status(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Comprehensive live Green Gram crop status: integrates stage, environmental status,
    water status, nutrient advisory, disease & pest risks with scientific citations.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    # Evaluate decision engine inputs
    normalized = engine.build_normalized_input(db, farm)
    stage = normalized.crop.growth_stage
    temp = normalized.environment.temperature
    humidity = normalized.environment.humidity
    moisture = normalized.soil.moisture_pct
    rain_24h = normalized.weather.forecast_rainfall_24h

    synth = knowledge_base.synthesize_crop_status(
        growth_stage=stage,
        temperature=temp,
        humidity=humidity,
        soil_moisture=moisture,
        soil_type=farm.soil_type,
        rainfall_forecast_24h=rain_24h,
        soil_ph=getattr(farm, "soil_ph", None),
        soil_ec=getattr(farm, "soil_ec", None)
    )

    all_sources = knowledge_base.get_all_sources()
    citations = [
        all_sources["ICAR-IIPR-2018"].dict(),
        all_sources["TNAU-AGRITECH-PULSES"].dict(),
        all_sources["FAO-56-CROPWAT"].dict()
    ]

    return FarmCropStatusResponse(
        farm_id=farm.id,
        farm_name=farm.name,
        crop=farm.crop_type or "Green Gram (Moong)",
        variety=farm.crop_variety,
        growth_stage=stage,
        days_after_sowing=normalized.crop.age_days,
        water_sensitivity=synth.get("water_sensitivity", "MODERATE"),
        crop_coefficient_kc=synth.get("crop_coefficient_kc", 0.75),
        environmental_status=synth["environmental_status"],
        water_status=synth["water_status"],
        nutrient_advisory=synth["nutrient_advisory"],
        disease_risks=synth["disease_risks"],
        pest_risks=synth["pest_risks"],
        extreme_conditions=synth["extreme_conditions"],
        management_advisory=synth["management_advisory"],
        evidence=[],
        citations=citations
    )

