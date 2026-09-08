"""
Terravyn Green Gram Knowledge Base V1 Package.
Scientifically grounded, machine-readable agricultural knowledge base.
"""

from .provenance import (
    SOURCES, SourceReference, ConfidenceLevel, KnowledgeStatus, get_source
)
from .fundamentals import CROP_FUNDAMENTALS
from .varieties import (
    VARIETIES, VarietyModel, get_variety, list_all_varieties
)
from .growth_stages import (
    GROWTH_STAGES, GrowthStageDefinition, get_stage_by_name, list_all_stages
)
from .climate import (
    CLIMATE_KNOWLEDGE, evaluate_climate_risk
)
from .soil import (
    SOIL_PROFILES, SoilTypeProfile, get_soil_profile, evaluate_soil_chemical_status
)
from .water_irrigation import (
    WATER_REQUIREMENTS_KNOWLEDGE, MASTER_IRRIGATION_RULES,
    IrrigationRuleModel, get_irrigation_rules_for_stage
)
from .nutrients import (
    NUTRIENT_GUIDELINES, FOLIAR_NUTRITION_TECHNOLOGY, diagnose_chlorosis
)
from .diseases import (
    DISEASES, DiseaseModel, evaluate_disease_risk
)
from .pests import (
    PESTS, PestModel, evaluate_pest_risk
)
from .extreme_conditions import (
    EXTREME_PROTOCOLS, evaluate_extreme_conditions
)
from .regional import (
    REGIONAL_PROFILES, RegionalProfile, get_regional_profile
)
from .manager import (
    GreenGramKnowledgeBase, knowledge_base
)

__all__ = [
    "SOURCES",
    "SourceReference",
    "ConfidenceLevel",
    "KnowledgeStatus",
    "get_source",
    "CROP_FUNDAMENTALS",
    "VARIETIES",
    "VarietyModel",
    "get_variety",
    "list_all_varieties",
    "GROWTH_STAGES",
    "GrowthStageDefinition",
    "get_stage_by_name",
    "list_all_stages",
    "CLIMATE_KNOWLEDGE",
    "evaluate_climate_risk",
    "SOIL_PROFILES",
    "SoilTypeProfile",
    "get_soil_profile",
    "evaluate_soil_chemical_status",
    "WATER_REQUIREMENTS_KNOWLEDGE",
    "MASTER_IRRIGATION_RULES",
    "IrrigationRuleModel",
    "get_irrigation_rules_for_stage",
    "NUTRIENT_GUIDELINES",
    "FOLIAR_NUTRITION_TECHNOLOGY",
    "diagnose_chlorosis",
    "DISEASES",
    "DiseaseModel",
    "evaluate_disease_risk",
    "PESTS",
    "PestModel",
    "evaluate_pest_risk",
    "EXTREME_PROTOCOLS",
    "evaluate_extreme_conditions",
    "REGIONAL_PROFILES",
    "RegionalProfile",
    "get_regional_profile",
    "GreenGramKnowledgeBase",
    "knowledge_base"
]
