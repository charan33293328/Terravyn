"""
Green Gram (Vigna radiata) Pest Repository & Integrated Pest Management (IPM).
Authoritative source grounding: ICAR-IIPR, TNAU Agritech Portal, ANGRAU Vyavasaya Panchangam.
Adheres strictly to IPM principles; no automated chemical spray triggers.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class PestModel(BaseModel):
    pest_id: str
    common_name: str
    scientific_name: str
    order_family: str
    vulnerable_stages: List[str]
    symptoms_of_damage: str
    economic_threshold_level_etl: str
    favorable_environmental_conditions: str
    monitoring_method: str
    ipm_cultural_biological: List[str]
    ipm_chemical_intervention: List[str]
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

PESTS: Dict[str, PestModel] = {
    "Whitefly": PestModel(
        pest_id="PEST-GG-WHITEFLY-01",
        common_name="Whitefly",
        scientific_name="Bemisia tabaci (Gennadius)",
        order_family="Hemiptera: Aleyrodidae",
        vulnerable_stages=["Seedling", "Vegetative", "Branching", "Flowering"],
        symptoms_of_damage="Both nymphs and adults suck sap from under-surface of leaves, excrete sticky honeydew fostering black sooty mold. Most critically, transmits Mungbean Yellow Mosaic Virus (MYMV).",
        economic_threshold_level_etl="5 to 8 whiteflies per plant or 1 whitefly per leaf on young crop.",
        favorable_environmental_conditions="Warm, dry, sunny weather (28-36°C) with low rainfall and moderate relative humidity.",
        monitoring_method="Yellow sticky traps installed at crop canopy height (15-20 traps/ha); weekly early-morning leaf scouting.",
        ipm_cultural_biological=[
            "Grow MYMV-resistant varieties (IPM 02-03, Virat, MH 421).",
            "Seed treatment with Imidacloprid 70 WS (5 g/kg seed) to provide 25-30 days seedling systemic protection.",
            "Install yellow sticky traps; maintain field sanitation free of solanaceous and malvaceous weed hosts.",
            "Conserve natural predators: Chrysoperla carnea (green lacewings) and Coccinellid beetles."
        ],
        ipm_chemical_intervention=[
            "Spray 5% Neem Seed Kernel Extract (NSKE) or Azadirachtin 0.03% (3 ml/L).",
            "If ETL crossed: Spray Diafenthiuron 50 WP (1.2 g/L) or Spiromesifen 22.9 SC (1 ml/L)."
        ],
        source=get_source("ICAR-IIPR-2018")
    ),
    "Thrips": PestModel(
        pest_id="PEST-GG-THRIPS-02",
        common_name="Flower Thrips / Bean Blossom Thrips",
        scientific_name="Megalurothrips usitatus (Bagnall) / Caliothrips indicus",
        order_family="Thysanoptera: Thripidae",
        vulnerable_stages=["Branching", "Flowering"],
        symptoms_of_damage="Nymphs and adults lacerate floral parts and suck exuded sap. Flower buds fail to open, turn dark brown, and drop prematurely. Distorted petals and severe flower drop.",
        economic_threshold_level_etl="3 to 5 thrips per flower / flower cluster.",
        favorable_environmental_conditions="Hot, dry weather spells with low rainfall during early flowering.",
        monitoring_method="Tap 10 flower clusters onto white paper sheet or white tray to count dislodged active thrips.",
        ipm_cultural_biological=[
            "Install blue or white sticky traps (15-20/ha) at canopy height.",
            "Conserve predatory anthocorid bugs (Orius spp.).",
            "Spray neem oil (5 ml/L) at first appearance of flower buds."
        ],
        ipm_chemical_intervention=[
            "If ETL crossed during flowering: Spray Spinosad 45 SC (0.3 ml/L) or Dimethoate 30 EC (1.7 ml/L)."
        ],
        source=get_source("TNAU-AGRITECH-PULSES")
    ),
    "Spotted_Pod_Borer": PestModel(
        pest_id="PEST-GG-SPOTTED-BORER-03",
        common_name="Spotted Pod Borer / Webbing Caterpillar",
        scientific_name="Maruca vitrata (Fabricius)",
        order_family="Lepidoptera: Crambidae",
        vulnerable_stages=["Flowering", "Pod Formation", "Pod Filling"],
        symptoms_of_damage="Caterpillar webs together flower buds, flowers, and young pods into an unsightly mass, feeding from within. Bored entry holes plugged with dark granular frass.",
        economic_threshold_level_etl="1 larva or webbed flower cluster per meter row.",
        favorable_environmental_conditions="Humid, warm cloudy weather with moderate intermittent rainfall.",
        monitoring_method="Examine terminal shoots and floral clusters for distinctive webbing and fecal pellets.",
        ipm_cultural_biological=[
            "Early sowing to escape peak pest population.",
            "Conserve larval parasitoids (Campoletis, Bracon).",
            "Spray Bacillus thuringiensis (Bt) @ 1.5 kg/ha or Beauveria bassiana @ 2 kg/ha."
        ],
        ipm_chemical_intervention=[
            "Spray Chlorantraniliprole 18.5 SC (0.3 ml/L) or Flubendiamide 39.35 SC (0.2 ml/L) at early webbing stage."
        ],
        source=get_source("ICAR-IIPR-2018")
    ),
    "Gram_Pod_Borer": PestModel(
        pest_id="PEST-GG-GRAM-BORER-04",
        common_name="Gram Pod Borer / American Bollworm",
        scientific_name="Helicoverpa armigera (Hübner)",
        order_family="Lepidoptera: Noctuidae",
        vulnerable_stages=["Pod Formation", "Pod Filling"],
        symptoms_of_damage="Stout green/brown caterpillar feeds by keeping anterior half of body inside the pod while posterior half remains outside. Neat circular holes on pods with missing seeds.",
        economic_threshold_level_etl="1 larva per meter row or 5-10% damaged pods.",
        favorable_environmental_conditions="Warm days (25-32°C) with high floral nectar availability.",
        monitoring_method="Install sex pheromone traps (Helilure @ 5-8 traps/ha) to monitor adult moth activity.",
        ipm_cultural_biological=[
            "Install bird perches (T-shaped wooden poles, 40-50/ha) for predatory birds.",
            "Conserve Trichogramma egg parasitoids.",
            "Spray Helicoverpa Nuclear Polyhedrosis Virus (HaNPV @ 250 LE/ha) with 0.1% jaggery in evening hours."
        ],
        ipm_chemical_intervention=[
            "If ETL crossed: Spray Emamectin Benzoate 5 SG (0.4 g/L) or Chlorantraniliprole 18.5 SC (0.3 ml/L)."
        ],
        source=get_source("ANGRAU-PULSES-2021")
    ),
    "Stem_Fly": PestModel(
        pest_id="PEST-GG-STEM-FLY-05",
        common_name="Stem Fly / Bean Shoot Fly",
        scientific_name="Ophiomyia phaseoli (Tryon)",
        order_family="Diptera: Agromyzidae",
        vulnerable_stages=["Seedling", "Vegetative"],
        symptoms_of_damage="Maggot tunnels down inside the petiole into main stem down to collar region, disrupting vascular flow. Affected seedlings wilt, turn pale yellow, and dry up within 2-3 weeks of emergence.",
        economic_threshold_level_etl="5 to 10% seedling mortality or 1 fly egg/puncture per leaf.",
        favorable_environmental_conditions="Warm, humid post-emergence weather.",
        monitoring_method="Inspect cotyledonary leaves for tiny oviposition punctures; split wilting seedling stems vertically to check for white maggots or puparia.",
        ipm_cultural_biological=[
            "Seed treatment with Imidacloprid 70 WS (5 g/kg seed) or Thiamethoxam 30 FS (5 ml/kg seed) is the single most effective preventive practice.",
            "Avoid staggered sowings in neighboring fields.",
            "Earthing-up at 20 DAS to cover stem cracking and encourage adventitious rooting above damaged area."
        ],
        ipm_chemical_intervention=[
            "Spray Dimethoate 30 EC (1.7 ml/L) if seedling wilting is observed in untreated crops."
        ],
        source=get_source("TNAU-AGRITECH-PULSES")
    )
}

def evaluate_pest_risk(growth_stage: str) -> List[Dict[str, Any]]:
    """
    Identifies active insect pests vulnerable to current crop stage.
    """
    active_pests = []
    for pest_id, p in PESTS.items():
        if any(growth_stage.lower() in s.lower() for s in p.vulnerable_stages):
            active_pests.append({
                "pest_name": p.common_name,
                "scientific_name": p.scientific_name,
                "stage": growth_stage,
                "etl": p.economic_threshold_level_etl,
                "monitoring": p.monitoring_method,
                "cultural_control": p.ipm_cultural_biological[0] if p.ipm_cultural_biological else "Scout weekly.",
                "source": p.source
            })
    return active_pests
