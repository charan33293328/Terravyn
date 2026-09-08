import os
from database.connection import engine, Base
from models import domain
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Migrating `devices` table...")
        columns_devices = [
            "ADD COLUMN last_bmp_temperature FLOAT;",
            "ADD COLUMN last_pressure FLOAT;",
            "ADD COLUMN last_altitude FLOAT;",
            "ADD COLUMN last_weather_prediction VARCHAR(100);",
            "ADD COLUMN last_signal_quality VARCHAR(50);",
            "ADD COLUMN last_uptime_seconds INTEGER;",
            "ADD COLUMN last_low_water_alert BOOLEAN DEFAULT FALSE;",
            "ADD COLUMN last_pump_timeout_alert BOOLEAN DEFAULT FALSE;"
        ]
        
        for col in columns_devices:
            try:
                conn.execute(text(f"ALTER TABLE devices {col}"))
                print(f"Success: {col}")
            except Exception as e:
                print(f"Failed (might already exist): {col} -> {e}")

        print("\nMigrating `device_telemetry` table...")
        columns_telemetry = [
            "ADD COLUMN bmp_temperature FLOAT;",
            "ADD COLUMN altitude FLOAT;",
            "ADD COLUMN weather_prediction VARCHAR(100);",
            "ADD COLUMN signal_quality VARCHAR(50);",
            "ADD COLUMN firmware_version VARCHAR(50);",
            "ADD COLUMN uptime_seconds INTEGER;",
            "ADD COLUMN operation_mode VARCHAR(50);",
            "ADD COLUMN pump_status BOOLEAN DEFAULT FALSE;",
            "ADD COLUMN low_water_alert BOOLEAN DEFAULT FALSE;",
            "ADD COLUMN pump_timeout_alert BOOLEAN DEFAULT FALSE;"
        ]
        
        for col in columns_telemetry:
            try:
                conn.execute(text(f"ALTER TABLE device_telemetry {col}"))
                print(f"Success: {col}")
            except Exception as e:
                print(f"Failed (might already exist): {col} -> {e}")
                
        conn.commit()

    print("\nRefreshing metadata (creating new tables if any)...")
    Base.metadata.create_all(bind=engine)
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
