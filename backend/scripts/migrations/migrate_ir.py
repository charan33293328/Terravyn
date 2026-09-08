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
        
        if 'obstacle_detected' not in columns:
            conn.execute(text("ALTER TABLE device_telemetry ADD COLUMN obstacle_detected BOOLEAN DEFAULT FALSE;"))
            print("Added obstacle_detected to device_telemetry")

        print("Migrating devices table...")
        device_cols = [c['name'] for c in inspector.get_columns('devices')]
        
        if 'last_obstacle_detected' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN last_obstacle_detected BOOLEAN DEFAULT FALSE;"))
            print("Added last_obstacle_detected to devices")
            
        conn.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
