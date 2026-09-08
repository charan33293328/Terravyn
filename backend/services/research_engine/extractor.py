"""
Terravyn Research Engine: Structured Evidence Extractor
Converts unstructured/semi-structured research sources into structured EvidenceClaims
preserving numerical bounds, units, conditions, and scientific context.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provider import ResearchSourceDTO


class ExtractedEvidenceClaim(BaseModel):
    source_url: Optional[str]
    source_title: str
    organization: str
    source_tier: int
    parameter: str
    claim_text: str
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    unit: Optional[str] = None
    condition_context: Dict[str, Any] = {}
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    applicability: str = "Specific to described environmental conditions"


class EvidenceExtractor:
    def extract_claims(self, source: ResearchSourceDTO) -> List[ExtractedEvidenceClaim]:
        """
        Extract structured claims from a research source.
        Preserves original values, units, and environmental conditions.
        """
        extracted = []
        for raw in source.raw_claims:
            claim = ExtractedEvidenceClaim(
                source_url=source.url,
                source_title=source.title,
                organization=source.organization,
                source_tier=source.source_tier,
                parameter=raw.get("parameter", "agronomic_recommendation"),
                claim_text=raw.get("claim_text", ""),
                value_min=raw.get("value_min"),
                value_max=raw.get("value_max"),
                unit=raw.get("unit"),
                condition_context=raw.get("conditions", {}),
                growth_stage=raw.get("growth_stage"),
                soil_type=raw.get("soil_type"),
                applicability=f"Grounded by {source.organization} ({source.source_type})"
            )
            extracted.append(claim)

        return extracted
