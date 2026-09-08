"""
Green Gram (Vigna radiata) Climate & Environmental Requirements.
Authoritative source grounding: ICAR-IIPR, CRIDA, FAO-56.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class TemperatureThresholds(BaseModel):
    min_cardinal_c: float # minimum below which growth halts
    optimum_min_c: float
    optimum_max_c: float
    max_cardinal_c: float # maximum above which thermal injury occurs
    critical_heat_stress_c: float
    critical_cold_stress_c: float
    base_temperature_gdd_c: float = 10.0 # Base temperature for Growing Degree Days calculation
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED

class HumidityThresholds(BaseModel):
    optimum_min_rh: float # %
    optimum_max_rh: float # %
    high_disease_risk_rh: float # %
    low_rh_desiccation_threshold: float # %
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED

CLIMATE_KNOWLEDGE: Dict[str, Any] = {
    "temperature": TemperatureThresholds(
        min_cardinal_c=15.0,
        optimum_min_c=28.0,
        optimum_max_c=35.0,
        max_cardinal_c=42.0,
        critical_heat_stress_c=38.0, # At flowering/podding, temp > 38°C leads to pollen desiccation & flower drop
        critical_cold_stress_c=15.0, # Below 15°C vegetative growth stalls, flowering delayed
        base_temperature_gdd_c=10.0,
        source=get_source("ICAR-IIPR-2018")
    ),
    "humidity": HumidityThresholds(
        optimum_min_rh=55.0,
        optimum_max_rh=75.0,
        high_disease_risk_rh=82.0, # Prolonged RH > 82-85% triggers fungal conidia germination (Cercospora, Colletotrichum)
        low_rh_desiccation_threshold=35.0, # Low RH coupled with dry winds causes high VPD and rapid flower drop
        source=get_source("TNAU-AGRITECH-PULSES")
    ),
    "sunshine_photoperiod": {
        "bright_sunshine_hours_day_optimum": (7.0, 9.0),
        "effect_of_cloudy_weather": "Prolonged overcast weather (>3 consecutive days) reduces photosynthesis, induces flower drop, and promotes foliar blights.",
        "source": get_source("CRIDA-CONTINGENCY-2019")
    },
    "evapotranspiration_demand": {
        "normal_et0_mm_day": (3.5, 5.0),
        "high_et0_threshold_mm_day": 5.5, # Atmospheric evaporative demand >= 5.5 mm/day
        "extreme_et0_threshold_mm_day": 7.0, # Extreme summer demand in Northern/Central India
        "source": get_source("FAO-56-CROPWAT")
    },
    "seasonal_thermal_units": {
        "total_gdd_c_days": (950, 1150),
        "explanation": "Calculated as sum of [ (T_max + T_min)/2 - 10.0 ] from sowing to physiological maturity.",
        "source": get_source("ICAR-IIPR-2018")
    }
}

def evaluate_climate_risk(
    temperature: Optional[float],
    humidity: Optional[float],
    growth_stage: str
) -> Dict[str, Any]:
    """
    Evaluates temperature and humidity against validated Green Gram thresholds.
    Returns structured risk levels and agronomic advisories.
    """
    risks = []
    heat_stress = False
    cold_stress = False
    high_rh_disease_risk = False
    dry_wind_risk = False

    t_data = CLIMATE_KNOWLEDGE["temperature"]
    h_data = CLIMATE_KNOWLEDGE["humidity"]

    if temperature is not None:
        if temperature >= t_data.critical_heat_stress_c:
            heat_stress = True
            if growth_stage in ["Flowering", "Pod Formation"]:
                risks.append({
                    "type": "HEAT_STRESS_CRITICAL",
                    "severity": "HIGH",
                    "message": f"Ambient temperature ({temperature:.1f}°C) exceeds heat tolerance threshold (38.0°C). Risk of flower abortion and pollen desiccation.",
                    "mitigation": "Provide light evening irrigation to cool field microclimate. Avoid water deficit.",
                    "source": t_data.source
                })
            else:
                risks.append({
                    "type": "HEAT_STRESS_MODERATE",
                    "severity": "MODERATE",
                    "message": f"Ambient temperature ({temperature:.1f}°C) is elevated; monitor crop canopy for midday wilting.",
                    "mitigation": "Ensure root zone has adequate moisture.",
                    "source": t_data.source
                })
        elif temperature < t_data.critical_cold_stress_c:
            cold_stress = True
            risks.append({
                "type": "COLD_STRESS",
                "severity": "MODERATE",
                "message": f"Ambient temperature ({temperature:.1f}°C) is below base physiological activity threshold (15.0°C). Growth rate decelerated.",
                "mitigation": "Withhold irrigation during cold snaps to avoid subsoil chilling.",
                "source": t_data.source
            })

    if humidity is not None:
        if humidity >= h_data.high_disease_risk_rh:
            high_rh_disease_risk = True
            risks.append({
                "type": "HIGH_HUMIDITY_DISEASE_RISK",
                "severity": "HIGH" if temperature and 25.0 <= temperature <= 32.0 else "MODERATE",
                "message": f"Relative humidity ({humidity:.1f}%) exceeds 82%. Warm, moist canopy conditions strongly favor fungal foliar pathogens (Cercospora, Web blight).",
                "mitigation": "Avoid overhead sprinkling. Scout lower canopy for circular brown leaf lesions.",
                "source": h_data.source
            })
        elif humidity <= h_data.low_rh_desiccation_threshold and (temperature and temperature >= 35.0):
            dry_wind_risk = True
            risks.append({
                "type": "ATMOSPHERIC_DROUGHT_VPD",
                "severity": "HIGH",
                "message": f"Low relative humidity ({humidity:.1f}%) combined with high temperature ({temperature:.1f}°C) causes severe Vapor Pressure Deficit (VPD).",
                "mitigation": "Maintain soil moisture in the root zone to sustain high transpirational demand.",
                "source": t_data.source
            })

    return {
        "status": "ALERT" if any(r["severity"] == "HIGH" for r in risks) else ("WARNING" if risks else "OPTIMAL"),
        "heat_stress": heat_stress,
        "cold_stress": cold_stress,
        "high_rh_disease_risk": high_rh_disease_risk,
        "dry_wind_risk": dry_wind_risk,
        "risks": risks
    }
