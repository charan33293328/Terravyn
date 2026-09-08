import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to sys.path to import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal

def run_migration():
    db = SessionLocal()
    
    try:
        print("Starting Phase 8 Support Migration...")

        # 1. Add farmer_id
        try:
            db.execute(text("ALTER TABLE support_tickets ADD COLUMN farmer_id INTEGER;"))
            db.execute(text("ALTER TABLE support_tickets ADD CONSTRAINT fk_support_farmer FOREIGN KEY (farmer_id) REFERENCES farmers(id);"))
            print("Added farmer_id column.")
        except Exception as e:
            print(f"farmer_id column might already exist: {e}")
            db.rollback()

        # 2. Add device_id
        try:
            db.execute(text("ALTER TABLE support_tickets ADD COLUMN device_id INTEGER;"))
            db.execute(text("ALTER TABLE support_tickets ADD CONSTRAINT fk_support_device FOREIGN KEY (device_id) REFERENCES devices(id);"))
            print("Added device_id column.")
        except Exception as e:
            print(f"device_id column might already exist: {e}")
            db.rollback()
            
        # 3. Add farm_id
        try:
            db.execute(text("ALTER TABLE support_tickets ADD COLUMN farm_id INTEGER;"))
            db.execute(text("ALTER TABLE support_tickets ADD CONSTRAINT fk_support_farm FOREIGN KEY (farm_id) REFERENCES farms(id);"))
            print("Added farm_id column.")
        except Exception as e:
            print(f"farm_id column might already exist: {e}")
            db.rollback()

        # 4. Add order_id
        try:
            db.execute(text("ALTER TABLE support_tickets ADD COLUMN order_id VARCHAR(50);"))
            db.execute(text("ALTER TABLE support_tickets ADD CONSTRAINT fk_support_order FOREIGN KEY (order_id) REFERENCES orders(order_id);"))
            print("Added order_id column.")
        except Exception as e:
            print(f"order_id column might already exist: {e}")
            db.rollback()

        # 5. Create ticket_attachments table
        try:
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS ticket_attachments (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    ticket_id INTEGER NOT NULL,
                    message_id INTEGER,
                    file_name VARCHAR(255) NOT NULL,
                    stored_file_name VARCHAR(255) NOT NULL UNIQUE,
                    file_path VARCHAR(1024) NOT NULL,
                    file_size INTEGER NOT NULL,
                    mime_type VARCHAR(100) NOT NULL,
                    uploaded_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(ticket_id) REFERENCES support_tickets(id),
                    FOREIGN KEY(message_id) REFERENCES ticket_messages(id),
                    FOREIGN KEY(uploaded_by) REFERENCES users(id)
                );
            """))
            print("Created ticket_attachments table.")
        except Exception as e:
            print(f"Error creating ticket_attachments table: {e}")
            db.rollback()

        # Create indices
        try:
            db.execute(text("CREATE INDEX ix_support_tickets_farmer_id ON support_tickets(farmer_id);"))
        except Exception:
            db.rollback()
            
        try:
            db.execute(text("CREATE INDEX ix_support_tickets_status ON support_tickets(status);"))
        except Exception:
            db.rollback()

        db.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
