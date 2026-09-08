"""
Terravyn Learning Engine: Report & Timeline Generator
Generates structured summaries, timeline views, and audit reports for learning.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    DecisionOutcomeAnalysis,
    LearningCandidate,
    PerformanceMetric,
    FieldCalibrationRecord,
    CropDecisionLog,
)

logger = logging.getLogger(__name__)


class LearningReportGenerator:
    """Generates structured reports and timelines for dashboard visualization."""

    @classmethod
    def generate_learning_report(
        cls,
        db: Session,
        farm_id: int,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Aggregates outcomes, candidates, and metrics for a comprehensive farm report."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        # 1. Total decisions vs analyzed
        total_decisions = db.query(CropDecisionLog).filter(
            CropDecisionLog.farm_id == farm_id,
            CropDecisionLog.timestamp >= cutoff,
        ).count()

        outcomes = db.query(DecisionOutcomeAnalysis).filter(
            DecisionOutcomeAnalysis.farm_id == farm_id,
            DecisionOutcomeAnalysis.created_at >= cutoff,
        ).all()

        classification_counts = {
            "CORRECT_IRRIGATION": 0,
            "POSSIBLE_UNNECESSARY_IRRIGATION": 0,
            "POSSIBLE_MISSED_IRRIGATION": 0,
            "CORRECT_WAIT": 0,
            "INSUFFICIENT_DATA": 0,
            "EXECUTION_FAILURE": 0,
            "UNKNOWN": 0,
        }
        for o in outcomes:
            classification_counts[o.classification] = classification_counts.get(o.classification, 0) + 1

        # 2. Learning candidates summary
        candidates = db.query(LearningCandidate).filter(
            (LearningCandidate.farm_id == farm_id) | (LearningCandidate.farm_id.is_(None))
        ).order_by(desc(LearningCandidate.updated_at)).all()

        cand_summary = {
            "total_candidates": len(candidates),
            "experimental": sum(1 for c in candidates if c.status == "EXPERIMENTAL"),
            "under_review": sum(1 for c in candidates if c.status == "UNDER_REVIEW"),
            "validated": sum(1 for c in candidates if c.status == "VALIDATED"),
            "promoted": sum(1 for c in candidates if c.status == "PROMOTED"),
            "rejected": sum(1 for c in candidates if c.status == "REJECTED"),
        }

        # 3. Active Calibration
        cal = db.query(FieldCalibrationRecord).filter(
            FieldCalibrationRecord.field_id == farm_id,
            FieldCalibrationRecord.status == "ACTIVE",
        ).order_by(desc(FieldCalibrationRecord.version)).first()

        cal_info = None
        if cal:
            cal_info = {
                "id": cal.id,
                "version": cal.version,
                "parameter": cal.parameter,
                "value": cal.value,
                "scope": cal.scope,
                "confidence": cal.confidence,
                "status": cal.status,
            }

        # 4. Performance trends snapshot
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.farm_id == farm_id
        ).order_by(desc(PerformanceMetric.created_at)).limit(5).all()

        return {
            "farm_id": farm_id,
            "period_days": lookback_days,
            "decisions_summary": {
                "total_decisions": total_decisions,
                "evaluated_outcomes": len(outcomes),
                "classification_breakdown": classification_counts,
            },
            "learning_pipeline": cand_summary,
            "active_calibration": cal_info,
            "recent_metrics": [
                {
                    "type": m.metric_type,
                    "value": m.value,
                    "sample_size": m.sample_size,
                    "period_end": m.period_end.isoformat(),
                }
                for m in metrics
            ],
            "generated_at": datetime.utcnow().isoformat(),
        }

    @classmethod
    def generate_timeline(
        cls,
        db: Session,
        farm_id: int,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Generates structured chronologically ordered timeline entries:
        Situation -> Decision -> Action -> Response -> Outcome -> Candidate -> Validation.
        """
        outcomes = (
            db.query(DecisionOutcomeAnalysis)
            .filter(DecisionOutcomeAnalysis.farm_id == farm_id)
            .order_by(desc(DecisionOutcomeAnalysis.created_at))
            .limit(limit)
            .all()
        )

        timeline = []
        for o in outcomes:
            fp = o.situation_fingerprint or {}
            sr = o.sensor_response or {}
            wr = o.weather_response or {}

            entry = {
                "outcome_id": o.id,
                "decision_log_id": o.decision_log_id,
                "timestamp": o.created_at.isoformat(),
                "crop": fp.get("crop", "green_gram"),
                "growth_stage": fp.get("growth_stage", "vegetative"),
                "soil_type": fp.get("soil_type", "sandy_loam"),
                "decision": o.decision,
                "actual_action": o.actual_action,
                "execution_outcome": o.execution_outcome,
                "classification": o.classification,
                "reasons": o.classification_reasons or [],
                "data_quality": o.data_quality,
                "sensor_delta": sr.get("delta"),
                "pre_moisture": sr.get("pre_moisture"),
                "post_moisture": sr.get("post_moisture"),
                "observed_rain_mm": wr.get("observed_precipitation_mm"),
                "forecast_rain_mm": wr.get("forecast_precipitation_mm"),
            }
            timeline.append(entry)

        return timeline
