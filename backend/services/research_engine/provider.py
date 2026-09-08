"""
Terravyn Research Engine: Research Providers & Source Tier Hierarchy
Implements AgriculturalResearchProvider abstraction with strict source ranking (Tier 1-4).
"""
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SourceTier:
    TIER_1_GOVT_INSTITUTES = 1    # ICAR, IIPR, SAUs, KVKs, FAO, Govt Depts
    TIER_2_PEER_REVIEWED = 2      # Scientific Journals, Systematic Reviews, DOIs
    TIER_3_EXTENSIONS = 3         # Research NGOs, Extension Publications
    TIER_4_OTHER = 4              # General blogs, unverified (never auto-promoted)


class ResearchSourceDTO(BaseModel):
    title: str
    organization: str
    url: Optional[str] = None
    domain: Optional[str] = None
    source_type: str  # GOVERNMENT, JOURNAL, EXTENSION, OTHER
    source_tier: int  # 1 to 4
    publication_date: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    doi: Optional[str] = None
    content_hash: Optional[str] = None
    abstract_text: str
    raw_claims: List[Dict[str, Any]] = Field(default_factory=list)


class AgriculturalResearchProvider(ABC):
    """Abstract interface for agricultural research sources."""

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 5,
        allowed_domains: Optional[List[str]] = None
    ) -> List[ResearchSourceDTO]:
        pass


class CuratedAgriculturalProvider(AgriculturalResearchProvider):
    """
    Curated repository of authoritative Tier 1 and Tier 2 agricultural literature
    from ICAR-IIPR, State Agricultural Universities, FAO, and peer-reviewed journals.
    """

    def __init__(self):
        self._corpus: List[ResearchSourceDTO] = self._init_corpus()

    def _init_corpus(self) -> List[ResearchSourceDTO]:
        corpus = [
            ResearchSourceDTO(
                title="ICAR-IIPR Mungbean Water Management & Irrigation Scheduling Bulletin",
                organization="ICAR - Indian Institute of Pulses Research, Kanpur",
                url="https://iipr.icar.gov.in/publications/mungbean-water-management-bulletin.pdf",
                domain="iipr.icar.gov.in",
                source_type="GOVERNMENT",
                source_tier=SourceTier.TIER_1_GOVT_INSTITUTES,
                publication_date="2021-04-15",
                doi=None,
                content_hash=hashlib.sha256(b"ICAR-IIPR-2021-PULSES").hexdigest(),
                abstract_text=(
                    "Under semi-arid conditions and coarse/sandy loam soils, Green Gram (Vigna radiata) exhibits "
                    "extreme sensitivity to moisture stress during flowering (30-35 DAS) and pod development (40-45 DAS). "
                    "Capacitive soil moisture below 24-26% in sandy loam triggers significant flower abortion. "
                    "A light irrigation of 25-35 mm applied at 50% flowering restores pod retention with zero waterlogging risk."
                ),
                raw_claims=[
                    {
                        "parameter": "flowering_irrigation_threshold",
                        "claim_text": "Apply light irrigation (25-35 mm) when capacitive moisture falls below 25% in sandy loam to prevent flower drop.",
                        "value_min": 24.0,
                        "value_max": 26.0,
                        "unit": "%",
                        "growth_stage": "flowering",
                        "soil_type": "sandy_loam",
                        "conditions": {"soil_type": "sandy_loam", "growth_stage": "flowering", "season": "summer/kharif"}
                    }
                ]
            ),
            ResearchSourceDTO(
                title="TNAU Agritech Portal: Pulses Irrigation under High Evaporative Demand",
                organization="Tamil Nadu Agricultural University (TNAU)",
                url="https://agritech.tnau.ac.in/agriculture/agri_irrigationmgt_greengram.html",
                domain="agritech.tnau.ac.in",
                source_type="GOVERNMENT",
                source_tier=SourceTier.TIER_1_GOVT_INSTITUTES,
                publication_date="2020-08-10",
                doi=None,
                content_hash=hashlib.sha256(b"TNAU-AGRITECH-PULSES-2020").hexdigest(),
                abstract_text=(
                    "When reference evapotranspiration (ET0) exceeds 5.5 mm/day combined with high temperatures (>35°C), "
                    "transpiration pull accelerates soil moisture depletion in the active root zone (0-30 cm). "
                    "During flowering, soil moisture must be maintained above 25% in light textured soils to preserve pollen viability."
                ),
                raw_claims=[
                    {
                        "parameter": "heat_stress_irrigation_deficit",
                        "claim_text": "High temperature (>35°C) and ET0 > 5.5 mm/day require timely irrigation to maintain soil moisture above 25%.",
                        "value_min": 25.0,
                        "value_max": 28.0,
                        "unit": "%",
                        "growth_stage": "flowering",
                        "soil_type": "sandy_loam",
                        "conditions": {"temperature": ">35C", "eto": ">5.5mm/day"}
                    }
                ]
            ),
            ResearchSourceDTO(
                title="Deficit Irrigation Strategies for Summer Mungbean in Semi-Arid Tropics",
                organization="Elsevier: Agricultural Water Management",
                url="https://doi.org/10.1016/j.agwat.2021.106894",
                domain="sciencedirect.com",
                source_type="JOURNAL",
                source_tier=SourceTier.TIER_2_PEER_REVIEWED,
                publication_date="2021-11-20",
                doi="10.1016/j.agwat.2021.106894",
                content_hash=hashlib.sha256(b"ELSEVIER-AGWAT-2021").hexdigest(),
                abstract_text=(
                    "Field experiments on Vigna radiata in sandy loam soils demonstrated that maintaining available soil moisture "
                    "at 25-28% during anthesis maximized water productivity (1.42 kg/m3). Delaying irrigation until moisture dropped "
                    "below 18% caused a 34% reduction in pod count per plant."
                ),
                raw_claims=[
                    {
                        "parameter": "anthesis_moisture_bound",
                        "claim_text": "Anthesis soil moisture threshold is 25-28% for sandy loam soils; severe deficit below 18% causes 34% pod drop.",
                        "value_min": 25.0,
                        "value_max": 28.0,
                        "unit": "%",
                        "growth_stage": "flowering",
                        "soil_type": "sandy_loam",
                        "conditions": {"growth_stage": "anthesis/flowering", "metric": "water_productivity"}
                    }
                ]
            ),
            ResearchSourceDTO(
                title="FAO Irrigation and Drainage Paper 33: Yield Response to Water (Grain Legumes)",
                organization="Food and Agriculture Organization (FAO)",
                url="https://www.fao.org/land-water/databases-and-software/crop-information/grain-legumes/en/",
                domain="fao.org",
                source_type="GOVERNMENT",
                source_tier=SourceTier.TIER_1_GOVT_INSTITUTES,
                publication_date="2018-01-01",
                doi=None,
                content_hash=hashlib.sha256(b"FAO-PAPER-33-LEGUMES").hexdigest(),
                abstract_text=(
                    "Grain legumes (including Vigna radiata) possess yield response factor Ky > 0.85 during flowering. "
                    "Irrigation should not be applied if heavy rainfall is imminent as surface ponding exceeding 24 hours "
                    "leads to root asphyxia and yield reduction up to 40%."
                ),
                raw_claims=[
                    {
                        "parameter": "rainfall_suspension_threshold",
                        "claim_text": "Suspend irrigation when >= 5mm rain is expected to avoid root hypoxia in grain legumes.",
                        "value_min": 5.0,
                        "value_max": 10.0,
                        "unit": "mm",
                        "growth_stage": "all",
                        "soil_type": "all",
                        "conditions": {"forecast_rain": ">=5mm"}
                    }
                ]
            ),
            ResearchSourceDTO(
                title="Super-Organic Miracle Yields Blog: Double Your Green Gram",
                organization="Commercial Farming Blog",
                url="https://superfarms.example.com/blog/mungbean-secret",
                domain="superfarms.example.com",
                source_type="OTHER",
                source_tier=SourceTier.TIER_4_OTHER,
                publication_date="2023-05-12",
                doi=None,
                content_hash=hashlib.sha256(b"TIER4-COMMERCIAL-BLOG").hexdigest(),
                abstract_text=(
                    "Irrigate your green gram every day regardless of soil moisture to double your pods. "
                    "Use our proprietary tonic for best results."
                ),
                raw_claims=[
                    {
                        "parameter": "daily_irrigation_claim",
                        "claim_text": "Irrigate daily regardless of moisture levels.",
                        "value_min": 1.0,
                        "value_max": 1.0,
                        "unit": "daily",
                        "growth_stage": "all",
                        "soil_type": "any",
                        "conditions": {}
                    }
                ]
            ),
            ResearchSourceDTO(
                title="Contradictory Pulse Agronomy Study (Low-Moisture Tolerance Claim)",
                organization="Alternative Agronomy Paper",
                url="https://alt-agri.example.org/papers/severe-stress-mung.pdf",
                domain="alt-agri.example.org",
                source_type="JOURNAL",
                source_tier=SourceTier.TIER_2_PEER_REVIEWED,
                publication_date="2019-03-01",
                doi="10.9999/altagri.2019.001",
                content_hash=hashlib.sha256(b"CONTRADICTION-STUDY-2019").hexdigest(),
                abstract_text=(
                    "Recommends withholding all irrigation during flowering until soil moisture reaches 10% "
                    "to force deeper taproot penetration in Green Gram, directly conflicting with standard ICAR guidelines."
                ),
                raw_claims=[
                    {
                        "parameter": "flowering_irrigation_threshold",
                        "claim_text": "Withhold irrigation until soil moisture drops to 10% during flowering.",
                        "value_min": 10.0,
                        "value_max": 12.0,
                        "unit": "%",
                        "growth_stage": "flowering",
                        "soil_type": "sandy_loam",
                        "conditions": {"growth_stage": "flowering", "strategy": "extreme_stress"}
                    }
                ]
            )
        ]
        return corpus

    def search(
        self,
        query: str,
        max_results: int = 5,
        allowed_domains: Optional[List[str]] = None
    ) -> List[ResearchSourceDTO]:
        """Search curated corpus using keyword token overlap."""
        tokens = set(query.lower().replace(",", " ").split())
        scored_results = []

        for source in self._corpus:
            if allowed_domains and source.domain not in allowed_domains:
                continue

            text_body = f"{source.title} {source.organization} {source.abstract_text}".lower()
            overlap = sum(1 for token in tokens if token in text_body)

            if overlap > 0:
                # Rank primarily by source tier (lower number = higher priority), then by keyword overlap
                rank_score = (5 - source.source_tier) * 20 + overlap
                scored_results.append((rank_score, source))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored_results[:max_results]]
