import pymysql

def upgrade_sensor_data_schema():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Charan@123',
        database='terravyn'
    )

    try:
        with connection.cursor() as cursor:
            # 1. Rename 'timestamp' to 'created_at'
            try:
                cursor.execute("ALTER TABLE sensor_data CHANGE timestamp created_at DATETIME")
                print("Column 'timestamp' renamed to 'created_at' successfully.")
            except pymysql.err.OperationalError as e:
                print(f"Skipping rename timestamp -> created_at: {e}")
                
            # 2. Add 'pump_status'
            try:
                cursor.execute("ALTER TABLE sensor_data ADD COLUMN pump_status BOOLEAN")
                print("Column 'pump_status' added successfully.")
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1060: # Duplicate column name
                    print("Column 'pump_status' already exists.")
                else:
                    print(f"Error adding 'pump_status': {e}")
                    
            # 3. Add 'mode_status'
            try:
                cursor.execute("ALTER TABLE sensor_data ADD COLUMN mode_status VARCHAR(50)")
                print("Column 'mode_status' added successfully.")
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1060:
                    print("Column 'mode_status' already exists.")
                else:
                    print(f"Error adding 'mode_status': {e}")

        connection.commit()
    finally:
        connection.close()

if __name__ == "__main__":
    upgrade_sensor_data_schema()
