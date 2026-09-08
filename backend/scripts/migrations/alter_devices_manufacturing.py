import sqlite3
import os

DB_PATH = "terravyn.db"

def alter_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create product_categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) UNIQUE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Insert default categories
    categories = [
        "TERRAVYN Soil Monitoring Device",
        "TERRAVYN Pest Repellent Device",
        "TERRAVYN Irrigation Automation Device",
        "TERRAVYN Multi-Sensor Agriculture Device",
        "TERRAVYN Weather Monitoring Device",
        "TERRAVYN Livestock Monitoring Device",
        "TERRAVYN Greenhouse Automation Device",
        "TERRAVYN Industrial Agriculture Device",
        "TERRAVYN Research & Development Prototype",
        "TERRAVYN Other"
    ]
    
    for cat in categories:
        cursor.execute("INSERT OR IGNORE INTO product_categories (name) VALUES (?)", (cat,))
        
    # 3. Alter devices table
    # Check existing columns first to make it idempotent
    cursor.execute("PRAGMA table_info(devices)")
    columns = [col[1] for col in cursor.fetchall()]
    
    alterations = {
        "product_category_id": "INTEGER",
        "product_category_name": "VARCHAR(255)",
        "custom_category": "VARCHAR(255)",
        "manufacturing_notes": "TEXT",
        "manufactured_at": "DATETIME"
    }
    
    for col_name, col_type in alterations.items():
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE devices ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
            
    conn.commit()
    conn.close()
    print("Database updated successfully.")

if __name__ == "__main__":
    alter_db()
