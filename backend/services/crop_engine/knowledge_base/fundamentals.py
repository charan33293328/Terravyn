"""
Green Gram (Vigna radiata) Fundamentals & Botanical Classification.
Authoritative source grounding: ICAR-IIPR & Directorate of Pulses Development (DPD).
"""

from typing import Dict, Any, List
from .provenance import ProvenanceItem, ConfidenceLevel, KnowledgeStatus, get_source

CROP_FUNDAMENTALS: Dict[str, Any] = {
    "crop_id": "green_gram",
    "botanical_name": "Vigna radiata (L.) R. Wilczek",
    "family": "Fabaceae (Leguminosae)",
    "subfamily": "Papilionoideae",
    "tribe": "Phaseoleae",
    "common_names": {
        "english": ["Green Gram", "Mung Bean", "Golden Gram"],
        "hindi": ["Moong", "Mung"],
        "telugu": ["Pesalu"],
        "tamil": ["Pasipayiru"],
        "kannada": ["Hesaru Kaalu"],
        "marathi": ["Mug"],
        "bengali": ["Mug Dal"]
    },
    "crop_classification": "Warm-season, short-duration food grain legume / pulse",
    "duration_range_days": (55, 75),
    "photosensitivity": "Predominantly day-neutral to quantitative short-day; modern improved varieties are photo-insensitive.",
    "symbiotic_nitrogen_fixation": {
        "rhizobium_species": "Bradyrhizobium japonicum / Rhizobium leguminosarum bv. phaseoli",
        "approx_n_fixed_kg_ha": (30, 50),
        "residual_soil_n_benefit_kg_ha": (15, 25),
        "source": get_source("ICAR-IIPR-2018")
    },
    "major_growing_seasons": [
        {"season": "Kharif", "sowing_window": "June to July (onset of South-West Monsoon)"},
        {"season": "Spring", "sowing_window": "Mid-February to March (post-wheat/potato harvest)"},
        {"season": "Summer", "sowing_window": "March to April (irrigated cropping catch crop)"},
        {"season": "Rabi (Rice Fallows)", "sowing_window": "November to December (coastal peninsular India)"}
    ],
    "national_importance_india": {
        "share_in_pulses_area": "Approx. 16-18% of national pulse acreage",
        "primary_states": ["Madhya Pradesh", "Rajasthan", "Maharashtra", "Andhra Pradesh", "Karnataka", "Gujarat", "Odisha", "Tamil Nadu", "Punjab", "Haryana"]
    }
}

FUNDAMENTALS_PROVENANCE: List[ProvenanceItem] = [
    ProvenanceItem(
        parameter="botanical_classification",
        value="Vigna radiata (L.) R. Wilczek, Fabaceae",
        unit="Taxonomy",
        source=get_source("ICAR-IIPR-2018"),
        confidence=ConfidenceLevel.HIGH,
        status=KnowledgeStatus.VALIDATED,
        notes="Standard pulse botanical taxonomy according to ICAR-IIPR."
    ),
    ProvenanceItem(
        parameter="symbiotic_n_fixation",
        value={"n_fixed_min": 30, "n_fixed_max": 50, "residual_benefit": 20},
        unit="kg N/ha",
        source=get_source("ICAR-IIPR-2018"),
        confidence=ConfidenceLevel.HIGH,
        status=KnowledgeStatus.VALIDATED,
        notes="Enriches soil fertility when effectively nodulated by Rhizobium."
    )
]
