import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine, SessionLocal
from models.domain import (
    Base, User, RoleEnum, Role, Permission, RolePermission,
    PlatformSettings, BrandingSettings, PaymentSettings, EmailSettings,
    NotificationSettings, DeviceDefaults, SecuritySettings, MaintenanceSchedule
)

def migrate():
    print("Creating new Phase 6F.3 settings and RBAC tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Singleton Settings
        print("Seeding default settings...")
        if not db.query(PlatformSettings).first():
            db.add(PlatformSettings())
        if not db.query(BrandingSettings).first():
            db.add(BrandingSettings())
        if not db.query(PaymentSettings).first():
            db.add(PaymentSettings())
        if not db.query(EmailSettings).first():
            db.add(EmailSettings())
        if not db.query(NotificationSettings).first():
            db.add(NotificationSettings())
        if not db.query(DeviceDefaults).first():
            db.add(DeviceDefaults())
        if not db.query(SecuritySettings).first():
            db.add(SecuritySettings())
        if not db.query(MaintenanceSchedule).first():
            db.add(MaintenanceSchedule())
        
        db.commit()

        # 2. Seed Permissions
        print("Seeding permissions...")
        permissions_data = [
            {"name": "Manage Devices", "module": "devices", "description": "Create, edit, and delete devices"},
            {"name": "Manage Orders", "module": "orders", "description": "Process and fulfill orders"},
            {"name": "Manage Customers", "module": "customers", "description": "Manage customer accounts"},
            {"name": "Manage Support", "module": "support", "description": "Respond to tickets"},
            {"name": "Manage CMS", "module": "cms", "description": "Edit landing page, FAQ, blog"},
            {"name": "Manage Settings", "module": "settings", "description": "Edit platform settings"},
            {"name": "View Analytics", "module": "analytics", "description": "View dashboard statistics"},
            {"name": "Export Reports", "module": "reports", "description": "Export CSV/PDF reports"}
        ]

        for p_data in permissions_data:
            existing = db.query(Permission).filter(Permission.name == p_data["name"]).first()
            if not existing:
                db.add(Permission(**p_data))
        
        db.commit()

        # 3. Seed Roles
        print("Seeding roles...")
        roles_data = [
            {"name": "Super Admin", "description": "Full access", "is_system": True},
            {"name": "Operations Admin", "description": "Orders & Devices", "is_system": True},
            {"name": "Support Admin", "description": "Customer Service", "is_system": True},
            {"name": "Content Admin", "description": "CMS Management", "is_system": True},
            {"name": "Analytics Viewer", "description": "Read only analytics", "is_system": True}
        ]

        for r_data in roles_data:
            existing = db.query(Role).filter(Role.name == r_data["name"]).first()
            if not existing:
                db.add(Role(**r_data))
        
        db.commit()

        # 4. Map Super Admin to all permissions
        super_admin_role = db.query(Role).filter(Role.name == "Super Admin").first()
        all_perms = db.query(Permission).all()

        for p in all_perms:
            existing_link = db.query(RolePermission).filter_by(role_id=super_admin_role.id, permission_id=p.id).first()
            if not existing_link:
                db.add(RolePermission(role_id=super_admin_role.id, permission_id=p.id))

        db.commit()

        # 5. Migrate Users
        print("Migrating existing users to dynamic roles...")
        admin_role = db.query(Role).filter(Role.name == "Operations Admin").first()
        support_role = db.query(Role).filter(Role.name == "Support Admin").first()

        users = db.query(User).all()
        for u in users:
            if not u.role_id:
                # Default assignments based on old Enum
                if u.role == RoleEnum.super_admin:
                    u.role_id = super_admin_role.id
                elif u.role == RoleEnum.admin or u.role == RoleEnum.operations_manager:
                    u.role_id = admin_role.id
                elif u.role == RoleEnum.support_agent:
                    u.role_id = support_role.id
                # user (customer) remains role_id = null for now, or we can map them to a Customer role.
                # The prompt asks for Admin RBAC, so customers might not need dynamic roles yet.
        
        db.commit()

        print("Migration complete!")

    except Exception as e:
        print("Error during migration:", e)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
