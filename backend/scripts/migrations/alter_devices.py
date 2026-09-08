import pymysql
import sys

def alter_table():
    try:
        connection = pymysql.connect(host='localhost', user='root', password='Charan@123', database='terravyn')
    except Exception as e:
        print(f"Failed to connect to MySQL: {e}")
        sys.exit(1)

    with connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute("ALTER TABLE devices ADD COLUMN claimed_at DATETIME NULL;")
                print("Column claimed_at added successfully.")
            except pymysql.err.OperationalError as e:
                # 1060 is Duplicate column name
                if e.args[0] == 1060:
                    print("Column already exists.")
                else:
                    print(f"Error: {e}")

if __name__ == "__main__":
    alter_table()
