from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class FarmerBase(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    address: str
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class FarmerCreate(FarmerBase):
    pass

class FarmerUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

class FarmerStatusUpdate(BaseModel):
    status: str

class FarmerResponse(FarmerBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    devices_count: int = 0
    orders_count: int = 0

    class Config:
        orm_mode = True

class FarmerListResponse(BaseModel):
    items: List[FarmerResponse]
    total: int
    page: int
    size: int
