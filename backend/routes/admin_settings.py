from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from models.domain import (
    PlatformSettings, BrandingSettings, PaymentSettings, EmailSettings,
    NotificationSettings, DeviceDefaults, SecuritySettings, AuditLog
)
from schemas.settings import (
    PlatformSettingsBase, BrandingSettingsBase, PaymentSettingsBase,
    PaymentSettingsResponse, EmailSettingsBase, EmailSettingsResponse,
    NotificationSettingsBase, DeviceDefaultsBase, SecuritySettingsBase
)
from utils.encryption import encrypt_value, decrypt_value
from auth.security import get_current_user

router = APIRouter()

def log_audit(db: Session, admin_id: int, action: str, resource: str):
    log = AuditLog(admin_id=admin_id, action=action, resource=resource, ip_address="127.0.0.1") # Simplification
    db.add(log)
    db.commit()

@router.get("/general", response_model=PlatformSettingsBase)
def get_general_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(PlatformSettings).first()
    if not settings:
        settings = PlatformSettings()
        db.add(settings)
        db.commit()
    return settings

@router.put("/general", response_model=PlatformSettingsBase)
def update_general_settings(data: PlatformSettingsBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(PlatformSettings).first()
    for key, value in data.model_dump().items():
        setattr(settings, key, value)
    db.commit()
    log_audit(db, current_user.id, "Update General Settings", "PlatformSettings")
    return settings

@router.get("/branding", response_model=BrandingSettingsBase)
def get_branding_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(BrandingSettings).first()
    if not settings:
        settings = BrandingSettings()
        db.add(settings)
        db.commit()
    return settings

@router.put("/branding", response_model=BrandingSettingsBase)
def update_branding_settings(data: BrandingSettingsBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(BrandingSettings).first()
    for key, value in data.model_dump().items():
        setattr(settings, key, value)
    db.commit()
    log_audit(db, current_user.id, "Update Branding Settings", "BrandingSettings")
    return settings

@router.get("/payment", response_model=PaymentSettingsResponse)
def get_payment_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(PaymentSettings).first()
    if not settings:
        settings = PaymentSettings()
        db.add(settings)
        db.commit()
    return {
        "razorpay_key_id": settings.razorpay_key_id,
        "has_razorpay_secret": bool(settings.razorpay_key_secret_encrypted),
        "enable_razorpay": settings.enable_razorpay,
        "enable_cod": settings.enable_cod,
        "max_cod_order_value": settings.max_cod_order_value,
        "cod_availability_regions": settings.cod_availability_regions
    }

@router.put("/payment", response_model=PaymentSettingsResponse)
def update_payment_settings(data: PaymentSettingsBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(PaymentSettings).first()
    
    settings.razorpay_key_id = data.razorpay_key_id
    if data.razorpay_key_secret: # Only update if provided
        settings.razorpay_key_secret_encrypted = encrypt_value(data.razorpay_key_secret)
    settings.enable_razorpay = data.enable_razorpay
    settings.enable_cod = data.enable_cod
    settings.max_cod_order_value = data.max_cod_order_value
    settings.cod_availability_regions = data.cod_availability_regions

    db.commit()
    log_audit(db, current_user.id, "Update Payment Settings", "PaymentSettings")
    
    return {
        "razorpay_key_id": settings.razorpay_key_id,
        "has_razorpay_secret": bool(settings.razorpay_key_secret_encrypted),
        "enable_razorpay": settings.enable_razorpay,
        "enable_cod": settings.enable_cod,
        "max_cod_order_value": settings.max_cod_order_value,
        "cod_availability_regions": settings.cod_availability_regions
    }

@router.get("/email", response_model=EmailSettingsResponse)
def get_email_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(EmailSettings).first()
    if not settings:
        settings = EmailSettings()
        db.add(settings)
        db.commit()
    return {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_username": settings.smtp_username,
        "has_smtp_password": bool(settings.smtp_password_encrypted),
        "encryption_type": settings.encryption_type,
        "sender_email": settings.sender_email,
        "sender_name": settings.sender_name
    }

@router.put("/email", response_model=EmailSettingsResponse)
def update_email_settings(data: EmailSettingsBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(EmailSettings).first()
    
    settings.smtp_host = data.smtp_host
    settings.smtp_port = data.smtp_port
    settings.smtp_username = data.smtp_username
    if data.smtp_password:
        settings.smtp_password_encrypted = encrypt_value(data.smtp_password)
    settings.encryption_type = data.encryption_type
    settings.sender_email = data.sender_email
    settings.sender_name = data.sender_name

    db.commit()
    log_audit(db, current_user.id, "Update Email Settings", "EmailSettings")

    return {
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "smtp_username": settings.smtp_username,
        "has_smtp_password": bool(settings.smtp_password_encrypted),
        "encryption_type": settings.encryption_type,
        "sender_email": settings.sender_email,
        "sender_name": settings.sender_name
    }

@router.get("/notifications", response_model=NotificationSettingsBase)
def get_notification_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(NotificationSettings).first()
    if not settings:
        settings = NotificationSettings()
        db.add(settings)
        db.commit()
    return settings

@router.put("/notifications", response_model=NotificationSettingsBase)
def update_notification_settings(data: NotificationSettingsBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(NotificationSettings).first()
    for key, value in data.model_dump().items():
        setattr(settings, key, value)
    db.commit()
    log_audit(db, current_user.id, "Update Notification Settings", "NotificationSettings")
    return settings

@router.get("/devices", response_model=DeviceDefaultsBase)
def get_device_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(DeviceDefaults).first()
    if not settings:
        settings = DeviceDefaults()
        db.add(settings)
        db.commit()
    return settings

@router.put("/devices", response_model=DeviceDefaultsBase)
def update_device_settings(data: DeviceDefaultsBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(DeviceDefaults).first()
    for key, value in data.model_dump().items():
        setattr(settings, key, value)
    db.commit()
    log_audit(db, current_user.id, "Update Device Settings", "DeviceDefaults")
    return settings

@router.get("/security", response_model=SecuritySettingsBase)
def get_security_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(SecuritySettings).first()
    if not settings:
        settings = SecuritySettings()
        db.add(settings)
        db.commit()
    return settings

@router.put("/security", response_model=SecuritySettingsBase)
def update_security_settings(data: SecuritySettingsBase, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    settings = db.query(SecuritySettings).first()
    for key, value in data.model_dump().items():
        setattr(settings, key, value)
    db.commit()
    log_audit(db, current_user.id, "Update Security Settings", "SecuritySettings")
    return settings
