"""
Green Gram (Vigna radiata) Soil Requirements & Physical/Chemical Parameters.
Authoritative source grounding: ICAR-IIPR, TNAU Agritech Portal, ANGRAU Vyavasaya Panchangam.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class SoilTypeProfile(BaseModel):
    soil_type: str
    drainage_character: str
    water_holding_capacity: str
    field_capacity_estimate_pct: float
    wilting_point_estimate_pct: float
    aeration_porosity: str
    waterlogging_risk: str # "Very Low", "Low", "Moderate", "High", "Very High"
    suitability_rating: str # "Highly Suitable", "Suitable", "Marginal", "Unsuitable"
    capacitive_moisture_offset: float # Offset applied to base volumetric sensor thresholds
    irrigation_guideline: str
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED

SOIL_PROFILES: Dict[str, SoilTypeProfile] = {
    "Sandy Loam": SoilTypeProfile(
        soil_type="Sandy Loam",
        drainage_character="Well-drained to rapid internal drainage",
        water_holding_capacity="Moderate (100-140 mm/m)",
        field_capacity_estimate_pct=22.0,
        wilting_point_estimate_pct=10.0,
        aeration_porosity="High (excellent oxygen diffusion to roots and rhizobial nodules)",
        waterlogging_risk="Low",
        suitability_rating="Highly Suitable",
        capacitive_moisture_offset=0.0, # Baseline
        irrigation_guideline="Requires timely, frequent, light irrigations (25-30 mm depth) to prevent rapid root zone drying.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Loam": SoilTypeProfile(
        soil_type="Loam",
        drainage_character="Well-drained with optimal permeability",
        water_holding_capacity="High (140-180 mm/m)",
        field_capacity_estimate_pct=25.0,
        wilting_point_estimate_pct=12.0,
        aeration_porosity="Optimal for pulse tap root development and nodulation",
        waterlogging_risk="Low",
        suitability_rating="Highly Suitable",
        capacitive_moisture_offset=+1.0,
        irrigation_guideline="Standard irrigation scheduling; excellent balance between aeration and moisture retention.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Alluvial Soil": SoilTypeProfile(
        soil_type="Alluvial Soil",
        drainage_character="Moderate internal drainage; high natural fertility",
        water_holding_capacity="High (150-190 mm/m)",
        field_capacity_estimate_pct=26.0,
        wilting_point_estimate_pct=12.5,
        aeration_porosity="Good",
        waterlogging_risk="Moderate",
        suitability_rating="Highly Suitable",
        capacitive_moisture_offset=+2.0,
        irrigation_guideline="Apply moderate irrigation volumes; ensure surface furrows allow drainage of post-irrigation excess.",
        source=get_source("IARI-PUSA-2019")
    ),
    "Clay Loam": SoilTypeProfile(
        soil_type="Clay Loam",
        drainage_character="Moderately slow drainage; higher clay fraction (28-40%)",
        water_holding_capacity="Very High (180-220 mm/m)",
        field_capacity_estimate_pct=32.0,
        wilting_point_estimate_pct=18.0,
        aeration_porosity="Moderate to low during prolonged saturation",
        waterlogging_risk="High",
        suitability_rating="Suitable with Good Drainage",
        capacitive_moisture_offset=+5.0,
        irrigation_guideline="Wider irrigation intervals. NEVER over-irrigate. Maintain raised beds or surface drainage furrows to avert root rot.",
        source=get_source("TNAU-AGRITECH-PULSES")
    ),
    "Black Soil (Regur)": SoilTypeProfile(
        soil_type="Black Soil (Regur)",
        drainage_character="Slow to very slow internal drainage; high swelling montmorillonite clay",
        water_holding_capacity="Extremely High (>220 mm/m)",
        field_capacity_estimate_pct=38.0,
        wilting_point_estimate_pct=22.0,
        aeration_porosity="Restricted when wet; deep cracks when dry",
        waterlogging_risk="Very High",
        suitability_rating="Marginal (requires ridge-and-furrow / broad-bed-furrow system)",
        capacitive_moisture_offset=+8.0,
        irrigation_guideline="Extremely cautious irrigation. Standing water > 24 hours induces severe rhizobial hypoxia and collar rot. Broad Bed Furrow (BBF) mandatory.",
        source=get_source("CRIDA-CONTINGENCY-2019")
    ),
    "Red Sandy Soil": SoilTypeProfile(
        soil_type="Red Sandy Soil",
        drainage_character="Excessive drainage; rapid percolation",
        water_holding_capacity="Low (80-110 mm/m)",
        field_capacity_estimate_pct=18.0,
        wilting_point_estimate_pct=7.0,
        aeration_porosity="Very High",
        waterlogging_risk="Very Low",
        suitability_rating="Suitable with Frequent Light Irrigation",
        capacitive_moisture_offset=-3.0,
        irrigation_guideline="Low moisture retention capacity; needs frequent light water applications. Prone to midday stress in summer.",
        source=get_source("ANGRAU-PULSES-2021")
    )
}

SOIL_CHEMICAL_THRESHOLDS: Dict[str, Any] = {
    "ph": {
        "critical_min": 5.5, # Below 5.5, Rhizobium nodulation drops by >70% due to Al/Mn toxicity
        "optimum_min": 6.5,
        "optimum_max": 7.5,
        "critical_max": 8.5, # Above 8.2-8.5, micronutrient lockup (Fe, Zn, Mn) causes severe interveinal chlorosis
        "unit": "pH scale",
        "advisories": {
            "acidic": "Soil pH < 6.0: Nodulation impaired. Lime application (1-2 t/ha) or seed pelleting with calcium carbonate recommended.",
            "optimum": "Soil pH 6.5-7.5: Ideal range for Green Gram root nodule development and nutrient uptake.",
            "alkaline": "Soil pH > 8.0: High risk of lime-induced Iron Chlorosis. Foliar spray of 0.5% FeSO4 + 0.1% citric acid recommended."
        },
        "source": get_source("ICAR-IIPR-2018")
    },
    "electrical_conductivity_salinity": {
        "optimum_max_ds_m": 1.5,
        "threshold_yield_decline_ds_m": 2.0, # Yield declines by ~10-15% per dS/m increase above 2.0 dS/m
        "critical_severe_loss_ds_m": 4.0,
        "unit": "dS/m (ECe at 25°C)",
        "advisory": "Green Gram is highly sensitive to soil salinity. Soils with ECe > 2.0 dS/m cause osmotic root desiccation and leaf necrosis.",
        "source": get_source("ICAR-IIPR-2018")
    },
    "organic_carbon": {
        "desirable_min_pct": 0.50,
        "optimum_pct": 0.75,
        "advisory": "Organic carbon > 0.5% sustains healthy indigenous rhizobial population and enhances moisture retention.",
        "source": get_source("TNAU-AGRITECH-PULSES")
    }
}

def get_soil_profile(soil_type: Optional[str]) -> SoilTypeProfile:
    if not soil_type:
        return SOIL_PROFILES["Sandy Loam"]
    clean = soil_type.strip().lower()
    # 1. Exact match first
    for key, prof in SOIL_PROFILES.items():
        if key.lower() == clean:
            return prof
    # 2. Check longest keys first so "Clay Loam" matches before "Loam"
    sorted_keys = sorted(SOIL_PROFILES.keys(), key=lambda k: len(k), reverse=True)
    for key in sorted_keys:
        if key.lower() in clean or clean in key.lower():
            return SOIL_PROFILES[key]
    return SOIL_PROFILES["Sandy Loam"]

def evaluate_soil_chemical_status(
    ph: Optional[float],
    ec: Optional[float]
) -> Dict[str, Any]:
    """
    Evaluates soil pH and EC against validated Green Gram thresholds.
    """
    notes = []
    status = "OPTIMAL"

    if ph is not None:
        if ph < 6.0:
            status = "WARNING"
            notes.append(SOIL_CHEMICAL_THRESHOLDS["ph"]["advisories"]["acidic"])
        elif ph > 8.0:
            status = "WARNING"
            notes.append(SOIL_CHEMICAL_THRESHOLDS["ph"]["advisories"]["alkaline"])
        else:
            notes.append(SOIL_CHEMICAL_THRESHOLDS["ph"]["advisories"]["optimum"])
    else:
        notes.append("Soil pH not provided; default neutral assumption applied (field soil testing advised).")

    if ec is not None:
        if ec >= 2.0:
            status = "ALERT"
            notes.append(f"Soil salinity (EC = {ec:.2f} dS/m) exceeds critical tolerance (2.0 dS/m). Risk of osmotic stress and poor stand.")
        elif ec >= 1.5:
            notes.append(f"Soil EC ({ec:.2f} dS/m) is approaching the upper sensitivity boundary for Green Gram.")

    return {
        "status": status,
        "ph_evaluated": ph,
        "ec_evaluated": ec,
        "notes": notes,
        "source": SOIL_CHEMICAL_THRESHOLDS["ph"]["source"]
    }
