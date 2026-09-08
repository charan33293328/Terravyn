from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PermissionBase(BaseModel):
    name: str
    module: str
    description: Optional[str] = None

class PermissionOut(PermissionBase):
    id: int
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: List[int] = []

class RoleUpdate(RoleBase):
    permission_ids: Optional[List[int]] = None

class RoleOut(RoleBase):
    id: int
    is_system: bool
    created_at: datetime
    permissions: List[PermissionOut] = []

    class Config:
        from_attributes = True
