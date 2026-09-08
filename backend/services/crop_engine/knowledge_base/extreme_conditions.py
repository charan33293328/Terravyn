"""
Green Gram (Vigna radiata) Extreme Weather & Abiotic Stress Protocols.
Authoritative source grounding: ICAR-CRIDA "Contingency Crop Planning for Pulses", ICAR-IIPR.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .provenance import SourceReference, get_source, ConfidenceLevel, KnowledgeStatus

class ExtremeConditionProtocol(BaseModel):
    condition_id: str
    condition_name: str
    meteorological_trigger: str
    vulnerable_stages: List[str]
    physiological_impact: str
    risk_level: str # "MODERATE", "HIGH", "CRITICAL"
    field_indicators_to_monitor: List[str]
    immediate_mitigation_action: str
    post_event_recovery: str
    source: SourceReference
    status: KnowledgeStatus = KnowledgeStatus.VALIDATED

EXTREME_PROTOCOLS: Dict[str, ExtremeConditionProtocol] = {
    "WATERLOGGING_HEAVY_RAIN": ExtremeConditionProtocol(
        condition_id="EXT-GG-WATERLOGGING-01",
        condition_name="Excess Rainfall & Surface Water Stagnation",
        meteorological_trigger="Rainfall > 40 mm in 24h or continuous standing water > 12 hours",
        vulnerable_stages=["ALL", "Seedling", "Vegetative", "Flowering", "Pod Formation"],
        physiological_impact="Severe rhizosphere hypoxia (oxygen depletion); cessation of root mitochondrial ATP generation; death of Bradyrhizobium nodules; rapid root rot infection.",
        risk_level="CRITICAL",
        field_indicators_to_monitor=[
            "Standing water in furrows or plot depressions",
            "Chlorosis (yellowing) and leaf drooping within 24-48 hours",
            "Darkened, decaying root tips without white feeder roots"
        ],
        immediate_mitigation_action="Drain excess water out of the field immediately by cutting drainage channels across low-lying corners. Ensure water evacuates within 12-24 hours.",
        post_event_recovery="Once topsoil is workable, spray 1% Urea or 2% DAP foliar spray to provide emergency nitrogen until damaged nodules regenerate.",
        source=get_source("CRIDA-CONTINGENCY-2019")
    ),
    "HEAT_WAVE_REPRODUCTIVE": ExtremeConditionProtocol(
        condition_id="EXT-GG-HEAT-WAVE-02",
        condition_name="Severe Heat Wave during Flowering & Pod Set",
        meteorological_trigger="Maximum temperature >= 38.0°C for >= 2 consecutive days",
        vulnerable_stages=["Flowering", "Pod Formation"],
        physiological_impact="High temperature induces pollen sterility, stigmatic desiccation, accelerated flower petal senescence, and flower drop (up to 50% yield loss).",
        risk_level="CRITICAL",
        field_indicators_to_monitor=[
            "Abscised (dropped) yellow flowers lying on soil surface",
            "Shriveled or aborted floral buds",
            "Midday temporary leaf folding / wilting"
        ],
        immediate_mitigation_action="Provide light, frequent evening irrigation (sprinkler or light furrow) to increase humidity and cool field canopy microclimate.",
        post_event_recovery="Foliar spray of 1% Potassium Nitrate (KNO3) or 2% DAP in early morning hours to assist osmoregulation and cell membrane stability.",
        source=get_source("ICAR-IIPR-2018")
    ),
    "DROUGHT_DRY_SPELL": ExtremeConditionProtocol(
        condition_id="EXT-GG-DROUGHT-03",
        condition_name="Prolonged Dry Spell / Meteorological Drought",
        meteorological_trigger="No rain for > 15 days in rainfed kharif or soil moisture < 20% ASM",
        vulnerable_stages=["Vegetative", "Flowering", "Pod Formation"],
        physiological_impact="Stomatal closure, reduced transpiration and CO2 assimilation; premature leaf senescence; forced early flowering with dwarf stature and poor podding.",
        risk_level="HIGH",
        field_indicators_to_monitor=[
            "Leaf rolling during morning hours",
            "Loss of turgor in terminal shoots",
            "Deep soil cracking"
        ],
        immediate_mitigation_action="Apply one life-saving protective irrigation (30-35 mm) using micro-irrigation (drip/sprinkler) or alternate-furrow irrigation.",
        post_event_recovery="Apply straw/crop residue mulch between rows (3-4 t/ha) to conserve residual soil moisture.",
        source=get_source("CRIDA-CONTINGENCY-2019")
    ),
    "COLD_SNAP_DELAY": ExtremeConditionProtocol(
        condition_id="EXT-GG-COLD-SNAP-04",
        condition_name="Low Temperature Shock / Cold Snap",
        meteorological_trigger="Minimum temperature < 15.0°C during early vegetative or spring crop",
        vulnerable_stages=["Germination", "Seedling", "Vegetative"],
        physiological_impact="Metabolic deceleration; delayed emergence; poor phosphorus uptake; purple pigmentation on leaves.",
        risk_level="MODERATE",
        field_indicators_to_monitor=[
            "Stunted seedling growth",
            "Purplish bronzing on leaf undersides",
            "Slow emergence taking > 8 days"
        ],
        immediate_mitigation_action="Withhold cold irrigation water during cold wave. Light shallow hoeing around plants to aerate soil.",
        post_event_recovery="Normal growth resumes spontaneously once day temperatures exceed 22-25°C.",
        source=get_source("IARI-PUSA-2019")
    ),
    "PROLONGED_OVERCAST_WEATHER": ExtremeConditionProtocol(
        condition_id="EXT-GG-OVERCAST-05",
        condition_name="Prolonged Cloudy / Overcast Weather",
        meteorological_trigger="> 3 consecutive days with < 3 hours sunshine/day and RH > 85%",
        vulnerable_stages=["Flowering", "Pod Formation"],
        physiological_impact="Low photosynthetically active radiation (PAR) restricts assimilate supply, resulting in massive flower abscission. Skyrocketing fungal foliar disease pressure.",
        risk_level="HIGH",
        field_indicators_to_monitor=[
            "Flower drop without water stress",
            "Water-soaked spotting on foliage (early blight / Cercospora)"
        ],
        immediate_mitigation_action="Suspend all irrigation. Do not apply nitrogenous fertilizers.",
        post_event_recovery="Scout field for fungal spotting; apply prophylactic biological or copper fungicide if lesions appear.",
        source=get_source("CRIDA-CONTINGENCY-2019")
    )
}

def evaluate_extreme_conditions(
    temperature: Optional[float],
    humidity: Optional[float],
    rainfall_forecast: Optional[float],
    growth_stage: str,
    soil_moisture: Optional[float]
) -> List[Dict[str, Any]]:
    """
    Checks live sensor and weather inputs against extreme condition triggers.
    """
    active_protocols = []

    # 1. Rain / Waterlogging risk
    if rainfall_forecast and rainfall_forecast >= 40.0:
        proto = EXTREME_PROTOCOLS["WATERLOGGING_HEAVY_RAIN"]
        active_protocols.append({
            "condition": proto.condition_name,
            "risk_level": proto.risk_level,
            "trigger": f"Forecast rainfall {rainfall_forecast:.1f} mm exceeds 40 mm",
            "action": proto.immediate_mitigation_action,
            "recovery": proto.post_event_recovery,
            "source": proto.source
        })

    # 2. Heat wave
    if temperature and temperature >= 38.0 and growth_stage in ["Flowering", "Pod Formation"]:
        proto = EXTREME_PROTOCOLS["HEAT_WAVE_REPRODUCTIVE"]
        active_protocols.append({
            "condition": proto.condition_name,
            "risk_level": proto.risk_level,
            "trigger": f"Temperature ({temperature:.1f}°C) >= 38.0°C during reproductive phase",
            "action": proto.immediate_mitigation_action,
            "recovery": proto.post_event_recovery,
            "source": proto.source
        })

    # 3. Cold shock
    if temperature and temperature < 15.0:
        proto = EXTREME_PROTOCOLS["COLD_SNAP_DELAY"]
        active_protocols.append({
            "condition": proto.condition_name,
            "risk_level": proto.risk_level,
            "trigger": f"Temperature ({temperature:.1f}°C) < 15.0°C",
            "action": proto.immediate_mitigation_action,
            "recovery": proto.post_event_recovery,
            "source": proto.source
        })

    # 4. Overcast / high humidity
    if humidity and humidity >= 88.0 and (temperature and 24.0 <= temperature <= 32.0):
        proto = EXTREME_PROTOCOLS["PROLONGED_OVERCAST_WEATHER"]
        active_protocols.append({
            "condition": proto.condition_name,
            "risk_level": proto.risk_level,
            "trigger": f"Relative humidity ({humidity:.1f}%) is excessively high",
            "action": proto.immediate_mitigation_action,
            "recovery": proto.post_event_recovery,
            "source": proto.source
        })

    return active_protocols
