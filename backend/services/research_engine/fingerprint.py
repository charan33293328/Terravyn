"""
Terravyn Research Engine: Situation Fingerprint Normalizer
Generates canonical, hashable representation of agricultural field situations.
"""
import hashlib
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SituationFingerprint(BaseModel):
    crop: str = "green_gram"
    variety: Optional[str] = None
    growth_stage: str = "vegetative"
    soil_type: str = "sandy_loam"
    soil_moisture_state: str = "optimal"  # critical_deficit, mild_deficit, optimal, excess
    temperature_state: str = "optimal"    # extreme_heat, high, optimal, low
    humidity_state: str = "medium"        # low, medium, high
    rain_forecast: str = "none"           # none, light, significant
    recent_rain: bool = False
    recent_irrigation: bool = False
    eto_state: str = "normal"             # low, normal, high
    problem_type: str = "water_stress"    # water_stress, heat_stress, waterlogging, general
    region: Optional[str] = "india_semi_arid"
    soil_moisture_pct: Optional[float] = None
    temperature_c: Optional[float] = None
    rain_forecast_mm: Optional[float] = None

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Return canonical dictionary with sorted keys for deterministic hashing."""
        return {
            "crop": self.crop.lower().strip(),
            "variety": (self.variety or "").lower().strip(),
            "growth_stage": self.growth_stage.lower().replace(" ", "_").strip(),
            "soil_type": self.soil_type.lower().replace(" ", "_").strip(),
            "soil_moisture_state": self.soil_moisture_state.lower().strip(),
            "temperature_state": self.temperature_state.lower().strip(),
            "humidity_state": self.humidity_state.lower().strip(),
            "rain_forecast": self.rain_forecast.lower().strip(),
            "recent_rain": bool(self.recent_rain),
            "recent_irrigation": bool(self.recent_irrigation),
            "eto_state": self.eto_state.lower().strip(),
            "problem_type": self.problem_type.lower().strip(),
            "region": (self.region or "india_semi_arid").lower().strip()
        }

    def compute_hash(self) -> str:
        """Compute SHA-256 fingerprint hash."""
        canonical = self.to_canonical_dict()
        serialized = json.dumps(canonical, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_moisture_state(moisture_pct: Optional[float], target_threshold: float = 25.0) -> str:
    if moisture_pct is None:
        return "unknown"
    if moisture_pct < target_threshold - 6.0:
        return "critical_deficit"
    elif moisture_pct < target_threshold:
        return "mild_deficit"
    elif moisture_pct <= 45.0:
        return "optimal"
    else:
        return "excess"


def normalize_temperature_state(temp_c: Optional[float]) -> str:
    if temp_c is None:
        return "optimal"
    if temp_c >= 40.0:
        return "extreme_heat"
    elif temp_c >= 35.0:
        return "high"
    elif temp_c < 18.0:
        return "low"
    else:
        return "optimal"


def normalize_rain_state(rain_24h_mm: Optional[float], rain_prob: Optional[int] = None) -> str:
    if rain_24h_mm is None:
        return "none"
    prob = rain_prob if rain_prob is not None else 0
    if rain_24h_mm >= 5.0 and prob >= 40:
        return "significant"
    elif rain_24h_mm >= 1.0 or prob >= 30:
        return "light"
    return "none"


def normalize_eto_state(eto: Optional[float]) -> str:
    if eto is None:
        return "normal"
    if eto >= 6.0:
        return "high"
    elif eto <= 2.5:
        return "low"
    return "normal"


def build_fingerprint_from_inputs(
    crop_name: str,
    variety: Optional[str],
    growth_stage: str,
    soil_type: str,
    soil_moisture_pct: Optional[float],
    temperature_c: Optional[float],
    humidity_pct: Optional[float],
    forecast_rain_mm: Optional[float],
    rain_probability_pct: Optional[int],
    et0_mm: Optional[float],
    recent_rain: bool,
    recent_irrigation: bool,
    target_threshold: float = 25.0,
    problem_type: Optional[str] = None,
    region: Optional[str] = None
) -> SituationFingerprint:
    """Builds a normalized SituationFingerprint from raw field inputs."""
    m_state = normalize_moisture_state(soil_moisture_pct, target_threshold)
    t_state = normalize_temperature_state(temperature_c)
    h_state = "low" if (humidity_pct and humidity_pct < 40) else ("high" if (humidity_pct and humidity_pct > 80) else "medium")
    r_state = normalize_rain_state(forecast_rain_mm, rain_probability_pct)
    e_state = normalize_eto_state(et0_mm)

    inferred_problem = problem_type
    if not inferred_problem:
        if m_state in ["critical_deficit", "mild_deficit"]:
            inferred_problem = "water_stress"
        elif m_state == "excess":
            inferred_problem = "waterlogging"
        elif t_state == "extreme_heat":
            inferred_problem = "heat_stress"
        else:
            inferred_problem = "general"

    return SituationFingerprint(
        crop="green_gram",
        variety=variety,
        growth_stage=growth_stage,
        soil_type=soil_type,
        soil_moisture_state=m_state,
        temperature_state=t_state,
        humidity_state=h_state,
        rain_forecast=r_state,
        recent_rain=recent_rain,
        recent_irrigation=recent_irrigation,
        eto_state=e_state,
        problem_type=inferred_problem,
        region=region or "india_semi_arid",
        soil_moisture_pct=soil_moisture_pct,
        temperature_c=temperature_c,
        rain_forecast_mm=forecast_rain_mm
    )
