"""
Terravyn Prompt 9: Closed-Loop Learning & Continuous Improvement Engine V1
Database Migration Script - Creates 7 new tables.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from database.connection import engine, Base
from models.domain import (
    DecisionOutcomeAnalysis,
    ForecastEvaluation,
    LearningCandidate,
    LearningEvidence,
    LearningRun,
    PerformanceMetric,
    ImprovementVersion,
)

TABLES = [
    DecisionOutcomeAnalysis.__table__,
    ForecastEvaluation.__table__,
    LearningCandidate.__table__,
    LearningEvidence.__table__,
    LearningRun.__table__,
    PerformanceMetric.__table__,
    ImprovementVersion.__table__,
]


def migrate():
    print("=" * 60)
    print("TERRAVYN PROMPT 9 MIGRATION")
    print("Closed-Loop Learning & Continuous Improvement Engine V1")
    print("=" * 60)

    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing = inspector.get_table_names()

    for table in TABLES:
        if table.name in existing:
            print(f"  [SKIP] Table '{table.name}' already exists.")
        else:
            table.create(engine)
            print(f"  [CREATE] Table '{table.name}' created successfully.")

    # Verify
    inspector = inspect(engine)
    final_tables = inspector.get_table_names()
    print("\n" + "-" * 60)
    print("VERIFICATION:")
    all_ok = True
    for table in TABLES:
        exists = table.name in final_tables
        status = "OK" if exists else "MISSING"
        if not exists:
            all_ok = False
        print(f"  [{status}] {table.name}")

    print("-" * 60)
    if all_ok:
        print("ALL 7 PROMPT 9 TABLES VERIFIED SUCCESSFULLY.")
    else:
        print("ERROR: Some tables are missing!")
    print("=" * 60)


if __name__ == "__main__":
    migrate()
