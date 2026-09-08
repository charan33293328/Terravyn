"""
Terravyn Learning Engine: Knowledge Conflict Detector
Compares Terravyn observations against Knowledge Base values.
Triggers Research Engine for investigation. Never auto-overwrites knowledge.
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import (
    DecisionOutcomeAnalysis,
    DynamicKnowledgeItem,
    LearningCandidate,
)

logger = logging.getLogger(__name__)


class KnowledgeConflictDetector:
    """Detects conflicts between repeated field observations and established knowledge."""

    @classmethod
    def detect_conflicts(
        cls,
        db: Session,
        farm_id: int,
        min_conflicting_outcomes: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Compare repeated outcome observations against DynamicKnowledgeItem values.
        E.g., if KB says moisture threshold is 25% but repeated outcomes show stress at 30%.
        """
        conflicts = []

        # Get POSSIBLE_MISSED_IRRIGATION outcomes — these suggest the threshold may be wrong
        missed = (
            db.query(DecisionOutcomeAnalysis)
            .filter(
                DecisionOutcomeAnalysis.farm_id == farm_id,
                DecisionOutcomeAnalysis.classification == "POSSIBLE_MISSED_IRRIGATION",
            )
            .all()
        )

        if len(missed) < min_conflicting_outcomes:
            return conflicts

        # Group missed irrigation outcomes by growth stage
        stage_groups = {}
        for m in missed:
            fp = m.situation_fingerprint or {}
            stage = (fp.get("growth_stage") or "Flowering").lower()
            sm = fp.get("soil_moisture_pct") or (m.sensor_response or {}).get("pre_moisture")
            if sm is not None:
                if stage not in stage_groups:
                    stage_groups[stage] = []
                stage_groups[stage].append(sm)

        # Compare against knowledge base items for moisture thresholds
        kb_items = (
            db.query(DynamicKnowledgeItem)
            .filter(
                DynamicKnowledgeItem.crop.ilike("%green gram%"),
                DynamicKnowledgeItem.parameter.ilike("%moisture%"),
                DynamicKnowledgeItem.status.in_(["VALIDATED", "PROVISIONAL"]),
            )
            .all()
        )

        for stage, moisture_values in stage_groups.items():
            if len(moisture_values) < min_conflicting_outcomes:
                continue

            avg_stress_moisture = sum(moisture_values) / len(moisture_values)

            for item in kb_items:
                item_stage = (item.growth_stage or "").lower()
                if item_stage and item_stage != stage:
                    continue

                try:
                    finding = item.finding or ""
                    import re
                    numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%', finding)
                    if not numbers:
                        continue

                    kb_threshold = float(numbers[0])
                    # If observed stress consistently occurs above KB threshold by at least 2%
                    if avg_stress_moisture > kb_threshold + 1.5:
                        conflict = {
                            "kb_item_id": item.id,
                            "kb_parameter": item.parameter,
                            "kb_threshold_pct": kb_threshold,
                            "observed_stress_moisture_pct": round(avg_stress_moisture, 1),
                            "conflicting_outcomes": len(moisture_values),
                            "discrepancy_pct": round(avg_stress_moisture - kb_threshold, 1),
                            "growth_stage": item.growth_stage or stage,
                            "soil_type": item.soil_type or "sandy_loam",
                        }

                        # Create KNOWLEDGE_CONFLICT candidate
                        idemp = f"conflict:{farm_id}:{item.id}:{item.growth_stage}"
                        existing = db.query(LearningCandidate).filter(
                            LearningCandidate.idempotency_key == idemp
                        ).first()

                        if not existing:
                            candidate = LearningCandidate(
                                candidate_type="KNOWLEDGE_CONFLICT",
                                crop=item.crop,
                                growth_stage=item.growth_stage,
                                soil_type=item.soil_type,
                                farm_id=farm_id,
                                pattern_description=(
                                    f"Repeated plant stress observed at {avg_stress_moisture:.1f}% soil moisture, "
                                    f"while Knowledge Base threshold is {kb_threshold:.1f}%. "
                                    f"Based on {len(moisture_values)} independent observations. "
                                    f"This may indicate the KB threshold needs field-specific adjustment."
                                ),
                                pattern_data=conflict,
                                observation_count=len(moisture_values),
                                event_count=len(moisture_values),
                                field_count=1,
                                data_quality="MEDIUM",
                                confidence=min(65, len(moisture_values) * 10),
                                priority="HIGH",
                                impact="HIGH",
                                risk_level="MEDIUM",
                                status="EXPERIMENTAL",
                                idempotency_key=idemp,
                            )
                            db.add(candidate)
                            db.commit()
                            db.refresh(candidate)
                            conflict["candidate_id"] = candidate.id
                        else:
                            existing.observation_count = len(moisture_values)
                            existing.event_count = len(moisture_values)
                            existing.updated_at = datetime.utcnow()
                            db.commit()
                            conflict["candidate_id"] = existing.id

                        conflicts.append(conflict)
                except Exception as e:
                    logger.warning(f"Error processing KB item #{item.id}: {e}")
                    continue

        return conflicts

    @classmethod
    def trigger_research(
        cls,
        db: Session,
        candidate_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Submit a KNOWLEDGE_CONFLICT candidate to the Research Engine for investigation."""
        candidate = db.query(LearningCandidate).filter(LearningCandidate.id == candidate_id).first()
        if not candidate or candidate.candidate_type != "KNOWLEDGE_CONFLICT":
            return None

        try:
            from services.research_engine.service import ResearchAndKnowledgeAcquisitionService
            from services.research_engine.fingerprint import SituationFingerprint

            research_svc = ResearchAndKnowledgeAcquisitionService()
            data = candidate.pattern_data or {}

            question = (
                f"Investigation: Why does Green Gram in {candidate.soil_type or 'field'} soil "
                f"during {candidate.growth_stage or 'crop'} stage exhibit plant stress "
                f"at {data.get('observed_stress_moisture_pct', '?')}% soil moisture "
                f"while established threshold is {data.get('kb_threshold_pct', '?')}%?"
            )

            fingerprint = SituationFingerprint(
                crop=candidate.crop or "green_gram",
                growth_stage=candidate.growth_stage or "flowering",
                soil_type=candidate.soil_type or "sandy_loam",
                problem_type="knowledge_conflict",
            )

            result = research_svc.process_field_situation(
                db=db,
                fingerprint=fingerprint,
                farm_id=candidate.farm_id or 1,
                force_research=True,
            )

            candidate.research_query_id = result.research_query_id
            candidate.status = "UNDER_REVIEW"
            db.commit()

            return {
                "research_triggered": result.research_triggered,
                "query_id": result.research_query_id,
                "sources_found": result.sources_searched,
                "summary": result.summary,
            }
        except Exception as e:
            logger.error(f"Research trigger failed for candidate #{candidate_id}: {e}")
            return {"research_triggered": False, "error": str(e)}
