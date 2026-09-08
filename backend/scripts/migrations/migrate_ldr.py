import os
import sys
import json
import sqlite3

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [info[1] for info in cursor.fetchall()]
    return column_name in columns

def migrate():
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "terravyn.db")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    default_health = json.dumps({
        "soil": "OK",
        "water": "OK",
        "rain": "OK",
        "dht22": "OK",
        "bmp280": "OK",
        "ldr": "OK"
    })

    # 1. Update device_telemetry table
    if not column_exists(cursor, 'device_telemetry', 'dark_detected'):
        print("Adding dark_detected to device_telemetry...")
        cursor.execute("ALTER TABLE device_telemetry ADD COLUMN dark_detected BOOLEAN DEFAULT 0")
        # Update existing to 0 (false)
        cursor.execute("UPDATE device_telemetry SET dark_detected = 0 WHERE dark_detected IS NULL")
    else:
        print("Column dark_detected already exists in device_telemetry")

    if not column_exists(cursor, 'device_telemetry', 'sensor_health'):
        print("Adding sensor_health to device_telemetry...")
        cursor.execute("ALTER TABLE device_telemetry ADD COLUMN sensor_health JSON")
        # Populate defaults
        cursor.execute("UPDATE device_telemetry SET sensor_health = ? WHERE sensor_health IS NULL", (default_health,))
    else:
        print("Column sensor_health already exists in device_telemetry")

    # 2. Update devices table
    if not column_exists(cursor, 'devices', 'last_dark_detected'):
        print("Adding last_dark_detected to devices...")
        cursor.execute("ALTER TABLE devices ADD COLUMN last_dark_detected BOOLEAN DEFAULT 0")
        cursor.execute("UPDATE devices SET last_dark_detected = 0 WHERE last_dark_detected IS NULL")
    else:
        print("Column last_dark_detected already exists in devices")

    if not column_exists(cursor, 'devices', 'sensor_health'):
        print("Adding sensor_health to devices...")
        cursor.execute("ALTER TABLE devices ADD COLUMN sensor_health JSON")
        cursor.execute("UPDATE devices SET sensor_health = ? WHERE sensor_health IS NULL", (default_health,))
    else:
        print("Column sensor_health already exists in devices")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
