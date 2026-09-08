import os
import sys
from sqlalchemy import create_engine, text

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import settings
from sqlalchemy import inspect

def migrate():
    print("Starting Phase 9 Migration: Registration with OTP...")
    
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        try:
            # 1. Add new columns to users table
            print("Adding phone_number, is_email_verified, is_phone_verified to users table...")
            
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'phone_number' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR(50) NULL"))
                conn.execute(text("CREATE UNIQUE INDEX ix_users_phone_number ON users (phone_number)"))
                print("Added phone_number.")
            
            if 'is_email_verified' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN DEFAULT 0"))
                print("Added is_email_verified.")
                
            if 'is_phone_verified' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_phone_verified BOOLEAN DEFAULT 0"))
                print("Added is_phone_verified.")
            
            # 2. Create verification_records table
            print("Creating verification_records table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS verification_records (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    identifier VARCHAR(255) NOT NULL,
                    otp_hash VARCHAR(255) NOT NULL,
                    otp_type VARCHAR(50) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    attempt_count INTEGER DEFAULT 0,
                    verified BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # For mysql, use CREATE INDEX
            # We can just ignore the IF NOT EXISTS for index if we check first
            indexes = [idx['name'] for idx in inspector.get_indexes('verification_records')] if 'verification_records' in inspector.get_table_names() else []
            if 'ix_verification_records_identifier' not in indexes:
                conn.execute(text("CREATE INDEX ix_verification_records_identifier ON verification_records (identifier)"))

            
            conn.commit()
            print("Phase 9 Migration completed successfully.")
            
        except Exception as e:
            conn.rollback()
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
