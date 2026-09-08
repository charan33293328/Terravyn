import sqlite3

try:
    conn = sqlite3.connect('terravyn.db')
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE products ADD COLUMN images JSON DEFAULT '[]';")
    conn.commit()
    print("Column added successfully")
except Exception as e:
    print(f"Error: {e}")
finally:
    if conn:
        conn.close()
