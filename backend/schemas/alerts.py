from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AlertResolveRequest(BaseModel):
    resolution_notes: Optional[str] = None

class AlertSummary(BaseModel):
    total_active: int
    total_critical: int
    total_warning: int
    total_resolved: int

class AlertDetailResponse(BaseModel):
    id: int
    farmer_id: Optional[int]
    farm_id: Optional[int]
    device_id: Optional[int]
    title: str
    description: str
    category: str
    severity: str
    status: str
    trigger_data: Optional[str]
    resolution_notes: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    # Associated info
    farm_name: Optional[str] = None
    crop_type: Optional[str] = None
    farm_status: Optional[str] = None
    
    device_name: Optional[str] = None
    device_uid: Optional[str] = None
    connection_status: Optional[str] = None
    last_heartbeat: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedAlertsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    alerts: List[AlertDetailResponse]
