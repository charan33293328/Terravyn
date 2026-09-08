import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), "terravyn.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "username" not in columns:
        print("Adding 'username' column to 'users' table...")
        cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR(255)")
        cursor.execute("CREATE UNIQUE INDEX ix_users_username ON users (username)")
        print("Successfully added 'username' column and index.")
    else:
        print("'username' column already exists.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
