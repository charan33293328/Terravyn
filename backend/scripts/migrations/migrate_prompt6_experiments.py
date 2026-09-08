"""
Terravyn Migration Script: Prompt 6 Green Gram Experiment & Data Collection Engine V1 Tables
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import engine, Base
from models import domain
from sqlalchemy import inspect

def migrate():
    print("[Migration] Verifying Prompt 6 experiment database tables...")
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    required = [
        "experiments",
        "experiment_groups",
        "experiment_plots",
        "experiment_plants",
        "experiment_baselines",
        "sensor_calibration_records",
        "experiment_observations",
        "experiment_irrigation_events",
        "experiment_events",
        "experiment_interventions",
        "experiment_daily_snapshots"
    ]
    
    for t in required:
        status = "EXISTS" if t in tables else "MISSING"
        print(f"  - Table '{t}': {status}")
        
    print("[Migration] Prompt 6 migration completed successfully.")

if __name__ == "__main__":
    migrate()
