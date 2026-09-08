from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:Charan%40123@localhost/terravyn"
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    try:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS farms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                farmer_id INT NOT NULL,
                location VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
            )
        """))
        print("Created farms table.")
    except Exception as e:
        print(f"Error creating farms table: {e}")

    try:
        conn.execute(text("ALTER TABLE devices ADD COLUMN farm_id INT"))
        conn.execute(text("ALTER TABLE devices ADD CONSTRAINT fk_device_farm FOREIGN KEY (farm_id) REFERENCES farms(id) ON DELETE SET NULL"))
        print("Added farm_id column to devices table.")
    except Exception as e:
        print(f"Error adding farm_id: {e}")

    try:
        conn.execute(text("ALTER TABLE devices ADD COLUMN installation_date DATETIME"))
        print("Added installation_date column to devices table.")
    except Exception as e:
        print(f"Error adding installation_date: {e}")

print("MySQL migration complete.")
