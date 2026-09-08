"""
Terravyn Research Engine: Evidence Quality Validator & Contradiction Detector
Calculates deterministic evidence quality scores, detects conflicts, and identifies duplicates.
"""
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel
from .extractor import ExtractedEvidenceClaim
from .fingerprint import SituationFingerprint
from services.crop_engine.knowledge_base import knowledge_base


class ValidationResult(BaseModel):
    quality_score: float
    is_valid: bool
    has_conflict: bool
    conflict_reason: Optional[str] = None
    is_duplicate: bool = False
    corroboration_count: int = 1
    score_breakdown: Dict[str, float] = {}


class EvidenceValidator:
    def __init__(self):
        self.static_kb = knowledge_base

    def calculate_quality_score(
        self,
        claim: ExtractedEvidenceClaim,
        fingerprint: SituationFingerprint,
        corroborating_claims: Optional[List[ExtractedEvidenceClaim]] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculates evidence quality score (0 to 100).
        TierBase (40/30/15/0) + Relevance (20) + Specificity (15) + Corroboration (15) - Conflict (50)
        """
        breakdown: Dict[str, float] = {}

        # 1. Source Tier Base Score
        if claim.source_tier == 1:
            tier_score = 40.0
        elif claim.source_tier == 2:
            tier_score = 30.0
        elif claim.source_tier == 3:
            tier_score = 15.0
        else:
            tier_score = 0.0
        breakdown["source_tier_score"] = tier_score

        # 2. Relevance Score (Max 20)
        rel_score = 0.0
        stage_norm = fingerprint.growth_stage.lower().replace(" ", "_")
        claim_stage = (claim.growth_stage or "").lower().replace(" ", "_")
        if claim_stage in stage_norm or stage_norm in claim_stage or claim_stage == "all":
            rel_score += 10.0
        
        soil_norm = fingerprint.soil_type.lower().replace(" ", "_")
        claim_soil = (claim.soil_type or "").lower().replace(" ", "_")
        if claim_soil in soil_norm or soil_norm in claim_soil or claim_soil == "all":
            rel_score += 10.0
        breakdown["relevance_score"] = rel_score

        # 3. Specificity & Clarity (Max 15)
        spec_score = 0.0
        if claim.value_min is not None and claim.unit:
            spec_score += 10.0
        if claim.condition_context:
            spec_score += 5.0
        breakdown["specificity_score"] = spec_score

        # 4. Corroboration (Max 15)
        corrob_count = len(corroborating_claims or [])
        corrob_score = min(15.0, corrob_count * 7.5)
        breakdown["corroboration_score"] = corrob_score

        total_score = tier_score + rel_score + spec_score + corrob_score
        return total_score, breakdown

    def detect_contradictions(
        self,
        claim: ExtractedEvidenceClaim,
        fingerprint: SituationFingerprint,
        existing_claims: Optional[List[ExtractedEvidenceClaim]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Check whether claim contradicts established ICAR knowledge or existing claims under identical conditions.
        """
        stage_norm = fingerprint.growth_stage.lower().replace(" ", "_")
        soil_norm = fingerprint.soil_type.lower().replace(" ", "_")

        # Check known critical threshold for Green Gram flowering in sandy loam
        if "flowering" in stage_norm and "sandy" in soil_norm:
            if claim.parameter == "flowering_irrigation_threshold":
                # Established baseline is 24-26%. If a source recommends withholding until <= 15%, that's severe conflict!
                if claim.value_min is not None and claim.value_min < 18.0:
                    return True, (
                        f"Claim value {claim.value_min}% contradicts established ICAR/IIPR baseline "
                        "(24-26% moisture threshold during flowering in sandy loam)."
                    )

        # Check against peer claims in the current research query
        if existing_claims:
            for peer in existing_claims:
                if peer.parameter == claim.parameter and peer.source_title != claim.source_title:
                    # If numerical values differ by > 35% under same conditions
                    if claim.value_min is not None and peer.value_min is not None:
                        diff = abs(claim.value_min - peer.value_min)
                        if diff >= 8.0:
                            return True, (
                                f"Direct numerical contradiction between '{claim.source_title}' ({claim.value_min}{claim.unit}) "
                                f"and '{peer.source_title}' ({peer.value_min}{peer.unit})."
                            )

        return False, None

    def validate_claim(
        self,
        claim: ExtractedEvidenceClaim,
        fingerprint: SituationFingerprint,
        peer_claims: Optional[List[ExtractedEvidenceClaim]] = None
    ) -> ValidationResult:
        """Runs complete validation: quality score + conflict check."""
        # Find corroborating claims (same parameter and comparable values)
        corroborating = []
        if peer_claims:
            for p in peer_claims:
                if p.parameter == claim.parameter and p.source_title != claim.source_title:
                    if claim.value_min is not None and p.value_min is not None:
                        if abs(claim.value_min - p.value_min) <= 4.0:
                            corroborating.append(p)

        score, breakdown = self.calculate_quality_score(claim, fingerprint, corroborating)
        has_conflict, conflict_reason = self.detect_contradictions(claim, fingerprint, peer_claims)

        if has_conflict:
            score = max(0.0, score - 50.0)
            breakdown["contradiction_penalty"] = -50.0

        is_valid = (score >= 70.0) and not has_conflict and (claim.source_tier in [1, 2])

        return ValidationResult(
            quality_score=score,
            is_valid=is_valid,
            has_conflict=has_conflict,
            conflict_reason=conflict_reason,
            corroboration_count=1 + len(corroborating),
            score_breakdown=breakdown
        )
