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

import socket
import ssl
import urllib.request
import platform
import os
import logging

logger = logging.getLogger("uvicorn.error")

@router.get("/network-diagnostics")
def network_diagnostics_route():
    """
    Live diagnostic check for outbound DNS, general HTTPS, default network route, and SMTP ports.
    Logs full diagnostic summary to server logs and returns structured JSON.
    """
    # 1. Environment Detection
    is_render = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))
    if is_render:
        runtime_desc = "Render Cloud Web Service (Linux Container)"
    elif platform.system() == "Windows":
        runtime_desc = "Local Windows Host"
    elif platform.system() == "Linux":
        runtime_desc = "Linux Environment / Container"
    else:
        runtime_desc = f"{platform.system()} Environment"

    # 2. Check Default Network Route
    default_route_status = "ABSENT"
    default_route_detail = "No route found"
    try:
        # Use UDP connect (doesn't send packets) to inspect local outbound routing table
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        default_route_status = "PRESENT"
        default_route_detail = f"Local route active via {local_ip}"
    except Exception as e:
        default_route_detail = str(e)

    # 3. DNS Resolution for smtp.gmail.com
    dns_status = "FAIL"
    resolved_ips = []
    dns_error = None
    try:
        ips = socket.gethostbyname_ex("smtp.gmail.com")
        resolved_ips = ips[2]
        dns_status = "PASS"
    except Exception as e:
        dns_error = str(e)

    # 4. General Outbound HTTPS Internet Connectivity (Port 443)
    https_status = "FAIL"
    https_code = None
    https_error = None
    try:
        req = urllib.request.Request("https://www.google.com", headers={"User-Agent": "TERRAVYN/1.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            https_code = res.status
            if res.status == 200:
                https_status = "PASS"
    except Exception as e:
        https_error = str(e)

    # 5. Test SMTP TCP Ports 587, 465, 2525
    smtp_results = {}
    smtp_summary_log = {}

    for port in [587, 465, 2525]:
        try:
            sock = socket.create_connection(("smtp.gmail.com", port), timeout=4)
            sock.close()
            smtp_results[f"port_{port}"] = True
            smtp_results[f"port_{port}_status"] = "PASS"
            smtp_summary_log[port] = "PASS"
        except OSError as e:
            err_cls = "NETWORK_UNREACHABLE" if e.errno in (101, 10051) else type(e).__name__
            smtp_results[f"port_{port}"] = False
            smtp_results[f"port_{port}_error"] = f"{err_cls}: {str(e)}"
            smtp_summary_log[port] = f"FAIL ({err_cls} - {str(e)})"
        except Exception as e:
            smtp_results[f"port_{port}"] = False
            smtp_results[f"port_{port}_error"] = f"{type(e).__name__}: {str(e)}"
            smtp_summary_log[port] = f"FAIL ({type(e).__name__} - {str(e)})"

    # 6. Determine Classification (Case A vs Case B)
    if https_status == "PASS" and not any([smtp_results.get("port_587"), smtp_results.get("port_465"), smtp_results.get("port_2525")]):
        diagnosis_case = "CASE B: General HTTPS outbound internet is OPEN and functional (PASS), but outbound SMTP ports (587, 465, 2525) are blocked by the host/network egress firewall."
    elif https_status == "FAIL":
        diagnosis_case = "CASE A: Environment has no outbound internet access."
    else:
        diagnosis_case = "SMTP connection succeeded."

    # 7. Server-Side Diagnostic Logging
    logger.info("==================== [NETWORK DIAGNOSTICS] ====================")
    logger.info(f"Runtime: {runtime_desc} ({platform.platform()})")
    logger.info(f"Default Network Route: {default_route_status} ({default_route_detail})")
    logger.info(f"DNS smtp.gmail.com: {dns_status} (Resolved: {len(resolved_ips)} IPs)")
    logger.info(f"General HTTPS (Port 443): {https_status} (HTTP {https_code})")
    logger.info(f"SMTP TCP 587: {smtp_summary_log[587]}")
    logger.info(f"SMTP TCP 465: {smtp_summary_log[465]}")
    logger.info(f"SMTP TCP 2525: {smtp_summary_log[2525]}")
    logger.info(f"Conclusion: {diagnosis_case}")
    logger.info("================================================================")

    return {
        "environment": {
            "runtime": runtime_desc,
            "platform": platform.platform(),
            "python_version": platform.python_version()
        },
        "default_route": {
            "status": default_route_status,
            "detail": default_route_detail
        },
        "dns": {
            "status": dns_status,
            "smtp_gmail_resolves": dns_status == "PASS",
            "resolved_count": len(resolved_ips),
            "error": dns_error
        },
        "https": {
            "status": https_status,
            "outbound_connectivity": https_status == "PASS",
            "http_status": https_code,
            "error": https_error
        },
        "smtp": smtp_results,
        "diagnosis": diagnosis_case
    }

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
    
    # 3. Attempt email delivery first
    email_sent = send_otp_email(normalized_email, otp, request.full_name)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't send the verification code right now. Please try again later."
        )
    
    # 4. Clean expired records for this email and store new record upon successful delivery
    db.query(VerificationRecord).filter(
        func.lower(VerificationRecord.identifier) == normalized_email.lower(),
        VerificationRecord.expires_at < datetime.utcnow()
    ).delete()
    
    record = VerificationRecord(
        identifier=normalized_email,
        otp_hash=hashed,
        otp_type="EMAIL",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(record)
    db.commit()
    
    return {"message": "Verification code sent to your email successfully.", "email_sent": True}

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
    clean_phone = request.phone_number.strip()
    user = db.query(User).filter(User.phone_number == clean_phone).first()
    if user:
        raise HTTPException(status_code=400, detail="Phone number already registered")
        
    otp = generate_otp()
    hashed = hash_otp(otp)
    
    sms_sent = send_phone_otp(clean_phone, otp)
    if not sms_sent or not settings.TWILIO_ACCOUNT_SID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't send the verification SMS right now. Please try again later."
        )
    
    # Clean expired records for this phone number
    db.query(VerificationRecord).filter(
        VerificationRecord.identifier == clean_phone,
        VerificationRecord.expires_at < datetime.utcnow()
    ).delete()
    
    # Store OTP
    record = VerificationRecord(
        identifier=clean_phone,
        otp_hash=hashed,
        otp_type="PHONE",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(record)
    db.commit()
    
    return {"message": "Verification code sent to your mobile phone.", "sms_sent": True}

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
    if not email_sent:
        logger.error(f"[FORGOT_PASSWORD] Failed to deliver password reset email to {user.email}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We couldn't send the password reset email right now. Please try again later."
        )
        
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
