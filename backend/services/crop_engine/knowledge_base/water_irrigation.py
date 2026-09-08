"""
Green Gram (Vigna radiata) Water & Irrigation Agronomic Knowledge.
Authoritative source grounding: ICAR-IIPR, FAO-56, FAO-33, CRIDA.
Includes explicit experimental tags for capacitive soil moisture sensor thresholds.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class IrrigationRuleModel(BaseModel):
    rule_id: str
    parameter: str
    crop: str = "Green Gram (Moong)"
    growth_stage: str
    soil_type: str
    condition: str
    action_recommendation: str
    scientific_rationale: str
    source: SourceReference
    status: KnowledgeStatus
    confidence: ConfidenceLevel
    is_experimental: bool = False
    calibration_required: bool = False

WATER_REQUIREMENTS_KNOWLEDGE: Dict[str, Any] = {
    "total_seasonal_water_need_mm": {
        "min_mm": 250.0,
        "optimum_mm": 300.0,
        "max_mm": 380.0,
        "explanation": "Total seasonal crop evapotranspiration (ETc) varies with summer evaporative demand (higher) vs kharif (lower).",
        "source": get_source("FAO-56-CROPWAT"),
        "status": KnowledgeStatus.VALIDATED
    },
    "critical_stages_hierarchy": [
        {
            "rank": 1,
            "stage": "Flowering",
            "das_window": (30, 40),
            "sensitivity": "CRITICAL",
            "yield_penalty_if_stressed_pct": (30, 45),
            "mechanism": "Water deficit triggers leaf ethylene synthesis, flower petal senescence, and premature flower abscission (shedding).",
            "source": get_source("ICAR-IIPR-2018")
        },
        {
            "rank": 2,
            "stage": "Pod Formation / Pod Enlargement",
            "das_window": (40, 50),
            "sensitivity": "CRITICAL",
            "yield_penalty_if_stressed_pct": (25, 35),
            "mechanism": "Drought stress induces pod abortion, reduces ovule fertilization, and results in shriveled, unfilled grains.",
            "source": get_source("ICAR-IIPR-2018")
        },
        {
            "rank": 3,
            "stage": "Vegetative / Branching",
            "das_window": (15, 28),
            "sensitivity": "MODERATE",
            "yield_penalty_if_stressed_pct": (10, 15),
            "mechanism": "Mild stress promotes deeper tap root exploration; severe stress reduces branching and bearing nodes.",
            "source": get_source("TNAU-AGRITECH-PULSES")
        },
        {
            "rank": 4,
            "stage": "Maturity / Harvest",
            "das_window": (55, 65),
            "sensitivity": "DETRIMENTAL",
            "yield_penalty_if_irrigated_pct": (20, 50),
            "mechanism": "Late irrigation or rainfall causes secondary vegetative flush, uneven maturity, pod rot, and viviparous sprouting in pod.",
            "source": get_source("ICAR-IIPR-2018")
        }
    ],
    "waterlogging_vulnerability": {
        "tolerance_rating": "EXTREMELY SENSITIVE",
        "hypoxia_threshold_hours": 24, # 24-48 hours of standing water causes irreversible root damage
        "yield_loss_stagnation_24h_pct": (25, 40),
        "yield_loss_stagnation_48h_pct": (50, 75),
        "pathology": "Root oxygen starvation halts ATP production, stops nodule nitrogenase activity, and initiates Rhizoctonia/Macrophomina root rot.",
        "management": "Ensure continuous surface drainage furrows every 2-4 meters. In heavy soils, Broad Bed Furrow (BBF) or ridge sowing is strongly advised.",
        "source": get_source("CRIDA-CONTINGENCY-2019"),
        "status": KnowledgeStatus.VALIDATED
    }
}

# Master Irrigation Knowledge Rules (Scientific Validated + Sensor Experimental)
MASTER_IRRIGATION_RULES: List[IrrigationRuleModel] = [
    IrrigationRuleModel(
        rule_id="RULE-IRR-MATURITY-CEASE-01",
        parameter="growth_stage",
        growth_stage="Maturity / Harvest",
        soil_type="ALL",
        condition="Crop age >= 55 DAS or pods transitioning to black/brown",
        action_recommendation="STRICTLY WITHHOLD ALL IRRIGATION.",
        scientific_rationale="Cessation of irrigation 10-12 days before harvest allows uniform drying of pods and prevents vivipary / seed sprouting (ICAR-IIPR Package of Practices).",
        source=get_source("ICAR-IIPR-2018"),
        status=KnowledgeStatus.VALIDATED,
        confidence=ConfidenceLevel.HIGH,
        is_experimental=False,
        calibration_required=False
    ),
    IrrigationRuleModel(
        rule_id="RULE-IRR-RAIN-FORECAST-02",
        parameter="forecast_rainfall_24h",
        growth_stage="ALL",
        soil_type="ALL",
        condition=">= 5.0 mm forecast rainfall in next 24 hours with >= 50% probability",
        action_recommendation="SUSPEND IRRIGATION; re-evaluate 6 hours post-weather event.",
        scientific_rationale="Applying irrigation prior to rain risks root-zone water stagnation and waste of water/power (Agromet Advisory Standards).",
        source=get_source("CRIDA-CONTINGENCY-2019"),
        status=KnowledgeStatus.VALIDATED,
        confidence=ConfidenceLevel.HIGH,
        is_experimental=False,
        calibration_required=False
    ),
    IrrigationRuleModel(
        rule_id="RULE-IRR-COOLDOWN-SOAK-03",
        parameter="hours_since_last_irrigation",
        growth_stage="ALL",
        soil_type="ALL",
        condition="< 2.0 hours since last irrigation event",
        action_recommendation="WAIT; allow redistribution and percolation through the root zone.",
        scientific_rationale="Infiltration and hydraulic equilibrium require at least 2 hours in agricultural loams before sensor values reflect stabilized soil moisture.",
        source=get_source("TERRAVYN-EXPERIMENTAL"),
        status=KnowledgeStatus.VALIDATED,
        confidence=ConfidenceLevel.HIGH,
        is_experimental=False,
        calibration_required=False
    ),
    IrrigationRuleModel(
        rule_id="RULE-IRR-HIGH-ET0-VPD-04",
        parameter="et0",
        growth_stage="Flowering / Pod Formation",
        soil_type="ALL",
        condition="ET0 >= 5.5 mm/day during reproductive phase",
        action_recommendation="MONITOR SOIL CLOSELY; transpirational draw is elevated.",
        scientific_rationale="Peak reproductive evaporative demand accelerates root-zone moisture exhaustion, warranting earlier replenishment (FAO-56 Penman-Monteith).",
        source=get_source("FAO-56-CROPWAT"),
        status=KnowledgeStatus.VALIDATED,
        confidence=ConfidenceLevel.HIGH,
        is_experimental=False,
        calibration_required=False
    ),
    # Experimental Sensor-Derived Calibration Rules (Hardware in-situ thresholds)
    IrrigationRuleModel(
        rule_id="RULE-EXP-SENSOR-FLOWERING-05",
        parameter="capacitive_soil_moisture",
        growth_stage="Flowering",
        soil_type="Sandy Loam",
        condition="Volumetric capacitive sensor < 40.0% (Experimental Terravyn threshold)",
        action_recommendation="IRRIGATE (Advisory recommendation; 25-30 mm light application).",
        scientific_rationale="Capacitive probe indicates soil water tension approaching allowable depletion during moisture-critical flowering stage.",
        source=get_source("TERRAVYN-EXPERIMENTAL"),
        status=KnowledgeStatus.EXPERIMENTAL,
        confidence=ConfidenceLevel.MEDIUM,
        is_experimental=True,
        calibration_required=True
    ),
    IrrigationRuleModel(
        rule_id="RULE-EXP-SENSOR-POD-FORMATION-06",
        parameter="capacitive_soil_moisture",
        growth_stage="Pod Formation",
        soil_type="Sandy Loam",
        condition="Volumetric capacitive sensor < 42.0% (Experimental Terravyn threshold)",
        action_recommendation="IRRIGATE (Advisory recommendation; avoid standing water).",
        scientific_rationale="Pod initiation demands moisture to support rapid ovule enlargement without pod shedding.",
        source=get_source("TERRAVYN-EXPERIMENTAL"),
        status=KnowledgeStatus.EXPERIMENTAL,
        confidence=ConfidenceLevel.MEDIUM,
        is_experimental=True,
        calibration_required=True
    ),
    IrrigationRuleModel(
        rule_id="RULE-EXP-SENSOR-VEGETATIVE-07",
        parameter="capacitive_soil_moisture",
        growth_stage="Vegetative",
        soil_type="Sandy Loam",
        condition="Volumetric capacitive sensor < 30.0% (Experimental Terravyn threshold)",
        action_recommendation="IRRIGATE (Light irrigation to replenish root zone).",
        scientific_rationale="Vegetative phase tolerates mild moisture stress, promoting root elongation down into subsoil.",
        source=get_source("TERRAVYN-EXPERIMENTAL"),
        status=KnowledgeStatus.EXPERIMENTAL,
        confidence=ConfidenceLevel.MEDIUM,
        is_experimental=True,
        calibration_required=True
    )
]

def get_irrigation_rules_for_stage(growth_stage: str) -> List[IrrigationRuleModel]:
    return [
        r for r in MASTER_IRRIGATION_RULES
        if r.growth_stage == "ALL" or growth_stage.lower() in r.growth_stage.lower()
    ]
