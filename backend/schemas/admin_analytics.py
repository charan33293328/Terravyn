from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class DateRangeParams(BaseModel):
    range: str = "30d"

# Widget Overviews
class OverviewStats(BaseModel):
    total_revenue: float
    total_orders: int
    total_devices: int
    total_customers: int

class DeviceStats(BaseModel):
    total: int
    online: int
    offline: int
    provisioned: int
    unprovisioned: int
    assigned: int
    unassigned: int
    added_today: int

class OrderStats(BaseModel):
    total: int
    today: int
    revenue_today: float
    revenue_this_month: float
    pending: int
    processing: int
    delivered: int
    cancelled: int

class CustomerStats(BaseModel):
    total: int
    new_today: int
    with_devices: int
    without_devices: int
    with_orders: int

class SupportStats(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    critical: int
    created_today: int

# Chart Data
class TimeSeriesDataPoint(BaseModel):
    date: str
    value: float

class CategoryDataPoint(BaseModel):
    name: str
    value: int

# Activity Feed
class ActivityEvent(BaseModel):
    id: int
    type: str
    message: str
    created_at: datetime
    reference_id: Optional[str] = None
