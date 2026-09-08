"""
Green Gram (Vigna radiata) Disease Repository & Epidemiological Risk Rules.
Authoritative source grounding: ICAR-IIPR "Diagnosis and Management of Mungbean Diseases", TNAU Agritech Portal.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class DiseaseModel(BaseModel):
    disease_id: str
    common_name: str
    causal_organism: str
    pathogen_type: str # "Viral", "Fungal", "Bacterial"
    transmission_vector: Optional[str] = None
    vulnerable_stages: List[str]
    early_symptoms: str
    advanced_symptoms: str
    favorable_weather: Dict[str, Any] # temp range, RH range, rainfall
    prevention_measures: List[str]
    ipm_management: List[str]
    resistant_varieties: List[str]
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

DISEASES: Dict[str, DiseaseModel] = {
    "MYMV": DiseaseModel(
        disease_id="DIS-GG-MYMV-01",
        common_name="Mungbean Yellow Mosaic Virus (MYMV)",
        causal_organism="Mungbean yellow mosaic India virus (MYMIV) / MYMV (Geminiviridae, Begomovirus)",
        pathogen_type="Viral",
        transmission_vector="Whitefly (Bemisia tabaci Gennadius)",
        vulnerable_stages=["Seedling", "Vegetative", "Branching", "Flowering"],
        early_symptoms="Small, irregular yellow specks or faint chlorotic flecks along minor leaf veins of young trifoliolate leaves.",
        advanced_symptoms="Complete yellowing of leaf blade; alternating bright yellow and green mosaic patches. Severe infection stunts plants, suppresses pod setting, and turns pods yellow and malformed.",
        favorable_weather={
            "temperature_range_c": (28.0, 36.0),
            "relative_humidity_pct": (60.0, 75.0),
            "conditions": "Warm, sunny, dry weather favoring high whitefly reproduction and dispersal."
        },
        prevention_measures=[
            "Grow certified MYMV-resistant varieties (IPM 02-03, Virat, MH 421, CO 8).",
            "Seed treatment with Imidacloprid 70 WS (5 g/kg seed) or Thiamethoxam 30 FS to protect seedlings for first 25-30 days.",
            "Install yellow sticky traps (15-20 traps/ha) at canopy height to trap whitefly vectors."
        ],
        ipm_management=[
            "Rogue out and destroy infected plants during first 3-4 weeks to eliminate viral inoculum reservoir.",
            "Conserve natural predators (ladybird beetles, green lacewings, mirid bugs).",
            "Foliar spray with 5% Neem Seed Kernel Extract (NSKE) or Azadirachtin 0.03% (3 ml/L).",
            "If vector crosses Economic Threshold Level (ETL: 5 whiteflies/leaf), apply recommended systemic insecticide."
        ],
        resistant_varieties=["IPM 02-03", "IPM 205-7 (VIRAT)", "MH 421", "CO 8", "WGG 42"],
        source=get_source("ICAR-IIPR-2018")
    ),
    "Cercospora_Leaf_Spot": DiseaseModel(
        disease_id="DIS-GG-CERCOSPORA-02",
        common_name="Cercospora Leaf Spot (Tikka-like spot)",
        causal_organism="Cercospora canescens Ellis & G. Martin / Cercospora cruenta",
        pathogen_type="Fungal",
        transmission_vector="Air-borne conidia and seed-borne mycelium",
        vulnerable_stages=["Vegetative", "Branching", "Flowering", "Pod Formation"],
        early_symptoms="Small circular spots with grey-white center and distinct dark reddish-brown margins on leaf surface.",
        advanced_symptoms="Spots coalesce into extensive necrotic blotches. Severe infection causes premature leaf yellowing and complete defoliation, leaving bare branches with few pods.",
        favorable_weather={
            "temperature_range_c": (25.0, 32.0),
            "relative_humidity_pct": (80.0, 95.0),
            "conditions": "High relative humidity (>82%), frequent light drizzles, and dense canopy microclimate."
        },
        prevention_measures=[
            "Seed treatment with Carbendazim + Mancozeb (2 g/kg seed) or Trichoderma viride (10 g/kg seed).",
            "Ensure proper plant spacing (30 x 10 cm) to facilitate canopy aeration and reduce intra-canopy humidity.",
            "Avoid excessive irrigation during vegetative stage that elevates humidity."
        ],
        ipm_management=[
            "Destroy diseased crop residues after harvest.",
            "Foliar spray with Carbendazim 50 WP (1 g/L) or Mancozeb 75 WP (2 g/L) at first symptom onset during humid spells.",
            "Repeat after 10-14 days if overcast, humid weather persists."
        ],
        resistant_varieties=["MH 421", "IPM 02-03"],
        source=get_source("ICAR-IIPR-2018")
    ),
    "Powdery_Mildew": DiseaseModel(
        disease_id="DIS-GG-POWDERY-MILDEW-03",
        common_name="Powdery Mildew",
        causal_organism="Erysiphe polygoni DC",
        pathogen_type="Fungal",
        transmission_vector="Wind-borne conidia",
        vulnerable_stages=["Flowering", "Pod Formation", "Pod Filling", "Maturity"],
        early_symptoms="Small, faint white circular floury or talcum-like powdery patches on upper leaf surface.",
        advanced_symptoms="Powdery white fungal mycelium covers entire leaf blade, petioles, stems, and pods. Leaves turn yellow, curl downwards, dry up, and shed prematurely. Pods remain small and shriveled.",
        favorable_weather={
            "temperature_range_c": (20.0, 28.0),
            "relative_humidity_pct": (70.0, 85.0),
            "conditions": "Cool nights with high morning dew followed by warm dry sunny days (common in late rabi / spring crops)."
        },
        prevention_measures=[
            "Sow tolerant varieties in rabi/spring.",
            "Avoid late sowing which exposes reproductive crop to peak powdery mildew sporulation."
        ],
        ipm_management=[
            "Dust wettable sulfur (2-2.5 g/L) or spray Hexaconazole 5 EC (1 ml/L) or Propiconazole 25 EC (1 ml/L) at initial patch detection.",
            "Ensure thorough under-leaf canopy coverage."
        ],
        resistant_varieties=["CO 8", "WGG 42"],
        source=get_source("TNAU-AGRITECH-PULSES")
    ),
    "Web_Blight": DiseaseModel(
        disease_id="DIS-GG-WEB-BLIGHT-04",
        common_name="Rhizoctonia Web Blight / Root Rot",
        causal_organism="Rhizoctonia solani Kühn (teleomorph: Thanatephorus cucumeris)",
        pathogen_type="Fungal",
        transmission_vector="Soil-borne sclerotia and splashing raindrops",
        vulnerable_stages=["Seedling", "Vegetative", "Branching"],
        early_symptoms="Water-soaked grayish-green oval lesions near base of stem or lower leaves.",
        advanced_symptoms="Spiderweb-like fungal mycelial threads spread across foliage; leaves blight and collapse rapidly under warm, humid conditions.",
        favorable_weather={
            "temperature_range_c": (26.0, 32.0),
            "relative_humidity_pct": (85.0, 100.0),
            "conditions": "High soil moisture, poor drainage, standing water, and high relative humidity."
        },
        prevention_measures=[
            "Strict surface field drainage; prevent any ponding.",
            "Seed treatment with Trichoderma harzianum (10 g/kg seed) + Pseudomonas fluorescens (10 g/kg seed).",
            "Deep summer plowing to bury surface sclerotia."
        ],
        ipm_management=[
            "Immediate drainage of surface runoff.",
            "Foliar spray with Validamycin 3 L (2 ml/L) or Carbendazim (1 g/L) focused on lower stem."
        ],
        resistant_varieties=["IPM 02-03"],
        source=get_source("ICAR-IIPR-2018")
    ),
    "Anthracnose": DiseaseModel(
        disease_id="DIS-GG-ANTHRACNOSE-05",
        common_name="Anthracnose",
        causal_organism="Colletotrichum lindemuthianum / Colletotrichum dematium",
        pathogen_type="Fungal",
        transmission_vector="Seed-borne and splash-borne conidia",
        vulnerable_stages=["Vegetative", "Flowering", "Pod Formation"],
        early_symptoms="Sunken circular dark brown to black spots with raised reddish borders on leaves and veins.",
        advanced_symptoms="Sunken circular spots on pods with pink gelatinous spore masses in humid weather. Pods fail to fill, seed coats stained.",
        favorable_weather={
            "temperature_range_c": (20.0, 27.0),
            "relative_humidity_pct": (80.0, 95.0),
            "conditions": "Intermittent rainfall, high humidity, and moderate temperature."
        },
        prevention_measures=[
            "Use certified disease-free seed.",
            "Seed treatment with Thiram + Carbendazim (1:1 @ 2 g/kg seed)."
        ],
        ipm_management=[
            "Spray Mancozeb 75 WP (2 g/L) or Copper Oxychloride 50 WP (2.5 g/L) on early detection."
        ],
        resistant_varieties=["IPM 02-03"],
        source=get_source("TNAU-AGRITECH-PULSES")
    )
}

def evaluate_disease_risk(
    growth_stage: str,
    temperature: Optional[float],
    humidity: Optional[float]
) -> List[Dict[str, Any]]:
    """
    Evaluates current stage and meteorological factors to identify disease vulnerability.
    """
    active_risks = []

    for dis_id, dis in DISEASES.items():
        is_stage_vulnerable = any(growth_stage.lower() in s.lower() for s in dis.vulnerable_stages)
        if not is_stage_vulnerable:
            continue

        weather_match = False
        t_range = dis.favorable_weather.get("temperature_range_c")
        rh_min = dis.favorable_weather.get("relative_humidity_pct", (0, 100))[0]

        t_ok = True
        if temperature is not None and t_range:
            t_ok = t_range[0] <= temperature <= t_range[1]

        rh_ok = True
        if humidity is not None and rh_min:
            rh_ok = humidity >= rh_min

        if t_ok and rh_ok:
            weather_match = True

        if weather_match:
            active_risks.append({
                "disease_name": dis.common_name,
                "causal_organism": dis.causal_organism,
                "risk_level": "HIGH" if (temperature is not None and humidity is not None) else "MODERATE",
                "stage": growth_stage,
                "early_symptoms": dis.early_symptoms,
                "ipm_action": dis.ipm_management[0] if dis.ipm_management else "Scout canopy.",
                "source": dis.source
            })

    return active_risks
