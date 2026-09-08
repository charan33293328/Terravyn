import sys
import os
from sqlalchemy import text
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database.connection import SessionLocal

def migrate():
    db = SessionLocal()
    try:
        # Create product_categories
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS product_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Insert categories
        categories = [
            "TERRAVYN Soil Monitoring Device",
            "TERRAVYN Pest Repellent Device",
            "TERRAVYN Irrigation Automation Device",
            "TERRAVYN Multi-Sensor Agriculture Device",
            "TERRAVYN Weather Monitoring Device",
            "TERRAVYN Livestock Monitoring Device",
            "TERRAVYN Greenhouse Automation Device",
            "TERRAVYN Industrial Agriculture Device",
            "TERRAVYN Research & Development Prototype",
            "TERRAVYN Other"
        ]
        
        for cat in categories:
            db.execute(text("INSERT IGNORE INTO product_categories (name) VALUES (:name)"), {"name": cat})
        
        # Alter devices table
        columns_to_add = {
            "product_category_id": "INT",
            "product_category_name": "VARCHAR(255)",
            "custom_category": "VARCHAR(255)",
            "manufacturing_notes": "TEXT",
            "manufactured_at": "DATETIME"
        }
        
        for col_name, col_type in columns_to_add.items():
            try:
                db.execute(text(f"ALTER TABLE devices ADD COLUMN {col_name} {col_type}"))
                print(f"Added column {col_name}")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"Column {col_name} already exists")
                else:
                    print(f"Error adding {col_name}: {e}")
        
        db.commit()
        print("Migration successful")
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
