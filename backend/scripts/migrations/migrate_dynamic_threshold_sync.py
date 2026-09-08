"""
Database migration script: Dynamic Crop/Variety Irrigation Threshold Sync fields.
Adds dynamic configuration versioning, threshold snapshots, and ACK columns to MySQL tables:
- devices
- device_telemetry
"""
import logging
from sqlalchemy import text
from database.connection import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def migrate():
    with engine.connect() as conn:
        logger.info("Checking and altering 'devices' table for dynamic config sync...")
        device_cols = [
            ("config_version", "INT DEFAULT 1"),
            ("applied_config_version", "INT NULL"),
            ("config_ack_status", "VARCHAR(50) DEFAULT 'PENDING'"),
            ("last_config_ack_at", "DATETIME NULL"),
            ("last_config_rejection_reason", "VARCHAR(255) NULL"),
            ("current_config_hash", "VARCHAR(64) NULL")
        ]
        for col_name, col_type in device_cols:
            try:
                conn.execute(text(f"ALTER TABLE devices ADD COLUMN {col_name} {col_type};"))
                conn.commit()
                logger.info(f"Added column {col_name} to devices.")
            except Exception as e:
                logger.info(f"Column {col_name} on devices may already exist.")

        logger.info("Checking and altering 'device_telemetry' table for dynamic config sync...")
        telem_cols = [
            ("configuration_version", "INT NULL"),
            ("dynamic_threshold_config_valid", "BOOLEAN NULL"),
            ("start_threshold", "FLOAT NULL"),
            ("stop_threshold", "FLOAT NULL"),
            ("configured_crop", "VARCHAR(100) NULL"),
            ("configured_variety", "VARCHAR(100) NULL"),
            ("configured_growth_stage", "VARCHAR(100) NULL"),
            ("irrigation_event_reason", "VARCHAR(255) NULL")
        ]
        for col_name, col_type in telem_cols:
            try:
                conn.execute(text(f"ALTER TABLE device_telemetry ADD COLUMN {col_name} {col_type};"))
                conn.commit()
                logger.info(f"Added column {col_name} to device_telemetry.")
            except Exception as e:
                logger.info(f"Column {col_name} on device_telemetry may already exist.")

    logger.info("Migration for dynamic threshold sync completed successfully.")

if __name__ == "__main__":
    migrate()
