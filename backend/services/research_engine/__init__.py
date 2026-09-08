"""
Terravyn Research & Knowledge Acquisition Engine V1
"""
from .fingerprint import (
    SituationFingerprint, build_fingerprint_from_inputs,
    normalize_moisture_state, normalize_temperature_state,
    normalize_rain_state, normalize_eto_state
)
from .matcher import KnowledgeMatcher, MatchResult, SufficiencyLevel, MatchedFactor
from .question import ResearchQuestionGenerator
from .provider import (
    AgriculturalResearchProvider, CuratedAgriculturalProvider,
    ResearchSourceDTO, SourceTier
)
from .extractor import EvidenceExtractor, ExtractedEvidenceClaim
from .validator import EvidenceValidator, ValidationResult
from .promoter import KnowledgePromoter
from .service import (
    ResearchAndKnowledgeAcquisitionService, ResearchLifecycleResult,
    ENGINE_VERSION as RESEARCH_ENGINE_VERSION
)

__all__ = [
    "SituationFingerprint",
    "build_fingerprint_from_inputs",
    "normalize_moisture_state",
    "normalize_temperature_state",
    "normalize_rain_state",
    "normalize_eto_state",
    "KnowledgeMatcher",
    "MatchResult",
    "SufficiencyLevel",
    "MatchedFactor",
    "ResearchQuestionGenerator",
    "AgriculturalResearchProvider",
    "CuratedAgriculturalProvider",
    "ResearchSourceDTO",
    "SourceTier",
    "EvidenceExtractor",
    "ExtractedEvidenceClaim",
    "EvidenceValidator",
    "ValidationResult",
    "KnowledgePromoter",
    "ResearchAndKnowledgeAcquisitionService",
    "ResearchLifecycleResult",
    "RESEARCH_ENGINE_VERSION"
]
