"""
Agronomic Rules Repository with Scientific Traceability.
Differentiates between peer-reviewed/ICAR validated rules and preliminary/experimental thresholds.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

STATUS_VALIDATED = "VALIDATED"
STATUS_PRELIMINARY = "PRELIMINARY / EXPERIMENTAL"

@dataclass
class AgronomicRule:
    rule_id: str
    parameter: str
    threshold: Any
    unit: str
    crop: str
    growth_stage: str
    soil_type: str
    source: str
    source_url: str
    confidence: int # 0-100
    status: str # VALIDATED or PRELIMINARY / EXPERIMENTAL
    description: str

# Soil type adjustment multipliers for capacitive volumetric soil moisture thresholds
SOIL_TYPE_FACTORS = {
    "Sandy Loam": {
        "moisture_threshold_offset": 0.0, # baseline
        "field_capacity_estimate_pct": 22.0,
        "drainage_speed": "Fast",
        "waterlogging_risk": "Low",
        "description": "Drains quickly, requires timely replenishment to avoid rapid root desiccation."
    },
    "Clay Loam": {
        "moisture_threshold_offset": +5.0, # higher bound due to higher wilting point in clays
        "field_capacity_estimate_pct": 32.0,
        "drainage_speed": "Slow",
        "waterlogging_risk": "High",
        "description": "High water-holding capacity but susceptible to aeration stress & root rot if over-irrigated."
    },
    "Black Soil (Regur)": {
        "moisture_threshold_offset": +8.0, # high swelling clay content (montmorillonite)
        "field_capacity_estimate_pct": 38.0,
        "drainage_speed": "Very Slow",
        "waterlogging_risk": "Very High",
        "description": "Deep black soils retain immense water; prone to surface water stagnation."
    },
    "Red Sandy Soil": {
        "moisture_threshold_offset": -3.0,
        "field_capacity_estimate_pct": 18.0,
        "drainage_speed": "Rapid",
        "waterlogging_risk": "Very Low",
        "description": "Poor water holding capacity; requires frequent light irrigations."
    },
    "Alluvial Soil": {
        "moisture_threshold_offset": +2.0,
        "field_capacity_estimate_pct": 26.0,
        "drainage_speed": "Moderate",
        "waterlogging_risk": "Moderate",
        "description": "Balanced texture with good moisture retention and permeability."
    },
    "DEFAULT": {
        "moisture_threshold_offset": 0.0,
        "field_capacity_estimate_pct": 25.0,
        "drainage_speed": "Moderate",
        "waterlogging_risk": "Moderate",
        "description": "Standard agricultural loam baseline."
    }
}

# Master Agronomic Rule Definitions
AGRONOMIC_RULES: List[AgronomicRule] = [
    AgronomicRule(
        rule_id="RULE-GG-STAGE-MATURITY-CEASE",
        parameter="growth_stage",
        threshold="Maturity / Harvest",
        unit="stage_name",
        crop="Green Gram (Moong)",
        growth_stage="Maturity / Harvest",
        soil_type="ALL",
        source="ICAR-Indian Institute of Pulses Research (IIPR) Package of Practices",
        source_url="https://iipr.icar.gov.in",
        confidence=95,
        status=STATUS_VALIDATED,
        description="Stop all irrigation 10 to 12 days prior to harvest. Excess moisture during maturity causes pod decay, vivipary (sprouting in pod), and uneven ripening."
    ),
    AgronomicRule(
        rule_id="RULE-GG-CRITICAL-FLOWERING",
        parameter="soil_moisture",
        threshold=40.0, # Preliminary capacitive sensor reading
        unit="% volumetric",
        crop="Green Gram (Moong)",
        growth_stage="Flowering",
        soil_type="Sandy Loam",
        source="Agricultural University Pulse Water Management Guidelines",
        source_url="https://agritech.tnau.ac.in",
        confidence=75,
        status=STATUS_PRELIMINARY,
        description="Flowering is moisture-critical. Soil moisture depletion below 40% triggers rapid abscission (dropping) of flowers."
    ),
    AgronomicRule(
        rule_id="RULE-GG-CRITICAL-POD-FORMATION",
        parameter="soil_moisture",
        threshold=42.0, # Preliminary capacitive sensor reading
        unit="% volumetric",
        crop="Green Gram (Moong)",
        growth_stage="Pod Formation",
        soil_type="Sandy Loam",
        source="Agricultural University Pulse Water Management Guidelines",
        source_url="https://agritech.tnau.ac.in",
        confidence=75,
        status=STATUS_PRELIMINARY,
        description="Pod initiation & early enlargement require adequate water. Severe stress causes pod abortion and shriveled grains."
    ),
    AgronomicRule(
        rule_id="RULE-GG-VEGETATIVE-THRESHOLD",
        parameter="soil_moisture",
        threshold=30.0,
        unit="% volumetric",
        crop="Green Gram (Moong)",
        growth_stage="Vegetative",
        soil_type="Sandy Loam",
        source="Terravyn Agronomy Framework",
        source_url="https://terravyn.com/docs/agronomy",
        confidence=60,
        status=STATUS_PRELIMINARY,
        description="During vegetative growth, moderate moisture stress encourages deep tap root establishment. Irrigation triggered below 30%."
    ),
    AgronomicRule(
        rule_id="RULE-GG-RAIN-FORECAST-HOLD",
        parameter="forecast_rainfall_24h",
        threshold=5.0, # 5mm rain threshold
        unit="mm",
        crop="Green Gram (Moong)",
        growth_stage="ALL",
        soil_type="ALL",
        source="ICAR Agromet Advisory Service Best Practices",
        source_url="https://imdagrimet.gov.in",
        confidence=90,
        status=STATUS_VALIDATED,
        description="When 5 mm or more rain is forecast in the next 24 hours with >= 50% probability, suspend irrigation to prevent waterlogging and conserve water."
    ),
    AgronomicRule(
        rule_id="RULE-GG-IRRIGATION-COOLDOWN",
        parameter="hours_since_last_irrigation",
        threshold=2.0, # 2 hours minimum cooldown
        unit="hours",
        crop="Green Gram (Moong)",
        growth_stage="ALL",
        soil_type="ALL",
        source="Precision Irrigation Automation Standards",
        source_url="https://terravyn.com/docs/hysteresis",
        confidence=85,
        status=STATUS_VALIDATED,
        description="Enforce a minimum 2-hour soaking and redistribution interval after an irrigation event before re-evaluating moisture."
    ),
    AgronomicRule(
        rule_id="RULE-GG-HIGH-ET0-ATMOSPHERIC-DEMAND",
        parameter="et0",
        threshold=5.5,
        unit="mm/day",
        crop="Green Gram (Moong)",
        growth_stage="ALL",
        soil_type="ALL",
        source="FAO Irrigation and Drainage Paper No. 56 (Penman-Monteith)",
        source_url="https://www.fao.org/land-water/databases-and-software/cropwat",
        confidence=90,
        status=STATUS_VALIDATED,
        description="Atmospheric evaporative demand >= 5.5 mm/day accelerates soil moisture depletion and transpiration stress."
    )
]

def get_soil_factor(soil_type: Optional[str]) -> Dict[str, Any]:
    if not soil_type:
        return SOIL_TYPE_FACTORS["DEFAULT"]
    
    clean_type = soil_type.strip()
    for key, val in SOIL_TYPE_FACTORS.items():
        if key.lower() in clean_type.lower() or clean_type.lower() in key.lower():
            return val
            
    return SOIL_TYPE_FACTORS["DEFAULT"]
