from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class CustomerListResponse(BaseModel):
    id: int
    full_name: str
    phone_number: str
    email: str
    is_active: bool
    total_orders: int
    total_devices: int
    created_at: datetime
    last_login: Optional[datetime] = None

class CustomerOrderHistory(BaseModel):
    order_id: str
    invoice_number: Optional[str]
    created_at: datetime
    payment_status: str
    order_status: str
    total_amount: float

class CustomerDeviceOwnership(BaseModel):
    device_uid: str
    status: str
    claimed_at: Optional[datetime]
    is_active: bool

class CustomerActivityInformation(BaseModel):
    registration_date: datetime
    last_login: Optional[datetime] = None
    total_support_tickets: int

class CustomerPersonalInformation(BaseModel):
    full_name: str
    phone_number: str
    email: str
    address: str

class CustomerDetailsResponse(BaseModel):
    id: int
    is_active: bool
    personal_information: CustomerPersonalInformation
    order_history: List[CustomerOrderHistory]
    device_ownership: List[CustomerDeviceOwnership]
    activity_information: CustomerActivityInformation
