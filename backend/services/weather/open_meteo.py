import requests
import logging
from typing import Dict, Any, List
from datetime import datetime
from .base import WeatherProvider

logger = logging.getLogger(__name__)

# WMO Weather interpretation codes (WW)
WMO_CODE_MAP = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    62: "Moderate rain",
    63: "Heavy rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

def get_weather_description(code: int) -> str:
    return WMO_CODE_MAP.get(code, "Unknown")


class OpenMeteoProvider(WeatherProvider):
    """
    Open-Meteo weather API client implementing WeatherProvider interface.
    No API key required. Provides agricultural metrics including FAO-56 Penman-Monteith ET0.
    """
    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    @property
    def provider_name(self) -> str:
        return "open-meteo"

    def fetch_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Fetch current observations, 7-day daily forecast, and 24-hour hourly forecast.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,"
                "weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,"
                "wind_direction_10m,wind_gusts_10m"
            ),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,"
                "apparent_temperature_min,sunrise,sunset,daylight_duration,sunshine_duration,"
                "uv_index_max,precipitation_sum,rain_sum,precipitation_hours,"
                "precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,"
                "wind_direction_10m_dominant,shortwave_radiation_sum,et0_fao_evapotranspiration"
            ),
            "hourly": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation_probability,precipitation,rain,weather_code,"
                "wind_speed_10m,et0_fao_evapotranspiration"
            ),
            "timezone": "auto",
            "forecast_days": 7
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"[OpenMeteoProvider] Failed to fetch weather for ({latitude}, {longitude}): {e}")
            raise RuntimeError(f"Open-Meteo API request failed: {str(e)}") from e

        return self._normalize_response(data)

    def _normalize_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Open-Meteo raw JSON format into standard Terravyn weather contract.
        """
        raw_current = raw.get("current", {})
        raw_daily = raw.get("daily", {})
        raw_hourly = raw.get("hourly", {})

        # Parse daily items
        daily_items: List[Dict[str, Any]] = []
        dates = raw_daily.get("time", [])
        for i, d in enumerate(dates):
            w_code = raw_daily.get("weather_code", [None])[i] if i < len(raw_daily.get("weather_code", [])) else None
            daily_items.append({
                "date": d,
                "weather_code": w_code,
                "weather_description": get_weather_description(w_code) if w_code is not None else None,
                "temperature_2m_max": raw_daily.get("temperature_2m_max", [None])[i] if i < len(raw_daily.get("temperature_2m_max", [])) else None,
                "temperature_2m_min": raw_daily.get("temperature_2m_min", [None])[i] if i < len(raw_daily.get("temperature_2m_min", [])) else None,
                "apparent_temperature_max": raw_daily.get("apparent_temperature_max", [None])[i] if i < len(raw_daily.get("apparent_temperature_max", [])) else None,
                "apparent_temperature_min": raw_daily.get("apparent_temperature_min", [None])[i] if i < len(raw_daily.get("apparent_temperature_min", [])) else None,
                "sunrise": raw_daily.get("sunrise", [None])[i] if i < len(raw_daily.get("sunrise", [])) else None,
                "sunset": raw_daily.get("sunset", [None])[i] if i < len(raw_daily.get("sunset", [])) else None,
                "daylight_duration": raw_daily.get("daylight_duration", [None])[i] if i < len(raw_daily.get("daylight_duration", [])) else None,
                "sunshine_duration": raw_daily.get("sunshine_duration", [None])[i] if i < len(raw_daily.get("sunshine_duration", [])) else None,
                "uv_index_max": raw_daily.get("uv_index_max", [None])[i] if i < len(raw_daily.get("uv_index_max", [])) else None,
                "precipitation_sum": raw_daily.get("precipitation_sum", [None])[i] if i < len(raw_daily.get("precipitation_sum", [])) else None,
                "rain_sum": raw_daily.get("rain_sum", [None])[i] if i < len(raw_daily.get("rain_sum", [])) else None,
                "precipitation_hours": raw_daily.get("precipitation_hours", [None])[i] if i < len(raw_daily.get("precipitation_hours", [])) else None,
                "precipitation_probability_max": raw_daily.get("precipitation_probability_max", [None])[i] if i < len(raw_daily.get("precipitation_probability_max", [])) else None,
                "wind_speed_10m_max": raw_daily.get("wind_speed_10m_max", [None])[i] if i < len(raw_daily.get("wind_speed_10m_max", [])) else None,
                "wind_gusts_10m_max": raw_daily.get("wind_gusts_10m_max", [None])[i] if i < len(raw_daily.get("wind_gusts_10m_max", [])) else None,
                "wind_direction_10m_dominant": raw_daily.get("wind_direction_10m_dominant", [None])[i] if i < len(raw_daily.get("wind_direction_10m_dominant", [])) else None,
                "shortwave_radiation_sum": raw_daily.get("shortwave_radiation_sum", [None])[i] if i < len(raw_daily.get("shortwave_radiation_sum", [])) else None,
                "et0_fao_evapotranspiration": raw_daily.get("et0_fao_evapotranspiration", [None])[i] if i < len(raw_daily.get("et0_fao_evapotranspiration", [])) else None,
            })

        # Parse hourly items (keep next 24-48 hours for detail view)
        hourly_items: List[Dict[str, Any]] = []
        h_times = raw_hourly.get("time", [])
        # Cap at 48 hours to save bandwidth and storage
        for i in range(min(len(h_times), 48)):
            hw_code = raw_hourly.get("weather_code", [None])[i] if i < len(raw_hourly.get("weather_code", [])) else None
            hourly_items.append({
                "time": h_times[i],
                "temperature_2m": raw_hourly.get("temperature_2m", [None])[i] if i < len(raw_hourly.get("temperature_2m", [])) else None,
                "relative_humidity_2m": raw_hourly.get("relative_humidity_2m", [None])[i] if i < len(raw_hourly.get("relative_humidity_2m", [])) else None,
                "dew_point_2m": raw_hourly.get("dew_point_2m", [None])[i] if i < len(raw_hourly.get("dew_point_2m", [])) else None,
                "apparent_temperature": raw_hourly.get("apparent_temperature", [None])[i] if i < len(raw_hourly.get("apparent_temperature", [])) else None,
                "precipitation_probability": raw_hourly.get("precipitation_probability", [None])[i] if i < len(raw_hourly.get("precipitation_probability", [])) else None,
                "precipitation": raw_hourly.get("precipitation", [None])[i] if i < len(raw_hourly.get("precipitation", [])) else None,
                "rain": raw_hourly.get("rain", [None])[i] if i < len(raw_hourly.get("rain", [])) else None,
                "weather_code": hw_code,
                "pressure_msl": raw_hourly.get("pressure_msl", [None])[i] if i < len(raw_hourly.get("pressure_msl", [])) else None,
                "cloud_cover": raw_hourly.get("cloud_cover", [None])[i] if i < len(raw_hourly.get("cloud_cover", [])) else None,
                "et0_fao_evapotranspiration": raw_hourly.get("et0_fao_evapotranspiration", [None])[i] if i < len(raw_hourly.get("et0_fao_evapotranspiration", [])) else None,
                "vapour_pressure_deficit": raw_hourly.get("vapour_pressure_deficit", [None])[i] if i < len(raw_hourly.get("vapour_pressure_deficit", [])) else None,
                "wind_speed_10m": raw_hourly.get("wind_speed_10m", [None])[i] if i < len(raw_hourly.get("wind_speed_10m", [])) else None,
                "wind_direction_10m": raw_hourly.get("wind_direction_10m", [None])[i] if i < len(raw_hourly.get("wind_direction_10m", [])) else None,
                "wind_gusts_10m": raw_hourly.get("wind_gusts_10m", [None])[i] if i < len(raw_hourly.get("wind_gusts_10m", [])) else None,
                "soil_temperature_0_to_7cm": raw_hourly.get("soil_temperature_0_to_7cm", [None])[i] if i < len(raw_hourly.get("soil_temperature_0_to_7cm", [])) else None,
                "soil_moisture_0_to_7cm": raw_hourly.get("soil_moisture_0_to_7cm", [None])[i] if i < len(raw_hourly.get("soil_moisture_0_to_7cm", [])) else None,
            })

        # Today's ET0 from daily
        today_et0 = daily_items[0]["et0_fao_evapotranspiration"] if daily_items else None

        cw_code = raw_current.get("weather_code")
        current_dict = {
            "temperature": raw_current.get("temperature_2m"),
            "relative_humidity": raw_current.get("relative_humidity_2m"),
            "apparent_temperature": raw_current.get("apparent_temperature"),
            "precipitation": raw_current.get("precipitation"),
            "rain": raw_current.get("rain"),
            "weather_code": cw_code,
            "weather_description": get_weather_description(cw_code) if cw_code is not None else None,
            "cloud_cover": raw_current.get("cloud_cover"),
            "pressure_msl": raw_current.get("pressure_msl"),
            "surface_pressure": raw_current.get("surface_pressure"),
            "wind_speed_10m": raw_current.get("wind_speed_10m"),
            "wind_direction_10m": raw_current.get("wind_direction_10m"),
            "wind_gusts_10m": raw_current.get("wind_gusts_10m"),
            "et0_fao_evapotranspiration": today_et0,
            "timestamp": datetime.fromisoformat(raw_current["time"]) if "time" in raw_current else datetime.utcnow(),
            "source": self.provider_name
        }

        return {
            "current": current_dict,
            "daily": daily_items,
            "hourly": hourly_items
        }
