from database.connection import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE devices MODIFY COLUMN device_uid VARCHAR(255) NULL;"))
            print("device_uid modified to accept NULL")
        except Exception as e:
            print("device_uid modify error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN hardware_version VARCHAR(50);"))
            print("Added hardware_version")
        except Exception as e:
            print("hardware_version error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN rssi INT;"))
            print("Added rssi")
        except Exception as e:
            print("rssi error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN registration_status VARCHAR(50) DEFAULT 'WAITING_FOR_PROVISIONING';"))
            print("Added registration_status")
        except Exception as e:
            print("registration_status error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN nvs_written BOOLEAN DEFAULT FALSE;"))
            print("Added nvs_written")
        except Exception as e:
            print("nvs_written error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN provisioned_at DATETIME;"))
            print("Added provisioned_at")
        except Exception as e:
            print("provisioned_at error:", e)
            
        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
