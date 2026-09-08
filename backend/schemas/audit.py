from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AuditLogOut(BaseModel):
    id: int
    admin_id: int
    admin_name: Optional[str] = None
    action: str
    resource: str
    ip_address: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class MaintenanceScheduleBase(BaseModel):
    is_active: bool
    message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    whitelist_ips: Optional[List[str]] = None

class MaintenanceScheduleOut(MaintenanceScheduleBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True

class BackupRecordOut(BaseModel):
    id: int
    file_name: str
    file_size: int
    status: str
    created_at: datetime
    created_by: Optional[int] = None
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True
