"""
Terravyn Irrigation Intelligence: Weather Validation & Forecast Guard
"""
from typing import Optional, Tuple, Dict, Any
from datetime import datetime


class IrrigationWeatherValidator:
    """
    Validates weather and forecast data for irrigation decisions.
    Strictly enforces that missing forecast data is flagged as UNKNOWN,
    NEVER defaulted or assumed to be 'NO_RAIN'.
    """

    @classmethod
    def validate_weather_context(
        cls,
        weather_summary: Optional[Dict[str, Any]],
        max_age_hours: float = 6.0,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, str, Optional[float], Optional[int], Optional[float], str, Dict[str, Any]]:
        """
        Validates weather context.
        Returns:
            (is_usable: bool,
             forecast_status: str ("VALID", "UNKNOWN", "STALE", "MISSING"),
             rain_24h_mm: Optional[float],
             rain_prob_pct: Optional[int],
             et0_mm: Optional[float],
             reason: str,
             metadata: dict)
        """
        now = current_time or datetime.utcnow()

        if not weather_summary:
            return False, "UNKNOWN", None, None, None, (
                "Weather forecast data is unavailable. Flagged as UNKNOWN (not assumed to be 'NO_RAIN')."
            ), {"weather_status": "UNKNOWN"}

        fetched_at = weather_summary.get("fetched_at")
        if fetched_at:
            if isinstance(fetched_at, str):
                try:
                    fetched_at = datetime.fromisoformat(fetched_at.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    fetched_at = None
            
            if fetched_at:
                age_hours = (now - fetched_at).total_seconds() / 3600.0
                if age_hours > max_age_hours:
                    return False, "STALE", None, None, None, (
                        f"Weather forecast is stale ({age_hours:.1f} hours old, max allowed: {max_age_hours}h). "
                        "Treating forecast confidence as degraded (UNKNOWN)."
                    ), {"age_hours": round(age_hours, 1), "weather_status": "STALE"}

        rain_24h = weather_summary.get("rainfall_forecast_24h")
        rain_prob = weather_summary.get("rainfall_probability_24h")
        et0 = weather_summary.get("et0")

        # Check if rain forecast is explicitly provided or missing
        if rain_24h is None and rain_prob is None:
            return False, "UNKNOWN", None, None, et0, (
                "Precipitation forecast missing from weather provider. "
                "Classified strictly as UNKNOWN to prevent erroneous irrigation suppression."
            ), {"weather_status": "UNKNOWN", "et0": et0}

        return True, "VALID", float(rain_24h or 0.0), int(rain_prob or 0), (float(et0) if et0 is not None else None), (
            f"Weather forecast verified: 24h rain={rain_24h or 0.0}mm ({rain_prob or 0}% prob), ET₀={et0}mm."
        ), {
            "weather_status": "VALID",
            "rain_24h": rain_24h,
            "rain_prob": rain_prob,
            "et0": et0
        }
