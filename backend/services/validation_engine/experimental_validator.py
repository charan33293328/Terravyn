"""
Terravyn Validation Engine: Experimental Data Validator
Validates Terravyn trial observations, replication, sensor calibration quality, and data completeness.
Enforces the mandatory Prompt 7 rule: NEVER automatically turn a single observation into validated knowledge.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.domain import (
    Experiment,
    ExperimentGroup,
    ExperimentPlot,
    ExperimentPlant,
    SensorCalibrationRecord,
    ExperimentObservation,
    ExperimentIrrigationEvent,
    ExperimentDailySnapshot,
    ExperimentIntervention,
    KnowledgeValidationRecord,
    DynamicKnowledgeItem,
)
from services.validation_engine.confidence_scorer import ValidationConfidenceScorer
from services.experiment_engine.analytics import ExperimentAnalytics


class ExperimentalDataValidator:
    """Validates empirical trial data, enforces replication requirements, and guards against premature calibration."""

    @classmethod
    def validate_trial_candidate(
        cls,
        db: Session,
        experiment_id: int,
        candidate_item: Optional[DynamicKnowledgeItem] = None,
    ) -> KnowledgeValidationRecord:
        """
        Validates whether experimental evidence from a trial is sufficiently replicated,
        technically calibrated, and consistent to warrant promotion to PROVISIONAL or FIELD_CALIBRATED.
        """
        exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        if not exp:
            raise ValueError(f"Experiment #{experiment_id} not found.")

        # 1. Replication Check (Pots & Plants)
        plots = (
            db.query(ExperimentPlot)
            .join(ExperimentGroup)
            .filter(ExperimentGroup.experiment_id == experiment_id)
            .all()
        )
        plot_count = len(plots)

        plants = (
            db.query(ExperimentPlant)
            .join(ExperimentPlot)
            .join(ExperimentGroup)
            .filter(ExperimentGroup.experiment_id == experiment_id)
            .all()
        )
        plant_count = len(plants)

        observations = (
            db.query(ExperimentObservation)
            .filter(ExperimentObservation.experiment_id == experiment_id)
            .all()
        )
        obs_count = len(observations)

        # 2. Single Observation Guard!
        # If obs_count <= 1 or plant_count <= 1, strictly block promotion.
        is_single_observation = obs_count <= 1 or plant_count <= 1
        sample_score = 15.0 if is_single_observation else min(100.0, 30.0 + (obs_count * 2.5) + (plant_count * 1.5))

        # 3. Measurement Quality (Capacitive sensor calibration check)
        cal_score, cal_notes = cls._evaluate_sensor_calibration(db, plots)

        # 4. Data Completeness & Quality (Daily Snapshots)
        snapshots = (
            db.query(ExperimentDailySnapshot)
            .filter(ExperimentDailySnapshot.experiment_id == experiment_id)
            .all()
        )
        quality_score, completeness_score = cls._evaluate_snapshot_completeness(snapshots)

        # 5. Confounding Factors (Interventions & Group imbalance)
        confounding_score, intervention_notes = cls._evaluate_confounding_factors(db, experiment_id)

        # 6. Terravyn vs Control Comparative Consistency
        analytics = ExperimentAnalytics.compare_groups(db, experiment_id)
        has_comparison = "error" not in analytics
        consistency_score = 80.0 if has_comparison else 40.0

        # 7. Assemble 10 Dimensional Scores
        dims = ValidationConfidenceScorer.score_dimensions(
            source_quality=50.0,  # Empirical
            applicability=85.0,  # Directly observed in-situ
            repeatability=65.0 if (plot_count >= 4 and obs_count >= 10) else 25.0,
            sample_size=sample_score,
            measurement_quality=cal_score,
            experimental_design=80.0 if has_comparison else 45.0,
            consistency=consistency_score,
            confounding_risk=confounding_score,
            temporal_consistency=70.0 if len(snapshots) >= 3 else 40.0,
            environmental_context=80.0,
        )

        conf, conf_level, reasons, limitations, next_step = ValidationConfidenceScorer.compute_overall_confidence(
            dimensions=dims,
            is_experimental=True,
        )

        # Add specific empirical notes
        reasons.extend(cal_notes)
        if is_single_observation:
            limitations.append("MANDATORY GUARD: Single observation detected (N=1). Cannot calibrate without replication.")
            next_step = "KEEP_EXPERIMENTAL"
            final_status = "EXPERIMENTAL"
        elif next_step == "SHADOW_TEST":
            final_status = "FIELD_CALIBRATED"
            reasons.append(f"Replication verified across {plot_count} pots and {plant_count} plants ({obs_count} measurements).")
        elif next_step == "PROMOTE_TO_PROVISIONAL":
            final_status = "PROVISIONAL"
        else:
            final_status = "EXPERIMENTAL"

        if intervention_notes:
            limitations.extend(intervention_notes)

        # Record validation audit
        rec = KnowledgeValidationRecord(
            target_type="EXPERIMENTAL_CANDIDATE",
            target_id=candidate_item.id if candidate_item else experiment_id,
            status=final_status,
            confidence=conf,
            confidence_level=conf_level,
            dimension_scores=dims,
            evidence_count=obs_count,
            experiment_count=1,
            data_quality="HIGH" if completeness_score >= 70 else ("MEDIUM" if completeness_score >= 40 else "LOW"),
            scope="FIELD",
            reasons=reasons,
            limitations=limitations,
            recommended_next_step=next_step,
        )
        db.add(rec)

        # If candidate item was passed, update its status
        if candidate_item:
            candidate_item.status = final_status
            candidate_item.confidence = conf
            candidate_item.last_reviewed_at = datetime.utcnow()

        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def _evaluate_sensor_calibration(
        cls,
        db: Session,
        plots: List[ExperimentPlot],
    ) -> Tuple[float, List[str]]:
        """Verifies if capacitive sensors used in trial have active, verified 4095=dry 1400=wet calibration."""
        notes = []
        device_ids = [p.device_id for p in plots if p.device_id is not None]

        if not device_ids:
            # Pot trial using manual or lab probes
            notes.append("Using standard lab two-point calibration standard (4095_DRY_0_WET).")
            return 80.0, notes

        # Check DB calibration records
        cal_recs = (
            db.query(SensorCalibrationRecord)
            .filter(SensorCalibrationRecord.device_id.in_(device_ids))
            .all()
        )

        if not cal_recs:
            notes.append("WARNING: No physical calibration record found for assigned telemetry probes.")
            return 40.0, notes

        # Verify freshness (< 30 days) and direction
        fresh = all(
            (datetime.utcnow() - c.calibration_date) <= timedelta(days=30)
            and c.direction == "4095_DRY_0_WET"
            for c in cal_recs
        )
        if fresh:
            notes.append(f"Probe calibration verified fresh ({len(cal_recs)} devices calibrated).")
            return 90.0, notes
        else:
            notes.append("Probe calibration is older than 30 days or has non-standard direction.")
            return 55.0, notes

    @classmethod
    def _evaluate_snapshot_completeness(
        cls,
        snapshots: List[ExperimentDailySnapshot],
    ) -> Tuple[float, float]:
        """Calculates data completeness from daily snapshots."""
        if not snapshots:
            return 40.0, 30.0

        high_quality_count = sum(1 for s in snapshots if s.data_quality_score == "HIGH")
        medium_quality_count = sum(1 for s in snapshots if s.data_quality_score == "MEDIUM")

        completeness_pct = ((high_quality_count * 1.0 + medium_quality_count * 0.6) / len(snapshots)) * 100.0
        quality_score = min(100.0, completeness_pct)
        return quality_score, completeness_pct

    @classmethod
    def _evaluate_confounding_factors(
        cls,
        db: Session,
        experiment_id: int,
    ) -> Tuple[float, List[str]]:
        """Checks for external human interventions that might confound results."""
        interventions = (
            db.query(ExperimentIntervention)
            .filter(ExperimentIntervention.experiment_id == experiment_id)
            .all()
        )
        notes = []
        if len(interventions) > 5:
            notes.append(f"High human intervention frequency ({len(interventions)} recorded actions).")
            return 50.0, notes
        elif interventions:
            notes.append(f"Controlled human interventions logged ({len(interventions)} actions).")
            return 75.0, notes
        return 90.0, notes
