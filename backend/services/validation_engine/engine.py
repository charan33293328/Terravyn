"""
Terravyn Knowledge Validation & Calibration Engine V1
Main orchestration service. Coordinates Scientific Validation, Experimental Validation,
Calibration Lifecycle, Shadow Mode Execution, and Research Engine Feedback.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from models.domain import (
    DynamicKnowledgeItem,
    FieldCalibrationRecord,
    KnowledgeValidationRecord,
    CropDecisionLog,
)
from services.validation_engine.confidence_scorer import ValidationConfidenceScorer
from services.validation_engine.scientific_validator import ScientificKnowledgeValidator
from services.validation_engine.experimental_validator import ExperimentalDataValidator
from services.validation_engine.calibration_manager import FieldCalibrationManager
from services.validation_engine.outcome_evaluator import DecisionOutcomeEvaluator


class KnowledgeValidationAndCalibrationEngine:
    """Unified facade for the Knowledge Validation & Calibration Engine V1."""

    @classmethod
    def validate_scientific_item(
        cls,
        db: Session,
        knowledge_item_id: int,
        target_field_context: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeValidationRecord:
        """Validates external scientific literature claims."""
        return ScientificKnowledgeValidator.validate_knowledge_item(
            db=db,
            knowledge_item_id=knowledge_item_id,
            target_field_context=target_field_context,
        )

    @classmethod
    def validate_experimental_trial(
        cls,
        db: Session,
        experiment_id: int,
        candidate_item: Optional[DynamicKnowledgeItem] = None,
    ) -> KnowledgeValidationRecord:
        """Validates trial replication, sensor calibration, and data completeness."""
        return ExperimentalDataValidator.validate_trial_candidate(
            db=db,
            experiment_id=experiment_id,
            candidate_item=candidate_item,
        )

    @classmethod
    def generate_candidate_calibration(
        cls,
        db: Session,
        experiment_id: int,
        field_id: Optional[int] = None,
        parameter: str = "capacitive_soil_moisture_threshold",
        growth_stage: str = "Flowering",
        soil_type: str = "sandy_loam",
        suggested_value: Optional[float] = None,
        hysteresis_delta: float = 10.0,
    ) -> FieldCalibrationRecord:
        """
        Creates a scoped candidate calibration from trial evidence.
        Status is EXPERIMENTAL initially until validated or placed in SHADOW mode.
        """
        # First validate the trial to assess sample size and data quality
        val_rec = ExperimentalDataValidator.validate_trial_candidate(db=db, experiment_id=experiment_id)

        cal = FieldCalibrationManager.create_calibration(
            db=db,
            parameter=parameter,
            field_id=field_id,
            crop="Green Gram (Moong)",
            soil_type=soil_type,
            growth_stage=growth_stage,
            value=suggested_value or 34.0,
            value_range={
                "min": (suggested_value - 3.0) if suggested_value else 31.0,
                "max": (suggested_value + 3.0) if suggested_value else 37.0,
                "stop_threshold": (suggested_value + hysteresis_delta) if suggested_value else 44.0,
            },
            hysteresis_delta=hysteresis_delta,
            scope="FIELD" if field_id else "SOIL_TYPE",
            status="EXPERIMENTAL" if val_rec.status == "EXPERIMENTAL" else "SHADOW",
            confidence=val_rec.confidence,
            sample_count=val_rec.evidence_count,
            experiment_ids=[experiment_id],
            rationale=(
                f"Generated from Experiment #{experiment_id}. Validation score: {val_rec.confidence}/100 "
                f"({val_rec.confidence_level}). Replicate evidence: {val_rec.evidence_count} observations."
            ),
        )
        return cal

    @classmethod
    def trigger_research_on_conflict(
        cls,
        db: Session,
        field_id: int,
        conflicting_parameter: str,
        observed_value: float,
        established_threshold: float,
        growth_stage: str,
        soil_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Integrates with Prompt 5: When an experimental result conflicts with established scientific thresholds,
        triggers an autonomous research query to investigate rather than blindly overriding or ignoring.
        """
        try:
            from services.research_engine import ResearchAndKnowledgeAcquisitionService, SituationFingerprint

            research_svc = ResearchAndKnowledgeAcquisitionService()
            question = (
                f"Investigation: Why does Green Gram (Moong) in {soil_type} during {growth_stage} stage "
                f"exhibit empirical moisture threshold of {observed_value}% while literature establishes {established_threshold}%?"
            )
            fingerprint = SituationFingerprint(
                crop="Green Gram (Moong)",
                growth_stage=growth_stage,
                soil_type=soil_type,
                soil_moisture_pct=observed_value,
                problem_type=f"conflict_{conflicting_parameter}",
            )
            result = research_svc.process_field_situation(
                db=db,
                farm_id=field_id,
                fingerprint=fingerprint,
                question=question,
                force_research=True,
            )
            return {
                "research_triggered": True,
                "query_id": result.query_id,
                "sources_found": len(result.sources),
                "summary": result.summary,
            }
        except Exception as e:
            return {"research_triggered": False, "error": str(e)}
