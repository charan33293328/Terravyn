"""
Terravyn Learning Engine: Performance Tracker
Calculates decision accuracy, water efficiency, crop performance,
and detects calibration regression. Returns INSUFFICIENT_SAMPLE when data is too small.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.domain import (
    DecisionOutcomeAnalysis,
    IrrigationExecutionRecord,
    FieldCalibrationRecord,
    PerformanceMetric,
)

logger = logging.getLogger(__name__)

MIN_ACTIONABLE_SAMPLE = 10


class PerformanceTracker:
    """Tracks and evaluates Terravyn decision performance with statistical honesty."""

    @classmethod
    def calculate_decision_accuracy(
        cls,
        db: Session,
        farm_id: int,
        period_days: int = 7,
    ) -> PerformanceMetric:
        """Calculate decision accuracy metrics for the period. Returns INSUFFICIENT_SAMPLE if too few."""
        end = datetime.utcnow()
        start = end - timedelta(days=period_days)

        outcomes = (
            db.query(DecisionOutcomeAnalysis)
            .filter(
                DecisionOutcomeAnalysis.farm_id == farm_id,
                DecisionOutcomeAnalysis.created_at >= start,
                DecisionOutcomeAnalysis.created_at <= end,
            )
            .all()
        )

        counts = {
            "CORRECT_IRRIGATION": 0,
            "POSSIBLE_UNNECESSARY_IRRIGATION": 0,
            "POSSIBLE_MISSED_IRRIGATION": 0,
            "CORRECT_WAIT": 0,
            "INSUFFICIENT_DATA": 0,
            "EXECUTION_FAILURE": 0,
            "UNKNOWN": 0,
        }
        for o in outcomes:
            counts[o.classification] = counts.get(o.classification, 0) + 1

        # Only count actionable outcomes for accuracy
        correct = counts["CORRECT_IRRIGATION"] + counts["CORRECT_WAIT"]
        actionable = correct + counts["POSSIBLE_UNNECESSARY_IRRIGATION"] + counts["POSSIBLE_MISSED_IRRIGATION"]
        is_sufficient = actionable >= MIN_ACTIONABLE_SAMPLE
        accuracy = round((correct / actionable) * 100.0, 1) if actionable > 0 else None

        breakdown = {
            "correct_irrigation": counts["CORRECT_IRRIGATION"],
            "possible_unnecessary_irrigation": counts["POSSIBLE_UNNECESSARY_IRRIGATION"],
            "possible_missed_irrigation": counts["POSSIBLE_MISSED_IRRIGATION"],
            "correct_wait": counts["CORRECT_WAIT"],
            "insufficient_data": counts["INSUFFICIENT_DATA"],
            "execution_failure": counts["EXECUTION_FAILURE"],
            "unknown": counts["UNKNOWN"],
            "total_evaluated": len(outcomes),
            "actionable_count": actionable,
            "correct_count": correct,
        }

        metric = PerformanceMetric(
            farm_id=farm_id,
            metric_type="DECISION_ACCURACY",
            period_start=start,
            period_end=end,
            sample_size=len(outcomes),
            value=accuracy,
            breakdown=breakdown,
            is_sufficient_sample=is_sufficient,
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric

    @classmethod
    def calculate_water_efficiency(
        cls,
        db: Session,
        farm_id: int,
        period_days: int = 7,
    ) -> PerformanceMetric:
        """Calculate water usage efficiency for the period."""
        end = datetime.utcnow()
        start = end - timedelta(days=period_days)

        executions = (
            db.query(IrrigationExecutionRecord)
            .filter(
                IrrigationExecutionRecord.farm_id == farm_id,
                IrrigationExecutionRecord.start_time >= start,
                IrrigationExecutionRecord.start_time <= end,
                IrrigationExecutionRecord.status.in_(["COMPLETED", "SUCCESS"]),
            )
            .all()
        )

        total_duration = sum(e.actual_duration_seconds or 0 for e in executions)
        total_volume = None  # Never fabricate
        measured_volumes = [e.water_volume_liters for e in executions if e.water_volume_liters is not None]
        if measured_volumes:
            total_volume = sum(measured_volumes)

        event_count = len(executions)

        breakdown = {
            "irrigation_events": event_count,
            "total_duration_seconds": total_duration,
            "total_water_volume_liters": total_volume,  # null if no flow meter
            "has_flow_measurement": len(measured_volumes) > 0,
            "avg_duration_seconds": round(total_duration / event_count, 0) if event_count > 0 else None,
        }

        metric = PerformanceMetric(
            farm_id=farm_id,
            metric_type="WATER_EFFICIENCY",
            period_start=start,
            period_end=end,
            sample_size=event_count,
            value=total_duration,  # Use duration as proxy when volume unavailable
            breakdown=breakdown,
            is_sufficient_sample=event_count >= 3,
        )
        db.add(metric)
        db.commit()
        db.refresh(metric)
        return metric

    @classmethod
    def detect_calibration_regression(
        cls,
        db: Session,
        farm_id: int,
        calibration_id: int,
        lookback_days: int = 14,
    ) -> Dict[str, Any]:
        """Compare outcomes before vs after calibration activation."""
        cal = db.query(FieldCalibrationRecord).filter(
            FieldCalibrationRecord.id == calibration_id
        ).first()
        if not cal or not cal.activated_at:
            return {"regression_detected": False, "reason": "Calibration not activated."}

        activation_time = cal.activated_at
        pre_start = activation_time - timedelta(days=lookback_days)

        # Pre-activation outcomes
        pre_outcomes = (
            db.query(DecisionOutcomeAnalysis)
            .filter(
                DecisionOutcomeAnalysis.farm_id == farm_id,
                DecisionOutcomeAnalysis.created_at >= pre_start,
                DecisionOutcomeAnalysis.created_at < activation_time,
            )
            .all()
        )

        # Post-activation outcomes
        post_outcomes = (
            db.query(DecisionOutcomeAnalysis)
            .filter(
                DecisionOutcomeAnalysis.farm_id == farm_id,
                DecisionOutcomeAnalysis.created_at >= activation_time,
            )
            .all()
        )

        def missed_rate(outcomes):
            actionable = [o for o in outcomes if o.classification not in ("INSUFFICIENT_DATA", "UNKNOWN")]
            if not actionable:
                return None
            missed = sum(1 for o in actionable if o.classification == "POSSIBLE_MISSED_IRRIGATION")
            return round((missed / len(actionable)) * 100.0, 1)

        pre_rate = missed_rate(pre_outcomes)
        post_rate = missed_rate(post_outcomes)

        regression = False
        if pre_rate is not None and post_rate is not None:
            regression = post_rate > pre_rate + 10.0  # >10% worse

        return {
            "calibration_id": calibration_id,
            "calibration_version": cal.version,
            "activation_time": activation_time.isoformat(),
            "pre_outcomes_count": len(pre_outcomes),
            "post_outcomes_count": len(post_outcomes),
            "pre_missed_rate_pct": pre_rate,
            "post_missed_rate_pct": post_rate,
            "regression_detected": regression,
            "recommendation": "ROLLBACK_REVIEW" if regression else "CONTINUE",
        }

    @classmethod
    def get_performance_trends(
        cls,
        db: Session,
        farm_id: int,
        metric_type: str = "DECISION_ACCURACY",
        periods: int = 12,
    ) -> List[Dict[str, Any]]:
        """Return performance metrics ordered by period for trend charting."""
        metrics = (
            db.query(PerformanceMetric)
            .filter(
                PerformanceMetric.farm_id == farm_id,
                PerformanceMetric.metric_type == metric_type,
            )
            .order_by(desc(PerformanceMetric.created_at))
            .limit(periods)
            .all()
        )

        return [
            {
                "period_start": m.period_start.isoformat(),
                "period_end": m.period_end.isoformat(),
                "value": m.value,
                "sample_size": m.sample_size,
                "is_sufficient_sample": m.is_sufficient_sample,
                "breakdown": m.breakdown,
            }
            for m in reversed(metrics)
        ]
