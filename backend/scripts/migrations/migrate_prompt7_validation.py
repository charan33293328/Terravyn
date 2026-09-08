"""
Terravyn Migration Script: Prompt 7 Knowledge Validation & Calibration Engine V1 Tables
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine, Base
from models import domain
from sqlalchemy import inspect


def migrate():
    print("[Migration] Creating and verifying Prompt 7 Knowledge Validation & Calibration tables...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required = [
        "knowledge_validation_records",
        "field_calibration_records",
        "calibration_versions",
        "decision_outcomes",
        "shadow_decision_logs",
    ]

    all_exist = True
    for t in required:
        status = "EXISTS" if t in tables else "MISSING"
        if status == "MISSING":
            all_exist = False
        print(f"  - Table '{t}': {status}")

    if all_exist:
        print("[Migration] Prompt 7 migration completed successfully. All 5 tables verified.")
    else:
        print("[Migration] ERROR: Some tables are missing.")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
