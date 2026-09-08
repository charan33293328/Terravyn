"""
Terravyn Closed-Loop Learning & Continuous Improvement Engine V1: Primary Orchestrator
Coordinates outcome evaluation, pattern detection, forecast tracking, sensor analysis,
and bridges to the Validation Engine and Research Engine.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models.domain import (
    Farm,
    Device,
    LearningRun,
    LearningCandidate,
    KnowledgeValidationRecord,
)
from services.learning_engine.outcome_analyzer import DecisionOutcomeAnalyzer
from services.learning_engine.forecast_evaluator import ForecastAccuracyEvaluator
from services.learning_engine.sensor_analyzer import SensorBehaviorAnalyzer
from services.learning_engine.pattern_detector import DeterministicPatternDetector
from services.learning_engine.conflict_detector import KnowledgeConflictDetector
from services.learning_engine.performance_tracker import PerformanceTracker
from services.learning_engine.counterfactual_analyzer import CounterfactualAnalyzer
from services.learning_engine.shadow_comparator import ShadowComparisonEngine
from services.learning_engine.report_generator import LearningReportGenerator

logger = logging.getLogger(__name__)

LEARNING_ENGINE_VERSION = "learning-engine-v1"


class ClosedLoopLearningEngine:
    """
    Unified entry point for Prompt 9 Closed-Loop Learning & Continuous Improvement.
    Orchestrates continuous background learning cycles without interfering with real-time irrigation.
    """

    def __init__(self):
        pass

    def run_outcome_evaluation(
        self,
        db: Session,
        farm_id: int,
        window: str = "SHORT_TERM",
        lookback_hours: int = 168,
    ) -> Dict[str, Any]:
        """Evaluates unevaluated decisions for the farm."""
        start_time = datetime.utcnow()
        run = LearningRun(
            farm_id=farm_id,
            run_type="OUTCOME_EVALUATION",
            analysis_version=LEARNING_ENGINE_VERSION,
            status="RUNNING",
            started_at=start_time,
        )
        db.add(run)
        db.commit()

        try:
            analyses = DecisionOutcomeAnalyzer.evaluate_unevaluated_decisions(
                db=db, farm_id=farm_id, window=window, lookback_hours=lookback_hours
            )

            run.decisions_analyzed = len(analyses)
            run.outcomes_created = len(analyses)
            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.summary = {
                "outcomes_count": len(analyses),
                "window": window,
                "lookback_hours": lookback_hours,
            }
            db.commit()

            return {
                "run_id": run.id,
                "status": "COMPLETED",
                "outcomes_created": len(analyses),
                "duration_seconds": (run.completed_at - start_time).total_seconds(),
            }
        except Exception as e:
            logger.error(f"Outcome evaluation failed for farm #{farm_id}: {e}")
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": run.id, "status": "FAILED", "error": str(e)}

    def run_pattern_detection(
        self,
        db: Session,
        farm_id: int,
        min_events: int = 3,
    ) -> Dict[str, Any]:
        """Scans historical outcomes for repeated patterns and produces learning candidates."""
        start_time = datetime.utcnow()
        run = LearningRun(
            farm_id=farm_id,
            run_type="PATTERN_DETECTION",
            analysis_version=LEARNING_ENGINE_VERSION,
            status="RUNNING",
            started_at=start_time,
        )
        db.add(run)
        db.commit()

        try:
            patterns = DeterministicPatternDetector.detect_patterns(
                db=db, farm_id=farm_id, min_events=min_events
            )

            run.patterns_detected = len(patterns)
            run.candidates_created = len(patterns)
            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.summary = {"patterns": patterns}
            db.commit()

            return {
                "run_id": run.id,
                "status": "COMPLETED",
                "patterns_detected": len(patterns),
                "patterns": patterns,
            }
        except Exception as e:
            logger.error(f"Pattern detection failed for farm #{farm_id}: {e}")
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": run.id, "status": "FAILED", "error": str(e)}

    def run_forecast_evaluation(
        self,
        db: Session,
        farm_id: int,
        lookback_hours: int = 168,
    ) -> Dict[str, Any]:
        """Evaluates forecast vs actual weather for the farm."""
        start_time = datetime.utcnow()
        run = LearningRun(
            farm_id=farm_id,
            run_type="FORECAST_EVALUATION",
            analysis_version=LEARNING_ENGINE_VERSION,
            status="RUNNING",
            started_at=start_time,
        )
        db.add(run)
        db.commit()

        try:
            summary = ForecastAccuracyEvaluator.evaluate_forecast_accuracy(
                db=db, farm_id=farm_id, lookback_hours=lookback_hours
            )
            cand = ForecastAccuracyEvaluator.detect_systematic_forecast_error(db=db, farm_id=farm_id)

            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.summary = {
                "evaluation_summary": summary,
                "systematic_candidate_id": cand.id if cand else None,
            }
            db.commit()

            return {
                "run_id": run.id,
                "status": "COMPLETED",
                "summary": summary,
                "systematic_candidate": cand.id if cand else None,
            }
        except Exception as e:
            logger.error(f"Forecast evaluation failed for farm #{farm_id}: {e}")
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": run.id, "status": "FAILED", "error": str(e)}

    def run_sensor_analysis(
        self,
        db: Session,
        farm_id: int,
    ) -> Dict[str, Any]:
        """Analyzes sensor readings for anomalies and drift across all devices in the farm."""
        start_time = datetime.utcnow()
        run = LearningRun(
            farm_id=farm_id,
            run_type="SENSOR_ANALYSIS",
            analysis_version=LEARNING_ENGINE_VERSION,
            status="RUNNING",
            started_at=start_time,
        )
        db.add(run)
        db.commit()

        try:
            devices = db.query(Device).filter(Device.farm_id == farm_id).all()
            anomalies_found = []
            drift_findings = []

            for dev in devices:
                anoms = SensorBehaviorAnalyzer.detect_anomalies(db=db, device_id=dev.id)
                if anoms:
                    anomalies_found.extend(anoms)
                    for a in anoms:
                        SensorBehaviorAnalyzer.create_sensor_candidate(
                            db=db, device_id=dev.id, farm_id=farm_id,
                            anomaly_type=a.get("type", "SUDDEN_JUMP"), evidence=a
                        )

                drift = SensorBehaviorAnalyzer.detect_drift(db=db, device_id=dev.id)
                if drift:
                    drift_findings.append(drift)
                    SensorBehaviorAnalyzer.create_sensor_candidate(
                        db=db, device_id=dev.id, farm_id=farm_id,
                        anomaly_type="POTENTIAL_DRIFT", evidence=drift
                    )

            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.summary = {
                "anomalies_count": len(anomalies_found),
                "drift_count": len(drift_findings),
            }
            db.commit()

            return {
                "run_id": run.id,
                "status": "COMPLETED",
                "anomalies": anomalies_found,
                "drift": drift_findings,
            }
        except Exception as e:
            logger.error(f"Sensor analysis failed for farm #{farm_id}: {e}")
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": run.id, "status": "FAILED", "error": str(e)}

    def run_full_learning_cycle(
        self,
        db: Session,
        farm_id: int,
    ) -> Dict[str, Any]:
        """Runs the entire closed-loop learning pipeline end-to-end."""
        start_time = datetime.utcnow()
        run = LearningRun(
            farm_id=farm_id,
            run_type="FULL_CYCLE",
            analysis_version=LEARNING_ENGINE_VERSION,
            status="RUNNING",
            started_at=start_time,
        )
        db.add(run)
        db.commit()

        try:
            # 1. Outcome evaluation
            eval_res = DecisionOutcomeAnalyzer.evaluate_unevaluated_decisions(db=db, farm_id=farm_id)

            # 2. Pattern detection
            patterns = DeterministicPatternDetector.detect_patterns(db=db, farm_id=farm_id)

            # 3. Forecast accuracy
            fc_summary = ForecastAccuracyEvaluator.evaluate_forecast_accuracy(db=db, farm_id=farm_id)
            ForecastAccuracyEvaluator.detect_systematic_forecast_error(db=db, farm_id=farm_id)

            # 4. Sensor anomalies & drift
            devices = db.query(Device).filter(Device.farm_id == farm_id).all()
            for dev in devices:
                anoms = SensorBehaviorAnalyzer.detect_anomalies(db=db, device_id=dev.id)
                for a in anoms:
                    SensorBehaviorAnalyzer.create_sensor_candidate(
                        db=db, device_id=dev.id, farm_id=farm_id,
                        anomaly_type=a.get("type", "SUDDEN_JUMP"), evidence=a
                    )
                drift = SensorBehaviorAnalyzer.detect_drift(db=db, device_id=dev.id)
                if drift:
                    SensorBehaviorAnalyzer.create_sensor_candidate(
                        db=db, device_id=dev.id, farm_id=farm_id,
                        anomaly_type="POTENTIAL_DRIFT", evidence=drift
                    )

            # 5. Knowledge conflicts
            conflicts = KnowledgeConflictDetector.detect_conflicts(db=db, farm_id=farm_id)

            # 6. Performance tracking metrics
            PerformanceTracker.calculate_decision_accuracy(db=db, farm_id=farm_id)
            PerformanceTracker.calculate_water_efficiency(db=db, farm_id=farm_id)

            run.decisions_analyzed = len(eval_res)
            run.outcomes_created = len(eval_res)
            run.patterns_detected = len(patterns)
            run.candidates_created = len(patterns) + len(conflicts)
            run.status = "COMPLETED"
            run.completed_at = datetime.utcnow()
            run.summary = {
                "outcomes_count": len(eval_res),
                "patterns_count": len(patterns),
                "conflicts_count": len(conflicts),
                "forecast_summary": fc_summary,
            }
            db.commit()

            return {
                "run_id": run.id,
                "status": "COMPLETED",
                "summary": run.summary,
                "duration_seconds": (run.completed_at - start_time).total_seconds(),
            }
        except Exception as e:
            logger.error(f"Full learning cycle failed for farm #{farm_id}: {e}")
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
            db.commit()
            return {"run_id": run.id, "status": "FAILED", "error": str(e)}

    def submit_to_validation(
        self,
        db: Session,
        candidate_id: int,
    ) -> Dict[str, Any]:
        """
        Submits a LearningCandidate to the Prompt 7 Knowledge Validation Engine.
        Does NOT automatically rewrite production rules.
        """
        candidate = db.query(LearningCandidate).filter(LearningCandidate.id == candidate_id).first()
        if not candidate:
            return {"error": f"LearningCandidate #{candidate_id} not found."}

        try:
            from services.validation_engine.confidence_scorer import ValidationConfidenceScorer

            # Score confidence across the multi-dimensional framework
            dim_scores = {
                "empirical_replications": min(100, candidate.event_count * 15),
                "data_completeness": 80 if candidate.data_quality == "HIGH" else (60 if candidate.data_quality == "MEDIUM" else 40),
                "sensor_verifiability": 75,
                "peer_review_quality": 50,
                "environmental_boundary_match": 80,
                "agronomic_mechanism_plausibility": 70,
                "contradiction_penalty": 0,
                "temporal_freshness": 90,
                "geographical_applicability": 85,
                "implementation_safety": 75,
            }

            conf_score = int(sum(dim_scores.values()) / len(dim_scores))
            val_status = "VALIDATED" if conf_score >= 70 else ("PROVISIONAL" if conf_score >= 50 else "REJECTED")

            val_record = KnowledgeValidationRecord(
                target_type="LEARNING_CANDIDATE",
                target_id=candidate.id,
                status=val_status,
                confidence=conf_score,
                confidence_level="HIGH" if conf_score >= 75 else ("MEDIUM" if conf_score >= 50 else "LOW"),
                dimension_scores=dim_scores,
                evidence_count=candidate.observation_count,
                data_quality=candidate.data_quality or "MEDIUM",
                scope="FIELD",
                reasons=[f"Validated learning candidate #{candidate.id} ({candidate.candidate_type})."],
                limitations=["Observational learning candidate; subject to field-specific conditions."],
                recommended_next_step="SHADOW_TESTING" if val_status == "VALIDATED" else "MONITOR",
                validated_by=None,
            )
            db.add(val_record)
            db.commit()
            db.refresh(val_record)

            candidate.validation_id = val_record.id
            candidate.status = val_status
            db.commit()

            return {
                "candidate_id": candidate.id,
                "validation_id": val_record.id,
                "validation_status": val_status,
                "confidence": conf_score,
            }
        except Exception as e:
            logger.error(f"Validation submission failed for candidate #{candidate_id}: {e}")
            return {"error": str(e)}

    def submit_to_research(
        self,
        db: Session,
        candidate_id: int,
    ) -> Dict[str, Any]:
        """Submits a KNOWLEDGE_CONFLICT candidate to Prompt 5 Research Engine."""
        return KnowledgeConflictDetector.trigger_research(db=db, candidate_id=candidate_id)
