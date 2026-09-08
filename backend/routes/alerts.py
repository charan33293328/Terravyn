from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from models.domain import Alert, User, Device
from schemas.domain import AlertResponse
from auth.security import get_current_active_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

@router.get("/", response_model=List[AlertResponse])
def get_alerts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Get alerts for devices owned by user
    device_ids = [d.id for d in current_user.devices]
    alerts = db.query(Alert).filter(Alert.device_id.in_(device_ids)).order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    return alerts
