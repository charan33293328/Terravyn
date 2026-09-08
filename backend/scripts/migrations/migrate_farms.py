import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'terravyn.db')

def column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    return column in columns

def migrate_farms():
    if not os.path.exists(DB_PATH):
        print("Database not found, nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    columns_to_add = [
        ("area_unit", "VARCHAR(50)", "'Acres'"),
        ("description", "TEXT", "NULL"),
        ("status", "VARCHAR(50)", "'ACTIVE'"),
        ("expected_harvest_date", "DATETIME", "NULL"),
        ("village", "VARCHAR(255)", "NULL"),
        ("district", "VARCHAR(255)", "NULL"),
        ("state", "VARCHAR(255)", "NULL"),
        ("country", "VARCHAR(255)", "'India'")
    ]

    for col_name, col_type, default_val in columns_to_add:
        if not column_exists(cursor, "farms", col_name):
            print(f"Adding column {col_name} to farms...")
            cursor.execute(f"ALTER TABLE farms ADD COLUMN {col_name} {col_type} DEFAULT {default_val}")
        else:
            print(f"Column {col_name} already exists. Skipping.")

    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate_farms()
