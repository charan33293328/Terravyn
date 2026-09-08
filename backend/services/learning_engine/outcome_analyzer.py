"""
Terravyn Learning Engine: Decision Outcome Analyzer
Traces the full decision-to-outcome chain and classifies results.
OBSERVATION ≠ CAUSATION — uses POSSIBLE_ prefix for uncertain classifications.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models.domain import (
    CropDecisionLog,
    IrrigationAuthorizationRecord,
    IrrigationCommandRecord,
    IrrigationExecutionRecord,
    DeviceTelemetry,
    WeatherForecast,
    WeatherObservation,
    ExperimentObservation,
    DecisionOutcomeAnalysis,
    Device,
)
from services.research_engine.fingerprint import (
    SituationFingerprint,
    normalize_moisture_state,
    normalize_temperature_state,
    normalize_rain_state,
    normalize_eto_state,
)

logger = logging.getLogger(__name__)

ANALYSIS_VERSION = "learning-engine-v1"

# Observation windows in hours
WINDOWS = {
    "IMMEDIATE": (0, 1),
    "SHORT_TERM": (0, 24),
    "LONG_TERM": (0, 168),
}


class DecisionOutcomeAnalyzer:
    """Analyzes decision outcomes with multi-window temporal evaluation."""

    @classmethod
    def analyze_decision_outcome(
        cls,
        db: Session,
        decision_log_id: int,
        window: str = "SHORT_TERM",
    ) -> Optional[DecisionOutcomeAnalysis]:
        """
        Traces the full chain: Decision → Authorization → Command → Execution → Response.
        Classifies the outcome and records it with idempotency protection.
        """
        idemp_key = f"{decision_log_id}:{window}"

        # Idempotency guard
        existing = db.query(DecisionOutcomeAnalysis).filter(
            DecisionOutcomeAnalysis.idempotency_key == idemp_key
        ).first()
        if existing:
            return existing

        # 1. Load decision
        log = db.query(CropDecisionLog).filter(CropDecisionLog.id == decision_log_id).first()
        if not log:
            logger.warning(f"CropDecisionLog #{decision_log_id} not found.")
            return None

        window_start, window_end_hours = WINDOWS.get(window, WINDOWS["SHORT_TERM"])
        decision_time = log.timestamp
        eval_end = decision_time + timedelta(hours=window_end_hours)

        # 2. Build situation fingerprint
        fingerprint = cls._build_fingerprint(log)
        situation_hash = fingerprint.compute_hash() if fingerprint else None

        # 3. Trace authorization chain
        auth = db.query(IrrigationAuthorizationRecord).filter(
            IrrigationAuthorizationRecord.decision_log_id == log.id
        ).order_by(desc(IrrigationAuthorizationRecord.evaluated_at)).first()

        # 4. Trace command chain
        command = None
        if auth:
            command = db.query(IrrigationCommandRecord).filter(
                IrrigationCommandRecord.authorization_id == auth.id
            ).first()

        # 5. Trace execution chain
        execution = None
        if command:
            execution = db.query(IrrigationExecutionRecord).filter(
                IrrigationExecutionRecord.command_id == command.id
            ).first()
        if not execution:
            execution = db.query(IrrigationExecutionRecord).filter(
                IrrigationExecutionRecord.decision_log_id == log.id
            ).first()

        # 6. Determine actual action and execution outcome
        actual_action, exec_outcome = cls._evaluate_execution(log, auth, command, execution)

        # 7. Measure sensor response
        sensor_response = cls._measure_sensor_response(db, log, eval_end)

        # 8. Measure weather response (forecast vs observed)
        weather_response = cls._measure_weather_response(db, log.farm_id, decision_time, eval_end)

        # 9. Measure plant response (if experiment data exists)
        plant_response = cls._measure_plant_response(db, log.farm_id, decision_time, eval_end)

        # 10. Measure water response
        water_response = cls._measure_water_response(execution)

        # 11. Classify outcome
        classification, reasons = cls._classify_outcome(
            log, actual_action, exec_outcome,
            sensor_response, weather_response, plant_response
        )

        # 12. Compute data quality
        data_quality, dq_details = cls._assess_data_quality(
            sensor_response, weather_response, plant_response
        )

        # 13. Enumerate confounding factors
        confounders = cls._enumerate_confounders(weather_response, sensor_response)

        # 14. Create the analysis record
        analysis = DecisionOutcomeAnalysis(
            decision_log_id=log.id,
            authorization_id=auth.id if auth else None,
            command_id=command.id if command else None,
            execution_id=execution.id if execution else None,
            farm_id=log.farm_id,
            device_id=log.device_id,
            situation_fingerprint=fingerprint.to_canonical_dict() if fingerprint else None,
            situation_hash=situation_hash,
            decision=log.decision,
            actual_action=actual_action,
            execution_outcome=exec_outcome,
            sensor_response=sensor_response,
            weather_response=weather_response,
            plant_response=plant_response,
            water_response=water_response,
            classification=classification,
            classification_reasons=reasons,
            data_quality=data_quality,
            data_quality_details=dq_details,
            observation_window=window,
            confounding_factors=confounders,
            analysis_version=ANALYSIS_VERSION,
            idempotency_key=idemp_key,
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @classmethod
    def evaluate_unevaluated_decisions(
        cls,
        db: Session,
        farm_id: int,
        window: str = "SHORT_TERM",
        lookback_hours: int = 168,
    ) -> List[DecisionOutcomeAnalysis]:
        """Finds unevaluated decisions and analyzes them."""
        cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
        window_hours = WINDOWS.get(window, WINDOWS["SHORT_TERM"])[1]
        maturity_cutoff = datetime.utcnow() - timedelta(hours=window_hours)

        # Get decisions old enough that the evaluation window has passed
        decisions = (
            db.query(CropDecisionLog)
            .filter(
                CropDecisionLog.farm_id == farm_id,
                CropDecisionLog.timestamp >= cutoff,
                CropDecisionLog.timestamp <= maturity_cutoff,
            )
            .order_by(CropDecisionLog.timestamp)
            .all()
        )

        results = []
        for d in decisions:
            idemp_key = f"{d.id}:{window}"
            existing = db.query(DecisionOutcomeAnalysis).filter(
                DecisionOutcomeAnalysis.idempotency_key == idemp_key
            ).first()
            if existing:
                continue
            analysis = cls.analyze_decision_outcome(db, d.id, window)
            if analysis:
                results.append(analysis)
        return results

    # =========================================================================
    # Private helpers
    # =========================================================================

    @classmethod
    def _build_fingerprint(cls, log: CropDecisionLog) -> Optional[SituationFingerprint]:
        """Build a SituationFingerprint from decision log fields."""
        try:
            return SituationFingerprint(
                crop=log.crop or "green_gram",
                variety=log.variety,
                growth_stage=log.growth_stage or "vegetative",
                soil_type="sandy_loam",
                soil_moisture_state=normalize_moisture_state(log.soil_moisture),
                temperature_state=normalize_temperature_state(log.temperature),
                rain_forecast=normalize_rain_state(
                    log.rainfall_forecast_24h, 
                    int(log.rainfall_probability_24h) if log.rainfall_probability_24h else None
                ),
                recent_irrigation=bool(log.recent_irrigation_age_hours and log.recent_irrigation_age_hours < 6),
                eto_state=normalize_eto_state(log.et0),
                soil_moisture_pct=log.soil_moisture,
                temperature_c=log.temperature,
                rain_forecast_mm=log.rainfall_forecast_24h,
            )
        except Exception as e:
            logger.warning(f"Failed to build fingerprint for decision #{log.id}: {e}")
            return None

    @classmethod
    def _evaluate_execution(cls, log, auth, command, execution):
        """Determine what actually happened and whether execution succeeded."""
        if log.decision not in ("IRRIGATE",):
            return "NOT_APPLICABLE", None

        # If execution record exists directly linked to decision
        if execution and execution.status in ("COMPLETED", "SUCCESS"):
            return "EXECUTED", "EXECUTION_SUCCESS"

        if not auth:
            return "NOT_EXECUTED", "EXECUTION_UNKNOWN"

        if auth.status == "BLOCKED":
            return "BLOCKED", None
        if auth.status == "DEFERRED":
            return "DEFERRED", None

        if not command:
            return "NOT_EXECUTED", "EXECUTION_UNKNOWN"

        if command.status in ("EXECUTED", "ACKNOWLEDGED"):
            if execution and execution.status in ("COMPLETED", "SUCCESS"):
                return "EXECUTED", "EXECUTION_SUCCESS"
            elif execution and execution.status in ("ABORTED_SAFETY", "FAILED", "TIMEOUT"):
                return "EXECUTED", "EXECUTION_FAILED"
            return "EXECUTED", "EXECUTION_SUCCESS"
        elif command.status in ("FAILED", "TIMEOUT"):
            return "NOT_EXECUTED", "EXECUTION_FAILED"
        elif command.status == "SKIPPED_DRY_RUN":
            return "SIMULATED", None

        return "NOT_EXECUTED", "EXECUTION_UNKNOWN"

    @classmethod
    def _measure_sensor_response(cls, db, log, eval_end):
        """Measure soil moisture change after the decision."""
        if not log.device_id:
            return None

        decision_time = log.timestamp
        pre_moisture = log.soil_moisture

        # Find post-decision sensor reading
        post_telemetry = (
            db.query(DeviceTelemetry)
            .filter(
                DeviceTelemetry.device_id == log.device_id,
                DeviceTelemetry.recorded_at > decision_time,
                DeviceTelemetry.recorded_at <= eval_end,
                DeviceTelemetry.soil_moisture.isnot(None),
            )
            .order_by(DeviceTelemetry.recorded_at)
            .first()
        )

        if not post_telemetry:
            return {"pre_moisture": pre_moisture, "post_moisture": None, "delta": None, "status": "NO_POST_DATA"}

        post_moisture = post_telemetry.soil_moisture
        delta = round(post_moisture - pre_moisture, 2) if pre_moisture is not None else None
        response_seconds = (post_telemetry.recorded_at - decision_time).total_seconds()

        return {
            "pre_moisture": pre_moisture,
            "post_moisture": post_moisture,
            "delta": delta,
            "response_time_seconds": round(response_seconds, 0),
            "status": "MEASURED",
        }

    @classmethod
    def _measure_weather_response(cls, db, farm_id, start, end):
        """Compare forecast with observed weather during the evaluation window."""
        forecast = (
            db.query(WeatherForecast)
            .filter(
                WeatherForecast.farm_id == farm_id,
                WeatherForecast.forecast_time >= start,
                WeatherForecast.forecast_time <= end,
            )
            .order_by(WeatherForecast.forecast_time)
            .first()
        )

        observation = (
            db.query(WeatherObservation)
            .filter(
                WeatherObservation.farm_id == farm_id,
                WeatherObservation.timestamp >= start,
                WeatherObservation.timestamp <= end,
            )
            .order_by(desc(WeatherObservation.timestamp))
            .first()
        )

        if not forecast and not observation:
            return None

        result = {"status": "PARTIAL"}
        if forecast:
            result["forecast_precipitation_mm"] = forecast.precipitation
            result["forecast_temperature"] = forecast.temperature
            result["forecast_probability"] = forecast.precipitation_probability
        if observation:
            result["observed_precipitation_mm"] = observation.precipitation
            result["observed_temperature"] = observation.temperature
            result["observed_humidity"] = observation.humidity
            result["status"] = "COMPLETE" if forecast else "OBSERVED_ONLY"
        if forecast and observation:
            result["status"] = "COMPLETE"
            result["precipitation_error"] = round(
                (observation.precipitation or 0) - (forecast.precipitation or 0), 2
            )
            result["unexpected_rain"] = (
                (observation.precipitation or 0) > 5.0 and (forecast.precipitation or 0) < 2.0
            )

        return result

    @classmethod
    def _measure_plant_response(cls, db, farm_id, start, end):
        """Check for plant stress observations in the evaluation window."""
        observations = (
            db.query(ExperimentObservation)
            .filter(
                ExperimentObservation.timestamp >= start,
                ExperimentObservation.timestamp <= end,
            )
            .all()
        )
        if not observations:
            return None

        stress = [o for o in observations if o.parameter in ("wilting_index", "stress") and (o.value_numeric or 0) > 1]
        return {
            "observations_count": len(observations),
            "stress_observations": len(stress),
            "max_wilting_index": max((o.value_numeric for o in stress), default=None),
            "has_stress": len(stress) > 0,
        }

    @classmethod
    def _measure_water_response(cls, execution):
        """Record water usage from execution — never fabricate."""
        if not execution:
            return None
        return {
            "duration_seconds": execution.actual_duration_seconds,
            "water_volume_liters": execution.water_volume_liters,  # Strictly null if unmeasured
            "status": execution.status,
        }

    @classmethod
    def _classify_outcome(cls, log, actual_action, exec_outcome, sensor, weather, plant):
        """Classify the decision outcome with explainable reasons."""
        reasons = []

        # Execution failure takes precedence
        if exec_outcome == "EXECUTION_FAILED":
            reasons.append("Hardware execution failed or was aborted.")
            return "EXECUTION_FAILURE", reasons

        if actual_action == "BLOCKED":
            reasons.append("Execution was blocked by safety engine.")
            return "EXECUTION_FAILURE", reasons

        decision = log.decision

        # Check data sufficiency
        has_sensor = sensor and sensor.get("status") == "MEASURED"
        has_weather = weather and weather.get("status") in ("COMPLETE", "OBSERVED_ONLY")
        has_plant = plant is not None

        if not has_sensor and not has_weather and not has_plant:
            reasons.append("Insufficient sensor, weather, and plant observation data for evaluation.")
            return "INSUFFICIENT_DATA", reasons

        # --- IRRIGATE decisions ---
        if decision == "IRRIGATE":
            if actual_action == "EXECUTED":
                # Check for unexpected rain after irrigation
                unexpected_rain = weather and weather.get("unexpected_rain", False)
                observed_rain = weather and (weather.get("observed_precipitation_mm") or 0) > 5.0

                if unexpected_rain or observed_rain:
                    rain_mm = weather.get("observed_precipitation_mm", 0)
                    reasons.append(f"Irrigation was executed but {rain_mm}mm rainfall observed afterward.")
                    reasons.append("Rain timing and forecast accuracy suggest irrigation may not have been needed.")
                    reasons.append("CAUTION: This is observational — other factors may have necessitated pre-emptive irrigation.")
                    return "POSSIBLE_UNNECESSARY_IRRIGATION", reasons

                # Check sensor recovery
                if has_sensor:
                    delta = sensor.get("delta")
                    if delta is not None and delta > 0:
                        reasons.append(f"Soil moisture recovered by +{delta}% after irrigation.")
                    elif delta is not None and delta <= 0:
                        reasons.append(f"Soil moisture did not recover (delta={delta}%). Possible sensor issue or drainage.")

                if has_plant and plant.get("has_stress"):
                    reasons.append("Plant stress observed despite irrigation — may indicate deeper issue.")
                else:
                    reasons.append("No plant stress observed after irrigation.")

                reasons.append("Irrigation executed and field conditions improved or remained stable.")
                return "CORRECT_IRRIGATION", reasons

            elif actual_action in ("NOT_EXECUTED", "DEFERRED", "SIMULATED"):
                if has_plant and plant.get("has_stress"):
                    reasons.append("Irrigation was recommended but not executed; plant stress was subsequently observed.")
                    return "POSSIBLE_MISSED_IRRIGATION", reasons
                reasons.append("Irrigation recommended but not executed. Insufficient data on plant impact.")
                return "INSUFFICIENT_DATA", reasons

        # --- WAIT / MONITOR decisions ---
        elif decision in ("WAIT", "MONITOR"):
            if has_plant and plant.get("has_stress"):
                wilting = plant.get("max_wilting_index")
                reasons.append(f"Decision was {decision} but plant stress observed (wilting index={wilting}).")
                reasons.append("NOTE: Stress may be caused by factors other than irrigation deficit (heat, pests, disease, nutrients).")
                return "POSSIBLE_MISSED_IRRIGATION", reasons
            else:
                if has_sensor:
                    post = sensor.get("post_moisture")
                    if post is not None:
                        reasons.append(f"Post-decision soil moisture: {post}%. Plant remained healthy.")
                reasons.append(f"Successful {decision}: No adverse outcomes observed in evaluation window.")
                return "CORRECT_WAIT", reasons

        # --- ALERT decisions ---
        elif decision == "ALERT":
            reasons.append("ALERT decision — outcome evaluation is informational only.")
            return "UNKNOWN", reasons

        reasons.append("Could not determine outcome with available data.")
        return "UNKNOWN", reasons

    @classmethod
    def _assess_data_quality(cls, sensor, weather, plant):
        """Assess per-dimension data quality."""
        dimensions = {}
        score = 0

        if sensor and sensor.get("status") == "MEASURED":
            dimensions["sensor"] = "PRESENT"
            score += 1
        else:
            dimensions["sensor"] = "MISSING"

        if weather and weather.get("status") in ("COMPLETE", "OBSERVED_ONLY"):
            dimensions["weather"] = "PRESENT"
            score += 1
        else:
            dimensions["weather"] = "MISSING"

        if plant:
            dimensions["plant_observation"] = "PRESENT"
            score += 1
        else:
            dimensions["plant_observation"] = "MISSING"

        quality_map = {3: "HIGH", 2: "MEDIUM", 1: "LOW", 0: "INSUFFICIENT"}
        return quality_map.get(score, "INSUFFICIENT"), dimensions

    @classmethod
    def _enumerate_confounders(cls, weather, sensor):
        """List potential confounding factors for the outcome."""
        confounders = []
        if weather:
            if weather.get("observed_precipitation_mm") and weather["observed_precipitation_mm"] > 0:
                confounders.append("rainfall_occurred")
            if weather.get("observed_temperature") and weather["observed_temperature"] > 38:
                confounders.append("high_temperature_stress")
        if sensor:
            delta = sensor.get("delta")
            if delta is not None and abs(delta) > 20:
                confounders.append("large_sensor_change_possible_noise")
        confounders.extend(["nutrient_status_unknown", "pest_disease_status_unknown"])
        return confounders
