from database.connection import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    logger.info("Starting pressure_trend migration...")
    
    with engine.connect() as conn:
        try:
            # Add last_pressure_trend to devices
            conn.execute(text("ALTER TABLE devices ADD COLUMN last_pressure_trend VARCHAR(50) NULL;"))
            logger.info("Added last_pressure_trend to devices")
        except Exception as e:
            logger.warning(f"Could not add last_pressure_trend to devices: {e}")
            
        try:
            # Add pressure_trend to device_telemetry
            conn.execute(text("ALTER TABLE device_telemetry ADD COLUMN pressure_trend VARCHAR(50) NULL;"))
            logger.info("Added pressure_trend to device_telemetry")
        except Exception as e:
            logger.warning(f"Could not add pressure_trend to device_telemetry: {e}")
            
        conn.commit()
        
    logger.info("Migration complete.")

if __name__ == '__main__':
    run_migration()
