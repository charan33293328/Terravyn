from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MonitoringSummaryResponse(BaseModel):
    total_devices: int
    online_devices: int
    avg_soil_moisture: Optional[float]
    avg_temperature: Optional[float]
    active_alerts: int

class TelemetrySnapshot(BaseModel):
    device_id: int
    device_name: str
    device_uid: str
    farm_name: Optional[str] = None
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rain_detected: Optional[bool] = None
    water_level: Optional[float] = None
    pressure: Optional[float] = None
    pressure_trend: Optional[str] = None
    bmp_temperature: Optional[float] = None
    pump_status: Optional[bool] = None
    signal_quality: Optional[str] = None
    weather_prediction: Optional[str] = None
    dark_detected: Optional[bool] = None
    light_status: Optional[str] = None
    sensor_health: Optional[dict] = None
    ultrasonic_distance: Optional[float] = None
    ultrasonic_water_level: Optional[int] = None
    tank_status: Optional[str] = None
    obstacle_detected: Optional[bool] = None
    recorded_at: datetime
    connection_status: str
    irrigation_mode: str = "AUTO"
    last_mode_change: Optional[datetime] = None

class TelemetryHistoryResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    pages: int

class ChartDataPoint(BaseModel):
    timestamp: datetime
    value: float

class ChartDataResponse(BaseModel):
    metric: str
    data: List[ChartDataPoint]
