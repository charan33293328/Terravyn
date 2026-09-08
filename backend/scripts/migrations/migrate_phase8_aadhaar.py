import os
import sys
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import settings

def migrate():
    print("Connecting to database...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("Adding Aadhaar columns to 'orders' table...")
        
        # We wrap in try-except in case they already exist
        columns = [
            ("aadhaar_number_masked", "VARCHAR(20)"),
            ("aadhaar_document_path", "VARCHAR(500)"),
            ("identity_verification_status", "VARCHAR(50) DEFAULT 'PENDING'"),
            ("identity_verified_at", "DATETIME")
        ]
        
        for col_name, col_type in columns:
            try:
                conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}"))
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Column {col_name} might already exist or error: {e}")
        
        conn.commit()
    
    print("Migration Phase 8 (Aadhaar Verification) completed successfully.")

if __name__ == "__main__":
    migrate()
