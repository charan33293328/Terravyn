"""
Green Gram (Vigna radiata / Moong) Agronomic Configuration Model.
Central repository for crop growth stages, variety characteristics, and moisture sensitivities.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date

# Standard Growth Stages
STAGE_SOWING = "Sowing"
STAGE_GERMINATION = "Germination"
STAGE_SEEDLING = "Seedling"
STAGE_VEGETATIVE = "Vegetative"
STAGE_FLOWERING = "Flowering"
STAGE_POD_FORMATION = "Pod Formation"
STAGE_POD_FILLING = "Pod Filling"
STAGE_MATURITY = "Maturity / Harvest"

ALL_STAGES = [
    STAGE_SOWING,
    STAGE_GERMINATION,
    STAGE_SEEDLING,
    STAGE_VEGETATIVE,
    STAGE_FLOWERING,
    STAGE_POD_FORMATION,
    STAGE_POD_FILLING,
    STAGE_MATURITY,
]

# Variety profiles with maturity cycle days (ICAR-IIPR references)
VARIETY_PROFILES = {
    "IPM 02-03": {
        "duration_days": 63,
        "description": "Short duration, resistant to Mungbean Yellow Mosaic Virus (MYMV).",
        "stage_durations": {
            STAGE_SOWING: (0, 0),
            STAGE_GERMINATION: (1, 5),
            STAGE_SEEDLING: (6, 14),
            STAGE_VEGETATIVE: (15, 27),
            STAGE_FLOWERING: (28, 40),
            STAGE_POD_FORMATION: (41, 50),
            STAGE_POD_FILLING: (51, 58),
            STAGE_MATURITY: (59, 65)
        }
    },
    "SML 668": {
        "duration_days": 60,
        "description": "Synchronous maturing variety, bold seeded, widely grown in summer.",
        "stage_durations": {
            STAGE_SOWING: (0, 0),
            STAGE_GERMINATION: (1, 4),
            STAGE_SEEDLING: (5, 13),
            STAGE_VEGETATIVE: (14, 25),
            STAGE_FLOWERING: (26, 38),
            STAGE_POD_FORMATION: (39, 48),
            STAGE_POD_FILLING: (49, 56),
            STAGE_MATURITY: (57, 62)
        }
    },
    "PUSA VISHAL": {
        "duration_days": 65,
        "description": "Extra early, bold seeded variety, suitable for spring/summer.",
        "stage_durations": {
            STAGE_SOWING: (0, 0),
            STAGE_GERMINATION: (1, 5),
            STAGE_SEEDLING: (6, 15),
            STAGE_VEGETATIVE: (16, 28),
            STAGE_FLOWERING: (29, 42),
            STAGE_POD_FORMATION: (43, 52),
            STAGE_POD_FILLING: (53, 60),
            STAGE_MATURITY: (61, 68)
        }
    },
    "MH 421": {
        "duration_days": 58,
        "description": "Early maturing summer/kharif variety developed by CCS HAU.",
        "stage_durations": {
            STAGE_SOWING: (0, 0),
            STAGE_GERMINATION: (1, 4),
            STAGE_SEEDLING: (5, 12),
            STAGE_VEGETATIVE: (13, 24),
            STAGE_FLOWERING: (25, 36),
            STAGE_POD_FORMATION: (37, 46),
            STAGE_POD_FILLING: (47, 54),
            STAGE_MATURITY: (55, 60)
        }
    },
    "DEFAULT": {
        "duration_days": 65,
        "description": "Standard baseline Green Gram profile.",
        "stage_durations": {
            STAGE_SOWING: (0, 0),
            STAGE_GERMINATION: (1, 5),
            STAGE_SEEDLING: (6, 15),
            STAGE_VEGETATIVE: (16, 28),
            STAGE_FLOWERING: (29, 42),
            STAGE_POD_FORMATION: (43, 52),
            STAGE_POD_FILLING: (53, 62),
            STAGE_MATURITY: (63, 70)
        }
    }
}

# Agronomic moisture sensitivities and irrigation management rules per stage
STAGE_AGRONOMY = {
    STAGE_SOWING: {
        "moisture_sensitivity": "Low",
        "crop_coefficient_kc": 0.40,
        "waterlogging_risk": "High",
        "description": "Pre-sowing irrigation (palewa) should ensure adequate seedbed moisture. Avoid sowing in standing water.",
        "irrigation_advice": "Ensure field capacity at sowing; avoid surface ponding."
    },
    STAGE_GERMINATION: {
        "moisture_sensitivity": "Medium",
        "crop_coefficient_kc": 0.45,
        "waterlogging_risk": "Severe",
        "description": "Emergence occurs in 3–5 days. Crust formation or water stagnation impairs germination.",
        "irrigation_advice": "Do not flood; surface crusting should be broken with light hoeing if needed."
    },
    STAGE_SEEDLING: {
        "moisture_sensitivity": "Low",
        "crop_coefficient_kc": 0.50,
        "waterlogging_risk": "Severe",
        "description": "Root development phase. Mild moisture stress encourages deeper tap root growth.",
        "irrigation_advice": "Withhold irrigation to encourage deep root penetration unless soil is desiccated."
    },
    STAGE_VEGETATIVE: {
        "moisture_sensitivity": "Medium",
        "crop_coefficient_kc": 0.75,
        "waterlogging_risk": "Moderate",
        "description": "Branching and nodulation phase. Nitrogen fixation active.",
        "irrigation_advice": "Maintain moderate soil moisture. One light irrigation if soil moisture drops significantly."
    },
    STAGE_FLOWERING: {
        "moisture_sensitivity": "CRITICAL",
        "crop_coefficient_kc": 1.05,
        "waterlogging_risk": "Moderate",
        "description": "First critical stage. Moisture stress causes massive flower drop and reduces pod count by 30-40%.",
        "irrigation_advice": "Ensure adequate moisture. Avoid moisture stress at all costs during peak flower opening."
    },
    STAGE_POD_FORMATION: {
        "moisture_sensitivity": "CRITICAL",
        "crop_coefficient_kc": 1.10,
        "waterlogging_risk": "Moderate",
        "description": "Second critical stage. Water deficit causes pod abortion and poor ovule fertilization.",
        "irrigation_advice": "Maintain moisture between 45-65% field capacity. Irrigation here directly protects final grain yield."
    },
    STAGE_POD_FILLING: {
        "moisture_sensitivity": "Medium-High",
        "crop_coefficient_kc": 0.85,
        "waterlogging_risk": "Moderate",
        "description": "Grain development and seed enlargement phase.",
        "irrigation_advice": "Light irrigation if topsoil is completely dry; prevent premature senescence."
    },
    STAGE_MATURITY: {
        "moisture_sensitivity": "None / Detrimental",
        "crop_coefficient_kc": 0.50,
        "waterlogging_risk": "Severe",
        "description": "Pods turn black/brown. Moisture during this stage causes pod shattering, vivipary, and seed rot.",
        "irrigation_advice": "STRICTLY CEASE IRRIGATION 10–12 days prior to harvest to ensure uniform pod drying."
    }
}


def get_variety_profile(variety_name: Optional[str]) -> Dict[str, Any]:
    if not variety_name:
        return VARIETY_PROFILES["DEFAULT"]
    
    clean_name = variety_name.strip().upper()
    for key, profile in VARIETY_PROFILES.items():
        if key.upper() in clean_name or clean_name in key.upper():
            return profile
            
    return VARIETY_PROFILES["DEFAULT"]


def determine_growth_stage(
    sowing_date: Optional[datetime],
    variety_name: Optional[str] = None,
    manual_override: Optional[str] = None,
    current_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Determine current crop growth stage from calendar days, variety timeline,
    or farmer's manual observation override.
    """
    if manual_override and manual_override in ALL_STAGES:
        return {
            "stage": manual_override,
            "age_days": None,
            "is_manual": True,
            "agronomy": STAGE_AGRONOMY.get(manual_override, {})
        }

    if not sowing_date:
        # Default baseline if sowing date unknown
        return {
            "stage": STAGE_VEGETATIVE,
            "age_days": None,
            "is_manual": False,
            "agronomy": STAGE_AGRONOMY[STAGE_VEGETATIVE]
        }

    ref_date = current_date or date.today()
    s_date = sowing_date.date() if isinstance(sowing_date, datetime) else sowing_date
    age_days = max(0, (ref_date - s_date).days)

    profile = get_variety_profile(variety_name)
    stage_durations = profile["stage_durations"]

    selected_stage = STAGE_MATURITY
    for stage, (start_day, end_day) in stage_durations.items():
        if start_day <= age_days <= end_day:
            selected_stage = stage
            break

    return {
        "stage": selected_stage,
        "age_days": age_days,
        "is_manual": False,
        "agronomy": STAGE_AGRONOMY.get(selected_stage, {})
    }
