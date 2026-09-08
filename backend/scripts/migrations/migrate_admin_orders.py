import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.connection import engine, Base
from models import domain
from sqlalchemy import text

def migrate():
    print("Starting Admin Orders table migration for MySQL...")
    
    # Create the new table
    print("Creating admin_notifications table if it doesn't exist...")
    domain.Base.metadata.create_all(bind=engine, tables=[domain.AdminNotification.__table__])

    with engine.connect() as conn:
        print("Altering orders table...")
        
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN unit_price FLOAT NOT NULL DEFAULT 14999.0;"))
            print("Added unit_price")
        except Exception as e:
            print(f"unit_price might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN subtotal FLOAT NOT NULL DEFAULT 14999.0;"))
            print("Added subtotal")
        except Exception as e:
            print(f"subtotal might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN tax_amount FLOAT NOT NULL DEFAULT 0.0;"))
            print("Added tax_amount")
        except Exception as e:
            print(f"tax_amount might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN shipping_amount FLOAT NOT NULL DEFAULT 0.0;"))
            print("Added shipping_amount")
        except Exception as e:
            print(f"shipping_amount might already exist: {e}")
            
        try:
            conn.execute(text("ALTER TABLE orders ADD COLUMN invoice_number VARCHAR(100) NULL;"))
            # Make it unique
            conn.execute(text("CREATE UNIQUE INDEX ix_orders_invoice_number ON orders (invoice_number);"))
            print("Added invoice_number")
        except Exception as e:
            print(f"invoice_number might already exist: {e}")
            
        conn.commit()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
