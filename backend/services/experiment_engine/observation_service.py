"""
Terravyn Experiment Engine: Observation & Event Service
Records plant phenotypic observations, interventions, and irrigation events.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    ExperimentObservation,
    ExperimentIrrigationEvent,
    ExperimentIntervention,
    ExperimentEvent,
    ExperimentPlot,
    ExperimentPlant,
)


class ExperimentObservationService:
    """Handles phenotypic measurements, interventions, and irrigation logging."""

    @classmethod
    def record_observation(
        cls,
        db: Session,
        experiment_id: int,
        plot_id: int,
        parameter: str,
        group_id: Optional[int] = None,
        plant_id: Optional[int] = None,
        value_numeric: Optional[float] = None,
        value_text: Optional[str] = None,
        unit: Optional[str] = None,
        method: str = "manual",
        observer: Optional[str] = None,
        confidence: int = 95,
        notes: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> ExperimentObservation:
        """Records a single phenotypic or agronomic observation."""
        # Auto-resolve group_id if not provided
        if not group_id:
            plot = db.query(ExperimentPlot).filter(ExperimentPlot.id == plot_id).first()
            if plot:
                group_id = plot.group_id
            else:
                raise ValueError(f"Plot {plot_id} not found.")

        obs = ExperimentObservation(
            experiment_id=experiment_id,
            group_id=group_id,
            plot_id=plot_id,
            plant_id=plant_id,
            timestamp=timestamp or datetime.utcnow(),
            parameter=parameter,
            value_numeric=value_numeric,
            value_text=value_text,
            unit=unit,
            method=method,
            observer=observer,
            confidence=confidence,
            notes=notes,
        )
        db.add(obs)
        db.commit()
        db.refresh(obs)
        return obs

    @classmethod
    def record_batch_observations(
        cls,
        db: Session,
        experiment_id: int,
        observations_data: List[Dict[str, Any]],
    ) -> List[ExperimentObservation]:
        """Batches multiple plant measurements."""
        created = []
        for item in observations_data:
            obs = cls.record_observation(
                db=db,
                experiment_id=experiment_id,
                plot_id=item["plot_id"],
                parameter=item["parameter"],
                group_id=item.get("group_id"),
                plant_id=item.get("plant_id"),
                value_numeric=item.get("value_numeric"),
                value_text=item.get("value_text"),
                unit=item.get("unit"),
                method=item.get("method", "manual"),
                observer=item.get("observer"),
                confidence=item.get("confidence", 95),
                notes=item.get("notes"),
                timestamp=item.get("timestamp"),
            )
            created.append(obs)
        return created

    @classmethod
    def record_irrigation_event(
        cls,
        db: Session,
        experiment_id: int,
        plot_id: int,
        source: str = "TERRAVYN",  # TERRAVYN, CONTROL, MANUAL
        mode: str = "AUTO",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        duration_seconds: Optional[int] = None,
        estimated_water_liters: Optional[float] = None,
        reason: Optional[str] = None,
        decision_log_id: Optional[int] = None,
        recorded_by: Optional[int] = None,
    ) -> ExperimentIrrigationEvent:
        """Records an irrigation event applied to an experiment replicate."""
        plot = db.query(ExperimentPlot).filter(ExperimentPlot.id == plot_id).first()
        if not plot:
            raise ValueError(f"Plot {plot_id} not found.")

        irr = ExperimentIrrigationEvent(
            experiment_id=experiment_id,
            group_id=plot.group_id,
            plot_id=plot_id,
            source=source,
            mode=mode,
            start_time=start_time or datetime.utcnow(),
            end_time=end_time,
            duration_seconds=duration_seconds,
            estimated_water_liters=estimated_water_liters,
            reason=reason,
            decision_log_id=decision_log_id,
            recorded_by=recorded_by,
        )
        db.add(irr)
        db.commit()
        db.refresh(irr)
        return irr

    @classmethod
    def record_intervention(
        cls,
        db: Session,
        experiment_id: int,
        plot_id: int,
        intervention_type: str,
        details: Optional[Dict[str, Any]] = None,
        actor: str = "user",
        timestamp: Optional[datetime] = None,
    ) -> ExperimentIntervention:
        """Records human agronomic intervention (fertilizer, thinning, weeding, pesticide)."""
        inter = ExperimentIntervention(
            experiment_id=experiment_id,
            plot_id=plot_id,
            timestamp=timestamp or datetime.utcnow(),
            intervention_type=intervention_type,
            details=details or {},
            actor=actor,
        )
        db.add(inter)
        db.commit()
        db.refresh(inter)
        return inter

    @classmethod
    def get_timeline(
        cls,
        db: Session,
        experiment_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Compiles a unified chronological timeline of observations, events, irrigations, and interventions."""
        timeline = []

        # 1. Observations
        obs = (
            db.query(ExperimentObservation)
            .filter(ExperimentObservation.experiment_id == experiment_id)
            .order_by(desc(ExperimentObservation.timestamp))
            .limit(limit)
            .all()
        )
        for o in obs:
            timeline.append({
                "type": "OBSERVATION",
                "timestamp": o.timestamp.isoformat(),
                "plot_id": o.plot_id,
                "plant_id": o.plant_id,
                "parameter": o.parameter,
                "value_numeric": o.value_numeric,
                "value_text": o.value_text,
                "unit": o.unit,
                "notes": o.notes,
            })

        # 2. Irrigation Events
        irrs = (
            db.query(ExperimentIrrigationEvent)
            .filter(ExperimentIrrigationEvent.experiment_id == experiment_id)
            .order_by(desc(ExperimentIrrigationEvent.start_time))
            .limit(limit)
            .all()
        )
        for i in irrs:
            timeline.append({
                "type": "IRRIGATION",
                "timestamp": i.start_time.isoformat(),
                "plot_id": i.plot_id,
                "source": i.source,
                "water_liters": i.estimated_water_liters,
                "duration_seconds": i.duration_seconds,
                "reason": i.reason,
            })

        # 3. Interventions
        inters = (
            db.query(ExperimentIntervention)
            .filter(ExperimentIntervention.experiment_id == experiment_id)
            .order_by(desc(ExperimentIntervention.timestamp))
            .limit(limit)
            .all()
        )
        for it in inters:
            timeline.append({
                "type": "INTERVENTION",
                "timestamp": it.timestamp.isoformat(),
                "plot_id": it.plot_id,
                "intervention_type": it.intervention_type,
                "details": it.details,
                "actor": it.actor,
            })

        # 4. Milestone Events
        events = (
            db.query(ExperimentEvent)
            .filter(ExperimentEvent.experiment_id == experiment_id)
            .order_by(desc(ExperimentEvent.timestamp))
            .limit(limit)
            .all()
        )
        for ev in events:
            timeline.append({
                "type": "EVENT",
                "timestamp": ev.timestamp.isoformat(),
                "event_type": ev.event_type,
                "actor": ev.actor,
                "notes": ev.notes,
            })

        # Sort combined timeline descending by timestamp
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        return timeline[:limit]
