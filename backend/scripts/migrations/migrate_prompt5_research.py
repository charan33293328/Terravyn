"""
Terravyn Migration Script: Prompt 5 Research and Knowledge Acquisition Engine V1 Tables
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine, Base
from models import domain
from sqlalchemy import inspect

def migrate():
    print("[Migration] Verifying Prompt 5 database tables...")
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required = [
        "research_queries",
        "research_sources",
        "evidence_claims",
        "dynamic_knowledge_items",
        "knowledge_review_queues"
    ]
    
    for t in required:
        status = "EXISTS" if t in tables else "MISSING"
        print(f"  - Table '{t}': {status}")
        
    print("[Migration] Migration completed successfully.")

if __name__ == "__main__":
    migrate()
