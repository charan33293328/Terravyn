import os
import sys
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db, Base
from models.domain import *

# Assuming MySQL setup from previous phases
DATABASE_URL = "mysql+pymysql://root:Charan%40123@localhost/terravyn"

def run_migration():
    print("Starting Phase FP-9 Profile database migration...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add new columns to farmers table if they don't exist
            print("Checking farmers table columns...")
            try:
                conn.execute(text("ALTER TABLE farmers ADD COLUMN username VARCHAR(255) UNIQUE;"))
                print("Added username column.")
            except Exception as e:
                print(f"Column username might already exist: {e}")
                
            try:
                conn.execute(text("ALTER TABLE farmers ADD COLUMN profile_photo VARCHAR(500);"))
                print("Added profile_photo column.")
            except Exception as e:
                print(f"Column profile_photo might already exist: {e}")
                
            # Now we use Base.metadata.create_all for the new tables
            print("Creating new tables for Notification Preferences, Sessions, and Activity Logs...")
            Base.metadata.create_all(bind=engine)
            print("Tables created successfully.")
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            raise e

if __name__ == "__main__":
    run_migration()
