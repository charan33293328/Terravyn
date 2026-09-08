from database.connection import engine, SessionLocal
from models.domain import User, RoleEnum
from auth.security import get_password_hash

db = SessionLocal()

admin_email = "admin@terravyn.com"
password = "AdminPassword123!"

existing_user = db.query(User).filter(User.email == admin_email).first()

if not existing_user:
    new_user = User(
        email=admin_email,
        full_name="System Administrator",
        hashed_password=get_password_hash(password),
        role=RoleEnum.super_admin,
        is_active=True,
        preferred_language="en"
    )
    db.add(new_user)
    db.commit()
    print(f"Created admin account:\\nEmail: {admin_email}\\nPassword: {password}")
else:
    existing_user.role = RoleEnum.super_admin
    existing_user.hashed_password = get_password_hash(password)
    existing_user.is_active = True
    db.commit()
    print(f"Updated existing admin account:\\nEmail: {admin_email}\\nPassword: {password}")

db.close()
