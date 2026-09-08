from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from database.connection import get_db, settings
from schemas.domain import (
    UserCreate, UserResponse, Token, UserUpdate, 
    UsernameCheckRequest, CheckEmailRequest, SendEmailOTPRequest, VerifyEmailOTPRequest, 
    SendPhoneOTPRequest, VerifyPhoneOTPRequest, ForgotPasswordRequest, ResetPasswordRequest
)
import secrets
from auth.security import get_password_hash, verify_password, create_access_token, get_current_active_user
from models.domain import User, VerificationRecord
from utils.verification import generate_otp, hash_otp, send_phone_otp
from services.email_service import send_otp_email, send_password_reset_email, validate_email_for_terravyn
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/check-username")
def check_username(request: UsernameCheckRequest, db: Session = Depends(get_db)):
    clean_username = request.username.strip()
    user = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
    if user:
        return {"available": False}
    return {"available": True}

@router.post("/login/check-email")
@router.post("/check-email")
def check_email_for_login(request: CheckEmailRequest, db: Session = Depends(get_db)):
    """
    Validates email format, domain, and MX deliverability,
    and checks whether an active account exists in Terravyn.
    """
    raw_identifier = (request.email or "").strip()
    if not raw_identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter your email address or username."
        )

    if "@" in raw_identifier:
        # Validate format, domain existence, and MX records via validate_email_for_terravyn
        normalized_email = validate_email_for_terravyn(raw_identifier)
        user = db.query(User).filter(func.lower(User.email) == normalized_email.lower()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Terravyn account found with this email address. Please check your email or create an account."
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated. Please contact support."
            )
        return {
            "success": True,
            "registered": True,
            "type": "email",
            "email": normalized_email,
            "full_name": user.full_name,
            "message": "Email verified. Please enter your password."
        }
    else:
        # Username check
        user = db.query(User).filter(func.lower(User.username) == raw_identifier.lower()).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Terravyn account found with this username. Please check your username or create an account."
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated. Please contact support."
            )
        return {
            "success": True,
            "registered": True,
            "type": "username",
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "message": "Account verified. Please enter your password."
        }

@router.post("/register/request-email-verification")
@router.post("/send-email-otp")
def send_email_otp_route(request: SendEmailOTPRequest, db: Session = Depends(get_db)):
    # 1. Validate email syntax, domain existence, and MX deliverability
    normalized_email = validate_email_for_terravyn(request.email)
    
    # 2. Check if an account is already registered with this email
    user = db.query(User).filter(func.lower(User.email) == normalized_email.lower()).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="An account with this email already exists. Please login instead."
        )
        
    otp = generate_otp()
    hashed = hash_otp(otp)
    
    # Clean expired records for this email
    db.query(VerificationRecord).filter(
        func.lower(VerificationRecord.identifier) == normalized_email.lower(),
        VerificationRecord.expires_at < datetime.utcnow()
    ).delete()
    
    # Store OTP (10 min expiry)
    record = VerificationRecord(
        identifier=normalized_email,
        otp_hash=hashed,
        otp_type="EMAIL",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(record)
    db.commit()
    
    email_sent = send_otp_email(normalized_email, otp, request.full_name)
    if email_sent:
        return {"message": "Verification OTP sent to your email successfully.", "email_sent": True}
    else:
        return {
            "message": f"Verification code generated (Test/Dev mode OTP: {otp})",
            "email_sent": False,
            "dev_otp": otp
        }

@router.post("/register/verify-email")
@router.post("/verify-email-otp")
def verify_email_otp_route(request: VerifyEmailOTPRequest, db: Session = Depends(get_db)):
    clean_email = (request.email or "").strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Email is required.")
        
    record = db.query(VerificationRecord).filter(
        func.lower(VerificationRecord.identifier) == clean_email,
        VerificationRecord.otp_type == "EMAIL",
        VerificationRecord.verified == False,
        VerificationRecord.expires_at > datetime.utcnow()
    ).order_by(VerificationRecord.created_at.desc()).first()
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
        
    if record.attempt_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum verification attempts reached. Please request a new code.")
        
    record.attempt_count += 1
    
    if record.otp_hash != hash_otp(request.otp.strip()):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid verification code.")
        
    record.verified = True
    db.commit()
    return {"message": "Email verified successfully.", "verified": True}

@router.post("/send-phone-otp")
def send_phone_otp_route(request: SendPhoneOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone_number == request.phone_number).first()
    if user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
        
    otp = generate_otp()
    hashed = hash_otp(otp)
    
    # Clean expired records for this phone number
    db.query(VerificationRecord).filter(
        VerificationRecord.identifier == request.phone_number,
        VerificationRecord.expires_at < datetime.utcnow()
    ).delete()
    
    # Store OTP
    record = VerificationRecord(
        identifier=request.phone_number,
        otp_hash=hashed,
        otp_type="PHONE",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(record)
    db.commit()
    
    sms_sent = send_phone_otp(request.phone_number, otp)
    if sms_sent and settings.TWILIO_ACCOUNT_SID:
        return {"message": "Verification code sent to your mobile phone.", "sms_sent": True}
    else:
        return {
            "message": f"Verification code generated (Test/Dev mode OTP: {otp})",
            "sms_sent": False,
            "dev_otp": otp
        }

@router.post("/verify-phone-otp")
def verify_phone_otp_route(request: VerifyPhoneOTPRequest, db: Session = Depends(get_db)):
    record = db.query(VerificationRecord).filter(
        VerificationRecord.identifier == request.phone_number,
        VerificationRecord.otp_type == "PHONE",
        VerificationRecord.verified == False,
        VerificationRecord.expires_at > datetime.utcnow()
    ).order_by(VerificationRecord.created_at.desc()).first()
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
        
    if record.attempt_count >= 5:
        raise HTTPException(status_code=400, detail="Maximum verification attempts reached.")
        
    record.attempt_count += 1
    
    if record.otp_hash != hash_otp(request.otp):
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")
        
    record.verified = True
    db.commit()
    return {"message": "Phone number verified successfully."}

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    clean_email = user.email.strip().lower()
    clean_username = user.username.strip()
    clean_phone = user.phone_number.strip()

    db_user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="An account with this email already exists. Please login instead.")
        
    db_username = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
    if db_username:
        raise HTTPException(status_code=400, detail="Username already registered.")
        
    db_phone = db.query(User).filter(User.phone_number == clean_phone).first()
    if db_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered.")
        
    # Check if email is verified
    email_record = db.query(VerificationRecord).filter(
        func.lower(VerificationRecord.identifier) == clean_email,
        VerificationRecord.otp_type == "EMAIL",
        VerificationRecord.verified == True
    ).order_by(VerificationRecord.created_at.desc()).first()
    
    if not email_record:
        raise HTTPException(status_code=400, detail="Email verification is required before creating an account.")
        
    # Check if phone is verified
    phone_record = db.query(VerificationRecord).filter(
        VerificationRecord.identifier == clean_phone,
        VerificationRecord.otp_type == "PHONE",
        VerificationRecord.verified == True
    ).order_by(VerificationRecord.created_at.desc()).first()
    
    if not phone_record:
        raise HTTPException(status_code=400, detail="Phone number verification is required.")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=clean_email,
        username=clean_username,
        phone_number=clean_phone,
        hashed_password=hashed_password,
        full_name=user.full_name.strip(),
        role=user.role,
        is_email_verified=True,
        is_phone_verified=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(
        or_(
            func.lower(User.email) == form_data.username.lower(),
            func.lower(User.username) == form_data.username.lower()
        )
    ).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(user_update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
    if user_update.preferred_language is not None:
        current_user.preferred_language = user_update.preferred_language
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/forgot-password")
def forgot_password_route(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == request.email.lower()).first()
    if not user:
        # We still return success to prevent email enumeration
        return {"message": "If an account with that email exists, we sent a password reset link."}
        
    token = secrets.token_urlsafe(32)
    hashed = hash_otp(token)
    
    # Clean expired records
    db.query(VerificationRecord).filter(
        VerificationRecord.identifier == user.email,
        VerificationRecord.otp_type == "RESET",
        VerificationRecord.expires_at < datetime.utcnow()
    ).delete()
    
    record = VerificationRecord(
        identifier=user.email,
        otp_hash=hashed,
        otp_type="RESET",
        expires_at=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(record)
    db.commit()
    
    frontend_url = (settings.FRONTEND_URL or "https://terravyn.vercel.app").rstrip("/")
    reset_link = f"{frontend_url}/reset-password?email={user.email}&token={token}"
    
    email_sent = send_password_reset_email(user.email, reset_link, user.full_name)
    if email_sent:
        return {"message": "If an account with that email exists, we sent a password reset link."}
    else:
        return {
            "message": "Password reset link generated. (Test/Dev mode active)",
            "reset_link": reset_link
        }

@router.post("/reset-password")
def reset_password_route(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    record = db.query(VerificationRecord).filter(
        VerificationRecord.identifier == request.email,
        VerificationRecord.otp_type == "RESET",
        VerificationRecord.verified == False,
        VerificationRecord.expires_at > datetime.utcnow()
    ).order_by(VerificationRecord.created_at.desc()).first()
    
    if not record or record.otp_hash != hash_otp(request.token):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.hashed_password = get_password_hash(request.new_password)
    record.verified = True
    db.commit()
    
    return {"message": "Password has been reset successfully"}
