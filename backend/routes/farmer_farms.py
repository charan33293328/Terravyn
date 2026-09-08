import io
import csv
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from models.domain import User, Farmer, Farm, Device
from schemas.domain import FarmCreate, FarmUpdate, FarmResponse
from auth.security import get_current_active_user

router = APIRouter()

def get_farmer_from_user(db: Session, user: User):
    conditions = [func.lower(Farmer.email) == func.lower(user.email)]
    if user.phone_number:
        conditions.append(Farmer.phone == user.phone_number)
    return db.query(Farmer).filter(or_(*conditions)).first()

@router.get("/api/farmer/farms", response_model=List[FarmResponse])
def get_farmer_farms(
    search: Optional[str] = None,
    status: Optional[str] = None,
    crop_type: Optional[str] = None,
    sort_by: Optional[str] = Query("created_at"),
    sort_desc: Optional[bool] = Query(True),
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        return []

    query = db.query(Farm).filter(Farm.farmer_id == farmer.id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Farm.name.ilike(search_term),
                Farm.crop_type.ilike(search_term),
                Farm.village.ilike(search_term),
                Farm.district.ilike(search_term),
            )
        )
    if status and status != "ALL":
        query = query.filter(Farm.status == status)
    if crop_type and crop_type != "ALL":
        query = query.filter(Farm.crop_type == crop_type)
        
    sort_column = getattr(Farm, sort_by, Farm.created_at)
    if sort_desc:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
        
    farms = query.offset(offset).limit(limit).all()
    
    # Calculate device count for each farm
    response = []
    for farm in farms:
        device_count = db.query(Device).filter(Device.farm_id == farm.id).count()
        farm_dict = farm.__dict__.copy()
        farm_dict["device_count"] = device_count
        response.append(farm_dict)
        
    return response

@router.post("/api/farmer/farms", response_model=FarmResponse)
def create_farmer_farm(payload: FarmCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        farmer = Farmer(
            full_name=current_user.full_name or "Unknown Farmer",
            email=current_user.email,
            phone=current_user.phone_number or "N/A",
            address="N/A"
        )
        db.add(farmer)
        db.flush()
        
    new_farm = Farm(
        name=payload.name,
        farmer_id=farmer.id,
        crop_type=payload.crop_type,
        area=payload.area,
        area_unit=payload.area_unit,
        description=payload.description,
        status=payload.status,
        expected_harvest_date=payload.expected_harvest_date,
        village=payload.village,
        district=payload.district,
        state=payload.state,
        country=payload.country,
        latitude=payload.latitude,
        longitude=payload.longitude,
        sowing_date=payload.sowing_date,
        crop_variety=payload.crop_variety,
        soil_type=payload.soil_type,
        plot_type=payload.plot_type or "STANDARD",
        experiment_active=payload.experiment_active or False,
        growth_stage_override=payload.growth_stage_override
    )
    db.add(new_farm)
    db.commit()
    db.refresh(new_farm)
    
    farm_dict = new_farm.__dict__.copy()
    farm_dict["device_count"] = 0
    return farm_dict

@router.get("/api/farmer/farms/export")
def export_farmer_farms(
    format: str = "csv",
    search: Optional[str] = None,
    status: Optional[str] = None,
    crop_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")

    query = db.query(Farm).filter(Farm.farmer_id == farmer.id)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Farm.name.ilike(search_term),
                Farm.crop_type.ilike(search_term),
                Farm.village.ilike(search_term),
            )
        )
    if status and status != "ALL":
        query = query.filter(Farm.status == status)
    if crop_type and crop_type != "ALL":
        query = query.filter(Farm.crop_type == crop_type)
        
    farms = query.order_by(Farm.name.asc()).all()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"terravyn_farms_{timestamp}"
    headers = ["Farm Name", "Crop Type", "Area", "Location", "Status", "Number of Devices", "Created Date"]
    
    rows = []
    for f in farms:
        dev_count = db.query(Device).filter(Device.farm_id == f.id).count()
        loc_parts = [p for p in [f.village, f.district, f.state, f.country] if p]
        location_str = ", ".join(loc_parts) if loc_parts else "N/A"
        
        rows.append([
            f.name or "N/A",
            f.crop_type or "N/A",
            f"{f.area} {f.area_unit}" if f.area else "N/A",
            location_str,
            f.status or "N/A",
            dev_count,
            f.created_at.strftime("%Y-%m-%d") if f.created_at else "N/A"
        ])

    if format.lower() == "xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Farms"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        
        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return Response(
            content=stream.read(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
        )
    else:
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
        return Response(
            content=stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
        )

@router.get("/api/farmer/farms/{farm_id}", response_model=FarmResponse)
def get_farmer_farm_detail(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")
        
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    device_count = db.query(Device).filter(Device.farm_id == farm.id).count()
    farm_dict = farm.__dict__.copy()
    farm_dict["device_count"] = device_count
    return farm_dict

@router.put("/api/farmer/farms/{farm_id}", response_model=FarmResponse)
def update_farmer_farm(farm_id: int, payload: FarmUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")
        
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(farm, key, value)
        
    db.commit()
    db.refresh(farm)
    
    device_count = db.query(Device).filter(Device.farm_id == farm.id).count()
    farm_dict = farm.__dict__.copy()
    farm_dict["device_count"] = device_count
    return farm_dict

@router.delete("/api/farmer/farms/{farm_id}")
def delete_farmer_farm(farm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")
        
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    device_count = db.query(Device).filter(Device.farm_id == farm.id).count()
    if device_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete farm. Reassign or unlink devices first.")
        
    db.delete(farm)
    db.commit()
    return {"message": "Farm deleted successfully"}

@router.put("/api/farmer/farms/{farm_id}/devices/{device_id}")
def assign_device_to_farm(farm_id: int, device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")
        
    farm = db.query(Farm).filter(Farm.id == farm_id, Farm.farmer_id == farmer.id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
        
    device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found or not owned by you")
        
    device.farm_id = farm.id
    device.assigned_at = datetime.utcnow()
    device.device_status = "ASSIGNED"
    db.commit()
    return {"message": "Device assigned successfully"}

@router.delete("/api/farmer/farms/{farm_id}/devices/{device_id}")
def remove_device_from_farm(farm_id: int, device_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    farmer = get_farmer_from_user(db, current_user)
    if not farmer:
        raise HTTPException(status_code=403, detail="Farmer profile not found")
        
    device = db.query(Device).filter(Device.id == device_id, Device.owner_id == current_user.id, Device.farm_id == farm_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found in this farm")
        
    device.farm_id = None
    device.device_status = "UNASSIGNED"
    db.commit()
    return {"message": "Device removed from farm successfully"}
