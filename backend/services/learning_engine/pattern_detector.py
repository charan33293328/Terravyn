"""
Terravyn Learning Engine: Deterministic Pattern Detector
Groups outcomes by situation fingerprint and detects repeated patterns.
No ML — uses aggregation, comparison, and rule-based candidate generation.
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.domain import (
    DecisionOutcomeAnalysis,
    LearningCandidate,
    LearningEvidence,
)

logger = logging.getLogger(__name__)


class DeterministicPatternDetector:
    """Detects recurring patterns from decision outcomes using deterministic methods."""

    @classmethod
    def detect_patterns(
        cls,
        db: Session,
        farm_id: int,
        min_events: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Group outcomes by situation_hash, detect dominant patterns,
        and create/update LearningCandidates.
        """
        outcomes = (
            db.query(DecisionOutcomeAnalysis)
            .filter(
                DecisionOutcomeAnalysis.farm_id == farm_id,
                DecisionOutcomeAnalysis.situation_hash.isnot(None),
                DecisionOutcomeAnalysis.classification != "INSUFFICIENT_DATA",
            )
            .all()
        )

        # Group by situation hash
        groups = {}
        for o in outcomes:
            h = o.situation_hash
            if h not in groups:
                groups[h] = []
            groups[h].append(o)

        detected = []

        for sit_hash, group_outcomes in groups.items():
            if len(group_outcomes) < min_events:
                continue

            # Count classification frequencies
            class_counts = Counter(o.classification for o in group_outcomes)
            total = len(group_outcomes)
            dominant_class, dominant_count = class_counts.most_common(1)[0]
            dominance_ratio = dominant_count / total

            if dominance_ratio < 0.6:
                continue  # No clear dominant pattern

            # Count unique events (by decision_log_id — each decision is one event)
            unique_decisions = set(o.decision_log_id for o in group_outcomes)
            event_count = len(unique_decisions)

            # Count unique experiments
            unique_experiments = set(o.experiment_id for o in group_outcomes if o.experiment_id)
            experiment_count = len(unique_experiments)

            # Determine candidate type from dominant classification
            candidate_type = cls._classification_to_candidate_type(dominant_class)

            # Assess evidence strength
            confidence = cls.assess_evidence_strength(
                observation_count=total,
                event_count=event_count,
                experiment_count=experiment_count,
                field_count=1,
            )

            # Priority
            priority = cls.assign_priority(
                frequency=event_count,
                impact=dominant_class,
                risk="LOW",
            )

            # Build pattern data from the first outcome's fingerprint
            sample = group_outcomes[0]
            fingerprint_data = sample.situation_fingerprint or {}

            # Create or update candidate
            idemp = f"{sit_hash}:{candidate_type}:{farm_id}"
            existing = db.query(LearningCandidate).filter(
                LearningCandidate.idempotency_key == idemp
            ).first()

            if existing:
                existing.observation_count = total
                existing.event_count = event_count
                existing.experiment_count = experiment_count
                existing.confidence = confidence
                existing.priority = priority
                existing.updated_at = datetime.utcnow()
                existing.evidence_ids = [o.id for o in group_outcomes]
                db.commit()
                candidate = existing
            else:
                decision_val = sample.decision
                stage = fingerprint_data.get("growth_stage", "unknown")
                soil = fingerprint_data.get("soil_type", "unknown")

                candidate = LearningCandidate(
                    candidate_type=candidate_type,
                    crop=fingerprint_data.get("crop", "green_gram"),
                    growth_stage=stage,
                    soil_type=soil,
                    farm_id=farm_id,
                    situation_hash=sit_hash,
                    pattern_description=(
                        f"Repeated {dominant_class} pattern detected: "
                        f"{dominant_count}/{total} outcomes ({dominance_ratio*100:.0f}%) "
                        f"when decision is {decision_val} during {stage} in {soil} soil. "
                        f"Based on {event_count} independent events."
                    ),
                    pattern_data={
                        "dominant_classification": dominant_class,
                        "dominant_count": dominant_count,
                        "total_outcomes": total,
                        "dominance_ratio": round(dominance_ratio, 2),
                        "classification_distribution": dict(class_counts),
                        "fingerprint": fingerprint_data,
                    },
                    observation_count=total,
                    event_count=event_count,
                    experiment_count=experiment_count,
                    field_count=1,
                    data_quality="HIGH" if event_count >= 10 else ("MEDIUM" if event_count >= 5 else "LOW"),
                    confidence=confidence,
                    priority=priority,
                    impact="HIGH" if dominant_class in ("POSSIBLE_MISSED_IRRIGATION",) else "MEDIUM",
                    risk_level="HIGH" if dominant_class in ("POSSIBLE_MISSED_IRRIGATION",) else "MEDIUM",
                    status="EXPERIMENTAL",
                    evidence_ids=[o.id for o in group_outcomes],
                    idempotency_key=idemp,
                )
                db.add(candidate)
                db.commit()
                db.refresh(candidate)

            # Link evidence records
            for outcome in group_outcomes:
                existing_evidence = db.query(LearningEvidence).filter(
                    LearningEvidence.candidate_id == candidate.id,
                    LearningEvidence.outcome_analysis_id == outcome.id,
                ).first()
                if not existing_evidence:
                    ev_type = "SUPPORTING" if outcome.classification == dominant_class else "CONTRADICTING"
                    evidence = LearningEvidence(
                        candidate_id=candidate.id,
                        outcome_analysis_id=outcome.id,
                        evidence_type=ev_type,
                        weight=1.0 if outcome.data_quality == "HIGH" else 0.5,
                    )
                    db.add(evidence)

            db.commit()

            detected.append({
                "candidate_id": candidate.id,
                "situation_hash": sit_hash,
                "dominant_classification": dominant_class,
                "dominance_ratio": round(dominance_ratio, 2),
                "event_count": event_count,
                "confidence": confidence,
                "priority": priority,
            })

        logger.info(f"[PatternDetector] Detected {len(detected)} patterns for farm #{farm_id}")
        return detected

    @staticmethod
    def assess_evidence_strength(
        observation_count: int,
        event_count: int,
        experiment_count: int,
        field_count: int,
    ) -> int:
        """
        Calculate confidence 0-100 based on evidence hierarchy.
        1 plant < multiple plants < multiple plots < multiple experiments < multiple fields
        """
        score = 0

        # Base score from observation count (max 20)
        score += min(20, observation_count * 2)

        # Event independence (max 30)
        score += min(30, event_count * 5)

        # Experimental replication (max 30)
        score += min(30, experiment_count * 10)

        # Field replication (max 20)
        score += min(20, field_count * 15)

        return min(100, score)

    @staticmethod
    def assign_priority(frequency: int, impact: str, risk: str) -> str:
        """Assign priority based on frequency, impact, and risk."""
        score = 0

        # Frequency contribution
        if frequency >= 10:
            score += 3
        elif frequency >= 5:
            score += 2
        else:
            score += 1

        # Impact contribution
        if impact in ("POSSIBLE_MISSED_IRRIGATION", "EXECUTION_FAILURE"):
            score += 3
        elif impact in ("POSSIBLE_UNNECESSARY_IRRIGATION",):
            score += 2
        else:
            score += 1

        if score >= 5:
            return "HIGH"
        elif score >= 3:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _classification_to_candidate_type(classification: str) -> str:
        """Map outcome classification to learning candidate type."""
        mapping = {
            "CORRECT_IRRIGATION": "IRRIGATION_PATTERN",
            "POSSIBLE_UNNECESSARY_IRRIGATION": "IRRIGATION_PATTERN",
            "POSSIBLE_MISSED_IRRIGATION": "IRRIGATION_PATTERN",
            "CORRECT_WAIT": "IRRIGATION_PATTERN",
            "EXECUTION_FAILURE": "DATA_QUALITY_PATTERN",
        }
        return mapping.get(classification, "IRRIGATION_PATTERN")
