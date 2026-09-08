import uuid
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from models.domain import Device, User, RoleEnum
from schemas.domain import DeviceResponse, DeviceCreate, UserResponse, AdminProfileUpdate, AdminPasswordChange
from auth.security import get_current_active_user, verify_password, get_password_hash

router = APIRouter(prefix="/api/admin", tags=["admin"])

def check_admin(current_user: User):
    if current_user.role not in [RoleEnum.admin, RoleEnum.super_admin]:
        raise HTTPException(status_code=403, detail="Not authorized. Admin access required.")
    return current_user

@router.get("/profile", response_model=UserResponse)
def get_admin_profile(current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_admin_profile(update_data: AdminProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    # Check if email is being changed and is already taken
    if update_data.email != current_user.email:
        if db.query(User).filter(User.email == update_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
            
    # Check if username is being changed and is already taken
    if update_data.username != current_user.username:
        if db.query(User).filter(User.username == update_data.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")

    current_user.full_name = update_data.full_name
    current_user.username = update_data.username
    current_user.email = update_data.email
    current_user.phone_number = update_data.phone_number
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/profile/change-password")
def change_admin_password(pwd_data: AdminPasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    if not verify_password(pwd_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
        
    if pwd_data.new_password != pwd_data.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")
        
    if len(pwd_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
        
    current_user.hashed_password = get_password_hash(pwd_data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@router.post("/create-device", response_model=DeviceResponse)
def create_device(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    
    # Generate secrets
    new_device_uid = "TRV-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    new_activation_code = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    new_device_secret = secrets.token_hex(16)
    
    db_device = Device(
        device_uid=new_device_uid,
        activation_code=new_activation_code,
        device_secret=new_device_secret,
        status="offline"
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    
    return db_device

@router.get("/devices", response_model=List[DeviceResponse])
def get_all_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    devices = db.query(Device).offset(skip).limit(limit).all()
    return devices

@router.get("/devices/unclaimed", response_model=List[DeviceResponse])
def get_unclaimed_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    devices = db.query(Device).filter(Device.owner_id == None).offset(skip).limit(limit).all()
    return devices

@router.get("/devices/claimed", response_model=List[DeviceResponse])
def get_claimed_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    check_admin(current_user)
    devices = db.query(Device).filter(Device.owner_id != None).offset(skip).limit(limit).all()
    return devices
