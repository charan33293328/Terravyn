import sys
import os
import logging
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database.connection import engine, Base
from models.domain import DeviceTelemetry

logger = logging.getLogger("uvicorn.error")

def run_migration():
    print("Starting Telemetry Backend Migration...")
    
    # 1. Add new columns to devices table
    new_columns = [
        "last_seen DATETIME NULL",
        "last_rssi INT NULL",
        "last_temperature FLOAT NULL",
        "last_humidity FLOAT NULL",
        "last_soil_moisture FLOAT NULL"
    ]
    
    with engine.begin() as conn:
        for col_def in new_columns:
            col_name = col_def.split()[0]
            try:
                print(f"Adding column {col_name} to devices table...")
                conn.execute(text(f"ALTER TABLE devices ADD COLUMN {col_def}"))
                print(f"Column {col_name} added successfully.")
            except OperationalError as e:
                if "Duplicate column name" in str(e) or "duplicate column" in str(e).lower():
                    print(f"Column {col_name} already exists. Skipping.")
                else:
                    print(f"Error adding column {col_name}. Error: {e}")
                    # If using SQLite, ALTER TABLE ADD COLUMN might fail differently, but we ignore already exists error.
                    if "syntax error" in str(e).lower() and engine.url.drivername.startswith("sqlite"):
                         print(f"Ignoring SQLite alter table syntax error for {col_name}")
                    else:
                         raise e
    
    # 2. Create the device_telemetry table automatically using SQLAlchemy Base
    print("Creating device_telemetry table...")
    # This will create tables that don't exist yet, including device_telemetry
    # and any indices defined in the model.
    Base.metadata.create_all(bind=engine)
    print("Table device_telemetry verified/created.")

    print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
