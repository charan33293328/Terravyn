from fastapi import Depends, HTTPException, status
from models.domain import User
from auth.security import get_current_user

def require_admin_role(current_user: User = Depends(get_current_user)):
    """
    Dependency to ensure the current user has administrative privileges.
    Allows both SUPER_ADMIN and ADMIN roles.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
        
    admin_roles = ["super_admin", "admin"]
    
    if current_user.role not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have the required administrative privileges to perform this action.",
        )
        
    return current_user

def require_super_admin_role(current_user: User = Depends(get_current_user)):
    """
    Dependency to ensure the current user is specifically a SUPER_ADMIN.
    Used for highly sensitive operations (e.g., deleting other admins, system-wide config).
    """
    if not current_user or current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Super Administrators can perform this action.",
        )
        
    return current_user
