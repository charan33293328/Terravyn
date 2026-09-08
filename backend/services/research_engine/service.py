"""
Terravyn Research & Knowledge Acquisition Service V1
Orchestrates the entire closed-loop research lifecycle:
Situation -> Fingerprint -> Matcher -> Provider -> Extractor -> Validator -> Promoter
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.domain import (
    ResearchQuery, ResearchSource, EvidenceClaim, DynamicKnowledgeItem,
    KnowledgeReviewQueue, Farm
)
from .fingerprint import SituationFingerprint, build_fingerprint_from_inputs
from .matcher import KnowledgeMatcher, MatchResult, SufficiencyLevel
from .question import ResearchQuestionGenerator
from .provider import (
    AgriculturalResearchProvider, CuratedAgriculturalProvider, ResearchSourceDTO, SourceTier
)
from .extractor import EvidenceExtractor, ExtractedEvidenceClaim
from .validator import EvidenceValidator, ValidationResult
from .promoter import KnowledgePromoter

logger = logging.getLogger(__name__)

ENGINE_VERSION = "research-engine-v1"


class ResearchLifecycleResult:
    def __init__(
        self,
        fingerprint: SituationFingerprint,
        match_result: MatchResult,
        research_triggered: bool,
        research_query_id: Optional[int] = None,
        question: Optional[str] = None,
        sources_searched: int = 0,
        claims_extracted: int = 0,
        promoted_items: Optional[List[Dict[str, Any]]] = None,
        review_items: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        summary: str = ""
    ):
        self.fingerprint = fingerprint
        self.match_result = match_result
        self.research_triggered = research_triggered
        self.research_query_id = research_query_id
        self.question = question
        self.sources_searched = sources_searched
        self.claims_extracted = claims_extracted
        self.promoted_items = promoted_items or []
        self.review_items = review_items or []
        self.citations = citations or []
        self.summary = summary
        self.engine_version = ENGINE_VERSION


class ResearchAndKnowledgeAcquisitionService:
    def __init__(
        self,
        provider: Optional[AgriculturalResearchProvider] = None,
        matcher: Optional[KnowledgeMatcher] = None,
        question_gen: Optional[ResearchQuestionGenerator] = None,
        extractor: Optional[EvidenceExtractor] = None,
        validator: Optional[EvidenceValidator] = None,
        promoter: Optional[KnowledgePromoter] = None
    ):
        self.provider = provider or CuratedAgriculturalProvider()
        self.matcher = matcher or KnowledgeMatcher()
        self.question_gen = question_gen or ResearchQuestionGenerator()
        self.extractor = extractor or EvidenceExtractor()
        self.validator = validator or EvidenceValidator()
        self.promoter = promoter or KnowledgePromoter()

    def process_field_situation(
        self,
        db: Session,
        fingerprint: SituationFingerprint,
        farm_id: Optional[int] = None,
        force_research: bool = False
    ) -> ResearchLifecycleResult:
        """
        Executes closed-loop knowledge acquisition for a field situation.
        """
        logger.info(f"[LOG:SITUATION_RECEIVED] Crop={fingerprint.crop}, Stage={fingerprint.growth_stage}, Soil={fingerprint.soil_type}")
        fp_hash = fingerprint.compute_hash()
        logger.info(f"[LOG:FINGERPRINT_CREATED] Hash={fp_hash}")

        # 1. Match against existing static and dynamic knowledge
        logger.info("[LOG:KB_SEARCH_STARTED] Evaluating knowledge base sufficiency...")
        match_res = self.matcher.match_situation(fingerprint, db=db)

        if match_res.sufficiency == SufficiencyLevel.SUFFICIENT and not force_research:
            logger.info(f"[LOG:KB_MATCH_FOUND] Sufficient knowledge available ({match_res.similarity_score:.1f}%). Fast-path enabled.")
            return ResearchLifecycleResult(
                fingerprint=fingerprint,
                match_result=match_res,
                research_triggered=False,
                summary="Adequate validated knowledge exists in Knowledge Base. Zero research query needed."
            )

        # 2. Insufficient or partial knowledge -> Trigger Research
        logger.info(f"[LOG:KB_INSUFFICIENT] Sufficiency={match_res.sufficiency.value}, Score={match_res.similarity_score:.1f}%. Triggering Research Engine...")
        logger.info(f"[LOG:RESEARCH_STARTED] Starting research for {fingerprint.crop} in {fingerprint.growth_stage}...")

        # Check Cache / Research History
        existing_query = (
            db.query(ResearchQuery)
            .filter(
                ResearchQuery.fingerprint_hash == fp_hash,
                ResearchQuery.status == "COMPLETED"
            )
            .order_by(ResearchQuery.created_at.desc())
            .first()
        )

        if existing_query and not force_research:
            logger.info(f"[LOG:RESEARCH_CACHE_HIT] Reusing research query ID {existing_query.id} from history.")
            # Load dynamic knowledge items produced for this fingerprint
            dynamic_items = (
                db.query(DynamicKnowledgeItem)
                .filter(DynamicKnowledgeItem.crop.ilike(f"%{fingerprint.crop}%"))
                .all()
            )
            citations = []
            for item in dynamic_items:
                if item.source_provenance and isinstance(item.source_provenance, list):
                    citations.extend(item.source_provenance)

            return ResearchLifecycleResult(
                fingerprint=fingerprint,
                match_result=match_res,
                research_triggered=False,
                research_query_id=existing_query.id,
                question=existing_query.question,
                promoted_items=[{"id": i.id, "parameter": i.parameter, "finding": i.finding} for i in dynamic_items],
                citations=citations,
                summary="Reused previously acquired research from Terravyn research cache."
            )

        # 3. Generate targeted research question
        question = self.question_gen.generate_question(fingerprint)
        logger.info(f"[LOG:RESEARCH_QUESTION_GENERATED] '{question}'")

        # 4. Create ResearchQuery DB record
        db_query = ResearchQuery(
            farm_id=farm_id,
            fingerprint=fingerprint.to_canonical_dict(),
            fingerprint_hash=fp_hash,
            question=question,
            status="IN_PROGRESS",
            engine_version=ENGINE_VERSION,
            created_at=datetime.utcnow()
        )
        db.add(db_query)
        db.commit()

        promoted_records = []
        review_records = []
        all_citations = []
        sources_found_count = 0
        claims_extracted_count = 0

        try:
            # 5. Search approved agricultural sources
            sources: List[ResearchSourceDTO] = self.provider.search(question, max_results=4)
            sources_found_count = len(sources)

            if not sources:
                logger.warning(f"[LOG:RESEARCH_NO_SOURCES] No relevant sources returned for '{question}'.")
                db_query.status = "COMPLETED"
                db.commit()
                return ResearchLifecycleResult(
                    fingerprint=fingerprint,
                    match_result=match_res,
                    research_triggered=True,
                    research_query_id=db_query.id,
                    question=question,
                    summary="Research engine queried sources, but no high-quality evidence met relevance criteria."
                )

            # 6. Extract claims across all sources
            extracted_claims: List[ExtractedEvidenceClaim] = []
            source_claim_pairs: List[Any] = []

            for src in sources:
                logger.info(f"[LOG:SOURCE_FOUND] Title='{src.title}', Org='{src.organization}', Tier={src.source_tier}")
                claims = self.extractor.extract_claims(src)
                source_claim_pairs.append((src, claims))
                extracted_claims.extend(claims)
                claims_extracted_count += len(claims)

            # 7. Persist sources and claims, then validate and promote
            for src, claims in source_claim_pairs:
                db_source = ResearchSource(
                    query_id=db_query.id,
                    title=src.title,
                    organization=src.organization,
                    url=src.url,
                    source_type=src.source_type,
                    source_tier=src.source_tier,
                    publication_date=src.publication_date,
                    retrieved_at=src.retrieved_at,
                    doi=src.doi,
                    content_hash=src.content_hash
                )
                db.add(db_source)
                db.commit()

                for claim in claims:
                    logger.info(f"[LOG:EVIDENCE_EXTRACTED] Parameter='{claim.parameter}', Min={claim.value_min}, Unit={claim.unit}")
                    # Validate against peer claims
                    val_result: ValidationResult = self.validator.validate_claim(claim, fingerprint, extracted_claims)
                    logger.info(
                        f"[LOG:EVIDENCE_VALIDATED] Score={val_result.quality_score:.1f}/100, "
                        f"Valid={val_result.is_valid}, Conflict={val_result.has_conflict}"
                    )

                    db_claim = EvidenceClaim(
                        source_id=db_source.id,
                        parameter=claim.parameter,
                        claim_text=claim.claim_text,
                        value_min=claim.value_min,
                        value_max=claim.value_max,
                        unit=claim.unit,
                        condition_context=claim.condition_context,
                        growth_stage=claim.growth_stage,
                        soil_type=claim.soil_type,
                        quality_score=val_result.quality_score,
                        created_at=datetime.utcnow()
                    )
                    db.add(db_claim)
                    db.commit()

                    # Promote or Enqueue
                    promo_outcome = self.promoter.process_claim(
                        db=db,
                        claim=claim,
                        validation=val_result,
                        fingerprint=fingerprint,
                        evidence_claim_db_id=db_claim.id
                    )

                    if promo_outcome["action"].startswith("AUTO_PROMOTED"):
                        logger.info(f"[LOG:KNOWLEDGE_PROMOTED] Action={promo_outcome['action']}, Status={promo_outcome['status']}")
                        promoted_records.append(promo_outcome)
                        all_citations.append({
                            "sourceTitle": src.title,
                            "organization": src.organization,
                            "url": src.url,
                            "sourceTier": src.source_tier,
                            "qualityScore": val_result.quality_score,
                            "status": promo_outcome["status"]
                        })
                    else:
                        logger.info(f"[LOG:MANUAL_REVIEW_CREATED] Enqueued to review queue (ID: {promo_outcome.get('review_id')})")
                        review_records.append(promo_outcome)

            db_query.status = "COMPLETED"
            db.commit()

            summary = (
                f"Successfully researched {sources_found_count} trusted sources. "
                f"Extracted {claims_extracted_count} structured evidence claims. "
                f"Auto-promoted {len(promoted_records)} validated knowledge items; "
                f"{len(review_records)} items routed to agronomist review."
            )

        except Exception as e:
            logger.error(f"[LOG:RESEARCH_FAILED] Research execution encountered an error: {e}", exc_info=True)
            db_query.status = "FAILED"
            db.commit()
            summary = f"Research attempted but encountered non-fatal error: {str(e)}. Safe fallback active."

        return ResearchLifecycleResult(
            fingerprint=fingerprint,
            match_result=match_res,
            research_triggered=True,
            research_query_id=db_query.id,
            question=question,
            sources_searched=sources_found_count,
            claims_extracted=claims_extracted_count,
            promoted_items=promoted_records,
            review_items=review_records,
            citations=all_citations,
            summary=summary
        )
