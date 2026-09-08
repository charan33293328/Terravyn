import os
import shutil
import json
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database.connection import get_db
from models.domain import (
    User, Farmer, FarmerNotificationPreference, 
    FarmerSession, FarmerActivityLog, Device, Farm, Order, SupportTicket
)
from schemas.profile import (
    FarmerProfileResponse, FarmerProfileUpdate, PasswordChangeRequest,
    NotificationPreferencesSchema, FarmerSessionSchema, ActivityListResponse,
    FarmerActivityResponse, AccountDeactivationRequest
)
from auth.security import get_current_active_user, verify_password, get_password_hash

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_INSTALLED = True
except ImportError:
    REPORTLAB_INSTALLED = False

router = APIRouter(prefix="/profile", tags=["Farmer Profile"])

def get_farmer(db: Session, user: User) -> Farmer:
    farmer = db.query(Farmer).filter(
        (Farmer.email == user.email) | (Farmer.phone == user.phone_number)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer profile not found.")
    return farmer

def log_activity(db: Session, farmer_id: int, activity_type: str, description: str, source: str = "Farmer Panel"):
    log = FarmerActivityLog(
        farmer_id=farmer_id,
        activity_type=activity_type,
        description=description,
        source=source
    )
    db.add(log)
    db.commit()

# ==========================================
# Personal Information
# ==========================================

@router.get("", response_model=FarmerProfileResponse)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    return get_farmer(db, current_user)

@router.put("", response_model=FarmerProfileResponse)
def update_profile(
    full_name: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    profile_photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    
    updated = False
    if full_name is not None and full_name != farmer.full_name:
        farmer.full_name = full_name
        current_user.full_name = full_name
        updated = True
        
    if username is not None and username != farmer.username:
        # Check if username is taken
        existing = db.query(Farmer).filter(Farmer.username == username, Farmer.id != farmer.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username is already taken.")
        farmer.username = username
        updated = True

    if profile_photo:
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if profile_photo.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file format.")
            
        # Store in /uploads/profile-photos/{farmer_id}/
        upload_dir = f"uploads/profile-photos/{farmer.id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = profile_photo.filename.split('.')[-1]
        file_name = f"profile_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{file_extension}"
        file_path = os.path.join(upload_dir, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(profile_photo.file, buffer)
            
        farmer.profile_photo = f"/{file_path}"
        updated = True

    if updated:
        db.commit()
        db.refresh(farmer)
        log_activity(db, farmer.id, "PROFILE_UPDATED", "Personal information was updated.")

    return farmer

# ==========================================
# Security Settings
# ==========================================

@router.put("/change-password")
def change_password(request: PasswordChangeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
        
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")
        
    # Basic validation (could be enhanced)
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")
        
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    
    log_activity(db, farmer.id, "PASSWORD_CHANGED", "Account password was changed successfully.")
    
    return {"message": "Password changed successfully."}

@router.get("/sessions", response_model=List[FarmerSessionSchema])
def get_sessions(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    # In a real JWT stateless setup, we might extract the jti from the token to mark the current session.
    # For now, we return all sessions matching the farmer.
    sessions = db.query(FarmerSession).filter(FarmerSession.farmer_id == farmer.id).order_by(FarmerSession.last_active_at.desc()).all()
    
    # If no sessions exist in DB (first time viewing), let's create a mock current session for demonstration.
    if not sessions:
        mock_session = FarmerSession(
            session_id="mock-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            farmer_id=farmer.id,
            ip_address=request.client.host if request.client else "127.0.0.1",
            user_agent=request.headers.get("user-agent", "Unknown Browser"),
            is_current_session=True
        )
        db.add(mock_session)
        db.commit()
        db.refresh(mock_session)
        sessions = [mock_session]
        
    return sessions

@router.delete("/sessions/{session_id}")
def terminate_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    session = db.query(FarmerSession).filter(FarmerSession.session_id == session_id, FarmerSession.farmer_id == farmer.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    if session.is_current_session:
        raise HTTPException(status_code=400, detail="Cannot terminate current session here. Please log out instead.")
        
    db.delete(session)
    db.commit()
    
    log_activity(db, farmer.id, "SESSION_TERMINATED", f"Session {session_id} was terminated.")
    return {"message": "Session terminated successfully."}

@router.delete("/sessions")
def terminate_all_other_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    # Delete all non-current sessions
    db.query(FarmerSession).filter(
        FarmerSession.farmer_id == farmer.id,
        FarmerSession.is_current_session == False
    ).delete()
    
    db.commit()
    
    log_activity(db, farmer.id, "SESSIONS_TERMINATED", "All other active sessions were terminated.")
    return {"message": "All other sessions terminated successfully."}

# ==========================================
# Notification Preferences
# ==========================================

@router.get("/notifications", response_model=NotificationPreferencesSchema)
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    prefs = db.query(FarmerNotificationPreference).filter(FarmerNotificationPreference.farmer_id == farmer.id).first()
    if not prefs:
        prefs = FarmerNotificationPreference(farmer_id=farmer.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        
    return prefs

@router.put("/notifications", response_model=NotificationPreferencesSchema)
def update_notifications(prefs: NotificationPreferencesSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    db_prefs = db.query(FarmerNotificationPreference).filter(FarmerNotificationPreference.farmer_id == farmer.id).first()
    if not db_prefs:
        db_prefs = FarmerNotificationPreference(farmer_id=farmer.id)
        db.add(db_prefs)
        
    for key, value in prefs.model_dump().items():
        setattr(db_prefs, key, value)
        
    db.commit()
    db.refresh(db_prefs)
    
    log_activity(db, farmer.id, "NOTIFICATION_SETTINGS_UPDATED", "Notification preferences were updated.")
    
    return db_prefs

# ==========================================
# Account Settings
# ==========================================

@router.get("/export")
def export_personal_data(format: str = Query("json", pattern="^(json|pdf)$"), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    # Gather data
    data = {
        "profile": {
            "full_name": farmer.full_name,
            "email": farmer.email,
            "phone": farmer.phone,
            "username": farmer.username,
            "joined_date": farmer.created_at.isoformat()
        },
        "devices_count": db.query(Device).filter(Device.farmer_id == farmer.id).count(),
        "farms_count": db.query(Farm).filter(Farm.farmer_id == farmer.id).count(),
        "orders_count": db.query(Order).filter(Order.farmer_id == farmer.id).count(),
        "support_tickets_count": db.query(SupportTicket).filter(SupportTicket.farmer_id == farmer.id).count()
    }
    
    log_activity(db, farmer.id, "DATA_EXPORTED", f"Personal data exported in {format.upper()} format.")
    
    if format == "json":
        return data
        
    if format == "pdf":
        if not REPORTLAB_INSTALLED:
            raise HTTPException(status_code=500, detail="PDF generation library not available.")
            
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 750, "TERRAVYN Personal Data Export")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, 710, f"Name: {farmer.full_name}")
        c.drawString(50, 690, f"Email: {farmer.email}")
        c.drawString(50, 670, f"Phone: {farmer.phone}")
        c.drawString(50, 650, f"Joined: {farmer.created_at.strftime('%Y-%m-%d')}")
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 610, "Summary Statistics")
        c.setFont("Helvetica", 12)
        c.drawString(50, 580, f"Registered Devices: {data['devices_count']}")
        c.drawString(50, 560, f"Registered Farms: {data['farms_count']}")
        c.drawString(50, 540, f"Total Orders: {data['orders_count']}")
        c.drawString(50, 520, f"Support Tickets: {data['support_tickets_count']}")
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return StreamingResponse(
            buffer, 
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=terravyn_data_export.pdf"}
        )

@router.post("/deactivate")
def deactivate_account(request: AccountDeactivationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer(db, current_user)
    
    if not verify_password(request.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password.")
        
    farmer.status = "DEACTIVATION_REQUESTED"
    db.commit()
    
    log_activity(db, farmer.id, "ACCOUNT_DEACTIVATION_REQUESTED", f"Account deactivation requested. Reason: {request.reason}")
    
    return {"message": "Account deactivation request submitted successfully."}

# ==========================================
# Activity History
# ==========================================

@router.get("/activity", response_model=ActivityListResponse)
def get_activity_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer(db, current_user)
    
    query = db.query(FarmerActivityLog).filter(FarmerActivityLog.farmer_id == farmer.id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(FarmerActivityLog.description.ilike(search_term))
        
    if activity_type and activity_type != "All":
        query = query.filter(FarmerActivityLog.activity_type == activity_type)
        
    total_count = query.count()
    
    activities = query.order_by(FarmerActivityLog.created_at.desc()) \
                      .offset((page - 1) * page_size) \
                      .limit(page_size) \
                      .all()
                      
    return {
        "items": activities,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size if page_size > 0 else 0
    }
