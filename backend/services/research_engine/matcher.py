"""
Terravyn Research Engine: Knowledge Matcher & Sufficiency Checker
Deterministically evaluates existing static Knowledge Base and dynamic database items
against a SituationFingerprint.
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .fingerprint import SituationFingerprint
from services.crop_engine.knowledge_base import knowledge_base, KnowledgeStatus


class SufficiencyLevel(str, Enum):
    SUFFICIENT = "SUFFICIENT"
    PARTIAL = "PARTIAL"
    INSUFFICIENT = "INSUFFICIENT"


class MatchedFactor(str, Enum):
    CROP = "crop"
    GROWTH_STAGE = "growth_stage"
    SOIL_TYPE = "soil_type"
    PROBLEM_TYPE = "problem_type"
    ENVIRONMENTAL_STATE = "environmental_state"
    VARIETY = "variety"


class MatchResult(BaseModel):
    sufficiency: SufficiencyLevel
    similarity_score: float  # 0 to 100
    matched_factors: List[str]
    matched_knowledge_ids: List[str]
    matched_dynamic_item_ids: List[int]
    evidence_status: str  # VALIDATED, PROVISIONAL, EXPERIMENTAL, NONE
    missing_factors: List[str]
    description: str


class KnowledgeMatcher:
    def __init__(self):
        self.static_kb = knowledge_base

    def match_situation(
        self,
        fingerprint: SituationFingerprint,
        db: Optional[Session] = None
    ) -> MatchResult:
        """
        Evaluate current situation fingerprint against static Knowledge Base and dynamic DB items.
        Returns MatchResult with deterministic similarity score and sufficiency classification.
        """
        matched_factors: List[str] = []
        missing_factors: List[str] = []
        matched_kb_ids: List[str] = []
        matched_dynamic_ids: List[int] = []
        
        # 1. Base Factor: Crop Match (Weight: 30%)
        crop_norm = fingerprint.crop.lower()
        has_crop_match = crop_norm in ["green_gram", "green gram (moong)", "vigna radiata", "mung bean"]
        crop_score = 30.0 if has_crop_match else 0.0
        if has_crop_match:
            matched_factors.append(MatchedFactor.CROP.value)
        else:
            missing_factors.append(MatchedFactor.CROP.value)

        # 2. Growth Stage Match (Weight: 25%)
        stage_norm = fingerprint.growth_stage.lower().replace(" ", "_")
        static_stages = [s.stage_name.lower().replace(" ", "_") for s in self.static_kb.list_stages()]
        has_stage_match = any(s in stage_norm or stage_norm in s for s in static_stages)
        stage_score = 25.0 if has_stage_match else 0.0
        if has_stage_match:
            matched_factors.append(MatchedFactor.GROWTH_STAGE.value)
        else:
            missing_factors.append(MatchedFactor.GROWTH_STAGE.value)

        # 3. Soil Match (Weight: 15%)
        soil_norm = fingerprint.soil_type.lower().replace(" ", "_")
        known_soils = ["sandy_loam", "loam", "clay_loam", "sandy", "black_cotton", "alluvial", "red_sandy"]
        has_soil_match = any(s in soil_norm or soil_norm in s for s in known_soils)
        soil_score = 15.0 if has_soil_match else 5.0
        if has_soil_match:
            matched_factors.append(MatchedFactor.SOIL_TYPE.value)
        else:
            missing_factors.append(MatchedFactor.SOIL_TYPE.value)

        # 4. Problem & Moisture Context Match (Weight: 15%)
        has_problem_match = False
        if fingerprint.problem_type == "water_stress":
            # Check if static KB covers water stress for this stage
            if has_stage_match:
                has_problem_match = True
                matched_kb_ids.append(f"KB-STAGE-{stage_norm.upper()}")
                matched_kb_ids.append("RULE-IRR-SOIL-MOISTURE-01")
        elif fingerprint.problem_type == "waterlogging":
            has_problem_match = True
            matched_kb_ids.append("KB-SOIL-WATERLOGGING-01")

        problem_score = 15.0 if has_problem_match else 0.0
        if has_problem_match:
            matched_factors.append(MatchedFactor.PROBLEM_TYPE.value)
        else:
            missing_factors.append(MatchedFactor.PROBLEM_TYPE.value)

        # 5. Meteorological & Environmental Context (Weight: 15%)
        env_score = 0.0
        if fingerprint.rain_forecast in ["none", "significant"]:
            env_score += 7.5
            matched_factors.append(MatchedFactor.ENVIRONMENTAL_STATE.value)
        if fingerprint.temperature_state in ["optimal", "high", "extreme_heat"]:
            env_score += 7.5

        # Check for dynamic knowledge items in DB
        highest_status = "VALIDATED" if matched_kb_ids else "NONE"
        if db:
            from models.domain import DynamicKnowledgeItem
            dynamic_items = (
                db.query(DynamicKnowledgeItem)
                .filter(
                    DynamicKnowledgeItem.crop.ilike(f"%{fingerprint.crop}%"),
                    DynamicKnowledgeItem.status.in_(["VALIDATED", "PROVISIONAL"])
                )
                .all()
            )
            for item in dynamic_items:
                # Check if item matches stage or parameter
                item_stage = (item.growth_stage or "").lower().replace(" ", "_")
                if item_stage and (item_stage in stage_norm or stage_norm in item_stage):
                    matched_dynamic_ids.append(item.id)
                    if item.status == "VALIDATED":
                        highest_status = "VALIDATED"
                    elif highest_status != "VALIDATED" and item.status == "PROVISIONAL":
                        highest_status = "PROVISIONAL"

        # Calculate Total Similarity Score
        total_similarity = crop_score + stage_score + soil_score + problem_score + env_score

        # Check edge cases where knowledge is explicitly INSUFFICIENT:
        # e.g., if problem_type is an edge case like extreme heat with novel soil condition or unmapped stress
        if not has_crop_match or not has_stage_match:
            sufficiency = SufficiencyLevel.INSUFFICIENT
            desc = "Critical crop or stage agronomy missing from knowledge base."
        elif total_similarity >= 85.0 and highest_status == "VALIDATED":
            sufficiency = SufficiencyLevel.SUFFICIENT
            desc = f"Comprehensive validated agronomic knowledge available (Score: {total_similarity:.1f}%)."
        elif total_similarity >= 60.0:
            sufficiency = SufficiencyLevel.PARTIAL
            desc = f"Partial knowledge available ({total_similarity:.1f}%). Supplemental research may improve accuracy."
        else:
            sufficiency = SufficiencyLevel.INSUFFICIENT
            desc = f"Insufficient specific evidence for situation profile (Score: {total_similarity:.1f}%)."

        return MatchResult(
            sufficiency=sufficiency,
            similarity_score=total_similarity,
            matched_factors=matched_factors,
            matched_knowledge_ids=matched_kb_ids,
            matched_dynamic_item_ids=matched_dynamic_ids,
            evidence_status=highest_status,
            missing_factors=missing_factors,
            description=desc
        )
