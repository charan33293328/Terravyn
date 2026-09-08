from sqlalchemy import text
from sqlalchemy.engine.reflection import Inspector
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine

def migrate():
    inspector = Inspector.from_engine(engine)
    with engine.connect() as conn:
        print("Migrating devices table...")
        device_cols = [c['name'] for c in inspector.get_columns('devices')]
        
        if 'wifi_provisioning_requested' not in device_cols:
            conn.execute(text("ALTER TABLE devices ADD COLUMN wifi_provisioning_requested BOOLEAN DEFAULT FALSE;"))
            print("Added wifi_provisioning_requested to devices")
        else:
            print("wifi_provisioning_requested already exists in devices")
            
        conn.commit()
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
