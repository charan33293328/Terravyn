from sqlalchemy import create_engine, text

DATABASE_URL = "mysql+pymysql://root:Charan%40123@localhost/terravyn"
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE devices ADD COLUMN activated_at DATETIME"))
        print("Added activated_at column to MySQL devices table.")
    except Exception as e:
        print(f"Error adding activated_at: {e}")

    try:
        conn.execute(text("ALTER TABLE devices ADD COLUMN activation_method VARCHAR(50)"))
        print("Added activation_method column to MySQL devices table.")
    except Exception as e:
        print(f"Error adding activation_method: {e}")

print("MySQL migration complete.")
