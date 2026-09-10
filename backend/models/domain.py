from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Enum, JSON, Text, BigInteger
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from database.connection import Base

class RoleEnum(str, enum.Enum):
    super_admin = "super_admin"
    admin = "admin"
    support_agent = "support_agent"
    operations_manager = "operations_manager"
    farmer = "farmer"
    user = "user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(255), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(RoleEnum), default=RoleEnum.user)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True) # Added for Phase 6F.3 dynamic roles
    is_active = Column(Boolean, default=True)
    preferred_language = Column(String(10), default="en")
    phone_number = Column(String(50), unique=True, index=True, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    dynamic_role = relationship("Role")

    devices = relationship("Device", back_populates="owner")

class Farmer(Base):
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    address = Column(Text, nullable=False)
    village = Column(String(255), nullable=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(20), nullable=True)
    username = Column(String(255), unique=True, index=True, nullable=True)
    profile_photo = Column(String(500), nullable=True)
    status = Column(String(50), default="ACTIVE") # ACTIVE, INACTIVE
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    devices = relationship("Device", back_populates="farmer")
    farms = relationship("Farm", back_populates="farmer")
    alerts = relationship("Alert", back_populates="farmer")
    support_tickets = relationship("SupportTicket", back_populates="farmer", cascade="all, delete-orphan")
    
    # Phase FP-9 Relationships
    notification_preferences = relationship("FarmerNotificationPreference", back_populates="farmer", uselist=False, cascade="all, delete-orphan")
    sessions = relationship("FarmerSession", back_populates="farmer", cascade="all, delete-orphan")
    activities = relationship("FarmerActivityLog", back_populates="farmer", cascade="all, delete-orphan")

class FarmerNotificationPreference(Base):
    __tablename__ = "farmer_notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), unique=True, nullable=False)
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=True)
    in_app_notifications = Column(Boolean, default=True)
    monitoring_alerts = Column(Boolean, default=True)
    device_alerts = Column(Boolean, default=True)
    order_updates = Column(Boolean, default=True)
    support_updates = Column(Boolean, default=True)
    security_notifications = Column(Boolean, default=True)
    product_announcements = Column(Boolean, default=False)
    
    farmer = relationship("Farmer", back_populates="notification_preferences")

class FarmerSession(Base):
    __tablename__ = "farmer_sessions"
    
    session_id = Column(String(255), primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_current_session = Column(Boolean, default=False)
    
    farmer = relationship("Farmer", back_populates="sessions")

class FarmerActivityLog(Base):
    __tablename__ = "farmer_activity_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id", ondelete="CASCADE"), index=True, nullable=False)
    activity_type = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    farmer = relationship("Farmer", back_populates="activities")

class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), index=True, nullable=False) # Email or Phone number
    otp_hash = Column(String(255), nullable=False)
    otp_type = Column(String(50), nullable=False) # EMAIL or PHONE
    expires_at = Column(DateTime, nullable=False)
    attempt_count = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Farm(Base):
    __tablename__ = "farms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    location = Column(String(255), nullable=True)
    crop_type = Column(String(100), nullable=True)
    area = Column(Float, nullable=True) # in area_unit
    area_unit = Column(String(50), default="Acres")
    description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE")
    expected_harvest_date = Column(DateTime, nullable=True)
    village = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=True)
    country = Column(String(255), default="India")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    sowing_date = Column(DateTime, nullable=True)
    crop_variety = Column(String(100), nullable=True)
    soil_type = Column(String(100), nullable=True)
    plot_type = Column(String(50), default="STANDARD") # STANDARD, TERRAVYN, CONTROL
    experiment_active = Column(Boolean, default=False)
    growth_stage_override = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="farms")
    devices = relationship("Device", back_populates="farm")
    alerts = relationship("Alert", back_populates="farm")
    weather_observations = relationship("WeatherObservation", back_populates="farm", cascade="all, delete-orphan")
    weather_forecasts = relationship("WeatherForecast", back_populates="farm", cascade="all, delete-orphan")
    decision_logs = relationship("CropDecisionLog", back_populates="farm", cascade="all, delete-orphan")
    experiment_logs = relationship("CropExperimentLog", back_populates="farm", cascade="all, delete-orphan")

class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    retrieved_at = Column(DateTime, default=datetime.utcnow, index=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    weather_code = Column(Integer, nullable=True)
    weather_description = Column(String(100), nullable=True)
    et0 = Column(Float, nullable=True)

    farm = relationship("Farm", back_populates="weather_observations")

class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    forecast_time = Column(DateTime, index=True, nullable=False)
    retrieved_at = Column(DateTime, default=datetime.utcnow, index=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    precipitation_probability = Column(Integer, nullable=True)
    wind_speed = Column(Float, nullable=True)
    et0 = Column(Float, nullable=True)
    temp_max = Column(Float, nullable=True)
    temp_min = Column(Float, nullable=True)
    weather_code = Column(Integer, nullable=True)
    weather_description = Column(String(100), nullable=True)
    is_daily = Column(Boolean, default=False)

    farm = relationship("Farm", back_populates="weather_forecasts")

class CropDecisionLog(Base):
    __tablename__ = "crop_decision_logs"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    crop = Column(String(100), default="Green Gram (Moong)")
    variety = Column(String(100), nullable=True)
    growth_stage = Column(String(100), nullable=False)
    growth_stage_manual = Column(Boolean, default=False)
    soil_moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    rainfall_forecast_24h = Column(Float, nullable=True)
    rainfall_probability_24h = Column(Integer, nullable=True)
    et0 = Column(Float, nullable=True)
    recent_irrigation_age_hours = Column(Float, nullable=True)
    decision = Column(String(50), nullable=False) # "IRRIGATE", "WAIT", "MONITOR", "ALERT"
    confidence = Column(Integer, default=80)
    reasons = Column(JSON, nullable=False) # List of strings
    factors = Column(JSON, nullable=False) # Dict of factors evaluated
    recommended_action = Column(Text, nullable=True)
    engine_version = Column(String(50), default="green-gram-irrigation-v1")

    farm = relationship("Farm", back_populates="decision_logs")
    device = relationship("Device")
    experiment_logs = relationship("CropExperimentLog", back_populates="decision_log")

class CropExperimentLog(Base):
    __tablename__ = "crop_experiment_logs"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    decision_log_id = Column(Integer, ForeignKey("crop_decision_logs.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    recommendation = Column(String(50), nullable=False)
    actual_irrigation = Column(Boolean, default=False)
    water_used_liters = Column(Float, nullable=True)
    irrigation_duration_minutes = Column(Integer, nullable=True)
    plant_height_cm = Column(Float, nullable=True)
    canopy_cover_pct = Column(Float, nullable=True)
    flowering_count_per_m2 = Column(Integer, nullable=True)
    pod_count_per_plant = Column(Integer, nullable=True)
    plant_response_notes = Column(Text, nullable=True)
    manual_override = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    farm = relationship("Farm", back_populates="experiment_logs")
    decision_log = relationship("CropDecisionLog", back_populates="experiment_logs")
    user = relationship("User")

class ProductCategory(Base):
    __tablename__ = "product_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String(255), unique=True, index=True, nullable=True) # Now nullable for hardware pre-registration
    activation_code = Column(String(255), nullable=True)
    secret_code = Column(String(255), nullable=True)
    mac_address = Column(String(255), nullable=True, index=True)
    chip_id = Column(String(255), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    activation_method = Column(String(50), nullable=True)
    status = Column(String(50), default="offline")
    firmware_version = Column(String(50), nullable=True)
    
    # ESP32 Hardware Provisioning Fields
    hardware_version = Column(String(50), nullable=True)
    rssi = Column(Integer, nullable=True)
    registration_status = Column(String(50), default="WAITING_FOR_PROVISIONING")
    nvs_written = Column(Boolean, default=False)
    provisioned_at = Column(DateTime, nullable=True)
    
    # Admin Panel / Lifecycle Management Fields
    device_status = Column(String(50), default="UNASSIGNED")
    provision_status = Column(String(50), default="NOT_PROVISIONED")
    qr_code_path = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Phase 6 Farmer Assignment Fields
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    claim_status = Column(String(50), default="UNASSIGNED")
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Manufacturing Information
    product_category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    product_category_name = Column(String(255), nullable=True)
    custom_category = Column(String(255), nullable=True)
    manufacturing_notes = Column(Text, nullable=True)
    manufactured_at = Column(DateTime, nullable=True)
    
    # Backwards compatible user fields (can be set upon claiming)
    name = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    installation_date = Column(DateTime, nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    claimed_at = Column(DateTime, nullable=True)
    pump_status = Column(Boolean, default=False)
    irrigation_mode = Column(String(50), default="AUTO")
    last_mode_change = Column(DateTime, default=datetime.utcnow)
    wifi_provisioning_requested = Column(Boolean, default=False)


    # ESP32 Telemetry Snapshot Fields
    last_seen = Column(DateTime, nullable=True)
    last_rssi = Column(Integer, nullable=True)
    last_temperature = Column(Float, nullable=True)
    last_humidity = Column(Float, nullable=True)
    last_soil_moisture = Column(Float, nullable=True)
    last_rain_detected = Column(Boolean, default=False)
    last_bmp_temperature = Column(Float, nullable=True)
    last_pressure = Column(Float, nullable=True)
    last_pressure_trend = Column(String(50), nullable=True)
    last_altitude = Column(Float, nullable=True)
    last_weather_prediction = Column(String(100), nullable=True)
    last_signal_quality = Column(String(50), nullable=True)
    last_uptime_seconds = Column(Integer, nullable=True)
    last_low_water_alert = Column(Boolean, default=False)
    last_pump_timeout_alert = Column(Boolean, default=False)
    last_dark_detected = Column(Boolean, default=False)
    last_ultrasonic_distance = Column(Float, nullable=True)
    last_ultrasonic_water_level = Column(Integer, nullable=True)
    tank_height_cm = Column(Float, nullable=True)
    sensor_offset_cm = Column(Float, nullable=True)
    min_distance_cm = Column(Float, nullable=True)
    max_distance_cm = Column(Float, nullable=True)
    calibration_mode = Column(String(50), default="MANUAL")
    sensor_health = Column(JSON, nullable=True)
    last_obstacle_detected = Column(Boolean, default=False)
    
    # Dynamic Irrigation Configuration Sync Fields
    config_version = Column(Integer, default=1, nullable=True)
    applied_config_version = Column(Integer, nullable=True)
    config_ack_status = Column(String(50), default="PENDING") # PENDING, APPLIED, REJECTED
    last_config_ack_at = Column(DateTime, nullable=True)
    last_config_rejection_reason = Column(String(255), nullable=True)
    current_config_hash = Column(String(64), nullable=True)

    owner = relationship("User", back_populates="devices")
    farmer = relationship("Farmer", back_populates="devices")
    farm = relationship("Farm", back_populates="devices")
    sensor_data = relationship("SensorData", back_populates="device")
    alerts = relationship("Alert", back_populates="device")
    logs = relationship("IrrigationLog", back_populates="device")
    telemetry = relationship("DeviceTelemetry", back_populates="device")

class DeviceTelemetry(Base):
    __tablename__ = "device_telemetry"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), index=True, nullable=True)
    soil_moisture = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    rain_detected = Column(Boolean, default=False)
    water_level = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    pressure_trend = Column(String(50), nullable=True)
    light_intensity = Column(Float, nullable=True)
    battery_voltage = Column(Float, nullable=True)
    rssi = Column(Integer, nullable=True)
    bmp_temperature = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    weather_prediction = Column(String(100), nullable=True)
    signal_quality = Column(String(50), nullable=True)
    firmware_version = Column(String(50), nullable=True)
    uptime_seconds = Column(Integer, nullable=True)
    operation_mode = Column(String(50), nullable=True)
    pump_status = Column(Boolean, default=False)
    low_water_alert = Column(Boolean, default=False)
    pump_timeout_alert = Column(Boolean, default=False)
    dark_detected = Column(Boolean, default=False)
    ultrasonic_distance = Column(Float, nullable=True)
    ultrasonic_water_level = Column(Integer, nullable=True)
    sensor_health = Column(JSON, nullable=True)
    obstacle_detected = Column(Boolean, default=False)
    
    # Dynamic Irrigation Configuration Snapshot Fields
    configuration_version = Column(Integer, nullable=True)
    dynamic_threshold_config_valid = Column(Boolean, nullable=True)
    start_threshold = Column(Float, nullable=True)
    stop_threshold = Column(Float, nullable=True)
    configured_crop = Column(String(100), nullable=True)
    configured_variety = Column(String(100), nullable=True)
    configured_growth_stage = Column(String(100), nullable=True)
    irrigation_event_reason = Column(String(255), nullable=True)
    
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="telemetry")

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    soil_moisture = Column(Float)
    water_level = Column(Float, nullable=True)
    temperature = Column(Float)
    humidity = Column(Float)
    rain_status = Column(Boolean)
    light_intensity = Column(Float)
    pump_status = Column(Boolean)
    mode_status = Column(String(50))

    device = relationship("Device", back_populates="sensor_data")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), index=True, nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), index=True, nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True, nullable=True)
    title = Column(String(255))
    description = Column(Text)
    category = Column(String(100)) # Soil Moisture Alerts, System Alerts, etc.
    severity = Column(String(50), index=True) # CRITICAL, WARNING, INFO
    status = Column(String(50), default="UNREAD", index=True) # UNREAD, READ, RESOLVED
    trigger_data = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farmer = relationship("Farmer", back_populates="alerts")
    farm = relationship("Farm", back_populates="alerts")
    device = relationship("Device", back_populates="alerts")

class IrrigationLog(Base):
    __tablename__ = "irrigation_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    action = Column(String(50)) # pump_on, pump_off, mode_auto, mode_manual
    triggered_by = Column(String(50)) # user, schedule, auto_sensor
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    device = relationship("Device", back_populates="logs")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, index=True, nullable=False) # TERRAVYN ID
    razorpay_order_id = Column(String(100), unique=True, index=True, nullable=True)
    razorpay_payment_id = Column(String(100), unique=True, index=True, nullable=True)
    # Farmer Link (Phase FP-7)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)

    # Customer Details
    customer_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(20), nullable=False)
    landmark = Column(String(255), nullable=True)
    
    # Product Details (DEPRECATED: Migrated to OrderItem in Phase FP-7)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=True)
    unit_price = Column(Float, nullable=True)
    subtotal = Column(Float, nullable=True)
    tax_amount = Column(Float, nullable=False, default=0.0)
    shipping_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False) # in Rupees
    invoice_number = Column(String(100), unique=True, index=True, nullable=True)
    
    payment_method = Column(String(50), nullable=False) # ONLINE or COD
    payment_status = Column(String(50), default="PENDING") # PENDING, SUCCESS, FAILED
    order_status = Column(String(50), default="PENDING") # PENDING, PROCESSING, SHIPPED, DELIVERED, CANCELLED
    
    # Tracking Details
    courier_name = Column(String(255), nullable=True)
    tracking_number = Column(String(255), nullable=True)
    tracking_url = Column(String(500), nullable=True)
    shipment_date = Column(DateTime, nullable=True)
    estimated_delivery_date = Column(DateTime, nullable=True)
    
    # Identity Verification
    aadhaar_number_masked = Column(String(20), nullable=True)
    aadhaar_document_path = Column(String(500), nullable=True)
    identity_verification_status = Column(String(50), default="PENDING") # PENDING, UNDER_REVIEW, APPROVED, REJECTED
    identity_verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Phase FP-7 Relationships
    farmer = relationship("Farmer", backref="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    return_requests = relationship("ReturnRequest", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"), index=True, nullable=False)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    reason = Column(Text, nullable=False)
    status = Column(String(50), default="Pending") # Pending, Approved, Rejected, Completed
    requested_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    order = relationship("Order", back_populates="return_requests")
    farmer = relationship("Farmer")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(50), unique=True, index=True, nullable=False)
    invoice_date = Column(DateTime, default=datetime.utcnow)
    
    customer_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    billing_address = Column(Text, nullable=False)
    
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    gst_percentage = Column(Float, default=0.0)
    gst_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    payment_method = Column(String(50), nullable=False)
    payment_status = Column(String(50), nullable=False)
    invoice_pdf_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderAuditLog(Base):
    __tablename__ = "order_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), index=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(255), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, index=True, nullable=True) # Added in migration
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id"), nullable=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"), nullable=True)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="GENERAL_INQUIRY")
    status = Column(String(50), default="OPEN") # OPEN, IN_PROGRESS, AWAITING_FARMER_RESPONSE, RESOLVED, CLOSED
    priority = Column(String(50), default="NORMAL") # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    internal_notes = relationship("TicketInternalNote", back_populates="ticket", cascade="all, delete-orphan")
    farmer = relationship("Farmer", back_populates="support_tickets", foreign_keys=[farmer_id])
    device = relationship("Device", foreign_keys=[device_id])
    farm = relationship("Farm", foreign_keys=[farm_id])
    order = relationship("Order", foreign_keys=[order_id])

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sender_type = Column(String(50), default="CUSTOMER") # CUSTOMER, ADMIN, SYSTEM, FARMER
    message = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True) # DEPRECATED, use TicketAttachment
    is_internal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="messages")
    attachments = relationship("TicketAttachment", back_populates="message", cascade="all, delete-orphan")

class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("ticket_messages.id"), nullable=True)
    file_name = Column(String(255), nullable=False)
    stored_file_name = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False) # bytes
    mime_type = Column(String(100), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    message = relationship("TicketMessage", back_populates="attachments")
    ticket = relationship("SupportTicket")

class TicketInternalNote(Base):
    __tablename__ = "ticket_internal_notes"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("SupportTicket", back_populates="internal_notes")

class WebsiteContent(Base):
    __tablename__ = "website_content"

    id = Column(Integer, primary_key=True, index=True)
    section_key = Column(String(100), unique=True, index=True, nullable=False)
    content = Column(JSON, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, index=True, nullable=False)
    setting_value = Column(Text, nullable=False)
    is_secret = Column(Boolean, default=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeviceAuditLog(Base):
    __tablename__ = "device_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String(255), index=True, nullable=False)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AdminNotification(Base):
    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="ORDER") # ORDER, ALERT, SYSTEM
    is_read = Column(Boolean, default=False)
    reference_id = Column(String(100), nullable=True) # e.g., order_id
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Phase 6F.2 CMS Models ---

class CMSPage(Base):
    __tablename__ = "cms_pages"

    id = Column(Integer, primary_key=True, index=True)
    page_identifier = Column(String(100), unique=True, index=True, nullable=False) # e.g. "landing_hero", "privacy_policy"
    content_data = Column(JSON, nullable=False) # Store multiple fields, translations, etc.
    status = Column(String(50), default="PUBLISHED") # DRAFT, PUBLISHED
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0)
    status = Column(String(50), default="PUBLISHED") # DRAFT, PUBLISHED
    translations = Column(JSON, nullable=True) # { "te": {"question": "...", "answer": "..."} }
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    featured_image = Column(String(500), nullable=True)
    content = Column(Text, nullable=False) # HTML from Tiptap
    tags = Column(JSON, nullable=True) # List of tags
    seo_title = Column(String(255), nullable=True)
    seo_description = Column(Text, nullable=True)
    status = Column(String(50), default="DRAFT") # DRAFT, PUBLISHED
    publish_date = Column(DateTime, nullable=True)
    translations = Column(JSON, nullable=True) # { "te": {"title": "...", "content": "..."} }
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), unique=True, nullable=False) # e.g. /static/media/images/file.jpg
    file_type = Column(String(50), nullable=False) # image/png, video/mp4, etc.
    file_size = Column(Integer, nullable=False) # bytes
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

class ContentRevision(Base):
    __tablename__ = "content_revisions"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False) # CMSPage, FAQ, BlogPost
    entity_id = Column(Integer, nullable=False)
    editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    change_summary = Column(String(255), nullable=True)
    version_number = Column(Integer, nullable=False, default=1)
    snapshot_data = Column(JSON, nullable=False) # The serialized state of the entity at this version
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Phase 6F.3 Platform Settings & RBAC Models ---

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Permission(Base):
    __tablename__ = 'permissions'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    module = Column(String(50), nullable=False)
    description = Column(String(255), nullable=True)

class RolePermission(Base):
    __tablename__ = 'role_permissions'
    role_id = Column(Integer, ForeignKey('roles.id'), primary_key=True)
    permission_id = Column(Integer, ForeignKey('permissions.id'), primary_key=True)

class PlatformSettings(Base):
    __tablename__ = 'platform_settings'
    id = Column(Integer, primary_key=True, index=True)
    platform_name = Column(String(100), default='TERRAVYN')
    platform_description = Column(Text, nullable=True)
    company_name = Column(String(100), default='TERRAVYN Pvt Ltd')
    company_email = Column(String(100), nullable=True)
    company_phone = Column(String(50), nullable=True)
    company_address = Column(Text, nullable=True)
    support_email = Column(String(100), nullable=True)
    support_phone = Column(String(50), nullable=True)
    default_language = Column(String(10), default='en')
    default_timezone = Column(String(50), default='UTC')
    currency = Column(String(10), default='USD')
    date_format = Column(String(20), default='YYYY-MM-DD')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BrandingSettings(Base):
    __tablename__ = 'branding_settings'
    id = Column(Integer, primary_key=True, index=True)
    platform_logo = Column(String(500), nullable=True)
    favicon = Column(String(500), nullable=True)
    admin_login_logo = Column(String(500), nullable=True)
    website_footer_logo = Column(String(500), nullable=True)
    primary_brand_color = Column(String(20), default='#0f766e')
    secondary_brand_color = Column(String(20), default='#115e59')
    accent_color = Column(String(20), default='#14b8a6')
    company_tagline = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PaymentSettings(Base):
    __tablename__ = 'payment_settings'
    id = Column(Integer, primary_key=True, index=True)
    razorpay_key_id = Column(String(255), nullable=True)
    razorpay_key_secret_encrypted = Column(Text, nullable=True)
    enable_razorpay = Column(Boolean, default=False)
    enable_cod = Column(Boolean, default=True)
    max_cod_order_value = Column(Float, default=10000.0)
    cod_availability_regions = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailSettings(Base):
    __tablename__ = 'email_settings'
    id = Column(Integer, primary_key=True, index=True)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_username = Column(String(255), nullable=True)
    smtp_password_encrypted = Column(Text, nullable=True)
    encryption_type = Column(String(20), default='TLS')
    sender_email = Column(String(255), nullable=True)
    sender_name = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationSettings(Base):
    __tablename__ = 'notification_settings'
    id = Column(Integer, primary_key=True, index=True)
    new_orders = Column(Boolean, default=True)
    new_customer_registrations = Column(Boolean, default=True)
    support_tickets = Column(Boolean, default=True)
    device_provisioning = Column(Boolean, default=True)
    payment_success = Column(Boolean, default=True)
    payment_failures = Column(Boolean, default=True)
    low_inventory_alerts = Column(Boolean, default=True)
    maintenance_notifications = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DeviceDefaults(Base):
    __tablename__ = 'device_defaults'
    id = Column(Integer, primary_key=True, index=True)
    heartbeat_timeout_threshold = Column(Integer, default=300)
    provision_polling_interval = Column(Integer, default=60)
    default_firmware_version = Column(String(50), nullable=True)
    supported_hardware_revisions = Column(JSON, nullable=True)
    default_irrigation_thresholds = Column(JSON, nullable=True)
    device_offline_alert_duration = Column(Integer, default=3600)
    qr_code_expiration_period = Column(Integer, default=86400)
    activation_code_expiration_period = Column(Integer, default=3600)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SecuritySettings(Base):
    __tablename__ = 'security_settings'
    id = Column(Integer, primary_key=True, index=True)
    session_timeout_duration = Column(Integer, default=3600)
    password_complexity_requirements = Column(String(255), default='High')
    minimum_password_length = Column(Integer, default=8)
    maximum_login_attempts = Column(Integer, default=5)
    account_lockout_duration = Column(Integer, default=900)
    require_two_factor_auth = Column(Boolean, default=False)
    allowed_admin_ip_addresses = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MaintenanceSchedule(Base):
    __tablename__ = 'maintenance_schedules'
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=False)
    message = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    whitelist_ips = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(255), nullable=False)
    resource = Column(String(255), nullable=False)
    ip_address = Column(String(100), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class BackupRecord(Base):
    __tablename__ = 'backup_records'
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), unique=True, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    status = Column(String(50), default='COMPLETED')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

# --- Phase 7 Product Pricing Models ---

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    short_description = Column(Text, nullable=True)
    full_description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    tagline = Column(String(255), nullable=True)
    
    current_price = Column(Float, nullable=False)
    mrp = Column(Float, nullable=False)
    discount_percentage = Column(Float, default=0.0)
    tax_percentage = Column(Float, default=0.0)
    shipping_charges = Column(Float, default=0.0)
    
    primary_image = Column(String(255), nullable=True)
    
    status = Column(String(50), default="DRAFT") # DRAFT, PUBLISHED, ARCHIVED
    is_active = Column(Boolean, default=True)
    stock_status = Column(String(50), default="IN_STOCK") # IN_STOCK, OUT_OF_STOCK
    
    # We remove the JSON `images` column from Python model for simplicity
    # or keep it out of the mappings if it still exists in DB to prevent conflicts
    # Let's remove it entirely from the Python model.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.display_order")
    specifications = relationship("ProductSpecification", back_populates="product", cascade="all, delete-orphan")
    features = relationship("ProductFeature", back_populates="product", cascade="all, delete-orphan", order_by="ProductFeature.display_order")

class ProductImage(Base):
    __tablename__ = "product_images"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    product = relationship("Product", back_populates="images")

class ProductSpecification(Base):
    __tablename__ = "product_specifications"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(String(255), nullable=False)
    product = relationship("Product", back_populates="specifications")

class ProductFeature(Base):
    __tablename__ = "product_features"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    feature = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    product = relationship("Product", back_populates="features")

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    old_mrp = Column(Float, nullable=False)
    new_mrp = Column(Float, nullable=False)
    
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    
    effective_from = Column(DateTime, default=datetime.utcnow)
    effective_until = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")


# --- Prompt 5: Research & Knowledge Acquisition Engine V1 Models ---

class ResearchQuery(Base):
    __tablename__ = "research_queries"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), nullable=True, index=True)
    fingerprint = Column(JSON, nullable=False)
    fingerprint_hash = Column(String(64), index=True, nullable=False)
    question = Column(Text, nullable=False)
    status = Column(String(50), default="COMPLETED")  # COMPLETED, IN_PROGRESS, FAILED
    engine_version = Column(String(50), default="research-engine-v1")
    created_at = Column(DateTime, default=datetime.utcnow)

    farm = relationship("Farm")
    sources = relationship("ResearchSource", back_populates="query", cascade="all, delete-orphan")


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("research_queries.id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=False)
    url = Column(String(500), nullable=True)
    source_type = Column(String(50), default="GOVERNMENT")  # GOVERNMENT, JOURNAL, EXTENSION, OTHER
    source_tier = Column(Integer, default=1)  # 1 (ICAR/FAO), 2 (Journals), 3 (Extensions), 4 (Other)
    publication_date = Column(String(50), nullable=True)
    retrieved_at = Column(DateTime, default=datetime.utcnow)
    doi = Column(String(100), nullable=True)
    content_hash = Column(String(64), nullable=True)

    query = relationship("ResearchQuery", back_populates="sources")
    claims = relationship("EvidenceClaim", back_populates="source", cascade="all, delete-orphan")


class EvidenceClaim(Base):
    __tablename__ = "evidence_claims"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("research_sources.id", ondelete="CASCADE"), index=True, nullable=False)
    parameter = Column(String(100), nullable=False)
    claim_text = Column(Text, nullable=False)
    value_min = Column(Float, nullable=True)
    value_max = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    condition_context = Column(JSON, nullable=True)
    growth_stage = Column(String(100), nullable=True)
    soil_type = Column(String(100), nullable=True)
    quality_score = Column(Float, default=70.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("ResearchSource", back_populates="claims")


class DynamicKnowledgeItem(Base):
    __tablename__ = "dynamic_knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), default="Green Gram (Moong)", index=True)
    variety = Column(String(100), nullable=True)
    parameter = Column(String(100), index=True, nullable=False)
    finding = Column(Text, nullable=False)
    conditions = Column(JSON, nullable=True)
    growth_stage = Column(String(100), nullable=True, index=True)
    soil_type = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    status = Column(String(50), default="PROVISIONAL")  # VALIDATED, PROVISIONAL, EXPERIMENTAL, UNDER_REVIEW, REJECTED
    confidence = Column(Integer, default=75)
    version = Column(Integer, default=1)
    source_provenance = Column(JSON, nullable=True)
    last_reviewed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KnowledgeReviewQueue(Base):
    __tablename__ = "knowledge_review_queues"

    id = Column(Integer, primary_key=True, index=True)
    knowledge_item_id = Column(Integer, ForeignKey("dynamic_knowledge_items.id", ondelete="SET NULL"), nullable=True)
    evidence_claim_id = Column(Integer, ForeignKey("evidence_claims.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text, nullable=False)
    conflict_details = Column(JSON, nullable=True)
    priority = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW
    status = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    knowledge_item = relationship("DynamicKnowledgeItem")
    evidence_claim = relationship("EvidenceClaim")
    resolver = relationship("User")


# --- Prompt 6: Green Gram Experiment & Data Collection Engine V1 Models ---

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    crop = Column(String(100), default="Green Gram (Moong)")
    scientific_name = Column(String(100), default="Vigna radiata")
    variety = Column(String(100), nullable=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    expected_end_date = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)
    protocol = Column(JSON, nullable=True)
    status = Column(String(50), default="PLANNED")  # PLANNED, ACTIVE, PAUSED, COMPLETED, CANCELLED
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    groups = relationship("ExperimentGroup", back_populates="experiment", cascade="all, delete-orphan")
    baseline = relationship("ExperimentBaseline", back_populates="experiment", uselist=False, cascade="all, delete-orphan")
    observations = relationship("ExperimentObservation", back_populates="experiment", cascade="all, delete-orphan")
    events = relationship("ExperimentEvent", back_populates="experiment", cascade="all, delete-orphan")
    creator = relationship("User")


class ExperimentGroup(Base):
    __tablename__ = "experiment_groups"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(100), nullable=False)  # "Terravyn", "Control"
    type = Column(String(50), nullable=False)  # "TERRAVYN", "CONTROL"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="groups")
    plots = relationship("ExperimentPlot", back_populates="group", cascade="all, delete-orphan")


class ExperimentPlot(Base):
    __tablename__ = "experiment_plots"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("experiment_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(100), nullable=False)  # "Pot 1", "Replicate A", etc.
    plot_type = Column(String(50), default="POT")  # POT, PLOT, BED
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), nullable=True)
    soil_profile = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("ExperimentGroup", back_populates="plots")
    plants = relationship("ExperimentPlant", back_populates="plot", cascade="all, delete-orphan")
    device = relationship("Device")
    farm = relationship("Farm")


class ExperimentPlant(Base):
    __tablename__ = "experiment_plants"

    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey("experiment_plots.id", ondelete="CASCADE"), index=True, nullable=False)
    plant_tag = Column(String(100), nullable=False)
    sowing_date = Column(DateTime, nullable=True)
    germination_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="ALIVE")  # ALIVE, WILTING, DEAD, HARVESTED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    plot = relationship("ExperimentPlot", back_populates="plants")


class ExperimentBaseline(Base):
    __tablename__ = "experiment_baselines"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), unique=True, nullable=False)
    soil_type = Column(String(100), nullable=True)
    soil_ph = Column(Float, nullable=True)
    soil_ec = Column(Float, nullable=True)
    organic_carbon = Column(Float, nullable=True)
    available_n = Column(Float, nullable=True)
    available_p = Column(Float, nullable=True)
    available_k = Column(Float, nullable=True)
    seed_source = Column(String(255), nullable=True)
    sowing_date = Column(DateTime, nullable=True)
    seed_quantity = Column(String(100), nullable=True)
    planting_depth_cm = Column(Float, nullable=True)
    spacing_cm = Column(String(100), nullable=True)
    irrigation_source = Column(String(100), nullable=True)
    irrigation_method = Column(String(100), nullable=True)
    fertilizer_baseline = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    elevation_m = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="baseline")


class SensorCalibrationRecord(Base):
    __tablename__ = "sensor_calibration_records"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    sensor_type = Column(String(100), default="capacitive_soil_moisture")
    calibration_date = Column(DateTime, default=datetime.utcnow)
    calibration_method = Column(String(100), default="two_point_air_water")
    dry_reference = Column(Float, default=4095.0)  # 4095 = Air / Dry
    wet_reference = Column(Float, default=1400.0)  # Submerged / Wet
    direction = Column(String(50), default="4095_DRY_0_WET")
    soil_type = Column(String(100), nullable=True)
    calibration_version = Column(String(50), default="v1.0")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device")


class ExperimentObservation(Base):
    __tablename__ = "experiment_observations"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("experiment_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    plot_id = Column(Integer, ForeignKey("experiment_plots.id", ondelete="CASCADE"), index=True, nullable=False)
    plant_id = Column(Integer, ForeignKey("experiment_plants.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    parameter = Column(String(100), nullable=False)  # plant_height, leaf_count, flower_count, pod_count, wilting, etc.
    value_numeric = Column(Float, nullable=True)
    value_text = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    method = Column(String(50), default="manual")
    observer = Column(String(100), nullable=True)
    confidence = Column(Integer, default=95)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="observations")


class ExperimentIrrigationEvent(Base):
    __tablename__ = "experiment_irrigation_events"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("experiment_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    plot_id = Column(Integer, ForeignKey("experiment_plots.id", ondelete="CASCADE"), index=True, nullable=False)
    source = Column(String(50), default="TERRAVYN")  # TERRAVYN, CONTROL, MANUAL
    mode = Column(String(50), default="AUTO")  # AUTO, MANUAL
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    estimated_water_liters = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    decision_log_id = Column(Integer, ForeignKey("crop_decision_logs.id", ondelete="SET NULL"), nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExperimentEvent(Base):
    __tablename__ = "experiment_events"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("experiment_groups.id", ondelete="SET NULL"), nullable=True)
    plot_id = Column(Integer, ForeignKey("experiment_plots.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(100), nullable=False)
    actor = Column(String(100), default="system")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="events")


class ExperimentIntervention(Base):
    __tablename__ = "experiment_interventions"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    plot_id = Column(Integer, ForeignKey("experiment_plots.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    intervention_type = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    actor = Column(String(100), default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class ExperimentDailySnapshot(Base):
    __tablename__ = "experiment_daily_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), index=True, nullable=False)
    group_id = Column(Integer, ForeignKey("experiment_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    plot_id = Column(Integer, ForeignKey("experiment_plots.id", ondelete="CASCADE"), index=True, nullable=False)
    snapshot_date = Column(DateTime, index=True, nullable=False)
    soil_moisture_summary = Column(JSON, nullable=True)
    temperature_summary = Column(JSON, nullable=True)
    humidity_summary = Column(JSON, nullable=True)
    rainfall_summary = Column(JSON, nullable=True)
    irrigation_summary = Column(JSON, nullable=True)
    growth_stage = Column(String(100), nullable=True)
    plant_observations = Column(JSON, nullable=True)
    health_observations = Column(JSON, nullable=True)
    data_quality_score = Column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Prompt 7: Knowledge Validation & Calibration Engine V1 Models ---

class KnowledgeValidationRecord(Base):
    __tablename__ = "knowledge_validation_records"

    id = Column(Integer, primary_key=True, index=True)
    target_type = Column(String(50), nullable=False)  # "SCIENTIFIC_KNOWLEDGE", "EXPERIMENTAL_CANDIDATE", "FIELD_CALIBRATION"
    target_id = Column(Integer, nullable=True, index=True)
    status = Column(String(50), default="UNVALIDATED", index=True)  # UNVALIDATED, UNDER_REVIEW, EXPERIMENTAL, PROVISIONAL, VALIDATED, FIELD_CALIBRATED, REJECTED, SUPERSEDED
    confidence = Column(Integer, default=0)
    confidence_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH
    dimension_scores = Column(JSON, nullable=True)  # 10 validation dimensions
    evidence_count = Column(Integer, default=0)
    experiment_count = Column(Integer, default=0)
    data_quality = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW
    scope = Column(String(50), default="FIELD")  # GLOBAL, REGION, SOIL_TYPE, FIELD, PLOT, SENSOR, CROP, VARIETY, GROWTH_STAGE
    reasons = Column(JSON, nullable=True)  # List of explanation strings
    limitations = Column(JSON, nullable=True)  # List of limitation strings
    recommended_next_step = Column(String(50), default="REVIEW_REQUIRED")  # SHADOW_TEST, REVIEW_REQUIRED, KEEP_EXPERIMENTAL, PROMOTE_TO_PROVISIONAL, PROMOTE_TO_VALIDATED, FIELD_CALIBRATE, REJECT
    validated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    validator = relationship("User")


class FieldCalibrationRecord(Base):
    __tablename__ = "field_calibration_records"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=True, index=True)
    plot_id = Column(Integer, ForeignKey("experiment_plots.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    crop = Column(String(100), default="Green Gram (Moong)")
    variety = Column(String(100), nullable=True)
    soil_type = Column(String(100), nullable=True)
    growth_stage = Column(String(100), nullable=True, index=True)
    parameter = Column(String(100), nullable=False, index=True)  # "capacitive_soil_moisture_threshold", "soil_moisture_trigger"
    value = Column(Float, nullable=True)
    value_range = Column(JSON, nullable=True)  # {"min": 30.0, "max": 35.0, "stop_threshold": 42.0}
    hysteresis_delta = Column(Float, nullable=True)  # e.g., 10.0% difference between trigger and stop
    unit = Column(String(50), default="% volumetric")
    scope = Column(String(50), default="FIELD")  # GLOBAL, REGION, SOIL_TYPE, FIELD, PLOT, SENSOR
    status = Column(String(50), default="EXPERIMENTAL", index=True)  # EXPERIMENTAL, SHADOW, ACTIVE, SUPERSEDED, REJECTED
    confidence = Column(Integer, default=50)
    sample_count = Column(Integer, default=0)
    experiment_ids = Column(JSON, nullable=True)  # List of experiment IDs
    version = Column(Integer, default=1)
    previous_version_id = Column(Integer, ForeignKey("field_calibration_records.id", ondelete="SET NULL"), nullable=True)
    rationale = Column(Text, nullable=True)
    activated_at = Column(DateTime, nullable=True)
    activated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm = relationship("Farm")
    plot = relationship("ExperimentPlot")
    device = relationship("Device")
    activator = relationship("User", foreign_keys=[activated_by])
    previous_version = relationship("FieldCalibrationRecord", remote_side=[id])


class CalibrationVersion(Base):
    __tablename__ = "calibration_versions"

    id = Column(Integer, primary_key=True, index=True)
    calibration_id = Column(Integer, ForeignKey("field_calibration_records.id", ondelete="CASCADE"), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # "CREATED", "SHADOW_ENABLED", "ACTIVATED", "ROLLED_BACK", "SUPERSEDED"
    config_snapshot = Column(JSON, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    calibration = relationship("FieldCalibrationRecord")
    actor = relationship("User")


class DecisionOutcomeRecord(Base):
    __tablename__ = "decision_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    decision_log_id = Column(Integer, ForeignKey("crop_decision_logs.id", ondelete="CASCADE"), index=True, nullable=False)
    irrigation_event_id = Column(Integer, ForeignKey("experiment_irrigation_events.id", ondelete="SET NULL"), nullable=True)
    observation_id = Column(Integer, ForeignKey("experiment_observations.id", ondelete="SET NULL"), nullable=True)
    classification = Column(String(50), nullable=False, index=True)  # "CORRECT_WAIT", "CORRECT_IRRIGATION", "MISSED_IRRIGATION", "FALSE_IRRIGATION", "INSUFFICIENT_DATA"
    hours_to_response = Column(Float, nullable=True)
    plant_response_summary = Column(Text, nullable=True)
    environmental_context = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    decision_log = relationship("CropDecisionLog")
    irrigation_event = relationship("ExperimentIrrigationEvent")
    observation = relationship("ExperimentObservation")


class ShadowDecisionLog(Base):
    __tablename__ = "shadow_decision_logs"

    id = Column(Integer, primary_key=True, index=True)
    decision_log_id = Column(Integer, ForeignKey("crop_decision_logs.id", ondelete="CASCADE"), index=True, nullable=False)
    calibration_id = Column(Integer, ForeignKey("field_calibration_records.id", ondelete="CASCADE"), index=True, nullable=False)
    production_decision = Column(String(50), nullable=False)
    shadow_decision = Column(String(50), nullable=False)
    production_factors = Column(JSON, nullable=True)
    shadow_factors = Column(JSON, nullable=True)
    divergence = Column(Boolean, default=False)
    simulated_impact = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    decision_log = relationship("CropDecisionLog")
    calibration = relationship("FieldCalibrationRecord")


# =====================================================================
# PROMPT 8: PRODUCTION IRRIGATION INTELLIGENCE & SAFE CONTROL MODELS
# =====================================================================

class IrrigationControlConfig(Base):
    __tablename__ = "irrigation_control_configs"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    
    intelligence_mode = Column(String(50), default="SHADOW", index=True)  # OBSERVATION, SHADOW, ASSISTED, AUTOMATIC
    automatic_irrigation_enabled = Column(Boolean, default=False)
    control_mode = Column(String(50), default="AUTO")  # AUTO, MANUAL (mirrors device control mode)
    
    decision_confidence_min = Column(Integer, default=75)
    sensor_freshness_seconds = Column(Integer, default=600)
    decision_validity_seconds = Column(Integer, default=600)
    cooldown_seconds = Column(Integer, default=1800)  # 30 min minimum cooldown between irrigations
    max_pump_runtime_seconds = Column(Integer, default=300)  # Hard hardware safety limit (5 min)
    default_duration_seconds = Column(Integer, default=120)  # Default auto irrigation cycle duration (2 min)
    
    min_water_level_pct = Column(Float, default=15.0)  # Low water protection cutoff
    min_water_level_liters = Column(Float, nullable=True)
    require_esp32_ack = Column(Boolean, default=True)
    dry_run_mode = Column(Boolean, default=False)
    config_version = Column(String(50), default="v1.0")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm = relationship("Farm")
    device = relationship("Device")


class IrrigationAuthorizationRecord(Base):
    __tablename__ = "irrigation_authorizations"

    id = Column(Integer, primary_key=True, index=True)
    decision_log_id = Column(Integer, ForeignKey("crop_decision_logs.id", ondelete="CASCADE"), index=True, nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status = Column(String(50), nullable=False, index=True)  # AUTHORIZED, BLOCKED, DEFERRED, FAILED
    failure_reason = Column(Text, nullable=True)
    checks_passed = Column(JSON, nullable=True)  # ["decision_irrigate", "confidence_met", "water_level_ok", ...]
    checks_failed = Column(JSON, nullable=True)  # ["cooldown_active", ...]
    input_snapshot = Column(JSON, nullable=False)  # Complete frozen input snapshot at authorization time
    
    evaluated_at = Column(DateTime, default=datetime.utcnow, index=True)

    decision_log = relationship("CropDecisionLog")
    farm = relationship("Farm")
    device = relationship("Device")
    commands = relationship("IrrigationCommandRecord", back_populates="authorization")


class IrrigationCommandRecord(Base):
    __tablename__ = "irrigation_commands"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(String(100), unique=True, index=True, nullable=False)  # UUID4
    idempotency_key = Column(String(100), unique=True, index=True, nullable=False)
    authorization_id = Column(Integer, ForeignKey("irrigation_authorizations.id", ondelete="SET NULL"), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    
    command_type = Column(String(50), default="IRRIGATION_ON")  # IRRIGATION_ON, IRRIGATION_OFF
    source = Column(String(50), default="TERRAVYN_AUTO")  # TERRAVYN_AUTO, USER_ASSISTED, USER_MANUAL, SIMULATION
    duration_seconds = Column(Integer, default=120)
    max_runtime_seconds = Column(Integer, default=300)
    
    status = Column(String(50), default="PENDING", index=True)  # PENDING, SENT, ACKNOWLEDGED, EXECUTED, FAILED, TIMEOUT, SIMULATED, SKIPPED_DRY_RUN
    sent_at = Column(DateTime, nullable=True)
    ack_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    authorization = relationship("IrrigationAuthorizationRecord", back_populates="commands")
    farm = relationship("Farm")
    device = relationship("Device")
    executions = relationship("IrrigationExecutionRecord", back_populates="command")


class IrrigationExecutionRecord(Base):
    __tablename__ = "irrigation_executions"

    id = Column(Integer, primary_key=True, index=True)
    command_id = Column(Integer, ForeignKey("irrigation_commands.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    decision_log_id = Column(Integer, ForeignKey("crop_decision_logs.id", ondelete="SET NULL"), nullable=True)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    actual_duration_seconds = Column(Float, nullable=True)
    water_volume_liters = Column(Float, nullable=True)  # Null if no physical flow meter exists
    
    status = Column(String(50), default="RUNNING", index=True)  # RUNNING, COMPLETED, ABORTED_SAFETY, TIMEOUT, FAILED, SIMULATED
    desired_pump_state = Column(Boolean, default=True)
    reported_pump_state = Column(Boolean, nullable=True)
    state_reconciled = Column(Boolean, default=False)
    post_sensor_moisture_delta = Column(Float, nullable=True)  # Moisture % change 30 min after irrigation
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    command = relationship("IrrigationCommandRecord", back_populates="executions")
    device = relationship("Device")
    farm = relationship("Farm")
    decision_log = relationship("CropDecisionLog")


# =============================================================================
# PROMPT 9: CLOSED-LOOP LEARNING & CONTINUOUS IMPROVEMENT ENGINE V1
# =============================================================================

class DecisionOutcomeAnalysis(Base):
    """Extended outcome analysis linking the full decision-to-outcome chain."""
    __tablename__ = "decision_outcome_analyses"

    id = Column(Integer, primary_key=True, index=True)
    decision_log_id = Column(Integer, ForeignKey("crop_decision_logs.id", ondelete="CASCADE"), index=True, nullable=False)
    authorization_id = Column(Integer, ForeignKey("irrigation_authorizations.id", ondelete="SET NULL"), nullable=True)
    command_id = Column(Integer, ForeignKey("irrigation_commands.id", ondelete="SET NULL"), nullable=True)
    execution_id = Column(Integer, ForeignKey("irrigation_executions.id", ondelete="SET NULL"), nullable=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    device_id = Column(Integer, nullable=True)

    situation_fingerprint = Column(JSON, nullable=True)
    situation_hash = Column(String(64), index=True, nullable=True)

    decision = Column(String(50), nullable=False)
    actual_action = Column(String(50), nullable=True)  # EXECUTED, BLOCKED, NOT_EXECUTED, MANUAL_OVERRIDE
    execution_outcome = Column(String(50), nullable=True)  # EXECUTION_SUCCESS, EXECUTION_FAILED, EXECUTION_UNKNOWN

    sensor_response = Column(JSON, nullable=True)  # pre/post moisture, delta, response time, stability
    weather_response = Column(JSON, nullable=True)  # forecast vs observed comparison
    plant_response = Column(JSON, nullable=True)  # phenotypic observations
    water_response = Column(JSON, nullable=True)  # volume, flow, duration (null if unmeasured)

    classification = Column(String(50), index=True, nullable=False)
    # CORRECT_IRRIGATION, POSSIBLE_UNNECESSARY_IRRIGATION, POSSIBLE_MISSED_IRRIGATION,
    # CORRECT_WAIT, INSUFFICIENT_DATA, EXECUTION_FAILURE, UNKNOWN
    classification_reasons = Column(JSON, nullable=True)
    data_quality = Column(String(20), nullable=True)  # HIGH, MEDIUM, LOW, INSUFFICIENT
    data_quality_details = Column(JSON, nullable=True)

    observation_window = Column(String(20), nullable=True)  # IMMEDIATE, SHORT_TERM, LONG_TERM
    confounding_factors = Column(JSON, nullable=True)

    analysis_version = Column(String(50), nullable=True)
    knowledge_version = Column(Integer, nullable=True)
    calibration_version = Column(Integer, nullable=True)

    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    decision_log = relationship("CropDecisionLog")
    farm = relationship("Farm")


class ForecastEvaluation(Base):
    """Tracks weather forecast accuracy per field."""
    __tablename__ = "forecast_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    forecast_id = Column(Integer, ForeignKey("weather_forecasts.id", ondelete="SET NULL"), nullable=True)
    forecast_time = Column(DateTime, nullable=False)
    lead_time_hours = Column(Float, nullable=True)
    variable = Column(String(50), nullable=False)  # precipitation, temperature, humidity
    forecast_value = Column(Float, nullable=True)
    observed_value = Column(Float, nullable=True)
    error = Column(Float, nullable=True)
    error_pct = Column(Float, nullable=True)
    season = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    farm = relationship("Farm")


class LearningCandidate(Base):
    """Structured learning candidates generated from repeated patterns."""
    __tablename__ = "learning_candidates"

    id = Column(Integer, primary_key=True, index=True)
    candidate_type = Column(String(50), index=True, nullable=False)
    # IRRIGATION_PATTERN, SENSOR_PATTERN, WEATHER_PATTERN, CROP_RESPONSE,
    # CALIBRATION_PATTERN, FORECAST_ERROR, DATA_QUALITY_PATTERN, KNOWLEDGE_CONFLICT

    crop = Column(String(100), nullable=True)
    variety = Column(String(100), nullable=True)
    growth_stage = Column(String(50), nullable=True)
    soil_type = Column(String(50), nullable=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="SET NULL"), nullable=True, index=True)

    situation_hash = Column(String(64), index=True, nullable=True)
    pattern_description = Column(Text, nullable=True)
    pattern_data = Column(JSON, nullable=True)

    observation_count = Column(Integer, default=0)
    event_count = Column(Integer, default=0)
    experiment_count = Column(Integer, default=0)
    field_count = Column(Integer, default=1)

    data_quality = Column(String(20), nullable=True)  # HIGH, MEDIUM, LOW
    confidence = Column(Integer, default=0)  # 0-100
    priority = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW
    impact = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW
    risk_level = Column(String(20), default="MEDIUM")  # HIGH, MEDIUM, LOW

    status = Column(String(50), default="EXPERIMENTAL", index=True)
    # EXPERIMENTAL, UNDER_REVIEW, VALIDATED, REJECTED, PROMOTED

    validation_id = Column(Integer, ForeignKey("knowledge_validation_records.id", ondelete="SET NULL"), nullable=True)
    research_query_id = Column(Integer, ForeignKey("research_queries.id", ondelete="SET NULL"), nullable=True)
    calibration_id = Column(Integer, ForeignKey("field_calibration_records.id", ondelete="SET NULL"), nullable=True)

    evidence_ids = Column(JSON, nullable=True)  # Array of outcome analysis IDs
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    farm = relationship("Farm")


class LearningEvidence(Base):
    """Links individual outcome analyses to learning candidates."""
    __tablename__ = "learning_evidence"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("learning_candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    outcome_analysis_id = Column(Integer, ForeignKey("decision_outcome_analyses.id", ondelete="CASCADE"), index=True, nullable=False)
    evidence_type = Column(String(20), nullable=False)  # SUPPORTING, CONTRADICTING, NEUTRAL
    weight = Column(Float, default=1.0)  # 0.0-1.0
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("LearningCandidate")
    outcome_analysis = relationship("DecisionOutcomeAnalysis")


class LearningRun(Base):
    """Audit log for each learning analysis execution."""
    __tablename__ = "learning_runs"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    run_type = Column(String(50), nullable=False)
    # OUTCOME_EVALUATION, PATTERN_DETECTION, FORECAST_EVALUATION, SENSOR_ANALYSIS, FULL_CYCLE

    data_range_start = Column(DateTime, nullable=True)
    data_range_end = Column(DateTime, nullable=True)
    decisions_analyzed = Column(Integer, default=0)
    outcomes_created = Column(Integer, default=0)
    patterns_detected = Column(Integer, default=0)
    candidates_created = Column(Integer, default=0)
    candidates_updated = Column(Integer, default=0)

    analysis_version = Column(String(50), nullable=True)
    knowledge_version = Column(Integer, nullable=True)
    calibration_version = Column(Integer, nullable=True)

    summary = Column(JSON, nullable=True)
    status = Column(String(20), default="RUNNING")  # RUNNING, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    farm = relationship("Farm")


class PerformanceMetric(Base):
    """Periodic performance snapshots for trend tracking."""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), index=True, nullable=False)
    metric_type = Column(String(50), index=True, nullable=False)
    # DECISION_ACCURACY, EXECUTION_RELIABILITY, SENSOR_RELIABILITY,
    # FORECAST_RELIABILITY, WATER_EFFICIENCY, CROP_PERFORMANCE

    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    sample_size = Column(Integer, default=0)
    value = Column(Float, nullable=True)
    breakdown = Column(JSON, nullable=True)
    is_sufficient_sample = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    farm = relationship("Farm")


class ImprovementVersion(Base):
    """Tracks versioned calibration improvements with full evidence chain."""
    __tablename__ = "improvement_versions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("learning_candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    calibration_id = Column(Integer, ForeignKey("field_calibration_records.id", ondelete="SET NULL"), nullable=True)
    previous_version = Column(Integer, nullable=True)
    new_version = Column(Integer, nullable=True)

    improvement_type = Column(String(50), nullable=True)
    # THRESHOLD_ADJUSTMENT, HYSTERESIS_CHANGE, DURATION_CHANGE
    reason = Column(Text, nullable=True)
    evidence_summary = Column(JSON, nullable=True)
    experiments = Column(JSON, nullable=True)  # Array of experiment IDs
    validation_id = Column(Integer, ForeignKey("knowledge_validation_records.id", ondelete="SET NULL"), nullable=True)

    confidence = Column(Integer, default=0)
    status = Column(String(50), default="PROPOSED")
    # PROPOSED, SHADOW_TESTING, APPROVED, ACTIVATED, ROLLED_BACK
    shadow_comparison = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    approved_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)

    candidate = relationship("LearningCandidate")
    calibration = relationship("FieldCalibrationRecord")

