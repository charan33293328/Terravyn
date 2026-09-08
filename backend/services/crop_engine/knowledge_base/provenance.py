"""
Terravyn Agronomic Provenance & Scientific Citation Registry.
Tracks the provenance of every agronomic value, rule, and threshold.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class KnowledgeStatus(str, Enum):
    VALIDATED = "VALIDATED"                 # Supported by published ICAR/SAU research
    PRELIMINARY = "PRELIMINARY"             # Agronomic estimate requiring broader field verification
    EXPERIMENTAL = "EXPERIMENTAL"           # In-situ sensor calibration specific to Terravyn hardware

class SourceReference(BaseModel):
    source_id: str
    title: str
    organization: str
    publication_year: Optional[int] = None
    url: Optional[str] = None
    citation_type: str = "ICAR / SAU Official Package of Practices"
    notes: Optional[str] = None

# Master Agricultural Citations Catalog
SOURCES: Dict[str, SourceReference] = {
    "ICAR-IIPR-2018": SourceReference(
        source_id="ICAR-IIPR-2018",
        title="Package of Practices for Pulses: Mungbean (Green Gram)",
        organization="ICAR - Indian Institute of Pulses Research (IIPR), Kanpur",
        publication_year=2018,
        url="https://iipr.icar.gov.in",
        citation_type="National Research Institute Bulletin",
        notes="Primary national baseline for pulse agronomy, critical growth stages, and disease resistance."
    ),
    "ICAR-IIPR-VARIETIES-2020": SourceReference(
        source_id="ICAR-IIPR-VARIETIES-2020",
        title="Varietal Directory of Pulses: Mungbean Varieties Released in India",
        organization="ICAR - Indian Institute of Pulses Research (IIPR), Kanpur",
        publication_year=2020,
        url="https://iipr.icar.gov.in/varieties",
        citation_type="Official Varietal Gazette",
        notes="Definitive duration, parentage, yield potential, and disease reaction for Indian mungbean varieties."
    ),
    "IARI-PUSA-2019": SourceReference(
        source_id="IARI-PUSA-2019",
        title="Cultivation of Summer and Spring Mungbean in North and Central India",
        organization="ICAR - Indian Agricultural Research Institute (IARI), New Delhi",
        publication_year=2019,
        url="https://www.iari.res.in",
        citation_type="ICAR Institute Technical Bulletin",
        notes="Agrotechnology for extra-early varieties (Pusa Vishal) and summer irrigation management."
    ),
    "TNAU-AGRITECH-PULSES": SourceReference(
        source_id="TNAU-AGRITECH-PULSES",
        title="Crop Production Guide: Pulses - Greengram (Vigna radiata)",
        organization="Tamil Nadu Agricultural University (TNAU), Coimbatore",
        publication_year=2020,
        url="https://agritech.tnau.ac.in/agriculture/agri_greengram.html",
        citation_type="State Agricultural University Extension Guide",
        notes="Foliar nutrition (2% DAP / TNAU Pulse Wonder), spacing, weed management, and microclimate thresholds."
    ),
    "ANGRAU-PULSES-2021": SourceReference(
        source_id="ANGRAU-PULSES-2021",
        title="Vyavasaya Panchangam: Pulses Production Technologies for Andhra Pradesh",
        organization="Acharya N.G. Ranga Agricultural University (ANGRAU), Guntur, AP",
        publication_year=2021,
        url="https://angrau.ac.in",
        citation_type="State Agricultural University Package of Practices",
        notes="Cultivation in Coastal AP and Rayalaseema, upland kharif and rice fallow management."
    ),
    "CCS-HAU-MH421-2017": SourceReference(
        source_id="CCS-HAU-MH421-2017",
        title="Package of Practices for Kharif & Summer Crops: Moong MH 421",
        organization="Chaudhary Charan Singh Haryana Agricultural University (CCS HAU), Hisar",
        publication_year=2017,
        url="https://hau.ac.in",
        citation_type="SAU Production Bulletin",
        notes="Short-duration summer crop water management and synchrony of maturity."
    ),
    "PAU-SML668-2018": SourceReference(
        source_id="PAU-SML668-2018",
        title="Package of Practices for Crops of Punjab: Pulses",
        organization="Punjab Agricultural University (PAU), Ludhiana",
        publication_year=2018,
        url="https://www.pau.edu",
        citation_type="SAU Package of Practices",
        notes="SML 668 bold seeded agronomy, irrigation intervals in sandy loams."
    ),
    "FAO-56-CROPWAT": SourceReference(
        source_id="FAO-56-CROPWAT",
        title="Crop Evapotranspiration - Guidelines for Computing Crop Water Requirements (FAO Irrigation and Drainage Paper 56)",
        organization="Food and Agriculture Organization of the United Nations (FAO), Rome",
        publication_year=1998,
        url="https://www.fao.org/land-water/databases-and-software/cropwat",
        citation_type="International Irrigation Standard",
        notes="Single and dual crop coefficients (Kc) for mungbean: initial (0.40), mid-season (1.05), end-season (0.50)."
    ),
    "FAO-33-YIELD-WATER": SourceReference(
        source_id="FAO-33-YIELD-WATER",
        title="Yield Response to Water (FAO Irrigation and Drainage Paper 33)",
        organization="Food and Agriculture Organization of the United Nations (FAO), Rome",
        publication_year=1979,
        url="https://www.fao.org/land-water",
        citation_type="International Agrometeorological Standard",
        notes="Yield response factor Ky for grain legumes, sensitivity during flowering and pod development."
    ),
    "CRIDA-CONTINGENCY-2019": SourceReference(
        source_id="CRIDA-CONTINGENCY-2019",
        title="Contingency Crop Planning for Pulses in Drought and Waterlogging Situations",
        organization="ICAR - Central Research Institute for Dryland Agriculture (CRIDA), Hyderabad",
        publication_year=2019,
        url="https://www.crida.in",
        citation_type="National Dryland Research Bulletin",
        notes="Extreme weather mitigation: surface drainage, life-saving irrigation, anti-transpirants."
    ),
    "DPD-GOI-2022": SourceReference(
        source_id="DPD-GOI-2022",
        title="Pulses in India: Retrospect & Prospects",
        organization="Directorate of Pulses Development, Dept of Agriculture & Farmers Welfare, Ministry of Agriculture, Govt of India",
        publication_year=2022,
        url="https://dpd.dacnet.nic.in",
        citation_type="Government of India Technical Monograph",
        notes="National production statistics, agro-climatic zones, and recommended cropping systems."
    ),
    "TERRAVYN-EXPERIMENTAL": SourceReference(
        source_id="TERRAVYN-EXPERIMENTAL",
        title="Terravyn In-Situ Precision Agro-Telemetry Calibration Protocol",
        organization="Terravyn Agronomic Research Lab",
        publication_year=2026,
        url="https://terravyn.com/docs/sensor-calibration",
        citation_type="In-Situ Sensor Framework",
        notes="Capacitive probe thresholds subject to dual-plot local soil calibration."
    )
}

class ProvenanceItem(BaseModel):
    parameter: str
    crop: str = "Green Gram (Vigna radiata)"
    value: Any
    unit: str
    condition: Optional[str] = None
    growth_stage: Optional[str] = "ALL"
    soil_type: Optional[str] = "ALL"
    source: SourceReference
    confidence: ConfidenceLevel
    status: KnowledgeStatus
    notes: Optional[str] = None

def get_source(source_id: str) -> SourceReference:
    return SOURCES.get(source_id, SOURCES["TERRAVYN-EXPERIMENTAL"])
