import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.domain import Farm, Device, DeviceTelemetry, WeatherObservation, WeatherForecast
from .base import WeatherProvider
from .open_meteo import OpenMeteoProvider

logger = logging.getLogger(__name__)

# Cache duration in minutes
DEFAULT_WEATHER_CACHE_MINUTES = 30


class WeatherService:
    def __init__(self, provider: Optional[WeatherProvider] = None, cache_minutes: int = DEFAULT_WEATHER_CACHE_MINUTES):
        self.provider = provider or OpenMeteoProvider()
        self.cache_minutes = cache_minutes

    def get_weather_for_farm(
        self,
        db: Session,
        farm: Farm,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get weather data for a farm field.
        Uses database cache if available and younger than cache_minutes.
        Gracefully handles missing coordinates and API outages.
        """
        # Validate coordinates
        if farm.latitude is None or farm.longitude is None:
            return {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "latitude": None,
                "longitude": None,
                "location_configured": False,
                "current": None,
                "daily": [],
                "hourly": [],
                "last_updated": None,
                "cached": False,
                "provider": self.provider.provider_name,
                "error": "Field coordinates (latitude and longitude) are not configured. Please set them in Farm Settings."
            }

        lat = float(farm.latitude)
        lon = float(farm.longitude)

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "latitude": lat,
                "longitude": lon,
                "location_configured": False,
                "current": None,
                "daily": [],
                "hourly": [],
                "last_updated": None,
                "cached": False,
                "provider": self.provider.provider_name,
                "error": f"Invalid coordinates: latitude ({lat}) or longitude ({lon}) out of bounds."
            }

        # Check DB cache
        latest_obs = (
            db.query(WeatherObservation)
            .filter(WeatherObservation.farm_id == farm.id)
            .order_by(desc(WeatherObservation.timestamp))
            .first()
        )

        now = datetime.utcnow()
        cache_valid = (
            latest_obs is not None
            and not force_refresh
            and (now - latest_obs.timestamp) < timedelta(minutes=self.cache_minutes)
        )

        if cache_valid:
            logger.info(f"[WeatherService] Returning cached weather for farm {farm.id} (updated {latest_obs.timestamp})")
            return self._build_response_from_db(db, farm, latest_obs, cached=True)

        # Fresh fetch from provider
        try:
            logger.info(f"[WeatherService] Fetching fresh weather for farm {farm.id} from {self.provider.provider_name}")
            weather_data = self.provider.fetch_weather(lat, lon)
            
            # Persist observation
            curr = weather_data["current"]
            obs = WeatherObservation(
                farm_id=farm.id,
                timestamp=curr.get("timestamp", now),
                retrieved_at=now,
                temperature=curr.get("temperature"),
                humidity=curr.get("relative_humidity"),
                precipitation=curr.get("precipitation"),
                wind_speed=curr.get("wind_speed_10m"),
                weather_code=curr.get("weather_code"),
                weather_description=curr.get("weather_description"),
                et0=curr.get("et0_fao_evapotranspiration")
            )
            db.add(obs)

            # Persist daily forecasts (delete existing forecasts for this farm to keep fresh 7 days)
            db.query(WeatherForecast).filter(WeatherForecast.farm_id == farm.id).delete()
            for d in weather_data.get("daily", []):
                try:
                    d_time = datetime.strptime(d["date"], "%Y-%m-%d")
                except Exception:
                    d_time = now

                fc = WeatherForecast(
                    farm_id=farm.id,
                    forecast_time=d_time,
                    retrieved_at=now,
                    temperature=d.get("temperature_2m_max"),
                    temp_max=d.get("temperature_2m_max"),
                    temp_min=d.get("temperature_2m_min"),
                    humidity=None,
                    precipitation=d.get("precipitation_sum"),
                    precipitation_probability=int(d.get("precipitation_probability_max") or 0) if d.get("precipitation_probability_max") is not None else None,
                    wind_speed=d.get("wind_speed_10m_max"),
                    weather_code=d.get("weather_code"),
                    weather_description=d.get("weather_description"),
                    et0=d.get("et0_fao_evapotranspiration"),
                    is_daily=True
                )
                db.add(fc)

            db.commit()

            return {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "latitude": lat,
                "longitude": lon,
                "location_configured": True,
                "current": curr,
                "daily": weather_data.get("daily", []),
                "hourly": weather_data.get("hourly", []),
                "last_updated": curr.get("timestamp", now),
                "cached": False,
                "provider": self.provider.provider_name,
                "error": None
            }

        except Exception as e:
            logger.error(f"[WeatherService] Weather fetch failed for farm {farm.id}: {e}", exc_info=True)
            db.rollback()
            # Resilient fallback: use latest existing observation if available
            if latest_obs:
                resp = self._build_response_from_db(db, farm, latest_obs, cached=True)
                resp["error"] = f"Weather provider temporarily unreachable. Showing cached data from {latest_obs.timestamp.strftime('%Y-%m-%d %H:%M:%S')}."
                return resp
            
            # If no cached data exists at all
            return {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "latitude": lat,
                "longitude": lon,
                "location_configured": True,
                "current": None,
                "daily": [],
                "hourly": [],
                "last_updated": None,
                "cached": False,
                "provider": self.provider.provider_name,
                "error": f"Failed to retrieve weather data: {str(e)}"
            }

    def _build_response_from_db(
        self,
        db: Session,
        farm: Farm,
        obs: WeatherObservation,
        cached: bool = True
    ) -> Dict[str, Any]:
        """
        Build standardized weather response from database observation and forecast records.
        """
        forecasts = (
            db.query(WeatherForecast)
            .filter(WeatherForecast.farm_id == farm.id)
            .order_by(WeatherForecast.forecast_time.asc())
            .all()
        )

        daily_items = []
        for f in forecasts:
            daily_items.append({
                "date": f.forecast_time.strftime("%Y-%m-%d"),
                "weather_code": f.weather_code,
                "weather_description": f.weather_description,
                "temperature_2m_max": f.temp_max,
                "temperature_2m_min": f.temp_min,
                "apparent_temperature_max": f.temp_max,
                "apparent_temperature_min": f.temp_min,
                "sunrise": None,
                "sunset": None,
                "daylight_duration": None,
                "sunshine_duration": None,
                "uv_index_max": None,
                "precipitation_sum": f.precipitation,
                "rain_sum": f.precipitation,
                "precipitation_hours": None,
                "precipitation_probability_max": f.precipitation_probability,
                "wind_speed_10m_max": f.wind_speed,
                "wind_gusts_10m_max": None,
                "wind_direction_10m_dominant": None,
                "shortwave_radiation_sum": None,
                "et0_fao_evapotranspiration": f.et0,
            })

        current_dict = {
            "temperature": obs.temperature,
            "relative_humidity": obs.humidity,
            "apparent_temperature": obs.temperature,
            "precipitation": obs.precipitation,
            "rain": obs.precipitation,
            "weather_code": obs.weather_code,
            "weather_description": obs.weather_description,
            "cloud_cover": None,
            "pressure_msl": None,
            "surface_pressure": None,
            "wind_speed_10m": obs.wind_speed,
            "wind_direction_10m": None,
            "wind_gusts_10m": None,
            "et0_fao_evapotranspiration": obs.et0,
            "timestamp": obs.timestamp,
            "source": self.provider.provider_name
        }

        return {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "latitude": farm.latitude,
            "longitude": farm.longitude,
            "location_configured": True,
            "current": current_dict,
            "daily": daily_items,
            "hourly": [],
            "last_updated": obs.timestamp,
            "cached": cached,
            "provider": self.provider.provider_name,
            "error": None
        }

    def get_decision_context(self, db: Session, farm: Farm) -> Dict[str, Any]:
        """
        Build integrated context contract combining:
        - Crop stage & variety (e.g. Green Gram / Moong)
        - Field & soil metadata
        - In-situ ESP32 sensor telemetry
        - Meteorological conditions & evapotranspiration (ET0)
        """
        now = datetime.utcnow()

        # 1. Crop calculation
        crop_name = farm.crop_type or "Green Gram (Moong)"
        variety = farm.crop_variety or "IPM 02-03"
        age_days = None
        stage = "Vegetative"

        if farm.sowing_date:
            age_days = max(0, (now.date() - farm.sowing_date.date()).days)
            if age_days <= 10:
                stage = "Germination & Seedling"
            elif age_days <= 25:
                stage = "Early Vegetative"
            elif age_days <= 45:
                stage = "Flowering & Pod Initiation (Critical)"
            elif age_days <= 65:
                stage = "Pod Development & Filling"
            else:
                stage = "Maturity & Pre-harvest"

        crop_ctx = {
            "crop_name": crop_name,
            "crop_variety": variety,
            "sowing_date": farm.sowing_date,
            "age_days": age_days,
            "growth_stage": stage
        }

        # 2. Field profile
        field_ctx = {
            "farm_id": farm.id,
            "farm_name": farm.name,
            "area": farm.area,
            "area_unit": farm.area_unit or "Acres",
            "soil_type": farm.soil_type or "Sandy Loam",
            "latitude": farm.latitude,
            "longitude": farm.longitude
        }

        # 3. Sensor & ESP32 Telemetry
        device = db.query(Device).filter(Device.farm_id == farm.id).first()
        latest_telem = None
        telemetry_age_seconds = None
        
        soil_moisture = None
        temperature_c = None
        humidity_pct = None
        pump_status_str = "OFF"
        irr_mode = "AUTO"
        last_telem_time = None

        if device:
            irr_mode = device.irrigation_mode or "AUTO"
            pump_status_str = "ON" if device.pump_status else "OFF"
            soil_moisture = device.last_soil_moisture
            temperature_c = device.last_temperature
            humidity_pct = device.last_humidity
            last_telem_time = device.last_seen

            latest_telem = (
                db.query(DeviceTelemetry)
                .filter(DeviceTelemetry.device_id == device.id)
                .order_by(desc(DeviceTelemetry.recorded_at))
                .first()
            )
            if latest_telem:
                if latest_telem.soil_moisture is not None:
                    soil_moisture = latest_telem.soil_moisture
                if latest_telem.temperature is not None:
                    temperature_c = latest_telem.temperature
                if latest_telem.humidity is not None:
                    humidity_pct = latest_telem.humidity
                if latest_telem.pump_status is not None:
                    pump_status_str = "ON" if latest_telem.pump_status else "OFF"
                if latest_telem.recorded_at:
                    last_telem_time = latest_telem.recorded_at

            if last_telem_time:
                telemetry_age_seconds = int((now - last_telem_time).total_seconds())

        sensor_ctx = {
            "device_id": device.id if device else None,
            "device_uid": device.device_uid if device else None,
            "soil_moisture_pct": soil_moisture,
            "soil_moisture_raw": None,
            "temperature_c": temperature_c,
            "humidity_pct": humidity_pct,
            "pump_status": pump_status_str,
            "irrigation_mode": irr_mode,
            "telemetry_age_seconds": telemetry_age_seconds,
            "last_telemetry_at": last_telem_time
        }

        # 4. Weather status
        weather_res = self.get_weather_for_farm(db, farm, force_refresh=False)
        curr_w = weather_res.get("current") or {}
        daily_w = weather_res.get("daily") or []

        rain_prob_24h = daily_w[0].get("precipitation_probability_max") if daily_w else None
        rain_sum_24h = daily_w[0].get("precipitation_sum") if daily_w else None
        et0_today = daily_w[0].get("et0_fao_evapotranspiration") if daily_w else curr_w.get("et0_fao_evapotranspiration")

        weather_ctx = {
            "temperature": curr_w.get("temperature"),
            "relative_humidity": curr_w.get("relative_humidity"),
            "precipitation": curr_w.get("precipitation"),
            "et0_today": et0_today,
            "rain_probability_max_24h": rain_prob_24h,
            "rain_sum_next_24h": rain_sum_24h,
            "weather_description": curr_w.get("weather_description"),
            "last_weather_at": weather_res.get("last_updated")
        }

        # 5. Advisory notes (informative context, no autonomous pump changes)
        advisories = []
        if stage == "Flowering & Pod Initiation (Critical)":
            advisories.append("Crop is in flowering stage. Water stress can reduce pod formation by up to 40%.")
        if rain_prob_24h and rain_prob_24h > 60:
            advisories.append(f"High probability of rain ({rain_prob_24h}%) in the next 24 hours. Monitor before applying irrigation.")
        if et0_today and et0_today > 5.0:
            advisories.append(f"High reference evapotranspiration ({et0_today:.1f} mm/day). Soil moisture depletion will be accelerated.")
        if not advisories:
            advisories.append("Standard monitoring active. Soil moisture within regular bounds.")

        return {
            "crop": crop_ctx,
            "field": field_ctx,
            "sensor": sensor_ctx,
            "weather": weather_ctx,
            "status": "READY",
            "advisory_notes": advisories
        }
