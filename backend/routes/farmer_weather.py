import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from database.connection import get_db
from models.domain import User, Farmer, Farm
from schemas.domain import FarmWeatherResponse, DecisionContextResponse
from auth.security import get_current_active_user
from services.weather import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter()
weather_service = WeatherService()

def get_farmer_from_user(db: Session, user: User) -> Farmer:
    conditions = [func.lower(Farmer.email) == func.lower(user.email)]
    if user.phone_number:
        conditions.append(Farmer.phone == user.phone_number)
    return db.query(Farmer).filter(or_(*conditions)).first()


@router.get("/api/farmer/weather/{farm_id}", response_model=FarmWeatherResponse)
def get_farm_weather(
    farm_id: int,
    force_refresh: bool = Query(False, description="Force fresh fetch from weather provider bypassing cache"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current weather, 7-day daily forecast, and 48-hour hourly forecast for a farm field.
    Returns cached data if within TTL (30 min) unless force_refresh is requested.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    weather_data = weather_service.get_weather_for_farm(db, farm, force_refresh=force_refresh)
    return weather_data


@router.post("/api/farmer/weather/{farm_id}/refresh", response_model=FarmWeatherResponse)
def refresh_farm_weather(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Explicitly force-refresh meteorological data from Open-Meteo for a farm field.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    weather_data = weather_service.get_weather_for_farm(db, farm, force_refresh=True)
    return weather_data


@router.get("/api/farmer/weather/{farm_id}/decision-context", response_model=DecisionContextResponse)
def get_farm_decision_context(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve unified Decision Context contract for future crop intelligence / irrigation optimization:
    Combines Crop Profile, Field Characteristics, Live ESP32 Sensor Telemetry, and Weather/ET0 metrics.
    """
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found or access denied")

    decision_context = weather_service.get_decision_context(db, farm)
    return decision_context
