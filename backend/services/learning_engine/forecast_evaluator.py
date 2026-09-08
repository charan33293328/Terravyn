"""
Terravyn Learning Engine: Weather Forecast Accuracy Evaluator
Tracks forecast vs observed weather, detects systematic errors.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.domain import (
    WeatherForecast,
    WeatherObservation,
    ForecastEvaluation,
    LearningCandidate,
)

logger = logging.getLogger(__name__)


class ForecastAccuracyEvaluator:
    """Evaluates weather forecast accuracy per field."""

    @classmethod
    def evaluate_forecast_accuracy(
        cls,
        db: Session,
        farm_id: int,
        lookback_hours: int = 168,
    ) -> Dict[str, Any]:
        """Compare forecast records with observed weather and create evaluation records."""
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)

        forecasts = (
            db.query(WeatherForecast)
            .filter(
                WeatherForecast.farm_id == farm_id,
                WeatherForecast.forecast_time >= cutoff,
                WeatherForecast.is_daily == True,
            )
            .order_by(WeatherForecast.forecast_time)
            .all()
        )

        created = 0
        errors = {"precipitation": [], "temperature": [], "humidity": []}

        for fc in forecasts:
            # Find closest observation within 3 hours of forecast target
            candidates_obs = (
                db.query(WeatherObservation)
                .filter(
                    WeatherObservation.farm_id == farm_id,
                    WeatherObservation.timestamp >= fc.forecast_time - timedelta(hours=3),
                    WeatherObservation.timestamp <= fc.forecast_time + timedelta(hours=3),
                )
                .all()
            )
            if not candidates_obs:
                continue

            obs = min(candidates_obs, key=lambda o: abs((o.timestamp - fc.forecast_time).total_seconds()))

            lead_hours = None
            if fc.retrieved_at:
                lead_hours = (fc.forecast_time - fc.retrieved_at).total_seconds() / 3600.0

            # Evaluate each variable
            for variable, fc_val, obs_val in [
                ("precipitation", fc.precipitation, obs.precipitation),
                ("temperature", fc.temperature, obs.temperature),
                ("humidity", fc.humidity, obs.humidity),
            ]:
                if fc_val is None or obs_val is None:
                    continue

                error = round(abs(obs_val - fc_val), 2)
                error_pct = round((error / obs_val) * 100.0, 1) if obs_val != 0 else None

                eval_rec = ForecastEvaluation(
                    farm_id=farm_id,
                    forecast_id=fc.id,
                    forecast_time=fc.forecast_time,
                    lead_time_hours=round(lead_hours, 1) if lead_hours else None,
                    variable=variable,
                    forecast_value=fc_val,
                    observed_value=obs_val,
                    error=error,
                    error_pct=error_pct,
                )
                db.add(eval_rec)
                created += 1
                errors[variable].append(error)

        if created > 0:
            db.commit()

        summary = {"evaluations_created": created}
        for var in ("precipitation", "temperature", "humidity"):
            vals = errors[var]
            if vals:
                summary[f"{var}_mean_error"] = round(sum(vals) / len(vals), 2)
                summary[f"{var}_count"] = len(vals)
            else:
                summary[f"{var}_mean_error"] = None
                summary[f"{var}_count"] = 0

        return summary

    @classmethod
    def get_forecast_reliability(
        cls,
        db: Session,
        farm_id: int,
        variable: str = "precipitation",
        min_samples: int = 10,
    ) -> Dict[str, Any]:
        """Aggregate forecast evaluation metrics for a variable."""
        evals = (
            db.query(ForecastEvaluation)
            .filter(
                ForecastEvaluation.farm_id == farm_id,
                ForecastEvaluation.variable == variable,
                ForecastEvaluation.error.isnot(None),
            )
            .all()
        )

        if len(evals) < min_samples:
            return {
                "variable": variable,
                "sample_count": len(evals),
                "is_sufficient_sample": False,
                "reliability_score": None,
                "mean_error": None,
                "status": "INSUFFICIENT_SAMPLE",
            }

        errors = [e.error for e in evals]
        mean_err = sum(errors) / len(errors)
        max_acceptable = {"precipitation": 5.0, "temperature": 3.0, "humidity": 15.0}
        threshold = max_acceptable.get(variable, 5.0)
        reliability = max(0, min(100, int(100 * (1 - mean_err / threshold))))

        return {
            "variable": variable,
            "sample_count": len(evals),
            "is_sufficient_sample": True,
            "reliability_score": reliability,
            "mean_error": round(mean_err, 2),
            "status": "EVALUATED",
        }

    @classmethod
    def detect_systematic_forecast_error(
        cls,
        db: Session,
        farm_id: int,
        threshold_pct: float = 30.0,
        min_events: int = 5,
    ) -> Optional[LearningCandidate]:
        """Create FORECAST_ERROR candidate if systematic errors detected."""
        for variable in ("precipitation", "temperature", "humidity"):
            evals = (
                db.query(ForecastEvaluation)
                .filter(
                    ForecastEvaluation.farm_id == farm_id,
                    ForecastEvaluation.variable == variable,
                    ForecastEvaluation.error_pct.isnot(None),
                )
                .order_by(desc(ForecastEvaluation.created_at))
                .limit(min_events * 2)
                .all()
            )
            if len(evals) < min_events:
                continue

            high_error_count = sum(1 for e in evals if (e.error_pct or 0) > threshold_pct)
            if high_error_count >= min_events:
                idemp = f"forecast_error:{farm_id}:{variable}"
                existing = db.query(LearningCandidate).filter(
                    LearningCandidate.idempotency_key == idemp
                ).first()
                if existing:
                    existing.observation_count = len(evals)
                    existing.event_count = high_error_count
                    existing.updated_at = datetime.utcnow()
                    db.commit()
                    return existing

                mean_pct = sum(e.error_pct for e in evals if e.error_pct) / len(evals)
                candidate = LearningCandidate(
                    candidate_type="FORECAST_ERROR",
                    farm_id=farm_id,
                    pattern_description=(
                        f"Systematic {variable} forecast error detected. "
                        f"{high_error_count}/{len(evals)} recent forecasts exceed {threshold_pct}% error. "
                        f"Mean error: {mean_pct:.1f}%."
                    ),
                    pattern_data={"variable": variable, "mean_error_pct": round(mean_pct, 1), "high_error_count": high_error_count},
                    observation_count=len(evals),
                    event_count=high_error_count,
                    field_count=1,
                    data_quality="MEDIUM",
                    confidence=min(70, int(high_error_count * 10)),
                    priority="MEDIUM",
                    impact="MEDIUM",
                    risk_level="LOW",
                    status="EXPERIMENTAL",
                    idempotency_key=idemp,
                )
                db.add(candidate)
                db.commit()
                db.refresh(candidate)
                return candidate

        return None
