from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class PlatformSettingsBase(BaseModel):
    platform_name: str
    platform_description: Optional[str] = None
    company_name: str
    company_email: Optional[EmailStr] = None
    company_phone: Optional[str] = None
    company_address: Optional[str] = None
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None
    default_language: str
    default_timezone: str
    currency: str
    date_format: str

class BrandingSettingsBase(BaseModel):
    platform_logo: Optional[str] = None
    favicon: Optional[str] = None
    admin_login_logo: Optional[str] = None
    website_footer_logo: Optional[str] = None
    primary_brand_color: str
    secondary_brand_color: str
    accent_color: str
    company_tagline: Optional[str] = None

class PaymentSettingsBase(BaseModel):
    razorpay_key_id: Optional[str] = None
    razorpay_key_secret: Optional[str] = None
    enable_razorpay: bool
    enable_cod: bool
    max_cod_order_value: float
    cod_availability_regions: Optional[List[str]] = None

class PaymentSettingsResponse(BaseModel):
    razorpay_key_id: Optional[str] = None
    has_razorpay_secret: bool
    enable_razorpay: bool
    enable_cod: bool
    max_cod_order_value: float
    cod_availability_regions: Optional[List[str]] = None

class EmailSettingsBase(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    encryption_type: str
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None

class EmailSettingsResponse(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    has_smtp_password: bool
    encryption_type: str
    sender_email: Optional[EmailStr] = None
    sender_name: Optional[str] = None

class NotificationSettingsBase(BaseModel):
    new_orders: bool
    new_customer_registrations: bool
    support_tickets: bool
    device_provisioning: bool
    payment_success: bool
    payment_failures: bool
    low_inventory_alerts: bool
    maintenance_notifications: bool

class DeviceDefaultsBase(BaseModel):
    heartbeat_timeout_threshold: int
    provision_polling_interval: int
    default_firmware_version: Optional[str] = None
    supported_hardware_revisions: Optional[List[str]] = None
    default_irrigation_thresholds: Optional[Dict[str, Any]] = None
    device_offline_alert_duration: int
    qr_code_expiration_period: int
    activation_code_expiration_period: int

class SecuritySettingsBase(BaseModel):
    session_timeout_duration: int
    password_complexity_requirements: str
    minimum_password_length: int
    maximum_login_attempts: int
    account_lockout_duration: int
    require_two_factor_auth: bool
    allowed_admin_ip_addresses: Optional[List[str]] = None
