from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from models.domain import Role, Permission, RolePermission, AuditLog, User
from schemas.rbac import RoleCreate, RoleUpdate, RoleOut, PermissionOut
from auth.security import get_current_user
from typing import List

router = APIRouter()

def log_audit(db: Session, admin_id: int, action: str, resource: str):
    log = AuditLog(admin_id=admin_id, action=action, resource=resource, ip_address="127.0.0.1")
    db.add(log)

@router.get("/permissions", response_model=List[PermissionOut])
def get_permissions(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Permission).all()

@router.get("/roles", response_model=List[RoleOut])
def get_roles(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    roles = db.query(Role).all()
    # Populate permissions manually or via relationship. We'll fetch them.
    result = []
    for role in roles:
        role_dict = role.__dict__.copy()
        perms = db.query(Permission).join(RolePermission).filter(RolePermission.role_id == role.id).all()
        role_dict["permissions"] = perms
        result.append(role_dict)
    return result

@router.post("/roles", response_model=RoleOut)
def create_role(data: RoleCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    role = Role(name=data.name, description=data.description)
    db.add(role)
    db.commit()
    db.refresh(role)

    for p_id in data.permission_ids:
        db.add(RolePermission(role_id=role.id, permission_id=p_id))
    
    db.commit()
    log_audit(db, current_user.id, f"Created Role {role.name}", "Role")

    role_dict = role.__dict__.copy()
    role_dict["permissions"] = db.query(Permission).join(RolePermission).filter(RolePermission.role_id == role.id).all()
    return role_dict

@router.put("/roles/{role_id}", response_model=RoleOut)
def update_role(role_id: int, data: RoleUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    role.name = data.name
    role.description = data.description

    if data.permission_ids is not None:
        db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
        for p_id in data.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))

    db.commit()
    log_audit(db, current_user.id, f"Updated Role {role.name}", "Role")

    role_dict = role.__dict__.copy()
    role_dict["permissions"] = db.query(Permission).join(RolePermission).filter(RolePermission.role_id == role.id).all()
    return role_dict

@router.delete("/roles/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system role")
    
    # Reassign users to a default role or handle them. Here we just set role_id to null
    db.query(User).filter(User.role_id == role.id).update({"role_id": None})
    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
    db.delete(role)
    db.commit()
    log_audit(db, current_user.id, f"Deleted Role {role.name}", "Role")
    return {"message": "Role deleted successfully"}
