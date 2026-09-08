from database.connection import engine, Base
from models import domain

Base.metadata.create_all(bind=engine)
print("Tables created.")
