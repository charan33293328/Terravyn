import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import Base
from database.connection import settings

def migrate():
    print("Starting Phase FP-7 Orders Migration...")
    
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Step 1: Add farmer_id column to orders if it doesn't exist
        print("Checking if farmer_id exists in orders table...")
        try:
            session.execute(text("ALTER TABLE orders ADD COLUMN farmer_id INTEGER REFERENCES farmers(id);"))
            print("Successfully added farmer_id column to orders table.")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Column farmer_id already exists in orders table.")
            else:
                print(f"Warning/Error when adding farmer_id (might already exist): {e}")

        # Step 2: Create new tables
        print("Creating order_items and return_requests tables...")
        Base.metadata.create_all(bind=engine)
        print("New tables created successfully.")

        # Step 3: Migrate existing orders into order_items
        print("Migrating legacy orders into order_items table...")
        # Get all orders
        orders = session.execute(text("SELECT order_id, product_id, product_name, quantity, unit_price, subtotal FROM orders")).fetchall()
        
        migrated_count = 0
        for order in orders:
            order_id = order[0]
            product_id = order[1]
            product_name = order[2]
            quantity = order[3]
            unit_price = order[4]
            subtotal = order[5]
            
            # Check if order item already exists for this order_id
            existing_items = session.execute(
                text("SELECT id FROM order_items WHERE order_id = :order_id"), 
                {"order_id": order_id}
            ).fetchall()
            
            if not existing_items and product_name:
                print(f"Migrating order {order_id} (Product: {product_name})...")
                # Insert legacy order as order item
                session.execute(
                    text("""
                        INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, subtotal, created_at, updated_at)
                        VALUES (:order_id, :product_id, :product_name, :quantity, :unit_price, :subtotal, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    {
                        "order_id": order_id,
                        "product_id": product_id,
                        "product_name": product_name,
                        "quantity": quantity if quantity is not None else 1,
                        "unit_price": unit_price if unit_price is not None else 0.0,
                        "subtotal": subtotal if subtotal is not None else 0.0
                    }
                )
                migrated_count += 1
            else:
                if existing_items:
                    print(f"Order {order_id} already migrated. Skipping.")
                
        session.commit()
        print(f"Migration completed successfully. Migrated {migrated_count} legacy orders.")
        
    except Exception as e:
        session.rollback()
        print(f"Migration failed! Rolling back changes. Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    migrate()
