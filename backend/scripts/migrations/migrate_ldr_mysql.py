from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine

def migrate():
    inspector = Inspector.from_engine(engine)
    
    with engine.begin() as conn:
        # device_telemetry
        cols = [c['name'] for c in inspector.get_columns('device_telemetry')]
        if 'dark_detected' not in cols:
            conn.execute(text("ALTER TABLE device_telemetry ADD COLUMN dark_detected BOOLEAN DEFAULT FALSE"))
            print("Added dark_detected to device_telemetry")
        if 'sensor_health' not in cols:
            conn.execute(text("ALTER TABLE device_telemetry ADD COLUMN sensor_health JSON"))
            print("Added sensor_health to device_telemetry")
            
        # devices
        cols = [c['name'] for c in inspector.get_columns('devices')]
        if 'last_dark_detected' not in cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN last_dark_detected BOOLEAN DEFAULT FALSE"))
            print("Added last_dark_detected to devices")
        if 'sensor_health' not in cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN sensor_health JSON"))
            print("Added sensor_health to devices")
        
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
