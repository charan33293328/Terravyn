"""
Terravyn Research Engine: Knowledge Promoter & Review Queue Manager
Auto-promotes strong verified evidence into DynamicKnowledgeItem or queues for manual agronomist review.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.domain import DynamicKnowledgeItem, KnowledgeReviewQueue, EvidenceClaim
from .extractor import ExtractedEvidenceClaim
from .validator import ValidationResult
from .fingerprint import SituationFingerprint

logger = logging.getLogger(__name__)


class KnowledgePromoter:
    def process_claim(
        self,
        db: Session,
        claim: ExtractedEvidenceClaim,
        validation: ValidationResult,
        fingerprint: SituationFingerprint,
        evidence_claim_db_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluate validation outcome:
        - If strong (is_valid=True, Quality >= 70, no conflict, Tier 1/2) -> Auto-store in DynamicKnowledgeItem.
        - If conflict or weak -> Route to KnowledgeReviewQueue with status UNDER_REVIEW / PENDING.
        """
        crop_name = fingerprint.crop
        stage = claim.growth_stage or fingerprint.growth_stage
        soil = claim.soil_type or fingerprint.soil_type

        # Construct Provenance Record
        provenance_entry = {
            "sourceTitle": claim.source_title,
            "organization": claim.organization,
            "url": claim.source_url,
            "sourceTier": claim.source_tier,
            "qualityScore": validation.quality_score,
            "corroborationCount": validation.corroboration_count,
            "retrievedAt": datetime.utcnow().isoformat(),
            "scoreBreakdown": validation.score_breakdown
        }

        # Case 1: Contradiction Detected OR Weak/Unreliable Evidence
        if validation.has_conflict or not validation.is_valid:
            priority = "HIGH" if validation.has_conflict else "MEDIUM"
            reason = (
                f"Contradiction detected: {validation.conflict_reason}"
                if validation.has_conflict
                else f"Insufficient evidence quality score ({validation.quality_score:.1f}/100) from Tier {claim.source_tier} source."
            )

            review_entry = KnowledgeReviewQueue(
                knowledge_item_id=None,
                evidence_claim_id=evidence_claim_db_id,
                reason=reason,
                conflict_details={
                    "claim_text": claim.claim_text,
                    "parameter": claim.parameter,
                    "value_min": claim.value_min,
                    "value_max": claim.value_max,
                    "unit": claim.unit,
                    "source": provenance_entry,
                    "score_breakdown": validation.score_breakdown
                },
                priority=priority,
                status="PENDING",
                created_at=datetime.utcnow()
            )
            db.add(review_entry)
            db.commit()
            logger.warning(
                f"[KnowledgePromoter] Enqueued item to KnowledgeReviewQueue (ID: {review_entry.id}, Priority: {priority})"
            )
            return {
                "action": "ENQUEUED_FOR_REVIEW",
                "status": "UNDER_REVIEW",
                "review_id": review_entry.id,
                "reason": reason,
                "quality_score": validation.quality_score
            }

        # Case 2: Strong Evidence Auto-Promotion
        # Check if existing dynamic knowledge item exists for this crop + stage + parameter
        existing_item = (
            db.query(DynamicKnowledgeItem)
            .filter(
                DynamicKnowledgeItem.crop.ilike(f"%{crop_name}%"),
                DynamicKnowledgeItem.parameter == claim.parameter,
                DynamicKnowledgeItem.growth_stage == stage
            )
            .first()
        )

        status = "VALIDATED" if (validation.quality_score >= 80.0 and claim.source_tier == 1) else "PROVISIONAL"

        if existing_item:
            # Increment version, append provenance, update finding without erasing past history
            existing_item.version += 1
            existing_item.finding = claim.claim_text
            existing_item.status = status
            existing_item.confidence = min(95, int(validation.quality_score))
            existing_item.last_reviewed_at = datetime.utcnow()
            existing_item.updated_at = datetime.utcnow()

            curr_prov = existing_item.source_provenance or []
            if isinstance(curr_prov, list):
                curr_prov.append(provenance_entry)
                existing_item.source_provenance = curr_prov

            db.commit()
            logger.info(
                f"[KnowledgePromoter] Updated DynamicKnowledgeItem ID {existing_item.id} to v{existing_item.version} ({status})"
            )
            return {
                "action": "AUTO_PROMOTED_UPDATE",
                "status": status,
                "knowledge_id": existing_item.id,
                "version": existing_item.version,
                "quality_score": validation.quality_score
            }
        else:
            # Create new DynamicKnowledgeItem
            new_item = DynamicKnowledgeItem(
                crop="Green Gram (Moong)",
                variety=fingerprint.variety,
                parameter=claim.parameter,
                finding=claim.claim_text,
                conditions=claim.condition_context,
                growth_stage=stage,
                soil_type=soil,
                region=fingerprint.region,
                status=status,
                confidence=min(95, int(validation.quality_score)),
                version=1,
                source_provenance=[provenance_entry],
                last_reviewed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_item)
            db.commit()
            logger.info(
                f"[KnowledgePromoter] Auto-stored new DynamicKnowledgeItem ID {new_item.id} ({status})"
            )
            return {
                "action": "AUTO_PROMOTED_NEW",
                "status": status,
                "knowledge_id": new_item.id,
                "version": 1,
                "quality_score": validation.quality_score
            }
