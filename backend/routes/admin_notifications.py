import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database.connection import get_db
from models.domain import AdminNotification, User, RoleEnum
from schemas.domain import AdminNotificationResponse
from auth.security import get_current_active_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/api/admin/notifications", tags=["admin_notifications"])

def check_admin(current_user: User):
    if current_user.role not in [RoleEnum.admin, RoleEnum.super_admin]:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
    return current_user

@router.get("", response_model=List[AdminNotificationResponse])
def get_notifications(limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    notifications = db.query(AdminNotification).order_by(desc(AdminNotification.created_at)).limit(limit).all()
    return notifications

@router.put("/{notification_id}/read", response_model=AdminNotificationResponse)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    notif = db.query(AdminNotification).filter(AdminNotification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif
