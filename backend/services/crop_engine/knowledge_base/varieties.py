"""
Green Gram (Vigna radiata) Variety Repository.
Authoritative source grounding: ICAR-IIPR Varietal Directory, IARI, SAUs (TNAU, ANGRAU, CCS HAU, PAU).
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class VarietyModel(BaseModel):
    name: str
    developer_institution: str
    release_year: Optional[int] = None
    duration_days: int
    duration_range: tuple[int, int]
    suitable_seasons: List[str] # Kharif, Spring, Summer, Rabi
    recommended_regions: List[str]
    average_yield_q_ha: float # quintals/hectare (1 q = 100 kg)
    yield_potential_q_ha: float
    seed_characteristics: str
    disease_resistance: Dict[str, str] # e.g. {"MYMV": "Resistant", "Cercospora": "Tolerant"}
    special_traits: List[str]
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

VARIETIES: Dict[str, VarietyModel] = {
    "IPM 02-03": VarietyModel(
        name="IPM 02-03",
        developer_institution="ICAR - Indian Institute of Pulses Research (IIPR), Kanpur",
        release_year=2009,
        duration_days=63,
        duration_range=(60, 65),
        suitable_seasons=["Spring", "Summer", "Kharif"],
        recommended_regions=["North West Plain Zone (NWPZ)", "Central Zone (CZ)", "South Zone (SZ)"],
        average_yield_q_ha=10.5,
        yield_potential_q_ha=14.0,
        seed_characteristics="Medium-bold green lustrous seeds; 100-seed weight ~3.8-4.2 g.",
        disease_resistance={
            "MYMV": "Resistant",
            "Cercospora Leaf Spot": "Moderately Resistant",
            "Powdery Mildew": "Moderately Resistant"
        },
        special_traits=[
            "High stability across diverse environments",
            "High resistance to Mungbean Yellow Mosaic Virus",
            "Synchronous pod maturity reducing shattering losses"
        ],
        source=get_source("ICAR-IIPR-VARIETIES-2020")
    ),
    "SML 668": VarietyModel(
        name="SML 668",
        developer_institution="Punjab Agricultural University (PAU), Ludhiana",
        release_year=2002,
        duration_days=60,
        duration_range=(58, 62),
        suitable_seasons=["Summer", "Spring"],
        recommended_regions=["Punjab", "Haryana", "Western UP", "Northern Plains"],
        average_yield_q_ha=11.0,
        yield_potential_q_ha=15.0,
        seed_characteristics="Bold seeds; 100-seed weight ~5.0-5.5 g; bright shining green.",
        disease_resistance={
            "MYMV": "Moderately Resistant",
            "Cercospora Leaf Spot": "Tolerant"
        },
        special_traits=[
            "Bold grain fetching premium market price",
            "Synchronous ripening suited for single-pass mechanical harvest",
            "Early maturity allowing timely kharif paddy transplanting"
        ],
        source=get_source("PAU-SML668-2018")
    ),
    "PUSA VISHAL": VarietyModel(
        name="PUSA VISHAL",
        developer_institution="ICAR - Indian Agricultural Research Institute (IARI), New Delhi",
        release_year=2001,
        duration_days=65,
        duration_range=(62, 68),
        suitable_seasons=["Spring", "Summer", "Kharif"],
        recommended_regions=["Northern & Central India", "Indo-Gangetic Plains"],
        average_yield_q_ha=11.5,
        yield_potential_q_ha=15.5,
        seed_characteristics="Extra bold, shiny green; 100-seed weight ~5.5-6.0 g.",
        disease_resistance={
            "MYMV": "Tolerant / Moderately Resistant",
            "Macrophomina Blight": "Moderately Resistant"
        },
        special_traits=[
            "Excellent cooking quality and dal recovery",
            "Wide adaptability across irrigated summer tracts",
            "High pod bearing per plant under balanced nutrition"
        ],
        source=get_source("IARI-PUSA-2019")
    ),
    "MH 421": VarietyModel(
        name="MH 421",
        developer_institution="Chaudhary Charan Singh Haryana Agricultural University (CCS HAU), Hisar",
        release_year=2014,
        duration_days=58,
        duration_range=(55, 60),
        suitable_seasons=["Summer", "Spring", "Kharif"],
        recommended_regions=["Haryana", "Punjab", "Rajasthan", "Delhi", "UP"],
        average_yield_q_ha=10.0,
        yield_potential_q_ha=13.5,
        seed_characteristics="Medium-bold, cylindrical green seeds; 100-seed weight ~4.0-4.5 g.",
        disease_resistance={
            "MYMV": "Resistant",
            "Cercospora Leaf Spot": "Resistant",
            "Bacterial Leaf Blight": "Moderately Resistant"
        },
        special_traits=[
            "Short duration suited for intensive summer crop rotations",
            "High pod set even under rising late-summer temperatures",
            "Indeterminate branching with compact plant architecture"
        ],
        source=get_source("CCS-HAU-MH421-2017")
    ),
    "IPM 205-7 (VIRAT)": VarietyModel(
        name="IPM 205-7 (VIRAT)",
        developer_institution="ICAR - Indian Institute of Pulses Research (IIPR), Kanpur",
        release_year=2016,
        duration_days=53,
        duration_range=(52, 55),
        suitable_seasons=["Summer", "Spring"],
        recommended_regions=["Indo-Gangetic Plains", "Central Zone"],
        average_yield_q_ha=10.0,
        yield_potential_q_ha=13.0,
        seed_characteristics="Medium-bold green seeds; 100-seed weight ~4.2 g.",
        disease_resistance={
            "MYMV": "Highly Resistant"
        },
        special_traits=[
            "Super-early maturity (52-55 days), shortest duration commercial variety in India",
            "Ideal summer catch crop fitting tight wheat-rice rotations",
            "High lodging and shattering resistance"
        ],
        source=get_source("ICAR-IIPR-VARIETIES-2020")
    ),
    "CO 8": VarietyModel(
        name="CO 8",
        developer_institution="Tamil Nadu Agricultural University (TNAU), Coimbatore",
        release_year=2014,
        duration_days=60,
        duration_range=(55, 65),
        suitable_seasons=["Kharif", "Rabi", "Summer"],
        recommended_regions=["Tamil Nadu", "Southern Peninsular Zone"],
        average_yield_q_ha=9.5,
        yield_potential_q_ha=13.0,
        seed_characteristics="Medium green seeds; 100-seed weight ~3.6 g.",
        disease_resistance={
            "MYMV": "Resistant",
            "Root Rot": "Moderately Resistant"
        },
        special_traits=[
            "Well adapted to southern peninsular soil and climate conditions",
            "Performs well in rice-fallow systems",
            "High basal branching and stable podding"
        ],
        source=get_source("TNAU-AGRITECH-PULSES")
    ),
    "WGG 42": VarietyModel(
        name="WGG 42",
        developer_institution="Regional Agricultural Research Station, Warangal (PJTSAU / ANGRAU)",
        release_year=2008,
        duration_days=65,
        duration_range=(62, 68),
        suitable_seasons=["Kharif", "Rabi (Rice Fallow)"],
        recommended_regions=["Andhra Pradesh", "Telangana"],
        average_yield_q_ha=10.0,
        yield_potential_q_ha=13.5,
        seed_characteristics="Shiny green, medium-bold seeds.",
        disease_resistance={
            "MYMV": "Resistant",
            "Powdery Mildew": "Moderately Resistant"
        },
        special_traits=[
            "Widely cultivated in Krishna-Godavari and North Coastal zones of AP",
            "Excellent moisture scavenging in residual moisture rice fallows",
            "Good dal flavor and cooking properties"
        ],
        source=get_source("ANGRAU-PULSES-2021")
    )
}

def get_variety(name: Optional[str]) -> VarietyModel:
    if not name:
        return VARIETIES["IPM 02-03"]
    clean = name.strip().upper()
    for key, var in VARIETIES.items():
        if key.upper() in clean or clean in key.upper():
            return var
    return VARIETIES["IPM 02-03"]

def list_all_varieties() -> List[VarietyModel]:
    return list(VARIETIES.values())
