"""
Green Gram (Vigna radiata) Regional Agro-Climatic Profiles.
Authoritative source grounding: Directorate of Pulses Development (DPD, GOI), ANGRAU, TNAU, PAU.
Enables regional adaptation without hardcoding single-state assumptions into generic crop rules.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class RegionalProfile(BaseModel):
    zone_id: str
    zone_name: str
    states_covered: List[str]
    primary_cropping_systems: List[str]
    dominant_seasons: List[str]
    dominant_soil_types: List[str]
    regional_water_management: str
    priority_disease_pest_risks: List[str]
    recommended_varieties: List[str]
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED

REGIONAL_PROFILES: Dict[str, RegionalProfile] = {
    "SOUTHERN_PENINSULAR": RegionalProfile(
        zone_id="ZONE_SZ_PENINSULAR",
        zone_name="Southern Peninsular Zone (AP, Telangana, Tamil Nadu, Karnataka)",
        states_covered=["Andhra Pradesh", "Telangana", "Tamil Nadu", "Karnataka"],
        primary_cropping_systems=[
            "Rice - Green Gram (Rice Fallow zero-till system)",
            "Kharif upland pulse - Rabi sorghum / chickpea",
            "Summer irrigated Green Gram"
        ],
        dominant_seasons=["Rabi (Rice Fallow: Nov-Dec)", "Kharif (June-July)", "Summer (Feb-March)"],
        dominant_soil_types=["Alluvial delta soils", "Red sandy loam", "Black cotton soil"],
        regional_water_management="In rice fallows, relies entirely on residual moisture; excess irrigation strictly prohibited. In upland summer, 3-4 light irrigations required.",
        priority_disease_pest_risks=["MYMV (severe in summer)", "Powdery Mildew (rabi)", "Thrips", "Spotted pod borer"],
        recommended_varieties=["WGG 42", "CO 8", "IPM 02-03", "IPM 205-7 (VIRAT)"],
        source=get_source("ANGRAU-PULSES-2021")
    ),
    "NORTH_WEST_PLAINS": RegionalProfile(
        zone_id="ZONE_NWPZ_PLAINS",
        zone_name="North-West Plain Zone (Punjab, Haryana, Western UP, Rajasthan)",
        states_covered=["Punjab", "Haryana", "Uttar Pradesh", "Rajasthan", "Delhi"],
        primary_cropping_systems=[
            "Rice - Wheat - Summer Moong (tight 60-day catch crop window)",
            "Potato - Summer Moong - Maize",
            "Kharif pearl millet - Moong"
        ],
        dominant_seasons=["Summer (April-June post-wheat)", "Kharif (July-October)"],
        dominant_soil_types=["Alluvial loam", "Sandy loam", "Desert soils (Rajasthan)"],
        regional_water_management="Summer moong requires 3-5 irrigations due to high evaporation (ET0 > 6 mm/day). Last irrigation must be withheld by 50-52 DAS.",
        priority_disease_pest_risks=["MYMV", "Cercospora leaf spot", "Whitefly", "Blister beetle"],
        recommended_varieties=["SML 668", "MH 421", "PUSA VISHAL", "IPM 205-7 (VIRAT)"],
        source=get_source("PAU-SML668-2018")
    ),
    "CENTRAL_ZONE": RegionalProfile(
        zone_id="ZONE_CZ_CENTRAL",
        zone_name="Central Zone (Madhya Pradesh, Maharashtra, Gujarat)",
        states_covered=["Madhya Pradesh", "Maharashtra", "Gujarat"],
        primary_cropping_systems=[
            "Soybean - Moong / Wheat",
            "Cotton + Moong intercropping (1:1 or 1:2)",
            "Summer irrigated Moong"
        ],
        dominant_seasons=["Kharif (June-September)", "Summer (March-May)"],
        dominant_soil_types=["Deep Black soils (Vertisols)", "Medium black soils"],
        regional_water_management="In heavy black soils, drainage is the primary risk factor. Sowing on Broad Bed Furrow (BBF) or ridges is strongly advised to prevent waterlogging.",
        priority_disease_pest_risks=["Rhizoctonia Web Blight", "Macrophomina Root Rot", "Gram Pod Borer"],
        recommended_varieties=["IPM 02-03", "IPM 205-7 (VIRAT)", "PUSA VISHAL"],
        source=get_source("DPD-GOI-2022")
    )
}

def get_regional_profile(region_name: Optional[str]) -> RegionalProfile:
    if not region_name:
        return REGIONAL_PROFILES["SOUTHERN_PENINSULAR"]
    clean = region_name.strip().upper()
    for key, prof in REGIONAL_PROFILES.items():
        if any(state.upper() in clean for state in prof.states_covered) or key in clean:
            return prof
    return REGIONAL_PROFILES["SOUTHERN_PENINSULAR"]
