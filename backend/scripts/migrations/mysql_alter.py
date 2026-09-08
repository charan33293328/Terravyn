from database.connection import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE products ADD COLUMN images JSON DEFAULT ('[]');"))
        conn.commit()
    print("Column added successfully to MySQL.")
except Exception as e:
    print(f"Error: {e}")
