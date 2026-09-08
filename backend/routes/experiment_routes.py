"""
Terravyn API Routes: Green Gram Experiment & Data Collection Engine V1
Exposes trial management, multi-replicate hierarchies, observations, comparative analytics, and scientific CSV exports.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from database.connection import get_db
from models.domain import Experiment
from schemas.domain import (
    ExperimentCreate,
    ExperimentBaselineCreate,
    ObservationCreate,
    BatchObservationCreate,
    IrrigationEventCreate,
    InterventionCreate,
    SensorCalibrationCreate,
)
from services.experiment_engine import (
    ExperimentManager,
    ExperimentObservationService,
    ExperimentSnapshotService,
    ExperimentAnalytics,
    ExperimentObservationAnalyzer,
    ExperimentExporter,
    ExperimentSensorCollector,
)

router = APIRouter(prefix="/api/experiments", tags=["Green Gram Experiments"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_experiment(
    payload: ExperimentCreate,
    db: Session = Depends(get_db),
):
    """Creates an experiment and establishes the 2-group (Terravyn vs Control) replicate hierarchy."""
    exp = ExperimentManager.create_experiment(
        db=db,
        name=payload.name,
        crop=payload.crop or "Green Gram (Moong)",
        scientific_name=payload.scientific_name or "Vigna radiata",
        variety=payload.variety or "Pusa Vishal",
        start_date=payload.start_date,
        expected_end_date=payload.expected_end_date,
        location=payload.location,
        protocol=payload.protocol,
    )

    # Set up trial hierarchy
    hierarchy_info = ExperimentManager.setup_default_trial_hierarchy(
        db=db,
        experiment_id=exp.id,
        terravyn_device_id=payload.terravyn_device_id,
        control_device_id=payload.control_device_id,
        pots_per_group=payload.pots_per_group or 3,
        plants_per_pot=payload.plants_per_pot or 5,
        sowing_date=payload.start_date,
    )

    return {
        "message": "Experiment and replicate hierarchy created successfully.",
        "experiment_id": exp.id,
        "name": exp.name,
        "status": exp.status,
        "hierarchy": hierarchy_info,
    }


@router.get("")
def list_experiments(db: Session = Depends(get_db)):
    """Lists all experiments with high-level summaries."""
    experiments = db.query(Experiment).order_by(Experiment.created_at.desc()).all()
    results = []
    for exp in experiments:
        results.append({
            "id": exp.id,
            "name": exp.name,
            "crop": exp.crop,
            "variety": exp.variety,
            "status": exp.status,
            "start_date": exp.start_date.isoformat() if exp.start_date else None,
            "expected_end_date": exp.expected_end_date.isoformat() if exp.expected_end_date else None,
            "location": exp.location,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "groups_count": len(exp.groups),
        })
    return results


@router.get("/{experiment_id}")
def get_experiment_details(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """Retrieves full nested hierarchy and baseline for an experiment."""
    hierarchy = ExperimentManager.get_experiment_hierarchy(db, experiment_id)
    if not hierarchy:
        raise HTTPException(status_code=404, detail=f"Experiment #{experiment_id} not found.")
    return hierarchy


@router.post("/{experiment_id}/baseline")
def record_experiment_baseline(
    experiment_id: int,
    payload: ExperimentBaselineCreate,
    db: Session = Depends(get_db),
):
    """Records or updates soil chemistry and seed provenance baseline."""
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment #{experiment_id} not found.")

    baseline = ExperimentManager.set_baseline(
        db=db,
        experiment_id=experiment_id,
        baseline_data=payload.dict(exclude_unset=True),
    )
    return {
        "message": "Baseline recorded successfully.",
        "experiment_id": experiment_id,
        "baseline_id": baseline.id,
    }


@router.post("/{experiment_id}/observations")
def record_observation(
    experiment_id: int,
    payload: ObservationCreate,
    db: Session = Depends(get_db),
):
    """Records a single phenotypic observation."""
    try:
        obs = ExperimentObservationService.record_observation(
            db=db,
            experiment_id=experiment_id,
            plot_id=payload.plot_id,
            parameter=payload.parameter,
            group_id=payload.group_id,
            plant_id=payload.plant_id,
            value_numeric=payload.value_numeric,
            value_text=payload.value_text,
            unit=payload.unit,
            method=payload.method or "manual",
            observer=payload.observer,
            confidence=payload.confidence or 95,
            notes=payload.notes,
            timestamp=payload.timestamp,
        )
        return {
            "message": "Observation recorded successfully.",
            "observation_id": obs.id,
            "parameter": obs.parameter,
            "value_numeric": obs.value_numeric,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{experiment_id}/observations/batch")
def record_batch_observations(
    experiment_id: int,
    payload: BatchObservationCreate,
    db: Session = Depends(get_db),
):
    """Records multiple observations in one call."""
    try:
        obs_data = [item.dict() for item in payload.observations]
        created = ExperimentObservationService.record_batch_observations(
            db=db,
            experiment_id=experiment_id,
            observations_data=obs_data,
        )
        return {
            "message": f"{len(created)} observations recorded successfully.",
            "count": len(created),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{experiment_id}/irrigation-events")
def record_irrigation_event(
    experiment_id: int,
    payload: IrrigationEventCreate,
    db: Session = Depends(get_db),
):
    """Logs an irrigation event for a plot."""
    try:
        irr = ExperimentObservationService.record_irrigation_event(
            db=db,
            experiment_id=experiment_id,
            plot_id=payload.plot_id,
            source=payload.source or "TERRAVYN",
            mode=payload.mode or "AUTO",
            start_time=payload.start_time,
            end_time=payload.end_time,
            duration_seconds=payload.duration_seconds,
            estimated_water_liters=payload.estimated_water_liters,
            reason=payload.reason,
            decision_log_id=payload.decision_log_id,
        )
        return {
            "message": "Irrigation event logged.",
            "event_id": irr.id,
            "estimated_water_liters": irr.estimated_water_liters,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{experiment_id}/interventions")
def record_intervention(
    experiment_id: int,
    payload: InterventionCreate,
    db: Session = Depends(get_db),
):
    """Logs human agronomic intervention."""
    inter = ExperimentObservationService.record_intervention(
        db=db,
        experiment_id=experiment_id,
        plot_id=payload.plot_id,
        intervention_type=payload.intervention_type,
        details=payload.details,
        actor=payload.actor or "user",
        timestamp=payload.timestamp,
    )
    return {
        "message": "Intervention recorded.",
        "intervention_id": inter.id,
        "type": inter.intervention_type,
    }


@router.get("/{experiment_id}/timeline")
def get_experiment_timeline(
    experiment_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Returns chronological timeline of observations, irrigations, and events."""
    return ExperimentObservationService.get_timeline(db, experiment_id, limit=limit)


@router.post("/{experiment_id}/snapshots/generate")
def generate_snapshots(
    experiment_id: int,
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """Computes and stores daily plot-level snapshots and data quality ratings."""
    snapshots = ExperimentSnapshotService.generate_daily_snapshot(
        db=db,
        experiment_id=experiment_id,
        target_date=target_date,
    )
    return {
        "message": f"Generated {len(snapshots)} daily plot snapshots.",
        "snapshots_count": len(snapshots),
    }


@router.get("/{experiment_id}/comparison")
def get_comparative_analytics(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """Computes comparative trial analytics with scientific 'Observed difference' attribution."""
    analysis = ExperimentAnalytics.compare_groups(db, experiment_id)
    if "error" in analysis:
        raise HTTPException(status_code=400, detail=analysis["error"])
    return analysis


@router.post("/{experiment_id}/candidates/synthesize")
def synthesize_knowledge_candidates(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """Extracts empirical observations and creates EXPERIMENTAL Dynamic Knowledge items."""
    candidates = ExperimentObservationAnalyzer.synthesize_candidates(db, experiment_id)
    return {
        "message": f"Synthesized {len(candidates)} dynamic knowledge candidate(s).",
        "candidates": [
            {
                "id": c.id,
                "parameter": c.parameter,
                "finding": c.finding,
                "status": c.status,
                "confidence": c.confidence,
            }
            for c in candidates
        ],
    }


@router.get("/{experiment_id}/export/observations")
def export_observations_csv(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """Exports trial observations as CSV for offline scientific review."""
    csv_content = ExperimentExporter.export_observations_csv(db, experiment_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}_observations.csv"},
    )


@router.get("/{experiment_id}/export/snapshots")
def export_snapshots_csv(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """Exports daily snapshots as CSV for offline scientific review."""
    csv_content = ExperimentExporter.export_snapshots_csv(db, experiment_id)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=experiment_{experiment_id}_snapshots.csv"},
    )


@router.post("/{experiment_id}/complete")
def complete_experiment(
    experiment_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Concludes the experiment and transitions status to COMPLETED."""
    exp = ExperimentManager.complete_experiment(db, experiment_id, notes=notes)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment #{experiment_id} not found.")
    return {
        "message": f"Experiment '{exp.name}' completed.",
        "status": exp.status,
    }


@router.post("/calibration")
def record_sensor_calibration(
    payload: SensorCalibrationCreate,
    db: Session = Depends(get_db),
):
    """Records capacitive sensor calibration referencing 4095=dry, 0=wet standard."""
    rec = ExperimentSensorCollector.record_sensor_calibration(
        db=db,
        device_id=payload.device_id,
        dry_reference=payload.dry_reference or 4095.0,
        wet_reference=payload.wet_reference or 1400.0,
        soil_type=payload.soil_type or "sandy_loam",
        notes=payload.notes,
    )
    return {
        "message": "Sensor calibration recorded.",
        "calibration_id": rec.id,
        "direction": rec.direction,
        "dry_reference": rec.dry_reference,
        "wet_reference": rec.wet_reference,
    }
