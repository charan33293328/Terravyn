from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database.connection import get_db
from models.domain import SensorData

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/historical/{device_id}")
def get_historical_data(device_id: int, days: int = 7, db: Session = Depends(get_db)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    data = db.query(SensorData).filter(
        SensorData.device_id == device_id,
        SensorData.timestamp >= cutoff
    ).order_by(SensorData.timestamp.asc()).all()
    
    # Simple formatting for Recharts (e.g., extracting by hour or returning raw)
    # Return raw for now, frontend can aggregate or we can aggregate
    return [{"time": d.timestamp.strftime("%H:%M"), "moisture": d.soil_moisture, "temperature": d.temperature, "humidity": d.humidity} for d in data]

@router.get("/soil")
def get_soil_analytics(db: Session = Depends(get_db)):
    # Mock aggregation since we don't have enough data yet
    return [{"day": "Mon", "moisture": 60}, {"day": "Tue", "moisture": 62}, {"day": "Wed", "moisture": 65}]

@router.get("/water")
def get_water_analytics(db: Session = Depends(get_db)):
    return []

@router.get("/temperature")
def get_temperature_analytics(db: Session = Depends(get_db)):
    return [{"day": "Mon", "temp": 24}, {"day": "Tue", "temp": 25}, {"day": "Wed", "temp": 23}]

@router.get("/humidity")
def get_humidity_analytics(db: Session = Depends(get_db)):
    return [{"day": "Mon", "humidity": 45}, {"day": "Tue", "humidity": 48}, {"day": "Wed", "humidity": 50}]

@router.get("/light")
def get_light_analytics(db: Session = Depends(get_db)):
    # Mock data for Day/Night hours since we don't have full data yet
    return [
        {"day": "Mon", "day_hours": 12.5, "night_hours": 11.5}, 
        {"day": "Tue", "day_hours": 13.0, "night_hours": 11.0}, 
        {"day": "Wed", "day_hours": 11.5, "night_hours": 12.5}
    ]
