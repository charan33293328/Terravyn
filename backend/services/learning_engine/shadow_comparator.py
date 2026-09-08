"""
Terravyn Learning Engine: Shadow Comparison Engine
Evaluates candidate improvements against historical decisions in shadow mode.
Does NOT activate based solely on water savings.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    LearningCandidate,
    DecisionOutcomeAnalysis,
    ImprovementVersion,
    FieldCalibrationRecord,
)

logger = logging.getLogger(__name__)


class ShadowComparisonEngine:
    """Simulates and compares proposed candidate logic against historical production decisions."""

    @classmethod
    def compare_strategies(
        cls,
        db: Session,
        farm_id: int,
        candidate_id: int,
        sample_limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Retrieves the LearningCandidate, compares proposed changes against historical outcomes,
        evaluates divergence, water impact, and missed irrigation risk, and stores an ImprovementVersion.
        """
        candidate = db.query(LearningCandidate).filter(LearningCandidate.id == candidate_id).first()
        if not candidate:
            return {"error": f"LearningCandidate #{candidate_id} not found."}

        # Query historical decisions
        outcomes = (
            db.query(DecisionOutcomeAnalysis)
            .filter(
                DecisionOutcomeAnalysis.farm_id == farm_id,
                DecisionOutcomeAnalysis.classification.notin_(["INSUFFICIENT_DATA", "UNKNOWN"]),
            )
            .order_by(desc(DecisionOutcomeAnalysis.created_at))
            .limit(sample_limit)
            .all()
        )

        total_evaluated = len(outcomes)
        if total_evaluated == 0:
            return {
                "candidate_id": candidate_id,
                "farm_id": farm_id,
                "status": "INSUFFICIENT_HISTORY",
                "message": "No historical decision outcomes available for shadow comparison.",
            }

        # Simulate decisions under candidate logic
        # For instance, if candidate proposes threshold adjustment or timing changes
        simulated_changes = 0
        water_saved_events = 0
        potential_stress_risk_events = 0
        agreement_count = 0

        for out in outcomes:
            orig_decision = out.decision
            orig_classification = out.classification
            fp = out.situation_fingerprint or {}
            moisture = fp.get("soil_moisture_pct") or 25.0

            # Evaluate what candidate logic would recommend
            # If candidate type is IRRIGATION_PATTERN or CALIBRATION_PATTERN
            cand_data = candidate.pattern_data or {}
            suggested_threshold = cand_data.get("suggested_threshold", 28.0)

            # Heuristic simulation
            sim_decision = orig_decision
            if candidate.candidate_type in ("IRRIGATION_PATTERN", "CALIBRATION_PATTERN"):
                if moisture < suggested_threshold:
                    sim_decision = "IRRIGATE"
                else:
                    sim_decision = "WAIT"

            if sim_decision == orig_decision:
                agreement_count += 1
            else:
                simulated_changes += 1
                if orig_decision == "IRRIGATE" and sim_decision == "WAIT":
                    # Potentially saved water, but check if plant stressed
                    if orig_classification == "POSSIBLE_UNNECESSARY_IRRIGATION":
                        water_saved_events += 1
                    elif orig_classification == "CORRECT_IRRIGATION":
                        potential_stress_risk_events += 1
                elif orig_decision == "WAIT" and sim_decision == "IRRIGATE":
                    if orig_classification == "POSSIBLE_MISSED_IRRIGATION":
                        # Candidate would have prevented missed irrigation
                        pass

        divergence_rate = round((simulated_changes / total_evaluated) * 100.0, 1) if total_evaluated > 0 else 0
        agreement_rate = round((agreement_count / total_evaluated) * 100.0, 1) if total_evaluated > 0 else 100

        shadow_summary = {
            "total_decisions_evaluated": total_evaluated,
            "agreement_count": agreement_count,
            "agreement_rate_pct": agreement_rate,
            "simulated_changes_count": simulated_changes,
            "divergence_rate_pct": divergence_rate,
            "water_saving_opportunities": water_saved_events,
            "potential_stress_risk_events": potential_stress_risk_events,
            "overall_risk": "LOW" if potential_stress_risk_events == 0 else ("MEDIUM" if potential_stress_risk_events <= 2 else "HIGH"),
        }

        # Record ImprovementVersion
        cal = None
        if candidate.calibration_id:
            cal = db.query(FieldCalibrationRecord).filter(FieldCalibrationRecord.id == candidate.calibration_id).first()

        prev_ver = cal.version if cal else 1
        new_ver = prev_ver + 1

        improvement = ImprovementVersion(
            candidate_id=candidate.id,
            calibration_id=candidate.calibration_id,
            previous_version=prev_ver,
            new_version=new_ver,
            improvement_type=candidate.candidate_type,
            reason=candidate.pattern_description,
            evidence_summary=shadow_summary,
            confidence=candidate.confidence,
            status="SHADOW_TESTING",
            shadow_comparison=shadow_summary,
        )
        db.add(improvement)
        db.commit()
        db.refresh(improvement)

        return {
            "improvement_version_id": improvement.id,
            "candidate_id": candidate_id,
            "shadow_comparison": shadow_summary,
            "status": "SHADOW_TESTING",
        }
