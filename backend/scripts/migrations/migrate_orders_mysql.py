import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.connection import engine
from sqlalchemy import text

def migrate():
    print("Starting orders table migration for MySQL...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN courier_name VARCHAR(255) NULL;"))
            print("Added courier_name")
        except Exception as e:
            print(f"courier_name might already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN tracking_number VARCHAR(255) NULL;"))
            print("Added tracking_number")
        except Exception as e:
            print(f"tracking_number might already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN tracking_url VARCHAR(500) NULL;"))
            print("Added tracking_url")
        except Exception as e:
            print(f"tracking_url might already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN shipment_date DATETIME NULL;"))
            print("Added shipment_date")
        except Exception as e:
            print(f"shipment_date might already exist: {e}")

        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN estimated_delivery_date DATETIME NULL;"))
            print("Added estimated_delivery_date")
        except Exception as e:
            print(f"estimated_delivery_date might already exist: {e}")
            
        conn.commit()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
