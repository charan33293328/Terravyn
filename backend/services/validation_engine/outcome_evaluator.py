"""
Terravyn Validation Engine: Decision Outcome Evaluator
Links historical decisions to subsequent irrigations, weather events, and plant responses.
Classifies outcomes into CORRECT_WAIT, CORRECT_IRRIGATION, MISSED_IRRIGATION, FALSE_IRRIGATION, INSUFFICIENT_DATA.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    CropDecisionLog,
    ExperimentIrrigationEvent,
    ExperimentObservation,
    DecisionOutcomeRecord,
)


class DecisionOutcomeEvaluator:
    """Evaluates decision efficacy by linking recommendations with actual field and plant outcomes."""

    @classmethod
    def evaluate_decision_outcome(
        cls,
        db: Session,
        decision_log_id: int,
    ) -> DecisionOutcomeRecord:
        """
        Analyzes the subsequent 24 hours following a decision:
        - Did an irrigation occur?
        - Did the plant exhibit wilting/stress?
        - Did rain occur?
        Classifies outcome and logs to decision_outcomes.
        """
        log = db.query(CropDecisionLog).filter(CropDecisionLog.id == decision_log_id).first()
        if not log:
            raise ValueError(f"CropDecisionLog #{decision_log_id} not found.")

        start_time = log.timestamp
        end_time = start_time + timedelta(hours=24)

        # 1. Check for subsequent irrigation event
        irrigation = (
            db.query(ExperimentIrrigationEvent)
            .filter(
                ExperimentIrrigationEvent.decision_log_id == decision_log_id,
            )
            .first()
        )
        if not irrigation:
            # Check within 24 hours window
            irrigation = (
                db.query(ExperimentIrrigationEvent)
                .filter(
                    ExperimentIrrigationEvent.start_time >= start_time,
                    ExperimentIrrigationEvent.start_time <= end_time,
                )
                .first()
            )

        # 2. Check for subsequent plant phenotypic observations
        observations = (
            db.query(ExperimentObservation)
            .filter(
                ExperimentObservation.timestamp >= start_time,
                ExperimentObservation.timestamp <= end_time,
            )
            .order_by(desc(ExperimentObservation.timestamp))
            .all()
        )

        stress_obs = next(
            (o for o in observations if o.parameter in ("wilting_index", "stress") and (o.value_numeric or 0) > 1),
            None,
        )

        # 3. Classify outcome
        classification = "INSUFFICIENT_DATA"
        plant_summary = "No follow-up observation recorded within 24h window."
        hours_to_resp = None

        if not observations and not irrigation:
            classification = "INSUFFICIENT_DATA"
        elif log.decision == "IRRIGATE":
            if irrigation:
                hours_to_resp = (irrigation.start_time - start_time).total_seconds() / 3600.0
                if stress_obs:
                    classification = "CORRECT_IRRIGATION"
                    plant_summary = "Water applied; relieved plant stress noted during monitoring."
                else:
                    classification = "CORRECT_IRRIGATION"
                    plant_summary = "Irrigation applied according to threshold target; moisture maintained."
            else:
                if stress_obs:
                    classification = "MISSED_IRRIGATION"
                    plant_summary = "Irrigation recommended but not applied; plant exhibited stress symptoms."
                else:
                    classification = "INSUFFICIENT_DATA"
                    plant_summary = "Irrigation recommended; physical response data incomplete."
        elif log.decision in ("WAIT", "MONITOR"):
            if stress_obs:
                classification = "MISSED_IRRIGATION"
                plant_summary = f"Decision was {log.decision}, but plant developed wilting index {stress_obs.value_numeric}."
            elif irrigation and irrigation.estimated_water_liters and irrigation.estimated_water_liters > 2.5:
                classification = "FALSE_IRRIGATION" if log.decision == "WAIT" else "CORRECT_WAIT"
                plant_summary = "Irrigation executed despite WAIT recommendation."
            else:
                classification = "CORRECT_WAIT"
                plant_summary = f"Successful {log.decision}: Plant remained turgid with no adverse moisture stress."

        outcome = DecisionOutcomeRecord(
            decision_log_id=log.id,
            irrigation_event_id=irrigation.id if irrigation else None,
            observation_id=stress_obs.id if stress_obs else (observations[0].id if observations else None),
            classification=classification,
            hours_to_response=round(hours_to_resp, 1) if hours_to_resp else None,
            plant_response_summary=plant_summary,
            environmental_context={
                "decision": log.decision,
                "moisture": log.soil_moisture,
                "stage": log.growth_stage,
                "et0": log.et0,
            },
            notes=f"Evaluated outcome for decision #{log.id} ({log.decision}).",
        )
        db.add(outcome)
        db.commit()
        db.refresh(outcome)
        return outcome

    @classmethod
    def get_outcome_statistics(cls, db: Session, limit: int = 100) -> Dict[str, Any]:
        """Calculates outcome rates across recent decision logs."""
        outcomes = (
            db.query(DecisionOutcomeRecord)
            .order_by(desc(DecisionOutcomeRecord.created_at))
            .limit(limit)
            .all()
        )
        if not outcomes:
            return {
                "total_evaluated": 0,
                "correct_wait_count": 0,
                "correct_irrigation_count": 0,
                "missed_irrigation_count": 0,
                "false_irrigation_count": 0,
                "insufficient_data_count": 0,
                "accuracy_rate_pct": None,
            }

        counts = {
            "CORRECT_WAIT": 0,
            "CORRECT_IRRIGATION": 0,
            "MISSED_IRRIGATION": 0,
            "FALSE_IRRIGATION": 0,
            "INSUFFICIENT_DATA": 0,
        }
        for o in outcomes:
            counts[o.classification] = counts.get(o.classification, 0) + 1

        actionable_total = counts["CORRECT_WAIT"] + counts["CORRECT_IRRIGATION"] + counts["MISSED_IRRIGATION"] + counts["FALSE_IRRIGATION"]
        correct_total = counts["CORRECT_WAIT"] + counts["CORRECT_IRRIGATION"]
        accuracy = round((correct_total / actionable_total) * 100.0, 1) if actionable_total > 0 else None

        return {
            "total_evaluated": len(outcomes),
            "correct_wait_count": counts["CORRECT_WAIT"],
            "correct_irrigation_count": counts["CORRECT_IRRIGATION"],
            "missed_irrigation_count": counts["MISSED_IRRIGATION"],
            "false_irrigation_count": counts["FALSE_IRRIGATION"],
            "insufficient_data_count": counts["INSUFFICIENT_DATA"],
            "accuracy_rate_pct": accuracy,
        }
