import pymysql
import sys

def create_db():
    try:
        connection = pymysql.connect(host='localhost', user='root', password='Charan@123')
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        sys.exit(1)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS terravyn;")
            print("Database 'terravyn' created successfully or already exists.")

if __name__ == "__main__":
    create_db()
