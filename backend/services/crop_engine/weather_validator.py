"""
Weather Data Validation & Fallback Module.
Ensures weather data is treated as an informative enhancer, not a single point of failure.
"""

from typing import Tuple, List, Optional
from datetime import datetime, timedelta

def validate_weather_data(
    is_available: bool,
    last_updated: Optional[datetime],
    current_temp: Optional[float],
    forecast_rainfall_24h: Optional[float],
    et0_today: Optional[float],
    current_time: Optional[datetime] = None,
    max_forecast_stale_hours: int = 6
) -> Tuple[bool, bool, List[str]]:
    """
    Validate meteorological inputs.
    Returns (is_usable: bool, is_stale: bool, advisories: List[str])
    """
    advisories = []
    now = current_time or datetime.utcnow()

    if not is_available:
        advisories.append("External weather service is currently offline. Operating in baseline agronomic fallback mode.")
        return False, True, advisories

    if not last_updated:
        advisories.append("Weather timestamp missing. Meteorological indicators marked unverified.")
        return False, True, advisories

    age_hours = (now - last_updated).total_seconds() / 3600.0
    is_stale = age_hours > max_forecast_stale_hours

    if is_stale:
        advisories.append(f"Weather forecast is {age_hours:.1f} hours old (exceeds {max_forecast_stale_hours}h freshness window). Re-verifying with live provider.")

    # Check key metrics
    if forecast_rainfall_24h is None:
        advisories.append("Precipitation forecast missing from weather response.")
    
    if et0_today is None:
        advisories.append("Reference evapotranspiration (ET₀) unavailable. Using seasonal baseline estimate.")

    is_usable = is_available and not is_stale
    return is_usable, is_stale, advisories
