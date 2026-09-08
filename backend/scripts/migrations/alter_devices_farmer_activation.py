import sqlite3
import os

DB_PATH = "terravyn.db"

def alter_devices_table():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN activated_at DATETIME")
        print("Added activated_at column to devices table.")
    except sqlite3.OperationalError as e:
        print(f"Error adding activated_at: {e} (might already exist)")

    try:
        cursor.execute("ALTER TABLE devices ADD COLUMN activation_method VARCHAR(50)")
        print("Added activation_method column to devices table.")
    except sqlite3.OperationalError as e:
        print(f"Error adding activation_method: {e} (might already exist)")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    alter_devices_table()
