from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class FarmerProfileResponse(BaseModel):
    id: int
    full_name: str
    username: Optional[str] = None
    email: str
    phone: str
    profile_photo: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class FarmerProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    username: Optional[str] = Field(None, min_length=3, max_length=50)

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

class NotificationPreferencesSchema(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = True
    in_app_notifications: bool = True
    monitoring_alerts: bool = True
    device_alerts: bool = True
    order_updates: bool = True
    support_updates: bool = True
    security_notifications: bool = True
    product_announcements: bool = False
    
    class Config:
        from_attributes = True

class FarmerSessionSchema(BaseModel):
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    last_active_at: datetime
    is_current_session: bool
    
    class Config:
        from_attributes = True

class FarmerActivityResponse(BaseModel):
    id: int
    activity_type: str
    description: str
    source: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ActivityListResponse(BaseModel):
    items: List[FarmerActivityResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class AccountDeactivationRequest(BaseModel):
    password: str
    reason: Optional[str] = None
