from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class CropInput(BaseModel):
    crop_name: str = "Green Gram (Moong)"
    variety: Optional[str] = None
    sowing_date: Optional[datetime] = None
    age_days: Optional[int] = None
    growth_stage: str = "Vegetative"
    is_stage_manual: bool = False

class FieldInput(BaseModel):
    farm_id: int
    farm_name: str
    area: Optional[float] = None
    area_unit: Optional[str] = "Acres"
    soil_type: Optional[str] = "Sandy Loam"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    plot_type: str = "STANDARD" # STANDARD, TERRAVYN, CONTROL
    experiment_active: bool = False

class SoilInput(BaseModel):
    moisture_pct: Optional[float] = None
    ph: Optional[float] = None
    ec: Optional[float] = None
    nitrogen: Optional[float] = None
    phosphorus: Optional[float] = None
    potassium: Optional[float] = None

class EnvironmentInput(BaseModel):
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light: Optional[str] = None # DAY, NIGHT

class WeatherInput(BaseModel):
    current_temp: Optional[float] = None
    current_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    precipitation_probability_24h: Optional[int] = None
    forecast_rainfall_24h: Optional[float] = None
    wind_speed: Optional[float] = None
    et0_today: Optional[float] = None
    is_available: bool = True
    is_stale: bool = False
    last_updated: Optional[datetime] = None

class IrrigationHistoryInput(BaseModel):
    last_irrigation_at: Optional[datetime] = None
    hours_since_last_irrigation: Optional[float] = None
    last_action: Optional[str] = None # pump_on, pump_off
    recent_events_count_24h: int = 0

class NormalizedDecisionInput(BaseModel):
    crop: CropInput
    field: FieldInput
    soil: SoilInput
    environment: EnvironmentInput
    weather: WeatherInput
    irrigation: IrrigationHistoryInput
    device_id: Optional[int] = None
    device_uid: Optional[str] = None
    telemetry_age_seconds: Optional[int] = None
    evaluated_at: datetime = datetime.utcnow()

class DecisionFactors(BaseModel):
    soil_moisture: Optional[float] = None
    crop_stage: str
    rainfall_forecast_24h: Optional[float] = None
    rainfall_probability_24h: Optional[int] = None
    et0: Optional[float] = None
    temperature: Optional[float] = None
    hours_since_last_irrigation: Optional[float] = None
    soil_type: Optional[str] = None
    sensor_status: str = "VALID"
    weather_status: str = "VALID"

class DecisionResult(BaseModel):
    decision: str # "IRRIGATE" | "WAIT" | "MONITOR" | "ALERT"
    confidence: int # 0-100
    reasons: List[str]
    factors: Dict[str, Any]
    recommended_action: str
    engine_version: str = "green-gram-irrigation-v1"
    generated_at: datetime
    evidence: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    experimental_disclaimer: Optional[str] = "Preliminary / Experimental agronomic thresholds are used. Recommendations are advisory only."

