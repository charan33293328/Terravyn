from database.connection import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        try:
            print("Adding 'username' column to 'users' table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR(255)"))
            conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username)"))
            conn.commit()
            print("Successfully added 'username' column and index.")
        except Exception as e:
            print(f"Error (column might already exist): {e}")

if __name__ == "__main__":
    migrate()
