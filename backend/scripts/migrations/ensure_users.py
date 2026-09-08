import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import SessionLocal
from models.domain import User
from auth.security import get_password_hash

def ensure_users():
    db = SessionLocal()
    
    # Check admin
    admin = db.query(User).filter(User.email == "admin@terravyn.com").first()
    if not admin:
        admin = User(
            email="admin@terravyn.com",
            hashed_password=get_password_hash("admin123"),
            full_name="System Admin",
            role="admin"
        )
        db.add(admin)
        print("Created Admin user")
    else:
        admin.hashed_password = get_password_hash("admin123")
        admin.role = "admin"
        print("Reset Admin user password")
        
    # Check farmer
    farmer = db.query(User).filter(User.email == "farmer@terravyn.com").first()
    if not farmer:
        farmer = User(
            email="farmer@terravyn.com",
            hashed_password=get_password_hash("farmer123"),
            full_name="John Farmer",
            role="user"
        )
        db.add(farmer)
        print("Created Farmer user")
    else:
        farmer.hashed_password = get_password_hash("farmer123")
        farmer.role = "user"
        print("Reset Farmer user password")
        
    db.commit()
    db.close()

if __name__ == "__main__":
    ensure_users()
