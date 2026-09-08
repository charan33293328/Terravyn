import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from database.connection import settings

def column_exists(conn, table_name, column_name):
    query = text("""
        SELECT count(*) 
        FROM information_schema.columns 
        WHERE table_schema = DATABASE() 
        AND table_name = :table AND column_name = :column
    """)
    result = conn.execute(query, {"table": table_name, "column": column_name}).scalar()
    return result > 0

def index_exists(conn, table_name, index_name):
    query = text("""
        SELECT count(*) 
        FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = :table AND index_name = :index
    """)
    result = conn.execute(query, {"table": table_name, "index": index_name}).scalar()
    return result > 0

def migrate_monitoring_mysql():
    print(f"Connecting to {settings.DATABASE_URL} ...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as conn:
        columns_to_add = [
            ("farmer_id", "INT DEFAULT NULL"),
            ("farm_id", "INT DEFAULT NULL"),
            ("rain_detected", "BOOLEAN DEFAULT FALSE")
        ]
        
        for col_name, col_def in columns_to_add:
            if not column_exists(conn, "device_telemetry", col_name):
                print(f"Adding column {col_name} to device_telemetry...")
                conn.execute(text(f"ALTER TABLE device_telemetry ADD COLUMN {col_name} {col_def}"))
            else:
                print(f"Column {col_name} already exists. Skipping.")
                
        # Create Index
        if not index_exists(conn, "device_telemetry", "ix_device_telemetry_farm_id"):
            print("Adding index on farm_id to device_telemetry...")
            conn.execute(text("CREATE INDEX ix_device_telemetry_farm_id ON device_telemetry (farm_id)"))

        # Backfill data from devices table
        print("Backfilling farmer_id and farm_id from devices table...")
        update_query = text("""
            UPDATE device_telemetry dt
            JOIN devices d ON dt.device_id = d.id
            SET dt.farmer_id = d.farmer_id, dt.farm_id = d.farm_id
            WHERE dt.farmer_id IS NULL OR dt.farm_id IS NULL
        """)
        res = conn.execute(update_query)
        print(f"Backfilled {res.rowcount} records.")

    print("Migration complete!")

if __name__ == "__main__":
    migrate_monitoring_mysql()
