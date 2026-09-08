from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.domain import RoleEnum

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    username: Optional[str] = None
    phone_number: Optional[str] = None
    role: RoleEnum = RoleEnum.user
    preferred_language: str = "en"

class UserCreate(UserBase):
    username: str
    phone_number: str
    password: str

class UsernameCheckRequest(BaseModel):
    username: str

class SendEmailOTPRequest(BaseModel):
    email: EmailStr
    full_name: str
    username: str

class VerifyEmailOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class SendPhoneOTPRequest(BaseModel):
    phone_number: str

class VerifyPhoneOTPRequest(BaseModel):
    phone_number: str
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    preferred_language: Optional[str] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Device Schemas ---
class FarmBase(BaseModel):
    name: str
    crop_type: Optional[str] = None
    area: Optional[float] = None
    area_unit: Optional[str] = "Acres"
    description: Optional[str] = None
    status: Optional[str] = "ACTIVE"
    expected_harvest_date: Optional[datetime] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sowing_date: Optional[datetime] = None
    crop_variety: Optional[str] = None
    soil_type: Optional[str] = None
    plot_type: Optional[str] = "STANDARD" # STANDARD, TERRAVYN, CONTROL
    experiment_active: Optional[bool] = False
    growth_stage_override: Optional[str] = None

class FarmCreate(FarmBase):
    pass

class FarmUpdate(BaseModel):
    name: Optional[str] = None
    crop_type: Optional[str] = None
    area: Optional[float] = None
    area_unit: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    expected_harvest_date: Optional[datetime] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sowing_date: Optional[datetime] = None
    crop_variety: Optional[str] = None
    soil_type: Optional[str] = None
    plot_type: Optional[str] = None
    experiment_active: Optional[bool] = None
    growth_stage_override: Optional[str] = None

class FarmResponse(FarmBase):
    id: int
    farmer_id: int
    created_at: datetime
    device_count: Optional[int] = 0

    class Config:
        from_attributes = True

class DeviceBase(BaseModel):
    device_uid: str
    name: Optional[str] = None
    location: Optional[str] = None

class DeviceCreate(DeviceBase):
    activation_code: Optional[str] = None
    device_secret: Optional[str] = None
    mac_address: Optional[str] = None
    chip_id: Optional[str] = None
    firmware_version: Optional[str] = None
    owner_id: Optional[int] = None

class DeviceClaim(BaseModel):
    device_uid: str
    activation_code: str
    name: str
    location: str

class DeviceProvisionRequest(BaseModel):
    mac_address: str
    chip_id: str
    firmware_version: str

class DeviceProvisionResponse(BaseModel):
    device_uid: str
    activation_code: str
    device_secret: str

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None

class DeviceResponse(DeviceBase):
    id: int
    status: str
    owner_id: Optional[int] = None
    activation_code: Optional[str] = None
    device_secret: Optional[str] = None
    mac_address: Optional[str] = None
    chip_id: Optional[str] = None
    firmware_version: Optional[str] = None
    last_heartbeat: datetime
    claimed_at: Optional[datetime] = None
    pump_status: bool
    irrigation_mode: str
    last_mode_change: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class DeviceRenameRequest(BaseModel):
    device_name: str

class DeviceFarmAssignmentRequest(BaseModel):
    farm_id: Optional[int] = None

class DeviceModeRequest(BaseModel):
    device_id: int
    irrigation_mode: str

class DynamicIrrigationConfigResponse(BaseModel):
    enabled: bool = False
    crop: Optional[str] = None
    variety: Optional[str] = None
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    start_threshold: Optional[float] = None
    stop_threshold: Optional[float] = None
    hysteresis_enabled: bool = True
    configuration_version: Optional[int] = None
    source: Optional[str] = None
    status: Optional[str] = None # APPROVED, UNAVAILABLE, DISABLED
    reason: Optional[str] = None

class DeviceConfigResponse(BaseModel):
    irrigation_mode: str
    wifi_provisioning_requested: bool = False
    pump_command: Optional[str] = None
    command_id: Optional[str] = None
    max_runtime_seconds: Optional[int] = 300
    config_version: Optional[int] = None
    irrigation_config: Optional[DynamicIrrigationConfigResponse] = None

class DeviceConfigAckRequest(BaseModel):
    mac_address: Optional[str] = None
    device_uid: Optional[str] = None
    chip_id: Optional[str] = None
    configuration_version: int
    status: str = "APPLIED" # APPLIED, REJECTED, PENDING
    applied_start_threshold: Optional[float] = None
    applied_stop_threshold: Optional[float] = None
    crop: Optional[str] = None
    variety: Optional[str] = None
    growth_stage: Optional[str] = None
    rejection_reason: Optional[str] = None

class DeviceConfigAckResponse(BaseModel):
    success: bool
    device_uid: Optional[str] = None
    configuration_version: int
    status: str
    recorded_at: datetime

class FarmerDeviceResponse(BaseModel):
    id: int
    device_uid: str
    device_name: Optional[str] = None
    registration_status: str
    device_status: Optional[str] = None
    product_category_name: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    rssi: Optional[int] = None
    last_heartbeat: Optional[datetime] = None
    connectivity_status: str
    farm_id: Optional[int] = None
    farm_name: Optional[str] = None
    activation_date: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[str] = None
    pump_status: Optional[bool] = False
    temperature: Optional[float] = Field(None, validation_alias="last_temperature")
    humidity: Optional[float] = Field(None, validation_alias="last_humidity")
    rain_detected: Optional[bool] = Field(False, validation_alias="last_rain_detected")
    bmp_temperature: Optional[float] = Field(None, validation_alias="last_bmp_temperature")
    pressure: Optional[float] = Field(None, validation_alias="last_pressure")
    pressure_trend: Optional[str] = Field(None, validation_alias="last_pressure_trend")
    altitude: Optional[float] = Field(None, validation_alias="last_altitude")
    weather_prediction: Optional[str] = Field(None, validation_alias="last_weather_prediction")
    signal_quality: Optional[str] = Field(None, validation_alias="last_signal_quality")
    uptime_seconds: Optional[int] = Field(None, validation_alias="last_uptime_seconds")
    low_water_alert: Optional[bool] = Field(False, validation_alias="last_low_water_alert")
    pump_timeout_alert: Optional[bool] = Field(False, validation_alias="last_pump_timeout_alert")
    obstacle_detected: Optional[bool] = Field(False, validation_alias="last_obstacle_detected")
    wifi_provisioning_requested: Optional[bool] = False
    
    class Config:
        from_attributes = True

class DeviceAlert(BaseModel):
    id: int
    title: str
    severity: str
    generated_time: datetime

class DeviceActivity(BaseModel):
    type: str
    description: str
    timestamp: datetime

class FarmerDeviceDetailResponse(FarmerDeviceResponse):
    mac_address: Optional[str] = None
    chip_id: Optional[str] = None
    crop_type: Optional[str] = None
    manufacturing_date: Optional[datetime] = None
    telemetry: Optional[dict] = None
    alerts: List[DeviceAlert] = []
    activities: List[DeviceActivity] = []

# --- SensorData Schemas ---
class SensorDataCreate(BaseModel):
    device_uid: str
    soil_moisture: float
    water_level: Optional[float] = None
    temperature: float
    humidity: float
    rain_status: bool
    light_intensity: float
    pump_status: bool
    mode_status: str

class DeviceHeartbeat(BaseModel):
    device_uid: str

class SensorDataResponse(BaseModel):
    id: int
    device_id: int
    created_at: datetime
    soil_moisture: float
    water_level: Optional[float] = None
    temperature: float
    humidity: float
    rain_status: bool
    light_intensity: float
    pump_status: bool
    mode_status: str

    class Config:
        from_attributes = True

# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: int
    device_id: int
    category: str
    title: Optional[str] = None
    description: Optional[str] = None
    severity: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Control Schemas ---
class PumpControl(BaseModel):
    device_id: int
    action: str # on/off

class ModeControl(BaseModel):
    device_id: int
    mode: str # auto/manual

# --- Order Schemas ---
class CustomerDetails(BaseModel):
    name: str
    phone: str
    email: str
    address: str
    street: str
    city: str
    district: str
    state: str
    pincode: str
    landmark: Optional[str] = None
    aadhaar_number: str
    consent_accepted: bool
    aadhaar_document_path: Optional[str] = None

class CartItemSchema(BaseModel):
    productId: int
    quantity: int

class OrderCreate(BaseModel):
    items: Optional[List[CartItemSchema]] = None
    productId: Optional[int] = None
    quantity: Optional[int] = 1
    customerDetails: CustomerDetails
    paymentMethod: str # ONLINE or COD

class OrderResponse(BaseModel):
    id: int
    order_id: str
    razorpay_order_id: Optional[str] = None
    total_amount: float
    payment_method: str
    payment_status: str
    order_status: str

class PaymentVerify(BaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str

# --- Invoice Schemas ---
class OrderResponse(BaseModel):
    order_id: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    customer_name: str
    phone_number: str
    email: str
    address: str
    street: str
    city: str
    district: str
    state: str
    pincode: str
    landmark: Optional[str] = None
    product_name: str
    quantity: int
    total_amount: float
    payment_method: str
    payment_status: str
    order_status: str
    courier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    shipment_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderUpdateRequest(BaseModel):
    order_status: Optional[str] = None
    courier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    shipment_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None

class OrderAuditLogResponse(BaseModel):
    id: int
    order_id: str
    admin_id: int
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    order_id: str
    invoice_date: datetime
    customer_name: str
    email: str
    phone: str
    billing_address: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    gst_percentage: float
    gst_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    invoice_pdf_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Support Ticket Schemas ---
class TicketMessageBase(BaseModel):
    message: str
    is_internal: bool = False

class TicketMessageCreate(TicketMessageBase):
    pass

class TicketMessageResponse(TicketMessageBase):
    id: int
    ticket_id: int
    sender_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SupportTicketBase(BaseModel):
    subject: str
    description: str
    priority: str = "NORMAL"

class SupportTicketCreate(SupportTicketBase):
    pass

class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_agent_id: Optional[int] = None

class SupportTicketResponse(SupportTicketBase):
    id: int
    customer_id: int
    assigned_agent_id: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[TicketMessageResponse] = []

    class Config:
        from_attributes = True

# --- Website Content Schemas ---
class WebsiteContentUpdate(BaseModel):
    content: dict

class WebsiteContentResponse(BaseModel):
    id: int
    section_key: str
    content: dict
    updated_by: Optional[int]
    updated_at: datetime

    class Config:
        from_attributes = True

# --- System Settings Schemas ---
class SystemSettingUpdate(BaseModel):
    setting_value: str
    is_secret: bool = False

class SystemSettingResponse(BaseModel):
    id: int
    setting_key: str
    setting_value: str
    updated_by: Optional[int]
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    order_status: str

class PaymentStatusUpdate(BaseModel):
    payment_status: str

class AdminNotificationResponse(BaseModel):
    id: int
    message: str
    type: str
    is_read: bool
    reference_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class OrderAdminResponse(BaseModel):
    id: int
    order_id: str
    invoice_number: Optional[str] = None
    customer_name: str
    phone_number: str
    email: str
    address: str
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    payment_method: str
    payment_status: str
    order_status: str
    identity_verification_status: str
    identity_verified_at: Optional[datetime] = None
    aadhaar_number_masked: Optional[str] = None
    aadhaar_document_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class IdentityVerificationStatusUpdate(BaseModel):
    status: str



class CustomerDetailsSchema(BaseModel):
    name: str
    phone: str
    email: str

class ShippingAddressSchema(BaseModel):
    address: str
    city: str
    district: str
    state: str
    pincode: str

class ProductDetailsSchema(BaseModel):
    name: str
    quantity: int
    unit_price: float
    subtotal: float

class PricingDetailsSchema(BaseModel):
    tax: float
    shipping: float
    total: float

class PaymentDetailsSchema(BaseModel):
    method: str
    status: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None

class TimestampsSchema(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None

class IdentityVerificationDetailsSchema(BaseModel):
    status: str
    verified_at: Optional[datetime] = None
    aadhaar_number_masked: Optional[str] = None
    aadhaar_document_path: Optional[str] = None

class OrderDetailsNestedResponse(BaseModel):
    order_id: str
    invoice_number: Optional[str] = None
    customer: CustomerDetailsSchema
    shipping_address: ShippingAddressSchema
    product: ProductDetailsSchema
    pricing: PricingDetailsSchema
    payment: PaymentDetailsSchema
    order_status: str
    identity: IdentityVerificationDetailsSchema
    timestamps: TimestampsSchema

# --- Admin Profile Schemas ---
class AdminProfileUpdate(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    phone_number: str

class AdminPasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

# --- Phase FP-7 Orders Schemas ---
class OrderItemSchema(BaseModel):
    id: int
    product_id: Optional[int] = None
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float
    
    class Config:
        from_attributes = True

class ReturnRequestSchema(BaseModel):
    id: int
    reason: str
    status: str
    requested_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class ReturnRequestCreate(BaseModel):
    reason: str

class FarmerOrderResponse(BaseModel):
    order_id: str
    invoice_number: Optional[str] = None
    customer_name: str
    phone_number: str
    email: str
    address: str
    city: str
    district: str
    state: str
    pincode: str
    total_amount: float
    shipping_amount: float
    tax_amount: float
    payment_method: str
    payment_status: str
    order_status: str
    courier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    shipment_date: Optional[datetime] = None
    estimated_delivery_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    items: List[OrderItemSchema] = []
    return_requests: List[ReturnRequestSchema] = []
    
    class Config:
        from_attributes = True

class FarmerOrdersSummary(BaseModel):
    total_orders: int
    active_orders: int
    delivered_orders: int
    returned_orders: int


# --- Weather & Decision Context Schemas ---

class WeatherCurrentResponse(BaseModel):
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    apparent_temperature: Optional[float] = None
    precipitation: Optional[float] = None
    rain: Optional[float] = None
    weather_code: Optional[int] = None
    weather_description: Optional[str] = None
    cloud_cover: Optional[float] = None
    pressure_msl: Optional[float] = None
    surface_pressure: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    wind_direction_10m: Optional[float] = None
    wind_gusts_10m: Optional[float] = None
    et0_fao_evapotranspiration: Optional[float] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = "open-meteo"

class WeatherDailyItem(BaseModel):
    date: str
    weather_code: Optional[int] = None
    weather_description: Optional[str] = None
    temperature_2m_max: Optional[float] = None
    temperature_2m_min: Optional[float] = None
    apparent_temperature_max: Optional[float] = None
    apparent_temperature_min: Optional[float] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    daylight_duration: Optional[float] = None
    sunshine_duration: Optional[float] = None
    uv_index_max: Optional[float] = None
    precipitation_sum: Optional[float] = None
    rain_sum: Optional[float] = None
    precipitation_hours: Optional[float] = None
    precipitation_probability_max: Optional[float] = None
    wind_speed_10m_max: Optional[float] = None
    wind_gusts_10m_max: Optional[float] = None
    wind_direction_10m_dominant: Optional[float] = None
    shortwave_radiation_sum: Optional[float] = None
    et0_fao_evapotranspiration: Optional[float] = None

class WeatherHourlyItem(BaseModel):
    time: str
    temperature_2m: Optional[float] = None
    relative_humidity_2m: Optional[float] = None
    dew_point_2m: Optional[float] = None
    apparent_temperature: Optional[float] = None
    precipitation_probability: Optional[float] = None
    precipitation: Optional[float] = None
    rain: Optional[float] = None
    weather_code: Optional[int] = None
    pressure_msl: Optional[float] = None
    cloud_cover: Optional[float] = None
    et0_fao_evapotranspiration: Optional[float] = None
    vapour_pressure_deficit: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    wind_direction_10m: Optional[float] = None
    wind_gusts_10m: Optional[float] = None
    soil_temperature_0_to_7cm: Optional[float] = None
    soil_moisture_0_to_7cm: Optional[float] = None

class FarmWeatherResponse(BaseModel):
    farm_id: int
    farm_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_configured: bool = False
    current: Optional[WeatherCurrentResponse] = None
    daily: List[WeatherDailyItem] = []
    hourly: List[WeatherHourlyItem] = []
    last_updated: Optional[datetime] = None
    cached: bool = False
    provider: str = "open-meteo"
    error: Optional[str] = None

class CropDecisionContext(BaseModel):
    crop_name: Optional[str] = "Green Gram (Moong)"
    crop_variety: Optional[str] = None
    sowing_date: Optional[datetime] = None
    age_days: Optional[int] = None
    growth_stage: Optional[str] = None

class FieldDecisionContext(BaseModel):
    farm_id: int
    farm_name: str
    area: Optional[float] = None
    area_unit: Optional[str] = "Acres"
    soil_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class SensorDecisionContext(BaseModel):
    device_id: Optional[int] = None
    device_uid: Optional[str] = None
    soil_moisture_pct: Optional[float] = None
    soil_moisture_raw: Optional[int] = None
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    pump_status: Optional[str] = None
    irrigation_mode: Optional[str] = None
    telemetry_age_seconds: Optional[int] = None
    last_telemetry_at: Optional[datetime] = None

class WeatherDecisionContext(BaseModel):
    temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    precipitation: Optional[float] = None
    et0_today: Optional[float] = None
    rain_probability_max_24h: Optional[float] = None
    rain_sum_next_24h: Optional[float] = None
    weather_description: Optional[str] = None
    last_weather_at: Optional[datetime] = None

class DecisionContextResponse(BaseModel):
    crop: CropDecisionContext
    field: FieldDecisionContext
    sensor: SensorDecisionContext
    weather: WeatherDecisionContext
    status: str = "READY"
    advisory_notes: List[str] = []


# --- Green Gram Decision Engine Schemas ---

class StageOverrideRequest(BaseModel):
    stage: Optional[str] = None # None to reset back to calendar calculation

class DecisionResponse(BaseModel):
    farm_id: int
    farm_name: str
    crop: str
    variety: Optional[str] = None
    growth_stage: str
    growth_stage_manual: bool = False
    plot_type: str = "STANDARD"
    experiment_active: bool = False
    decision: str # "IRRIGATE" | "WAIT" | "MONITOR" | "ALERT"
    confidence: int # 0-100
    reasons: List[str]
    factors: Dict[str, Any]
    recommended_action: str
    engine_version: str = "green-gram-irrigation-v1"
    generated_at: datetime
    rules_disclaimer: str = "Preliminary / Experimental agronomic thresholds are used. Recommendations are advisory only."
    evidence: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Dict[str, Any]]] = None

class CropProfileResponse(BaseModel):
    crop: str
    common_names: Dict[str, Any]
    family: str
    classification: str
    duration_range_days: tuple[int, int]
    seasons: List[Dict[str, str]]
    symbiotic_fixation: Dict[str, Any]
    total_varieties_cataloged: int
    total_growth_stages: int
    total_sources_cataloged: int

class VarietyResponse(BaseModel):
    name: str
    developer_institution: str
    release_year: Optional[int] = None
    duration_days: int
    duration_range: tuple[int, int]
    suitable_seasons: List[str]
    recommended_regions: List[str]
    average_yield_q_ha: float
    yield_potential_q_ha: float
    seed_characteristics: str
    disease_resistance: Dict[str, str]
    special_traits: List[str]
    source: Dict[str, Any]
    status: str
    confidence: str

class GrowthStageResponse(BaseModel):
    stage_id: str
    stage_name: str
    standard_das_range: tuple[int, int]
    physiological_description: str
    water_sensitivity: str
    crop_coefficient_kc: float
    temp_min_c: float
    temp_opt_c: tuple[float, float]
    temp_max_c: float
    nutrient_priority: str
    disease_vulnerabilities: List[str]
    pest_vulnerabilities: List[str]
    management_advisory: str
    source: Dict[str, Any]
    status: str

class FarmCropStatusResponse(BaseModel):
    farm_id: int
    farm_name: str
    crop: str
    variety: Optional[str] = None
    growth_stage: str
    days_after_sowing: Optional[int] = None
    water_sensitivity: Optional[str] = "MODERATE"
    crop_coefficient_kc: Optional[float] = 0.75
    environmental_status: Dict[str, Any]
    water_status: Dict[str, Any]
    nutrient_advisory: Dict[str, Any]
    disease_risks: List[Dict[str, Any]]
    pest_risks: List[Dict[str, Any]]
    extreme_conditions: List[Dict[str, Any]]
    management_advisory: str
    evidence: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[Dict[str, Any]]] = None

class DecisionLogResponse(BaseModel):
    id: int
    farm_id: int
    device_id: Optional[int] = None
    timestamp: datetime
    crop: str
    variety: Optional[str] = None
    growth_stage: str
    growth_stage_manual: bool = False
    soil_moisture: Optional[float] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rainfall_forecast_24h: Optional[float] = None
    rainfall_probability_24h: Optional[int] = None
    et0: Optional[float] = None
    recent_irrigation_age_hours: Optional[float] = None
    decision: str
    confidence: int
    reasons: List[str]
    factors: Dict[str, Any]
    recommended_action: Optional[str] = None
    engine_version: str

    class Config:
        from_attributes = True

class ExperimentLogCreate(BaseModel):
    recommendation: str
    actual_irrigation: bool
    water_used_liters: Optional[float] = None
    irrigation_duration_minutes: Optional[int] = None
    plant_height_cm: Optional[float] = None
    canopy_cover_pct: Optional[float] = None
    flowering_count_per_m2: Optional[int] = None
    pod_count_per_plant: Optional[int] = None
    plant_response_notes: Optional[str] = None
    manual_override: bool = False
    override_reason: Optional[str] = None
    decision_log_id: Optional[int] = None

class ExperimentLogResponse(ExperimentLogCreate):
    id: int
    farm_id: int
    timestamp: datetime
    recorded_by: Optional[int] = None

    class Config:
        from_attributes = True

class ExperimentPlotSummary(BaseModel):
    farm_id: int
    farm_name: str
    plot_type: str
    crop: str
    variety: Optional[str] = None
    sowing_date: Optional[datetime] = None
    total_water_used_liters: float = 0.0
    irrigation_events_count: int = 0
    latest_decision: Optional[str] = None
    latest_moisture: Optional[float] = None
    observations_count: int = 0


# --- Prompt 5: Research & Knowledge Acquisition Schemas ---

class ResearchQueryCreate(BaseModel):
    farm_id: Optional[int] = None
    force_research: bool = False
    target_parameter: Optional[str] = None
    crop: Optional[str] = "Green Gram (Moong)"
    growth_stage: Optional[str] = "Flowering"
    soil_type: Optional[str] = "Sandy Loam"
    soil_moisture_pct: Optional[float] = None
    temperature_c: Optional[float] = None
    forecast_rain_mm: Optional[float] = None


class ResearchSourceResponse(BaseModel):
    id: int
    title: str
    organization: str
    url: Optional[str] = None
    source_type: str
    source_tier: int
    publication_date: Optional[str] = None
    retrieved_at: datetime
    doi: Optional[str] = None

    class Config:
        from_attributes = True


class EvidenceClaimResponse(BaseModel):
    id: int
    source_id: int
    parameter: str
    claim_text: str
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    unit: Optional[str] = None
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    quality_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchQueryResponse(BaseModel):
    id: int
    farm_id: Optional[int] = None
    fingerprint: Dict[str, Any]
    fingerprint_hash: str
    question: str
    status: str
    engine_version: str
    created_at: datetime
    sources: List[ResearchSourceResponse] = []

    class Config:
        from_attributes = True


class DynamicKnowledgeResponse(BaseModel):
    id: int
    crop: str
    variety: Optional[str] = None
    parameter: str
    finding: str
    conditions: Optional[Dict[str, Any]] = None
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    region: Optional[str] = None
    status: str
    confidence: int
    version: int
    source_provenance: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KnowledgeReviewItemResponse(BaseModel):
    id: int
    knowledge_item_id: Optional[int] = None
    evidence_claim_id: Optional[int] = None
    reason: str
    conflict_details: Optional[Dict[str, Any]] = None
    priority: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResolveReviewRequest(BaseModel):
    action: str  # "APPROVE", "REJECT"
    override_finding: Optional[str] = None
    notes: Optional[str] = None


# --- Prompt 6: Green Gram Experiment & Data Collection Engine V1 Schemas ---

class ExperimentCreate(BaseModel):
    name: str
    crop: Optional[str] = "Green Gram (Moong)"
    scientific_name: Optional[str] = "Vigna radiata"
    variety: Optional[str] = "Pusa Vishal"
    start_date: Optional[datetime] = None
    expected_end_date: Optional[datetime] = None
    location: Optional[str] = None
    protocol: Optional[Dict[str, Any]] = None
    pots_per_group: Optional[int] = 3
    plants_per_pot: Optional[int] = 5
    terravyn_device_id: Optional[int] = None
    control_device_id: Optional[int] = None


class ExperimentBaselineCreate(BaseModel):
    soil_type: Optional[str] = "sandy_loam"
    soil_ph: Optional[float] = None
    soil_ec: Optional[float] = None
    organic_carbon: Optional[float] = None
    available_n: Optional[float] = None
    available_p: Optional[float] = None
    available_k: Optional[float] = None
    seed_source: Optional[str] = None
    sowing_date: Optional[datetime] = None
    seed_quantity: Optional[str] = None
    planting_depth_cm: Optional[float] = 3.0
    spacing_cm: Optional[str] = "30x10"
    irrigation_source: Optional[str] = None
    irrigation_method: Optional[str] = "pot_drip"
    fertilizer_baseline: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None


class ObservationCreate(BaseModel):
    plot_id: int
    parameter: str
    group_id: Optional[int] = None
    plant_id: Optional[int] = None
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    method: Optional[str] = "manual"
    observer: Optional[str] = None
    confidence: Optional[int] = 95
    notes: Optional[str] = None
    timestamp: Optional[datetime] = None


class BatchObservationCreate(BaseModel):
    observations: List[ObservationCreate]


class IrrigationEventCreate(BaseModel):
    plot_id: int
    source: Optional[str] = "TERRAVYN"  # TERRAVYN, CONTROL, MANUAL
    mode: Optional[str] = "AUTO"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    estimated_water_liters: Optional[float] = None
    reason: Optional[str] = None
    decision_log_id: Optional[int] = None


class InterventionCreate(BaseModel):
    plot_id: int
    intervention_type: str
    details: Optional[Dict[str, Any]] = None
    actor: Optional[str] = "user"
    timestamp: Optional[datetime] = None


class SensorCalibrationCreate(BaseModel):
    device_id: Optional[int] = None
    dry_reference: Optional[float] = 4095.0
    wet_reference: Optional[float] = 1400.0
    soil_type: Optional[str] = "sandy_loam"
    notes: Optional[str] = None


# --- Prompt 7: Knowledge Validation & Calibration Schemas ---

class ValidationRunRequest(BaseModel):
    target_type: str  # "SCIENTIFIC_KNOWLEDGE", "EXPERIMENTAL_CANDIDATE"
    target_id: int
    field_id: Optional[int] = None
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None


class ValidationRecordResponse(BaseModel):
    id: int
    target_type: str
    target_id: Optional[int] = None
    status: str
    confidence: int
    confidence_level: str
    dimension_scores: Optional[Dict[str, float]] = None
    evidence_count: int = 0
    experiment_count: int = 0
    data_quality: str
    scope: str
    reasons: Optional[List[str]] = []
    limitations: Optional[List[str]] = []
    recommended_next_step: str
    created_at: datetime

    class Config:
        from_attributes = True


class CalibrationCreate(BaseModel):
    field_id: Optional[int] = None
    plot_id: Optional[int] = None
    parameter: Optional[str] = "capacitive_soil_moisture_threshold"
    crop: Optional[str] = "Green Gram (Moong)"
    growth_stage: Optional[str] = "Flowering"
    soil_type: Optional[str] = "sandy_loam"
    value: Optional[float] = None
    value_range: Optional[Dict[str, float]] = None
    hysteresis_delta: Optional[float] = 10.0
    scope: Optional[str] = "FIELD"
    status: Optional[str] = "EXPERIMENTAL"
    rationale: Optional[str] = None
    experiment_ids: Optional[List[int]] = None


class CalibrationResponse(BaseModel):
    id: int
    field_id: Optional[int] = None
    plot_id: Optional[int] = None
    crop: str
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    parameter: str
    value: Optional[float] = None
    value_range: Optional[Dict[str, float]] = None
    hysteresis_delta: Optional[float] = None
    unit: str
    scope: str
    status: str
    confidence: int
    sample_count: int
    version: int
    rationale: Optional[str] = None
    activated_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CalibrationActivateRequest(BaseModel):
    notes: Optional[str] = None


class DecisionOutcomeResponse(BaseModel):
    id: int
    decision_log_id: int
    classification: str
    hours_to_response: Optional[float] = None
    plant_response_summary: Optional[str] = None
    environmental_context: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# PROMPT 8: PRODUCTION IRRIGATION INTELLIGENCE SCHEMAS
# =====================================================================

class IrrigationControlConfigResponse(BaseModel):
    id: int
    farm_id: int
    device_id: Optional[int] = None
    intelligence_mode: str
    automatic_irrigation_enabled: bool
    control_mode: str
    decision_confidence_min: int
    sensor_freshness_seconds: int
    decision_validity_seconds: int
    cooldown_seconds: int
    max_pump_runtime_seconds: int
    default_duration_seconds: int
    min_water_level_pct: float
    min_water_level_liters: Optional[float] = None
    require_esp32_ack: bool
    dry_run_mode: bool
    config_version: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IrrigationControlConfigUpdate(BaseModel):
    intelligence_mode: Optional[str] = None
    automatic_irrigation_enabled: Optional[bool] = None
    decision_confidence_min: Optional[int] = None
    sensor_freshness_seconds: Optional[int] = None
    decision_validity_seconds: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    max_pump_runtime_seconds: Optional[int] = None
    default_duration_seconds: Optional[int] = None
    min_water_level_pct: Optional[float] = None
    min_water_level_liters: Optional[float] = None
    require_esp32_ack: Optional[bool] = None
    dry_run_mode: Optional[bool] = None
    notes: Optional[str] = None


class IrrigationAuthorizationResponse(BaseModel):
    id: int
    decision_log_id: int
    farm_id: int
    device_id: Optional[int] = None
    status: str
    failure_reason: Optional[str] = None
    checks_passed: Optional[List[str]] = None
    checks_failed: Optional[List[str]] = None
    input_snapshot: Dict[str, Any]
    evaluated_at: datetime

    class Config:
        from_attributes = True


class IrrigationCommandResponse(BaseModel):
    id: int
    command_id: str
    idempotency_key: str
    authorization_id: Optional[int] = None
    farm_id: int
    device_id: int
    command_type: str
    source: str
    duration_seconds: int
    max_runtime_seconds: int
    status: str
    sent_at: Optional[datetime] = None
    ack_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    retry_count: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IrrigationCommandAckRequest(BaseModel):
    command_id: str
    status: str = "ACKNOWLEDGED"  # ACKNOWLEDGED, EXECUTED, FAILED
    error_message: Optional[str] = None


class IrrigationCommandCompleteRequest(BaseModel):
    actual_duration_seconds: Optional[float] = None
    water_volume_liters: Optional[float] = None  # None if not measured by flow sensor
    notes: Optional[str] = None


class IrrigationExecutionResponse(BaseModel):
    id: int
    command_id: int
    device_id: int
    farm_id: int
    decision_log_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    actual_duration_seconds: Optional[float] = None
    water_volume_liters: Optional[float] = None
    status: str
    desired_pump_state: bool
    reported_pump_state: Optional[bool] = None
    state_reconciled: bool
    post_sensor_moisture_delta: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# PROMPT 9: CLOSED-LOOP LEARNING & CONTINUOUS IMPROVEMENT ENGINE V1
# =============================================================================

class DecisionOutcomeAnalysisResponse(BaseModel):
    id: int
    decision_log_id: int
    authorization_id: Optional[int] = None
    command_id: Optional[int] = None
    execution_id: Optional[int] = None
    experiment_id: Optional[int] = None
    farm_id: int
    device_id: Optional[int] = None

    situation_fingerprint: Optional[Dict[str, Any]] = None
    situation_hash: Optional[str] = None

    decision: str
    actual_action: Optional[str] = None
    execution_outcome: Optional[str] = None

    sensor_response: Optional[Dict[str, Any]] = None
    weather_response: Optional[Dict[str, Any]] = None
    plant_response: Optional[Dict[str, Any]] = None
    water_response: Optional[Dict[str, Any]] = None

    classification: str
    classification_reasons: Optional[List[str]] = None
    data_quality: Optional[str] = None
    data_quality_details: Optional[Dict[str, Any]] = None

    observation_window: Optional[str] = None
    confounding_factors: Optional[List[str]] = None

    analysis_version: Optional[str] = None
    idempotency_key: str
    created_at: datetime

    class Config:
        from_attributes = True


class ForecastEvaluationResponse(BaseModel):
    id: int
    farm_id: int
    forecast_id: Optional[int] = None
    forecast_time: datetime
    lead_time_hours: Optional[float] = None
    variable: str
    forecast_value: Optional[float] = None
    observed_value: Optional[float] = None
    error: Optional[float] = None
    error_pct: Optional[float] = None
    season: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LearningCandidateResponse(BaseModel):
    id: int
    candidate_type: str
    crop: Optional[str] = None
    variety: Optional[str] = None
    growth_stage: Optional[str] = None
    soil_type: Optional[str] = None
    farm_id: Optional[int] = None

    situation_hash: Optional[str] = None
    pattern_description: Optional[str] = None
    pattern_data: Optional[Dict[str, Any]] = None

    observation_count: int
    event_count: int
    experiment_count: int
    field_count: int

    data_quality: Optional[str] = None
    confidence: int
    priority: str
    impact: str
    risk_level: str

    status: str
    validation_id: Optional[int] = None
    research_query_id: Optional[int] = None
    calibration_id: Optional[int] = None

    evidence_ids: Optional[List[int]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LearningRunResponse(BaseModel):
    id: int
    farm_id: int
    run_type: str
    decisions_analyzed: int
    outcomes_created: int
    patterns_detected: int
    candidates_created: int
    candidates_updated: int
    analysis_version: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    status: str
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PerformanceMetricResponse(BaseModel):
    id: int
    farm_id: int
    metric_type: str
    period_start: datetime
    period_end: datetime
    sample_size: int
    value: Optional[float] = None
    breakdown: Optional[Dict[str, Any]] = None
    is_sufficient_sample: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ImprovementVersionResponse(BaseModel):
    id: int
    candidate_id: int
    calibration_id: Optional[int] = None
    previous_version: Optional[int] = None
    new_version: Optional[int] = None
    improvement_type: Optional[str] = None
    reason: Optional[str] = None
    evidence_summary: Optional[Dict[str, Any]] = None
    confidence: int
    status: str
    shadow_comparison: Optional[Dict[str, Any]] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LearningSummaryResponse(BaseModel):
    farm_id: int
    period_days: int
    decisions_summary: Dict[str, Any]
    learning_pipeline: Dict[str, Any]
    active_calibration: Optional[Dict[str, Any]] = None
    recent_metrics: List[Dict[str, Any]] = []
    generated_at: str
