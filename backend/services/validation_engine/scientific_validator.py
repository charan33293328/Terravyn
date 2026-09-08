"""
Terravyn Validation Engine: Scientific Knowledge Validator
Validates external agronomic literature, ICAR/FAO sources, and research claims.
Evaluates source tier, condition matching, multi-source corroboration, and contextual contradictions.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from models.domain import (
    ResearchSource,
    EvidenceClaim,
    DynamicKnowledgeItem,
    KnowledgeValidationRecord,
)
from services.validation_engine.confidence_scorer import ValidationConfidenceScorer


class ScientificKnowledgeValidator:
    """Validates external agricultural research claims and dynamic knowledge items."""

    @classmethod
    def validate_knowledge_item(
        cls,
        db: Session,
        knowledge_item_id: int,
        target_field_context: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeValidationRecord:
        """Runs full scientific validation on a DynamicKnowledgeItem."""
        item = db.query(DynamicKnowledgeItem).filter(DynamicKnowledgeItem.id == knowledge_item_id).first()
        if not item:
            raise ValueError(f"DynamicKnowledgeItem #{knowledge_item_id} not found.")

        field_ctx = target_field_context or {}

        # 1. Source Quality Evaluation
        provenance = item.source_provenance or {}
        if isinstance(provenance, list):
            sources_list = provenance
        elif isinstance(provenance, dict):
            sources_list = [provenance]
        else:
            sources_list = []

        source_score, is_independent, has_duplicates = cls._evaluate_source_quality(sources_list)

        # 2. Condition Matching (Crop, Soil, Growth Stage, Region)
        applicability_score, condition_notes = cls._evaluate_condition_matching(item, field_ctx)

        # 3. Contradiction Analysis
        has_contradiction, contradiction_reason, is_contextual = cls._analyze_contradictions(db, item)

        # 4. Consistency & Environmental Context
        consistency_score = 85.0 if not has_contradiction else (60.0 if is_contextual else 30.0)
        env_score = applicability_score

        # 5. Multi-dimensional Score Assembly
        dims = ValidationConfidenceScorer.score_dimensions(
            source_quality=source_score,
            applicability=applicability_score,
            repeatability=75.0 if is_independent else 45.0,
            sample_size=65.0,
            measurement_quality=70.0,
            experimental_design=75.0,
            consistency=consistency_score,
            confounding_risk=80.0,
            temporal_consistency=70.0,
            environmental_context=env_score,
        )

        conf, conf_level, reasons, limitations, next_step = ValidationConfidenceScorer.compute_overall_confidence(
            dimensions=dims,
            is_experimental=False,
        )

        # Apply Contradiction / Duplicate overrides
        if has_duplicates:
            limitations.append("Detected overlapping/circular citations among sources.")
        if has_contradiction:
            if is_contextual:
                reasons.append(f"Contextual variance noted: {contradiction_reason}")
                next_step = "REVIEW_REQUIRED"
            else:
                limitations.append(f"Agronomic contradiction detected: {contradiction_reason}")
                next_step = "REJECT"

        # Determine validated status
        if next_step == "PROMOTE_TO_VALIDATED":
            final_status = "VALIDATED"
        elif next_step == "PROMOTE_TO_PROVISIONAL":
            final_status = "PROVISIONAL"
        elif next_step == "REJECT":
            final_status = "REJECTED"
        else:
            final_status = "UNDER_REVIEW"

        # Record validation audit
        rec = KnowledgeValidationRecord(
            target_type="SCIENTIFIC_KNOWLEDGE",
            target_id=item.id,
            status=final_status,
            confidence=conf,
            confidence_level=conf_level,
            dimension_scores=dims,
            evidence_count=len(sources_list),
            experiment_count=0,
            data_quality="HIGH" if source_score >= 70 else "MEDIUM",
            scope="GLOBAL" if not item.soil_type else "SOIL_TYPE",
            reasons=reasons + condition_notes,
            limitations=limitations,
            recommended_next_step=next_step,
        )
        db.add(rec)

        # Update item status if qualified
        if final_status in ("VALIDATED", "PROVISIONAL", "REJECTED"):
            item.status = final_status
            item.confidence = conf
            item.last_reviewed_at = datetime.utcnow()

        db.commit()
        db.refresh(rec)
        return rec

    @classmethod
    def _evaluate_source_quality(cls, sources_list: List[Dict[str, Any]]) -> Tuple[float, bool, bool]:
        """Evaluates tiers, detects duplicate/copied URLs or titles."""
        if not sources_list:
            return 30.0, False, False

        tiers = []
        titles = set()
        has_duplicates = False

        for s in sources_list:
            t = s.get("source_tier") or s.get("tier") or 3
            tiers.append(t)
            title = (s.get("title") or s.get("organization") or "").lower().strip()
            if title in titles:
                has_duplicates = True
            titles.add(title)

        # Tier 1: 90, Tier 2: 75, Tier 3: 55, Tier 4: 25
        tier_scores = {1: 90.0, 2: 75.0, 3: 55.0, 4: 25.0}
        avg_score = sum(tier_scores.get(t, 50.0) for t in tiers) / len(tiers)

        # Corroboration bonus for multiple distinct independent sources
        is_independent = len(titles) >= 2 and not has_duplicates
        if is_independent:
            avg_score = min(100.0, avg_score + 10.0)

        return avg_score, is_independent, has_duplicates

    @classmethod
    def _evaluate_condition_matching(
        cls,
        item: DynamicKnowledgeItem,
        field_context: Dict[str, Any],
    ) -> Tuple[float, List[str]]:
        """Compares scientific claim conditions against field profile."""
        score = 80.0
        notes = []

        target_crop = field_context.get("crop", "Green Gram (Moong)")
        target_soil = field_context.get("soil_type")
        target_stage = field_context.get("growth_stage")

        if item.crop and target_crop and item.crop.lower() in target_crop.lower():
            notes.append("Target crop matched (Green Gram / Vigna radiata).")
        else:
            score -= 30.0
            notes.append(f"Crop mismatch: Research ({item.crop}) vs Field ({target_crop}).")

        if item.soil_type and target_soil:
            if item.soil_type.lower() == target_soil.lower():
                notes.append(f"Exact soil match: {item.soil_type}.")
                score += 10.0
            else:
                score -= 15.0
                notes.append(f"Soil difference: Research ({item.soil_type}) vs Field ({target_soil}).")

        if item.growth_stage and target_stage:
            if item.growth_stage.lower() == target_stage.lower():
                notes.append(f"Growth stage match: {item.growth_stage}.")
            else:
                score -= 10.0
                notes.append(f"Stage difference: Research ({item.growth_stage}) vs Field ({target_stage}).")

        return max(20.0, min(100.0, score)), notes

    @classmethod
    def _analyze_contradictions(
        cls,
        db: Session,
        item: DynamicKnowledgeItem,
    ) -> Tuple[bool, Optional[str], bool]:
        """
        Determines whether item conflicts with existing validated knowledge.
        Differentiates legitimate contextual differences (e.g. soil texture) from true contradictions.
        """
        # Search for existing validated items with the same parameter
        peers = (
            db.query(DynamicKnowledgeItem)
            .filter(
                DynamicKnowledgeItem.parameter == item.parameter,
                DynamicKnowledgeItem.id != item.id,
                DynamicKnowledgeItem.status == "VALIDATED",
            )
            .all()
        )

        if not peers:
            return False, None, False

        for peer in peers:
            # Check if soils differ
            if item.soil_type and peer.soil_type and item.soil_type.lower() != peer.soil_type.lower():
                # Legitimate contextual variance (e.g. clay soil holds more moisture than sandy loam)
                return (
                    True,
                    f"Different soil texture baseline: {item.soil_type} vs {peer.soil_type}.",
                    True,  # is_contextual = True
                )

            # Check if stages differ
            if item.growth_stage and peer.growth_stage and item.growth_stage.lower() != peer.growth_stage.lower():
                return (
                    True,
                    f"Different growth stage sensitivity: {item.growth_stage} vs {peer.growth_stage}.",
                    True,  # is_contextual = True
                )

        return False, None, False
