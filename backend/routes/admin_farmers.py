from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.domain import Farmer, Device, User, Order
from auth.rbac import require_admin_role
from schemas.farmers import FarmerCreate, FarmerUpdate, FarmerStatusUpdate, FarmerResponse, FarmerListResponse

router = APIRouter(prefix="/api/admin/farmers", tags=["Admin Farmers"])

@router.get("/", response_model=FarmerListResponse)
def get_farmers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    query = db.query(Farmer)
    
    if search:
        query = query.filter(
            or_(
                Farmer.full_name.ilike(f"%{search}%"),
                Farmer.phone.ilike(f"%{search}%"),
                Farmer.email.ilike(f"%{search}%"),
                Farmer.address.ilike(f"%{search}%"),
                Farmer.village.ilike(f"%{search}%")
            )
        )
        
    if status:
        query = query.filter(Farmer.status == status)
        
    total = query.count()
    farmers = query.order_by(desc(Farmer.created_at)).offset(skip).limit(limit).all()
    
    # Map to response with devices count
    results = []
    for f in farmers:
        count = db.query(Device).filter(Device.farmer_id == f.id).count()
        orders_count = db.query(Order).filter(Order.email == f.email).count()
        results.append(FarmerResponse(
            id=f.id,
            full_name=f.full_name,
            phone=f.phone,
            email=f.email,
            address=f.address,
            village=f.village,
            district=f.district,
            state=f.state,
            pincode=f.pincode,
            status=f.status,
            created_at=f.created_at,
            updated_at=f.updated_at,
            devices_count=count,
            orders_count=orders_count
        ))
        
    return {
        "items": results,
        "total": total,
        "page": (skip // limit) + 1,
        "size": limit
    }

@router.post("/", response_model=FarmerResponse)
def create_farmer(
    payload: FarmerCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    # Check for unique constraints
    if db.query(Farmer).filter(Farmer.phone == payload.phone).first():
        raise HTTPException(status_code=400, detail="Phone number is already registered")
        
    if db.query(Farmer).filter(Farmer.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")
        
    new_farmer = Farmer(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        village=payload.village,
        district=payload.district,
        state=payload.state,
        pincode=payload.pincode,
        status="ACTIVE"
    )
    
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)
    
    return FarmerResponse(
        id=new_farmer.id,
        full_name=new_farmer.full_name,
        phone=new_farmer.phone,
        email=new_farmer.email,
        address=new_farmer.address,
        village=new_farmer.village,
        district=new_farmer.district,
        state=new_farmer.state,
        pincode=new_farmer.pincode,
        status=new_farmer.status,
        created_at=new_farmer.created_at,
        updated_at=new_farmer.updated_at,
        devices_count=0
    )

@router.get("/{farmer_id}")
def get_farmer_details(
    farmer_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
        
    devices = db.query(Device).filter(Device.farmer_id == farmer_id).all()
    
    device_list = []
    for d in devices:
        device_list.append({
            "id": d.id,
            "device_uid": d.device_uid,
            "mac_address": d.mac_address,
            "assigned_at": d.assigned_at,
            "is_active": d.is_active,
            "claim_status": d.claim_status
        })
        
    return {
        "farmer": FarmerResponse(
            id=farmer.id,
            full_name=farmer.full_name,
            phone=farmer.phone,
            email=farmer.email,
            address=farmer.address,
            village=farmer.village,
            district=farmer.district,
            state=farmer.state,
            pincode=farmer.pincode,
            status=farmer.status,
            created_at=farmer.created_at,
            updated_at=farmer.updated_at,
            devices_count=len(devices)
        ),
        "devices": device_list
    }

@router.put("/{farmer_id}", response_model=FarmerResponse)
def update_farmer(
    farmer_id: int,
    payload: FarmerUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
        
    # Check constraints if changing email/phone
    if payload.phone and payload.phone != farmer.phone:
        if db.query(Farmer).filter(Farmer.phone == payload.phone).first():
            raise HTTPException(status_code=400, detail="Phone number is already registered")
            
    if payload.email and payload.email != farmer.email:
        if db.query(Farmer).filter(Farmer.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email is already registered")
            
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(farmer, key, value)
        
    db.commit()
    db.refresh(farmer)
    
    count = db.query(Device).filter(Device.farmer_id == farmer.id).count()
    return FarmerResponse(
        id=farmer.id,
        full_name=farmer.full_name,
        phone=farmer.phone,
        email=farmer.email,
        address=farmer.address,
        village=farmer.village,
        district=farmer.district,
        state=farmer.state,
        pincode=farmer.pincode,
        status=farmer.status,
        created_at=farmer.created_at,
        updated_at=farmer.updated_at,
        devices_count=count
    )

@router.put("/{farmer_id}/status")
def update_farmer_status(
    farmer_id: int,
    payload: FarmerStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin_role)
):
    farmer = db.query(Farmer).filter(Farmer.id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
        
    if payload.status not in ["ACTIVE", "INACTIVE"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    farmer.status = payload.status
    db.commit()
    
    return {"status": "success", "message": f"Farmer status updated to {payload.status}"}
