"""
Terravyn Experiment Engine: Data Exporter
Provides CSV generation of trial observations, daily snapshots, and irrigation events for offline scientific analysis.
"""
import io
import csv
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from models.domain import (
    Experiment,
    ExperimentGroup,
    ExperimentPlot,
    ExperimentPlant,
    ExperimentObservation,
    ExperimentIrrigationEvent,
    ExperimentDailySnapshot,
)


class ExperimentExporter:
    """Exports trial data to standardized scientific CSV formats."""

    @classmethod
    def export_observations_csv(cls, db: Session, experiment_id: int) -> str:
        """Generates CSV text for all individual plant and plot observations."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "observation_id",
            "experiment_id",
            "group_name",
            "plot_name",
            "plant_tag",
            "timestamp",
            "parameter",
            "value_numeric",
            "value_text",
            "unit",
            "method",
            "observer",
            "confidence",
            "notes",
        ])

        observations = (
            db.query(ExperimentObservation)
            .filter(ExperimentObservation.experiment_id == experiment_id)
            .order_by(ExperimentObservation.timestamp.asc())
            .all()
        )

        for o in observations:
            plot = db.query(ExperimentPlot).filter(ExperimentPlot.id == o.plot_id).first()
            group = plot.group if plot else None
            plant = db.query(ExperimentPlant).filter(ExperimentPlant.id == o.plant_id).first() if o.plant_id else None

            writer.writerow([
                o.id,
                o.experiment_id,
                group.name if group else "",
                plot.name if plot else "",
                plant.plant_tag if plant else "",
                o.timestamp.isoformat() if o.timestamp else "",
                o.parameter,
                o.value_numeric if o.value_numeric is not None else "",
                o.value_text or "",
                o.unit or "",
                o.method or "",
                o.observer or "",
                o.confidence or "",
                o.notes or "",
            ])

        return output.getvalue()

    @classmethod
    def export_snapshots_csv(cls, db: Session, experiment_id: int) -> str:
        """Generates CSV text for daily aggregated plot snapshots."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "snapshot_id",
            "experiment_id",
            "group_name",
            "plot_name",
            "snapshot_date",
            "moisture_mean_pct",
            "moisture_min_pct",
            "moisture_max_pct",
            "temp_mean_c",
            "humidity_mean_pct",
            "total_water_liters",
            "irrigation_events_count",
            "avg_plant_height_cm",
            "avg_leaf_count",
            "data_quality_score",
        ])

        snapshots = (
            db.query(ExperimentDailySnapshot)
            .filter(ExperimentDailySnapshot.experiment_id == experiment_id)
            .order_by(ExperimentDailySnapshot.snapshot_date.asc())
            .all()
        )

        for s in snapshots:
            plot = db.query(ExperimentPlot).filter(ExperimentPlot.id == s.plot_id).first()
            group = plot.group if plot else None

            moisture = s.soil_moisture_summary or {}
            temp = s.temperature_summary or {}
            hum = s.humidity_summary or {}
            irr = s.irrigation_summary or {}
            obs = s.plant_observations or {}

            writer.writerow([
                s.id,
                s.experiment_id,
                group.name if group else "",
                plot.name if plot else "",
                s.snapshot_date.isoformat() if s.snapshot_date else "",
                moisture.get("mean", ""),
                moisture.get("min", ""),
                moisture.get("max", ""),
                temp.get("mean", ""),
                hum.get("mean", ""),
                irr.get("total_water_liters", ""),
                irr.get("event_count", ""),
                obs.get("avg_height_cm", ""),
                obs.get("avg_leaf_count", ""),
                s.data_quality_score or "HIGH",
            ])

        return output.getvalue()
