"""
Terravyn Learning Engine: API Routes
Provides endpoints for learning summary, timeline, candidate review, outcome inspection,
and background cycle triggering.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from models.domain import (
    Farm,
    DecisionOutcomeAnalysis,
    LearningCandidate,
    LearningEvidence,
    LearningRun,
    PerformanceMetric,
    ForecastEvaluation,
    User,
)
from schemas.domain import (
    DecisionOutcomeAnalysisResponse,
    ForecastEvaluationResponse,
    LearningCandidateResponse,
    LearningRunResponse,
    PerformanceMetricResponse,
    LearningSummaryResponse,
)
from services.learning_engine.engine import ClosedLoopLearningEngine
from services.learning_engine.report_generator import LearningReportGenerator
from auth.security import get_current_active_user

router = APIRouter(prefix="/api/learning", tags=["Continuous Learning Engine"])
outcomes_router = APIRouter(prefix="/api/outcomes", tags=["Decision Outcomes"])
perf_router = APIRouter(prefix="/api/performance", tags=["Performance Tracking"])

learning_engine = ClosedLoopLearningEngine()


# =============================================================================
# LEARNING DASHBOARD & SUMMARY
# =============================================================================

@router.get("/summary/{farm_id}", response_model=LearningSummaryResponse)
def get_learning_summary(
    farm_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns comprehensive learning summary for the farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    report = LearningReportGenerator.generate_learning_report(db=db, farm_id=farm_id, lookback_days=days)
    return report


@router.get("/timeline/{farm_id}")
def get_learning_timeline(
    farm_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Returns structured timeline entries for the farm."""
    farm = db.query(Farm).filter(Farm.id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    return LearningReportGenerator.generate_timeline(db=db, farm_id=farm_id, limit=limit)


# =============================================================================
# LEARNING CANDIDATES
# =============================================================================

@router.get("/candidates", response_model=List[LearningCandidateResponse])
def list_learning_candidates(
    farm_id: Optional[int] = None,
    candidate_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all learning candidates with optional filtering."""
    query = db.query(LearningCandidate)
    if farm_id:
        query = query.filter((LearningCandidate.farm_id == farm_id) | (LearningCandidate.farm_id.is_(None)))
    if candidate_type:
        query = query.filter(LearningCandidate.candidate_type == candidate_type)
    if status:
        query = query.filter(LearningCandidate.status == status)

    return query.order_by(desc(LearningCandidate.updated_at)).all()


@router.get("/candidates/{candidate_id}", response_model=LearningCandidateResponse)
def get_candidate_details(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieve full details of a learning candidate including evidence."""
    candidate = db.query(LearningCandidate).filter(LearningCandidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Learning candidate not found")
    return candidate


@router.post("/candidates/{candidate_id}/validate")
def submit_candidate_for_validation(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit a learning candidate to the Knowledge Validation Engine."""
    res = learning_engine.submit_to_validation(db=db, candidate_id=candidate_id)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res


@router.post("/candidates/{candidate_id}/research")
def submit_candidate_for_research(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Submit a knowledge conflict candidate to the Research Engine."""
    res = learning_engine.submit_to_research(db=db, candidate_id=candidate_id)
    if not res or not res.get("research_triggered"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to trigger research"))
    return res


# =============================================================================
# LEARNING ENGINE TRIGGERS
# =============================================================================

@router.post("/evaluate/{farm_id}")
def trigger_outcome_evaluation(
    farm_id: int,
    window: str = Query("SHORT_TERM", pattern="^(IMMEDIATE|SHORT_TERM|LONG_TERM)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Triggers outcome evaluation for unevaluated decisions on a farm."""
    return learning_engine.run_outcome_evaluation(db=db, farm_id=farm_id, window=window)


@router.post("/run/{farm_id}")
def trigger_full_learning_cycle(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Triggers complete closed-loop learning cycle across all modules."""
    return learning_engine.run_full_learning_cycle(db=db, farm_id=farm_id)


# =============================================================================
# DECISION OUTCOMES ROUTER (/api/outcomes)
# =============================================================================

@outcomes_router.get("/{farm_id}", response_model=List[DecisionOutcomeAnalysisResponse])
def list_farm_outcomes(
    farm_id: int,
    limit: int = Query(50, ge=1, le=200),
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lists analyzed decision outcomes for a specific farm."""
    query = db.query(DecisionOutcomeAnalysis).filter(DecisionOutcomeAnalysis.farm_id == farm_id)
    if classification:
        query = query.filter(DecisionOutcomeAnalysis.classification == classification)
    return query.order_by(desc(DecisionOutcomeAnalysis.created_at)).limit(limit).all()


@outcomes_router.get("/detail/{outcome_id}", response_model=DecisionOutcomeAnalysisResponse)
def get_outcome_detail(
    outcome_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieves deep analysis record for a specific decision outcome."""
    outcome = db.query(DecisionOutcomeAnalysis).filter(DecisionOutcomeAnalysis.id == outcome_id).first()
    if not outcome:
        raise HTTPException(status_code=404, detail="Decision outcome analysis not found")
    return outcome


# =============================================================================
# PERFORMANCE TRACKING ROUTER (/api/performance)
# =============================================================================

@perf_router.get("/{farm_id}", response_model=List[PerformanceMetricResponse])
def get_performance_metrics(
    farm_id: int,
    metric_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieves computed performance metrics."""
    query = db.query(PerformanceMetric).filter(PerformanceMetric.farm_id == farm_id)
    if metric_type:
        query = query.filter(PerformanceMetric.metric_type == metric_type)
    return query.order_by(desc(PerformanceMetric.created_at)).limit(20).all()
