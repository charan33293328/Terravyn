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

def migrate_farms_mysql():
    print(f"Connecting to {settings.DATABASE_URL} ...")
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.begin() as conn:
        columns_to_add = [
            ("area_unit", "VARCHAR(50) DEFAULT 'Acres'"),
            ("description", "TEXT DEFAULT NULL"),
            ("status", "VARCHAR(50) DEFAULT 'ACTIVE'"),
            ("expected_harvest_date", "DATETIME DEFAULT NULL"),
            ("village", "VARCHAR(255) DEFAULT NULL"),
            ("district", "VARCHAR(255) DEFAULT NULL"),
            ("state", "VARCHAR(255) DEFAULT NULL"),
            ("country", "VARCHAR(255) DEFAULT 'India'")
        ]
        
        for col_name, col_def in columns_to_add:
            if not column_exists(conn, "farms", col_name):
                print(f"Adding column {col_name} to farms...")
                conn.execute(text(f"ALTER TABLE farms ADD COLUMN {col_name} {col_def}"))
            else:
                print(f"Column {col_name} already exists. Skipping.")
                
    print("Migration complete!")

if __name__ == "__main__":
    migrate_farms_mysql()
