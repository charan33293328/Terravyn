from sqlalchemy import text
from database.connection import engine

with engine.connect() as conn:
    print("Altering users.role Enum...")
    conn.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('super_admin', 'admin', 'support_agent', 'operations_manager', 'user') DEFAULT 'user'"))
    conn.commit()
    print("Migration successful.")
