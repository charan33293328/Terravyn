from database.connection import engine, Base
from models import domain
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN device_status VARCHAR(50) DEFAULT 'UNASSIGNED';"))
            print("Added device_status")
        except Exception as e:
            print("device_status error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN provision_status VARCHAR(50) DEFAULT 'NOT_PROVISIONED';"))
            print("Added provision_status")
        except Exception as e:
            print("provision_status error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN qr_code_path VARCHAR(500);"))
            print("Added qr_code_path")
        except Exception as e:
            print("qr_code_path error:", e)
            
        try:
            conn.execute(text("ALTER TABLE devices ADD COLUMN updated_at DATETIME;"))
            print("Added updated_at")
        except Exception as e:
            print("updated_at error:", e)
            
        conn.commit()

    print("Creating new tables...")
    Base.metadata.create_all(bind=engine)
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
