from database.connection import engine, Base
import models.domain

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")

import sqlite3
conn = sqlite3.connect('terravyn.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables after create:", tables)
conn.close()
