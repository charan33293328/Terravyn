"""
Terravyn Research & Knowledge Acquisition API Routes
Endpoints for executing research queries, viewing research history,
inspecting dynamic knowledge, and managing the agronomist review queue.
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from models.domain import (
    User, Farm, ResearchQuery, ResearchSource, EvidenceClaim,
    DynamicKnowledgeItem, KnowledgeReviewQueue
)
from schemas.domain import (
    ResearchQueryCreate, ResearchQueryResponse, DynamicKnowledgeResponse,
    KnowledgeReviewItemResponse, ResolveReviewRequest
)
from auth.security import get_current_active_user
from services.research_engine import (
    ResearchAndKnowledgeAcquisitionService, build_fingerprint_from_inputs,
    SituationFingerprint
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Research & Knowledge Acquisition"])
research_service = ResearchAndKnowledgeAcquisitionService()


@router.post("/research/query", response_model=ResearchQueryResponse)
def trigger_research_query(
    payload: ResearchQueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Trigger research and knowledge acquisition for a specific farm field or situation.
    """
    farm = None
    if payload.farm_id:
        farm = db.query(Farm).filter(Farm.id == payload.farm_id).first()

    crop = farm.crop_type if farm and farm.crop_type else (payload.crop or "Green Gram (Moong)")
    variety = farm.crop_variety if farm else None
    stage = farm.growth_stage_override if (farm and farm.growth_stage_override) else (payload.growth_stage or "Flowering")
    soil = farm.soil_type if farm and farm.soil_type else (payload.soil_type or "Sandy Loam")

    fingerprint = build_fingerprint_from_inputs(
        crop_name=crop,
        variety=variety,
        growth_stage=stage,
        soil_type=soil,
        soil_moisture_pct=payload.soil_moisture_pct or 20.0,
        temperature_c=payload.temperature_c or 34.0,
        humidity_pct=50.0,
        forecast_rain_mm=payload.forecast_rain_mm or 0.0,
        rain_probability_pct=20,
        et0_mm=5.2,
        recent_rain=False,
        recent_irrigation=False
    )

    result = research_service.process_field_situation(
        db=db,
        fingerprint=fingerprint,
        farm_id=payload.farm_id,
        force_research=payload.force_research
    )

    query_id = result.research_query_id
    if not query_id:
        # Retrieve existing query by hash
        q_record = (
            db.query(ResearchQuery)
            .filter(ResearchQuery.fingerprint_hash == fingerprint.compute_hash())
            .order_by(desc(ResearchQuery.created_at))
            .first()
        )
        if q_record:
            return q_record
        raise HTTPException(status_code=404, detail="No research record created or found.")

    query_record = db.query(ResearchQuery).filter(ResearchQuery.id == query_id).first()
    if not query_record:
        raise HTTPException(status_code=404, detail="Research query not found.")
    return query_record


@router.get("/research/history", response_model=List[ResearchQueryResponse])
def get_research_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve historical agricultural research queries and results.
    """
    queries = (
        db.query(ResearchQuery)
        .order_by(desc(ResearchQuery.created_at))
        .limit(limit)
        .all()
    )
    return queries


@router.get("/research/{query_id}", response_model=ResearchQueryResponse)
def get_research_query_details(
    query_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed breakdown of a research query including all retrieved sources and claims.
    """
    query_record = db.query(ResearchQuery).filter(ResearchQuery.id == query_id).first()
    if not query_record:
        raise HTTPException(status_code=404, detail="Research query not found")
    return query_record


@router.get("/knowledge/dynamic", response_model=List[DynamicKnowledgeResponse])
def get_dynamic_knowledge_items(
    crop: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Query dynamically acquired agricultural knowledge items.
    """
    q = db.query(DynamicKnowledgeItem)
    if crop:
        q = q.filter(DynamicKnowledgeItem.crop.ilike(f"%{crop}%"))
    if status:
        q = q.filter(DynamicKnowledgeItem.status == status)
    
    return q.order_by(desc(DynamicKnowledgeItem.updated_at)).limit(limit).all()


@router.get("/knowledge/review-queue", response_model=List[KnowledgeReviewItemResponse])
def get_review_queue(
    status: str = Query("PENDING"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List items in the agronomist review queue (weak or contradictory evidence).
    """
    items = (
        db.query(KnowledgeReviewQueue)
        .filter(KnowledgeReviewQueue.status == status)
        .order_by(desc(KnowledgeReviewQueue.created_at))
        .all()
    )
    return items


@router.post("/knowledge/review/{review_id}/resolve")
def resolve_review_queue_item(
    review_id: int,
    payload: ResolveReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Approve or reject an item in the knowledge review queue.
    """
    review_item = db.query(KnowledgeReviewQueue).filter(KnowledgeReviewQueue.id == review_id).first()
    if not review_item:
        raise HTTPException(status_code=404, detail="Review queue item not found")

    review_item.status = payload.action.upper()
    review_item.resolved_at = datetime.utcnow()
    review_item.resolved_by = current_user.id

    # If approved and backed by an evidence claim, promote into DynamicKnowledgeItem
    if payload.action.upper() == "APPROVE" and review_item.evidence_claim_id:
        claim = db.query(EvidenceClaim).filter(EvidenceClaim.id == review_item.evidence_claim_id).first()
        if claim:
            new_item = DynamicKnowledgeItem(
                crop="Green Gram (Moong)",
                parameter=claim.parameter,
                finding=payload.override_finding or claim.claim_text,
                growth_stage=claim.growth_stage,
                soil_type=claim.soil_type,
                status="VALIDATED",
                confidence=85,
                version=1,
                source_provenance=[{
                    "sourceId": claim.source_id,
                    "approvedByUserId": current_user.id,
                    "notes": payload.notes or "Manually approved by agronomist"
                }],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_item)
            review_item.knowledge_item_id = new_item.id

    db.commit()
    return {
        "message": f"Review item {review_id} resolved with action {payload.action}",
        "review_id": review_id,
        "status": review_item.status
    }
