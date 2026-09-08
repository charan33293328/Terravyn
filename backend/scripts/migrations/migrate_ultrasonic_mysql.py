from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine

def migrate():
    inspector = Inspector.from_engine(engine)
    with engine.connect() as conn:
        print("Migrating device_telemetry table...")
        columns = [c['name'] for c in inspector.get_columns('device_telemetry')]
        
        if 'ultrasonic_distance' not in columns:
            conn.execute(text("ALTER TABLE device_telemetry ADD COLUMN ultrasonic_distance FLOAT DEFAULT NULL;"))
            print("Added ultrasonic_distance to device_telemetry")
            
        if 'ultrasonic_water_level' not in columns:
            conn.execute(text("ALTER TABLE device_telemetry ADD COLUMN ultrasonic_water_level INTEGER DEFAULT NULL;"))
            print("Added ultrasonic_water_level to device_telemetry")

        print("Migrating devices table...")
        device_cols = [c['name'] for c in inspector.get_columns('devices')]
        
        if 'last_ultrasonic_distance' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN last_ultrasonic_distance FLOAT DEFAULT NULL;"))
            print("Added last_ultrasonic_distance to devices")

        if 'last_ultrasonic_water_level' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN last_ultrasonic_water_level INTEGER DEFAULT NULL;"))
            print("Added last_ultrasonic_water_level to devices")
            
        if 'tank_height_cm' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN tank_height_cm FLOAT DEFAULT NULL;"))
            print("Added tank_height_cm to devices")
            
        if 'sensor_offset_cm' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN sensor_offset_cm FLOAT DEFAULT NULL;"))
            print("Added sensor_offset_cm to devices")
            
        if 'min_distance_cm' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN min_distance_cm FLOAT DEFAULT NULL;"))
            print("Added min_distance_cm to devices")
            
        if 'max_distance_cm' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN max_distance_cm FLOAT DEFAULT NULL;"))
            print("Added max_distance_cm to devices")
            
        if 'calibration_mode' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN calibration_mode VARCHAR(50) DEFAULT 'MANUAL';"))
            print("Added calibration_mode to devices")
            
        conn.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
