"""
Terravyn Experiment Engine: Daily Snapshot & Quality Scorer
Aggregates daily plot microclimate, soil moisture, irrigations, and phenotypic progress.
Evaluates data completeness with strict scientific quality rating (HIGH, MEDIUM, LOW).
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.domain import (
    Experiment,
    ExperimentPlot,
    ExperimentDailySnapshot,
    ExperimentObservation,
    ExperimentIrrigationEvent,
    DeviceTelemetry,
)
from services.experiment_engine.sensor_collector import ExperimentSensorCollector


class ExperimentSnapshotService:
    """Computes and stores daily plot-level agronomic and telemetry aggregations."""

    @classmethod
    def generate_daily_snapshot(
        cls,
        db: Session,
        experiment_id: int,
        target_date: Optional[date] = None,
    ) -> List[ExperimentDailySnapshot]:
        """Generates snapshots for all plots in an experiment for the target date."""
        snap_date = target_date or datetime.utcnow().date()
        start_dt = datetime.combine(snap_date, datetime.min.time())
        end_dt = datetime.combine(snap_date, datetime.max.time())

        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            return []

        plots = (
            db.query(ExperimentPlot)
            .join(ExperimentPlot.group)
            .filter(ExperimentPlot.group.has(experiment_id=experiment_id))
            .all()
        )

        snapshots = []
        for plot in plots:
            # 1. Moisture & Microclimate Telemetry
            moisture_readings = []
            temp_readings = []
            hum_readings = []

            if plot.device_id:
                telemetries = (
                    db.query(DeviceTelemetry)
                    .filter(
                        DeviceTelemetry.device_id == plot.device_id,
                        DeviceTelemetry.recorded_at >= start_dt,
                        DeviceTelemetry.recorded_at <= end_dt,
                    )
                    .all()
                )
                for t in telemetries:
                    if t.soil_moisture is not None:
                        # Raw moisture converted to volumetric %
                        vol = ExperimentSensorCollector.raw_to_volumetric_moisture(t.soil_moisture)
                        if vol is not None:
                            moisture_readings.append(vol)
                    if t.temperature is not None:
                        temp_readings.append(t.temperature)
                    if t.humidity is not None:
                        hum_readings.append(t.humidity)

            # Summaries
            soil_summary = cls._compute_stats(moisture_readings, unit="%")
            temp_summary = cls._compute_stats(temp_readings, unit="°C")
            hum_summary = cls._compute_stats(hum_readings, unit="%")

            # 2. Irrigation Summary
            irrigations = (
                db.query(ExperimentIrrigationEvent)
                .filter(
                    ExperimentIrrigationEvent.plot_id == plot.id,
                    ExperimentIrrigationEvent.start_time >= start_dt,
                    ExperimentIrrigationEvent.start_time <= end_dt,
                )
                .all()
            )
            total_water = sum([i.estimated_water_liters or 0.0 for i in irrigations])
            irr_summary = {
                "event_count": len(irrigations),
                "total_water_liters": round(total_water, 2),
                "events": [
                    {
                        "source": i.source,
                        "liters": i.estimated_water_liters,
                        "duration_s": i.duration_seconds,
                    }
                    for i in irrigations
                ],
            }

            # 3. Phenotypic Observations
            observations = (
                db.query(ExperimentObservation)
                .filter(
                    ExperimentObservation.plot_id == plot.id,
                    ExperimentObservation.timestamp >= start_dt,
                    ExperimentObservation.timestamp <= end_dt,
                )
                .all()
            )
            heights = [o.value_numeric for o in observations if o.parameter in ("plant_height", "height") and o.value_numeric is not None]
            leaves = [o.value_numeric for o in observations if o.parameter in ("leaf_count", "leaves") and o.value_numeric is not None]
            flowers = [o.value_numeric for o in observations if o.parameter in ("flower_count", "flowers") and o.value_numeric is not None]
            pods = [o.value_numeric for o in observations if o.parameter in ("pod_count", "pods") and o.value_numeric is not None]

            plant_obs_summary = {
                "observation_count": len(observations),
                "avg_height_cm": round(sum(heights) / len(heights), 1) if heights else None,
                "avg_leaf_count": round(sum(leaves) / len(leaves), 1) if leaves else None,
                "total_flowers": sum(flowers) if flowers else None,
                "total_pods": sum(pods) if pods else None,
            }

            # 4. Data Quality Score
            quality_score = cls._evaluate_data_quality(
                telemetry_count=len(moisture_readings),
                observation_count=len(observations),
            )

            # Check if snapshot already exists for this plot & date
            existing = (
                db.query(ExperimentDailySnapshot)
                .filter(
                    ExperimentDailySnapshot.plot_id == plot.id,
                    func.date(ExperimentDailySnapshot.snapshot_date) == snap_date,
                )
                .first()
            )

            if existing:
                existing.soil_moisture_summary = soil_summary
                existing.temperature_summary = temp_summary
                existing.humidity_summary = hum_summary
                existing.irrigation_summary = irr_summary
                existing.plant_observations = plant_obs_summary
                existing.data_quality_score = quality_score
                snap = existing
            else:
                snap = ExperimentDailySnapshot(
                    experiment_id=experiment_id,
                    group_id=plot.group_id,
                    plot_id=plot.id,
                    snapshot_date=start_dt,
                    soil_moisture_summary=soil_summary,
                    temperature_summary=temp_summary,
                    humidity_summary=hum_summary,
                    irrigation_summary=irr_summary,
                    plant_observations=plant_obs_summary,
                    data_quality_score=quality_score,
                )
                db.add(snap)

            snapshots.append(snap)

        db.commit()
        for s in snapshots:
            db.refresh(s)
        return snapshots

    @staticmethod
    def _compute_stats(values: List[float], unit: str) -> Dict[str, Any]:
        if not values:
            return {"count": 0, "unit": unit, "min": None, "max": None, "mean": None}
        return {
            "count": len(values),
            "unit": unit,
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "mean": round(sum(values) / len(values), 2),
        }

    @staticmethod
    def _evaluate_data_quality(telemetry_count: int, observation_count: int) -> str:
        """
        Data Quality Matrix:
        HIGH: robust telemetry (>= 20 readings/day) and physical observations recorded
        MEDIUM: partial telemetry (1..19 readings) or physical observations only
        LOW: no telemetry and no observations
        """
        if telemetry_count >= 20 and observation_count > 0:
            return "HIGH"
        elif telemetry_count > 0 or observation_count > 0:
            return "MEDIUM"
        else:
            return "LOW"
