"""
Green Gram (Vigna radiata) 10-Stage Growth Model.
Authoritative source grounding: ICAR-IIPR Package of Practices, FAO-56 (Kc), TNAU Agritech Portal.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class GrowthStageDefinition(BaseModel):
    stage_id: str
    stage_name: str
    standard_das_range: tuple[int, int] # (start_das, end_das) for ~60-65 day variety baseline
    physiological_description: str
    water_sensitivity: str # "LOW", "MODERATE", "CRITICAL", "DETRIMENTAL"
    crop_coefficient_kc: float # FAO-56
    temp_min_c: float
    temp_opt_c: tuple[float, float]
    temp_max_c: float
    nutrient_priority: str
    disease_vulnerabilities: List[str]
    pest_vulnerabilities: List[str]
    management_advisory: str
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

GROWTH_STAGES: Dict[str, GrowthStageDefinition] = {
    "Sowing": GrowthStageDefinition(
        stage_id="STAGE_01_SOWING",
        stage_name="Sowing",
        standard_das_range=(0, 0),
        physiological_description="Seed placement into moist seedbed (3-4 cm depth). Seed imbibes 50-60% of dry weight in moisture to initiate metabolism.",
        water_sensitivity="LOW",
        crop_coefficient_kc=0.40,
        temp_min_c=15.0,
        temp_opt_c=(28.0, 32.0),
        temp_max_c=40.0,
        nutrient_priority="Basal starter N (15-20 kg/ha), full P2O5 (40-50 kg/ha), and Rhizobium/PSB biofertilizer seed treatment.",
        disease_vulnerabilities=["Seed-borne fungal pathogens", "Collar rot"],
        pest_vulnerabilities=["Termites", "Ants"],
        management_advisory="Ensure adequate seedbed moisture via pre-sowing irrigation (palewa). Avoid water stagnation.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Germination": GrowthStageDefinition(
        stage_id="STAGE_02_GERMINATION",
        stage_name="Germination",
        standard_das_range=(1, 5),
        physiological_description="Radicle emerges followed by hypocotyl elongation and epigeal emergence of cotyledons.",
        water_sensitivity="MODERATE",
        crop_coefficient_kc=0.45,
        temp_min_c=18.0,
        temp_opt_c=(28.0, 32.0),
        temp_max_c=38.0,
        nutrient_priority="Seedling relies on cotyledon reserves; no supplementary nutrients required.",
        disease_vulnerabilities=["Damping-off (Pythium / Rhizoctonia)", "Pre-emergence rot"],
        pest_vulnerabilities=["Cutworms"],
        management_advisory="Do not flood field. Surface soil crusting after rain must be broken by light hoeing to allow emergence.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Seedling": GrowthStageDefinition(
        stage_id="STAGE_03_SEEDLING",
        stage_name="Seedling",
        standard_das_range=(6, 14),
        physiological_description="Primary unifoliolate leaves expand, followed by emergence of first trifoliolate leaf. Tap root elongates rapidly.",
        water_sensitivity="LOW",
        crop_coefficient_kc=0.50,
        temp_min_c=18.0,
        temp_opt_c=(28.0, 35.0),
        temp_max_c=40.0,
        nutrient_priority="Rhizobial infection initiates root hair curling; young nodules begin forming by 10-14 DAS.",
        disease_vulnerabilities=["Collar rot (Sclerotium rolfsii)", "Early damping off"],
        pest_vulnerabilities=["Stem fly (Ophiomyia phaseoli)", "Early sucking pests"],
        management_advisory="Withhold irrigation to stimulate deep root penetration. Light weeding or thinning to maintain optimal plant density.",
        source=get_source("TNAU-AGRITECH-PULSES")
    ),
    "Vegetative": GrowthStageDefinition(
        stage_id="STAGE_04_VEGETATIVE",
        stage_name="Vegetative",
        standard_das_range=(15, 24),
        physiological_description="Rapid leaf expansion, trifoliolate development, and stem elongation. Active biological nitrogen fixation in pink nodules.",
        water_sensitivity="MODERATE",
        crop_coefficient_kc=0.75,
        temp_min_c=20.0,
        temp_opt_c=(28.0, 35.0),
        temp_max_c=40.0,
        nutrient_priority="Active symbiotic N-fixation. Inspect nodules: pink interior indicates active leghemoglobin and healthy N fixation.",
        disease_vulnerabilities=["Mungbean Yellow Mosaic Virus (early vector transmission)", "Bacterial leaf spot"],
        pest_vulnerabilities=["Whitefly (Bemisia tabaci)", "Aphids (Aphis craccivora)", "Thrips"],
        management_advisory="Inter-cultivation for weed control before canopy closure. One light irrigation only if soil displays visible drying.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Branching": GrowthStageDefinition(
        stage_id="STAGE_05_BRANCHING",
        stage_name="Branching",
        standard_das_range=(25, 29),
        physiological_description="Primary and secondary lateral branches develop from leaf axils, building reproductive bearing frame.",
        water_sensitivity="MODERATE",
        crop_coefficient_kc=0.85,
        temp_min_c=20.0,
        temp_opt_c=(28.0, 35.0),
        temp_max_c=40.0,
        nutrient_priority="High sulfur and phosphorus utilization for branch cell division and upcoming floral buds.",
        disease_vulnerabilities=["Cercospora leaf spot (early lesions)", "Web blight (Rhizoctonia)"],
        pest_vulnerabilities=["Thrips (Caliothrips indicus)", "Foliage caterpillars"],
        management_advisory="Final mechanical weeding. Install yellow sticky traps (12-15/ha) to monitor whitefly vector populations.",
        source=get_source("ANGRAU-PULSES-2021")
    ),
    "Flowering": GrowthStageDefinition(
        stage_id="STAGE_06_FLOWERING",
        stage_name="Flowering",
        standard_das_range=(30, 40),
        physiological_description="Racemes open bright yellow papilionaceous flowers. Anthesis occurs early morning with high cleistogamy (self-pollination).",
        water_sensitivity="CRITICAL",
        crop_coefficient_kc=1.05,
        temp_min_c=22.0,
        temp_opt_c=(28.0, 34.0),
        temp_max_c=38.0, # High temperatures (>38-40°C) cause flower shedding and pollen sterility
        nutrient_priority="Foliar spray of 2% DAP or TNAU Pulse Wonder (1%) to supply targeted N, P, and micronutrients to arrest flower drop.",
        disease_vulnerabilities=["Anthracnose (Colletotrichum)", "Cercospora leaf spot", "MYMV chlorosis"],
        pest_vulnerabilities=["Flower thrips (Megalurothrips usitatus)", "Spotted pod borer (Maruca vitrata) in buds"],
        management_advisory="MOST CRITICAL WATER STAGE. Maintain moisture between 50-65% ASM. Water deficit causes massive flower abscission (30-50% yield loss).",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Pod Formation": GrowthStageDefinition(
        stage_id="STAGE_07_POD_FORMATION",
        stage_name="Pod Formation",
        standard_das_range=(41, 50),
        physiological_description="Fertilized ovaries elongate rapidly into green linear pubescent pods. Ovules initiate embryogenesis.",
        water_sensitivity="CRITICAL",
        crop_coefficient_kc=1.10,
        temp_min_c=20.0,
        temp_opt_c=(28.0, 34.0),
        temp_max_c=38.0,
        nutrient_priority="High assimilatory sink demand. Second foliar spray of 2% DAP or potassium nitrate (1%) to support pod elongation.",
        disease_vulnerabilities=["Powdery mildew (Erysiphe polygoni)", "Pod blight (Macrophomina)"],
        pest_vulnerabilities=["Gram pod borer (Helicoverpa armigera)", "Spotted pod borer (Maruca vitrata)", "Pod bugs (Riptortus)"],
        management_advisory="CRITICAL WATER STAGE. Ensure soil moisture is replenished. Moisture stress results in aborted pods, few seeds per pod, and low test weight.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Pod Filling": GrowthStageDefinition(
        stage_id="STAGE_08_POD_FILLING",
        stage_name="Pod Filling",
        standard_das_range=(51, 58),
        physiological_description="Cotyledon starch and storage protein accumulation. Pods reach maximum girth; seed weight increases linearly.",
        water_sensitivity="MODERATE",
        crop_coefficient_kc=0.85,
        temp_min_c=20.0,
        temp_opt_c=(26.0, 32.0),
        temp_max_c=36.0,
        nutrient_priority="Translocation of leaf assimilates to grain. Avoid excess mineral N which triggers renewed vegetative flushing.",
        disease_vulnerabilities=["Powdery mildew", "Cercospora leaf spot"],
        pest_vulnerabilities=["Pod borer larvae feeding inside mature pods", "Stink bugs"],
        management_advisory="Light irrigation if soil is visibly desiccated and cracked, but avoid waterlogging which causes fungal pod infection.",
        source=get_source("FAO-56-CROPWAT")
    ),
    "Maturity": GrowthStageDefinition(
        stage_id="STAGE_09_MATURITY",
        stage_name="Maturity",
        standard_das_range=(59, 65),
        physiological_description="Pods change color from bright green to dark brown or black. Foliage begins natural senescence. Seeds reach physiological maturity (moisture drops <18%).",
        water_sensitivity="DETRIMENTAL",
        crop_coefficient_kc=0.50,
        temp_min_c=18.0,
        temp_opt_c=(25.0, 32.0),
        temp_max_c=38.0,
        nutrient_priority="No fertilizer input required. Plant redistributes internal reserves.",
        disease_vulnerabilities=["Pod rot and seed discoloration if unexpected rain occurs", "Viviparous sprouting in pod"],
        pest_vulnerabilities=["Pulse beetle (Callosobruchus chinensis) field infestation"],
        management_advisory="STRICTLY CEASE ALL IRRIGATION 10-12 days prior to harvest. Moisture now causes pod rot, viviparous sprouting, and uneven maturity.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "Harvest": GrowthStageDefinition(
        stage_id="STAGE_10_HARVEST",
        stage_name="Harvest",
        standard_das_range=(66, 75),
        physiological_description="80-90% of pods turn dark brown/black and brittle. Grain moisture is 12-14% for safe harvest.",
        water_sensitivity="DETRIMENTAL",
        crop_coefficient_kc=0.35,
        temp_min_c=15.0,
        temp_opt_c=(25.0, 35.0),
        temp_max_c=42.0,
        nutrient_priority="Harvest complete. Crop residue incorporated or removed.",
        disease_vulnerabilities=["Post-harvest storage molds"],
        pest_vulnerabilities=["Storage bruchids"],
        management_advisory="Harvest in early morning hours while dew softens pods to prevent shattering losses. Dry grain in sun to 9-10% moisture before bagging.",
        source=get_source("ICAR-IIPR-2018")
    )
}

def get_stage_by_name(name: Optional[str]) -> GrowthStageDefinition:
    if not name:
        return GROWTH_STAGES["Vegetative"]
    clean = name.strip()
    for key, stg in GROWTH_STAGES.items():
        if key.lower() == clean.lower() or clean.lower() in key.lower():
            return stg
    return GROWTH_STAGES["Vegetative"]

def list_all_stages() -> List[GrowthStageDefinition]:
    return list(GROWTH_STAGES.values())
