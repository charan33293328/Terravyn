"""
Green Gram (Vigna radiata) Nutrient Requirements & Diagnostic Knowledge.
Authoritative source grounding: ICAR-IIPR, TNAU Agritech Portal, ANGRAU Vyavasaya Panchangam.
Enforces multi-factor diagnostic logic to prevent superficial "yellow leaf = N deficiency" conclusions.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class NutrientGuideline(BaseModel):
    nutrient_symbol: str
    nutrient_name: str
    physiological_role: str
    recommended_dose_kg_ha: str
    application_timing: str
    deficiency_symptoms: str
    excess_toxicity_risks: str
    confounding_factors: List[str] # Other factors that mimic this deficiency
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED

NUTRIENT_GUIDELINES: Dict[str, NutrientGuideline] = {
    "N": NutrientGuideline(
        nutrient_symbol="N",
        nutrient_name="Nitrogen",
        physiological_role="Vegetative protein synthesis and chlorophyll formation until symbiotic nodulation becomes fully functional.",
        recommended_dose_kg_ha="15 - 20 kg N/ha (Basal starter dose only)",
        application_timing="Apply 100% as basal dose at sowing. NEVER top-dress high nitrogen.",
        deficiency_symptoms="General light green to pale yellowing starting on older/lower leaves first; stunted spindly growth.",
        excess_toxicity_risks="Excess mineral nitrogen inhibits Rhizobium nodulation, promotes excessive vegetative vine growth, delays flowering, and increases lodging.",
        confounding_factors=[
            "Waterlogging hypoxia (causes rapid root nodule death and yellowing)",
            "Sulfur deficiency (yellowing looks similar but starts on youngest leaves first)",
            "Iron chlorosis (interveinal yellowing on young leaves in high pH soils)",
            "Mungbean Yellow Mosaic Virus (bright yellow mosaic patches)",
            "Root rot / Nematode damage (impaired vascular water/nutrient transport)"
        ],
        source=get_source("ICAR-IIPR-2018")
    ),
    "P": NutrientGuideline(
        nutrient_symbol="P2O5",
        nutrient_name="Phosphorus",
        physiological_role="Crucial for root elongation, ATP energy transfer, and rapid Rhizobium nodule establishment.",
        recommended_dose_kg_ha="40 - 50 kg P2O5/ha",
        application_timing="Apply 100% basal placed 4-5 cm below seed. Single Super Phosphate (SSP) is preferred as it also provides 12% Sulfur and 19% Calcium.",
        deficiency_symptoms="Stunted root growth, few and small nodules, dull purplish or dark bronze discoloration on older leaves, delayed flowering.",
        excess_toxicity_risks="High available phosphorus can induce Zinc and Iron deficiency.",
        confounding_factors=["Cold soil temperatures (restricts P uptake even if soil P is adequate)"],
        source=get_source("ICAR-IIPR-2018")
    ),
    "K": NutrientGuideline(
        nutrient_symbol="K2O",
        nutrient_name="Potassium",
        physiological_role="Osmoregulation, stomatal aperture control, water use efficiency, and disease resistance.",
        recommended_dose_kg_ha="20 - 25 kg K2O/ha (in soils testing low to medium in K)",
        application_timing="Apply basal at sowing via Muriate of Potash (MOP) or Sulfate of Potash (SOP).",
        deficiency_symptoms="Marginal chlorosis and leaf scorch (firing) along edges of older leaves; weak stems.",
        excess_toxicity_risks="Can depress Magnesium and Calcium uptake in high concentrations.",
        confounding_factors=["Salinity salt burn (marginal leaf necrosis)"],
        source=get_source("TNAU-AGRITECH-PULSES")
    ),
    "S": NutrientGuideline(
        nutrient_symbol="S",
        nutrient_name="Sulfur",
        physiological_role="Essential for synthesis of sulfur-containing amino acids (methionine, cysteine, cystine) that constitute pulse protein.",
        recommended_dose_kg_ha="20 kg S/ha (supplied via SSP or Gypsum / elemental sulfur)",
        application_timing="Basal application at land preparation.",
        deficiency_symptoms="Uniform pale yellowing starting on YOUNG leaves first (unlike Nitrogen which starts on older leaves); small pale nodules.",
        excess_toxicity_risks="Rare in agricultural soils.",
        confounding_factors=["Nitrogen deficiency", "Iron chlorosis"],
        source=get_source("ICAR-IIPR-2018")
    ),
    "Zn": NutrientGuideline(
        nutrient_symbol="Zn",
        nutrient_name="Zinc",
        physiological_role="Auxin (indole acetic acid) synthesis, enzyme activation, and internode elongation.",
        recommended_dose_kg_ha="25 kg/ha Zinc Sulfate (ZnSO4) applied to soil once every 2-3 years, or foliar 0.5% ZnSO4.",
        application_timing="Soil application at sowing or foliar spray at early vegetative stage.",
        deficiency_symptoms="Interveinal chlorosis on middle leaves, rosetting of terminal leaves, and delayed flowering.",
        excess_toxicity_risks="Can induce iron deficiency chlorosis.",
        confounding_factors=["High soil phosphorus levels inducing Zn tie-up"],
        source=get_source("ANGRAU-PULSES-2021")
    ),
    "Fe": NutrientGuideline(
        nutrient_symbol="Fe",
        nutrient_name="Iron",
        physiological_role="Chlorophyll synthesis, electron transport in respiration, and leghemoglobin in root nodules.",
        recommended_dose_kg_ha="Foliar spray: 0.5% Ferrous Sulfate (FeSO4) + 0.1% Citric Acid at 25-30 DAS.",
        application_timing="Foliar spray when symptoms appear (common on calcareous/alkaline soils pH > 7.8).",
        deficiency_symptoms="Distinct interveinal chlorosis on youngest leaves where veins remain dark green while interveinal tissue turns ivory white/yellow.",
        excess_toxicity_risks="Can occur in acid waterlogged soils (bronzing).",
        confounding_factors=["Lime-induced high soil pH locking up ionic iron"],
        source=get_source("ANGRAU-PULSES-2021")
    ),
    "B": NutrientGuideline(
        nutrient_symbol="B",
        nutrient_name="Boron",
        physiological_role="Pollen grain germination, pollen tube elongation, sugar translocation, and ovule fertilization.",
        recommended_dose_kg_ha="Soil application: 1.0-1.5 kg Borax/ha; or foliar 0.1% Solubor at flower bud initiation.",
        application_timing="Early flowering stage.",
        deficiency_symptoms="Flower bud abortion, poor pod set, cracked or malformed pods, hollow heart in seeds.",
        excess_toxicity_risks="Narrow safety margin between deficiency and toxicity; excess causes leaf tip yellowing and necrosis.",
        confounding_factors=["Moisture stress causing flower drop"],
        source=get_source("ICAR-IIPR-2018")
    )
}

FOLIAR_NUTRITION_TECHNOLOGY: Dict[str, Any] = {
    "tnau_pulse_wonder": {
        "formula": "TNAU Pulse Wonder (Nutrient & Growth Regulator formulation)",
        "dosage": "5 kg/ha in 500 liters of water (1% spray)",
        "timing": "Single spray at peak flowering (30-35 DAS)",
        "effect": "Reduces flower drop by 20-25%, improves pod setting, and increases yield by 15-20%.",
        "source": get_source("TNAU-AGRITECH-PULSES")
    },
    "dap_foliar_spray": {
        "formula": "2% Diammonium Phosphate (DAP) spray (20 g DAP dissolved in 1 liter water, clear supernatant sprayed)",
        "dosage": "500 L spray solution/ha",
        "timing": "First spray at early flowering (30 DAS) and second spray at early pod development (45 DAS)",
        "effect": "Supplies readily absorbable N and P during high reproductive demand, preventing premature flower drop.",
        "source": get_source("ICAR-IIPR-2018")
    }
}

def diagnose_chlorosis(
    affected_leaves: str, # "YOUNG", "OLD", "PATCHY"
    soil_ph: Optional[float],
    soil_ec: Optional[float],
    has_waterlogging_history: bool,
    has_soil_test: bool
) -> Dict[str, Any]:
    """
    Multi-factor agronomic diagnostic to evaluate chlorosis / yellowing.
    Prevents simplistic single-cause attribution.
    """
    candidates = []

    if has_waterlogging_history:
        candidates.append({
            "cause": "Waterlogging Hypoxia",
            "probability": "HIGH",
            "reason": "Recent standing water causes root asphyxiation, nodule death, and rapid foliar yellowing.",
            "recommended_action": "Drain field immediately; withhold irrigation; aerate topsoil."
        })

    if affected_leaves == "YOUNG":
        if soil_ph and soil_ph > 7.8:
            candidates.append({
                "cause": "Lime-Induced Iron Chlorosis",
                "probability": "HIGH",
                "reason": "Alkaline soil pH precipitates ionic iron into unavailable forms.",
                "recommended_action": "Foliar spray with 0.5% FeSO4 + 0.1% citric acid."
            })
        candidates.append({
            "cause": "Sulfur Deficiency",
            "probability": "MODERATE",
            "reason": "Sulfur is immobile in plants; deficiency symptoms appear first on youngest leaves.",
            "recommended_action": "Apply gypsum or elemental sulfur if confirmed by soil test."
        })

    if affected_leaves == "OLD":
        candidates.append({
            "cause": "Nitrogen Starter Exhaustion",
            "probability": "MODERATE" if not has_waterlogging_history else "LOW",
            "reason": "Nitrogen is mobile in the plant and translocated from older foliage to new growth.",
            "recommended_action": "Check root nodules for healthy pink leghemoglobin before applying any supplemental nitrogen."
        })

    if affected_leaves == "PATCHY":
        candidates.append({
            "cause": "Mungbean Yellow Mosaic Virus (MYMV)",
            "probability": "HIGH",
            "reason": "Irregular bright yellow mosaic patches on leaf blade transmitted by Whitefly.",
            "recommended_action": "Rogue out infected plants early; inspect for Whitefly vectors; spray neem oil or recommended systemic insecticide."
        })

    return {
        "status": "ADVISORY",
        "soil_test_available": has_soil_test,
        "disclaimer": "Visual symptoms require soil or plant tissue analysis before commercial corrective application.",
        "candidates": candidates,
        "source": get_source("ICAR-IIPR-2018")
    }
