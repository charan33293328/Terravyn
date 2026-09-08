from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from database.connection import get_db
from schemas.domain import (
    UserCreate, UserResponse, Token, UserUpdate, 
    UsernameCheckRequest, SendEmailOTPRequest, VerifyEmailOTPRequest, 
    SendPhoneOTPRequest, VerifyPhoneOTPRequest, ForgotPasswordRequest, ResetPasswordRequest
)
import secrets
from auth.security import get_password_hash, verify_password, create_access_token, get_current_active_user
from models.domain import User, VerificationRecord
from utils.verification import generate_otp, hash_otp, send_phone_otp
from services.email_service import send_otp_email, send_password_reset_email
from datetime import datetime, timedelta
router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/check-username")
def check_username(request: UsernameCheckRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()
    if user:
        return {"available": False}
    return {"available": True}

@router.post("/send-email-otp")
def send_email_otp_route(request: SendEmailOTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    otp = generate_otp()
    hashed = hash_otp(otp)
    
    # Clean expired records for this email
    db.query(VerificationRecord).filter(
        VerificationRecord.identifier == request.email,
        VerificationRecord.expires_at < datetime.utcnow()
    ).delete()
    
    # Store OTP
    record = VerificationRecord(
        identifier=request.email,
        otp_hash=hashed,
        otp_type="EMAIL",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(record)
    db.commit()
    
    send_otp_email(request.email, otp, request.full_name)
    return {"message": "OTP sent successfully"}

@router.post("/verify-email-otp")
def verify_email_otp_route(request: VerifyEmailOTPRequest, db: Session = Depends(get_db)):
    record = db.query(VerificationRecord).filter(
        VerificationRecord.identifier == request.email,
        VerificationRecord.otp_type == "EMAIL",
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
    return {"message": "Email verified successfully."}

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
    
    send_phone_otp(request.phone_number, otp)
    return {"message": "OTP sent successfully"}

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
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    db_username = db.query(User).filter(User.username == user.username).first()
    if db_username:
        raise HTTPException(status_code=400, detail="Username already registered")
        
    db_phone = db.query(User).filter(User.phone_number == user.phone_number).first()
    if db_phone:
        raise HTTPException(status_code=400, detail="Phone number already registered")
        
    # Check if email is verified
    email_record = db.query(VerificationRecord).filter(
        VerificationRecord.identifier == user.email,
        VerificationRecord.otp_type == "EMAIL",
        VerificationRecord.verified == True
    ).first()
    
    if not email_record:
        raise HTTPException(status_code=400, detail="Email not verified")
        
    # Check if phone is verified
    phone_record = db.query(VerificationRecord).filter(
        VerificationRecord.identifier == user.phone_number,
        VerificationRecord.otp_type == "PHONE",
        VerificationRecord.verified == True
    ).first()
    
    if not phone_record:
        raise HTTPException(status_code=400, detail="Phone number not verified")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        phone_number=user.phone_number,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role,
        is_email_verified=True,
        is_phone_verified=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

from sqlalchemy import or_, func

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
    
    # Assume frontend is at localhost:5173 for local dev, but should ideally use env var
    import os
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?email={user.email}&token={token}"
    
    send_password_reset_email(user.email, reset_link, user.full_name)
    return {"message": "If an account with that email exists, we sent a password reset link."}

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
