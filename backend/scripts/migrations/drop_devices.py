import pymysql
import sys

def drop_tables():
    try:
        connection = pymysql.connect(host='localhost', user='root', password='Charan@123', database='terravyn')
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        sys.exit(1)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
            cursor.execute("DROP TABLE IF EXISTS sensor_data;")
            cursor.execute("DROP TABLE IF EXISTS alerts;")
            cursor.execute("DROP TABLE IF EXISTS irrigation_logs;")
            cursor.execute("DROP TABLE IF EXISTS devices;")
            cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
            print("Dropped devices and dependent tables.")

if __name__ == "__main__":
    drop_tables()
