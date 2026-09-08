"""
Terravyn Experiment Engine: Comparative Analytics
Compares Terravyn-guided replicates vs Control practice replicates.
Enforces rigorous scientific labeling: 'Observed difference' rather than premature claims of causation.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.domain import (
    Experiment,
    ExperimentGroup,
    ExperimentPlot,
    ExperimentObservation,
    ExperimentIrrigationEvent,
    ExperimentDailySnapshot,
)


class ExperimentAnalytics:
    """Computes comparative trial analytics between Terravyn and Control cohorts."""

    @classmethod
    def compare_groups(cls, db: Session, experiment_id: int) -> Dict[str, Any]:
        """
        Generates comparative metrics:
        - Water consumption (Liters)
        - Irrigation frequency
        - Phenotypic progress (Height, Leaves, Pods)
        - Moisture stability
        - Scientific attribution statement
        """
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            return {"error": f"Experiment #{experiment_id} not found."}

        groups = db.query(ExperimentGroup).filter(ExperimentGroup.experiment_id == experiment_id).all()
        terravyn_group = next((g for g in groups if g.type == "TERRAVYN"), None)
        control_group = next((g for g in groups if g.type == "CONTROL"), None)

        if not terravyn_group or not control_group:
            return {
                "error": "Comparative analytics requires both TERRAVYN and CONTROL groups.",
                "groups_present": [g.type for g in groups],
            }

        t_stats = cls._get_group_metrics(db, terravyn_group.id)
        c_stats = cls._get_group_metrics(db, control_group.id)

        # Compute differences
        # Water savings
        water_saved_liters = None
        water_diff_pct = None
        if t_stats["total_water_liters"] is not None and c_stats["total_water_liters"] is not None:
            water_saved_liters = round(c_stats["total_water_liters"] - t_stats["total_water_liters"], 2)
            if c_stats["total_water_liters"] > 0:
                water_diff_pct = round((water_saved_liters / c_stats["total_water_liters"]) * 100.0, 1)

        # Height difference
        height_diff_pct = None
        if t_stats["avg_height_cm"] is not None and c_stats["avg_height_cm"] is not None:
            if c_stats["avg_height_cm"] > 0:
                height_diff_pct = round(
                    ((t_stats["avg_height_cm"] - c_stats["avg_height_cm"]) / c_stats["avg_height_cm"]) * 100.0, 1
                )

        # Pod count difference
        pod_diff_pct = None
        if t_stats["total_pods"] is not None and c_stats["total_pods"] is not None:
            if c_stats["total_pods"] > 0:
                pod_diff_pct = round(
                    ((t_stats["total_pods"] - c_stats["total_pods"]) / c_stats["total_pods"]) * 100.0, 1
                )

        return {
            "experiment_id": exp.id,
            "experiment_name": exp.name,
            "variety": exp.variety,
            "status": exp.status,
            "scientific_disclaimer": (
                "Data represents observed differences in controlled pot/plot replicates. "
                "Causation cannot be definitively claimed without multi-season, multi-site replication."
            ),
            "terravyn_cohort": t_stats,
            "control_cohort": c_stats,
            "observed_differences": {
                "water_saved_liters": water_saved_liters,
                "water_saved_percentage": water_diff_pct,
                "irrigation_count_difference": (
                    (t_stats["irrigation_event_count"] - c_stats["irrigation_event_count"])
                    if t_stats["irrigation_event_count"] is not None and c_stats["irrigation_event_count"] is not None
                    else None
                ),
                "plant_height_difference_cm": (
                    round(t_stats["avg_height_cm"] - c_stats["avg_height_cm"], 2)
                    if t_stats["avg_height_cm"] is not None and c_stats["avg_height_cm"] is not None
                    else None
                ),
                "plant_height_observed_difference_pct": height_diff_pct,
                "pod_count_observed_difference_pct": pod_diff_pct,
            },
        }

    @classmethod
    def _get_group_metrics(cls, db: Session, group_id: int) -> Dict[str, Any]:
        """Aggregates water and phenotypic metrics for all plots in a group."""
        plots = db.query(ExperimentPlot).filter(ExperimentPlot.group_id == group_id).all()
        plot_ids = [p.id for p in plots]
        if not plot_ids:
            return {
                "plot_count": 0,
                "total_water_liters": 0.0,
                "irrigation_event_count": 0,
                "avg_height_cm": None,
                "avg_leaf_count": None,
                "total_flowers": 0,
                "total_pods": 0,
                "stress_wilting_events": 0,
            }

        # 1. Irrigation
        irrigations = (
            db.query(ExperimentIrrigationEvent)
            .filter(ExperimentIrrigationEvent.plot_id.in_(plot_ids))
            .all()
        )
        total_water = sum([i.estimated_water_liters or 0.0 for i in irrigations])
        irr_count = len(irrigations)

        # 2. Observations
        observations = (
            db.query(ExperimentObservation)
            .filter(ExperimentObservation.plot_id.in_(plot_ids))
            .all()
        )

        heights = [o.value_numeric for o in observations if o.parameter in ("plant_height", "height") and o.value_numeric is not None]
        leaves = [o.value_numeric for o in observations if o.parameter in ("leaf_count", "leaves") and o.value_numeric is not None]
        flowers = [o.value_numeric for o in observations if o.parameter in ("flower_count", "flowers") and o.value_numeric is not None]
        pods = [o.value_numeric for o in observations if o.parameter in ("pod_count", "pods") and o.value_numeric is not None]
        wilting = [o for o in observations if o.parameter in ("wilting_index", "stress") and (o.value_numeric or 0) > 1]

        return {
            "plot_count": len(plots),
            "total_water_liters": round(total_water, 2),
            "irrigation_event_count": irr_count,
            "avg_height_cm": round(sum(heights) / len(heights), 2) if heights else None,
            "avg_leaf_count": round(sum(leaves) / len(leaves), 1) if leaves else None,
            "total_flowers": int(sum(flowers)) if flowers else 0,
            "total_pods": int(sum(pods)) if pods else 0,
            "stress_wilting_events": len(wilting),
        }
