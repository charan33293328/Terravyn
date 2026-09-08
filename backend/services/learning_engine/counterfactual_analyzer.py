"""
Terravyn Learning Engine: Counterfactual Analyzer
Estimates what might have happened with the alternative choice.
All results are explicitly labeled as ESTIMATE, never as observed fact.
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import DecisionOutcomeAnalysis

logger = logging.getLogger(__name__)


class CounterfactualAnalyzer:
    """Estimates alternative outcomes from historical data. Always labeled ESTIMATE."""

    @classmethod
    def estimate_counterfactual(
        cls,
        db: Session,
        outcome_analysis_id: int,
    ) -> Dict[str, Any]:
        """
        For a given outcome, estimate what might have happened with the alternative decision.
        Searches historical outcomes with similar situation_hash but different decisions.
        """
        outcome = db.query(DecisionOutcomeAnalysis).filter(
            DecisionOutcomeAnalysis.id == outcome_analysis_id
        ).first()

        if not outcome:
            return {"error": "Outcome analysis not found.", "is_estimate": True}

        if not outcome.situation_hash:
            return {
                "actual_decision": outcome.decision,
                "actual_classification": outcome.classification,
                "counterfactual_estimate": None,
                "confidence": 0,
                "reason": "No situation fingerprint available for comparison.",
                "is_estimate": True,
            }

        # Find historical outcomes with same situation but different decision
        alternative_decision = "WAIT" if outcome.decision == "IRRIGATE" else "IRRIGATE"

        similar = (
            db.query(DecisionOutcomeAnalysis)
            .filter(
                DecisionOutcomeAnalysis.situation_hash == outcome.situation_hash,
                DecisionOutcomeAnalysis.decision == alternative_decision,
                DecisionOutcomeAnalysis.id != outcome.id,
                DecisionOutcomeAnalysis.classification != "INSUFFICIENT_DATA",
            )
            .all()
        )

        if not similar:
            return {
                "actual_decision": outcome.decision,
                "actual_classification": outcome.classification,
                "counterfactual_estimate": None,
                "confidence": 0,
                "comparable_outcomes": 0,
                "reason": f"No historical outcomes found for {alternative_decision} in similar situations.",
                "is_estimate": True,
            }

        # Count classification distribution from similar alternative decisions
        from collections import Counter
        alt_classes = Counter(s.classification for s in similar)
        dominant, count = alt_classes.most_common(1)[0]
        total = len(similar)
        ratio = count / total

        confidence = min(60, int(total * 10 * ratio))

        return {
            "actual_decision": outcome.decision,
            "actual_classification": outcome.classification,
            "alternative_decision": alternative_decision,
            "counterfactual_estimate": dominant,
            "counterfactual_distribution": dict(alt_classes),
            "comparable_outcomes": total,
            "estimate_dominance_ratio": round(ratio, 2),
            "confidence": confidence,
            "reason": (
                f"Based on {total} historical outcomes in similar situations where "
                f"{alternative_decision} was chosen, {dominant} occurred {count}/{total} times "
                f"({ratio*100:.0f}%). This is an estimate, not a certainty."
            ),
            "is_estimate": True,
            "disclaimer": (
                "ESTIMATE ONLY: This counterfactual analysis is based on historical pattern "
                "matching, not controlled experimentation. Many confounding factors may differ "
                "between the compared situations. Do not treat this as causal evidence."
            ),
        }
