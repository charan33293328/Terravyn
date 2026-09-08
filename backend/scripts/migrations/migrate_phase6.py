import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'terravyn.db')

def migrate():
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Create farmers table
        print("Creating farmers table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS farmers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name VARCHAR(255) NOT NULL,
                phone VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                address TEXT NOT NULL,
                village VARCHAR(255),
                district VARCHAR(100),
                state VARCHAR(100),
                pincode VARCHAR(20),
                status VARCHAR(50) DEFAULT 'ACTIVE',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add index for farmers
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_farmers_phone ON farmers (phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_farmers_email ON farmers (email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_farmers_id ON farmers (id)")
        
        # Add columns to devices table safely
        print("Adding columns to devices table...")
        columns_to_add = {
            "farmer_id": "INTEGER REFERENCES farmers(id)",
            "assigned_at": "DATETIME",
            "claim_status": "VARCHAR(50) DEFAULT 'UNASSIGNED'",
            "is_active": "BOOLEAN DEFAULT 1"
        }
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(devices)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                print(f"Adding column {col_name} to devices...")
                cursor.execute(f"ALTER TABLE devices ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists in devices, skipping.")

        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
