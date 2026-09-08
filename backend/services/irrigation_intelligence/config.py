"""
Terravyn Irrigation Intelligence: Configuration and Settings
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from models.domain import IrrigationControlConfig, Farm, Device


class IntelligenceMode(str, Enum):
    OBSERVATION = "OBSERVATION"  # Passive data collection only
    SHADOW = "SHADOW"            # Parallel evaluation, zero pump actuation
    ASSISTED = "ASSISTED"        # Recommends action, requires user approval
    AUTOMATIC = "AUTOMATIC"      # Autonomous execution when authorized


class ControlMode(str, Enum):
    AUTO = "AUTO"
    MANUAL = "MANUAL"


class IrrigationConfigService:
    """Manages field-level irrigation intelligence configuration."""

    @staticmethod
    def get_or_create_config(db: Session, farm_id: int) -> IrrigationControlConfig:
        cfg = db.query(IrrigationControlConfig).filter(IrrigationControlConfig.farm_id == farm_id).first()
        if not cfg:
            farm = db.query(Farm).filter(Farm.id == farm_id).first()
            device = db.query(Device).filter(Device.farm_id == farm_id).first() if farm else None
            
            cfg = IrrigationControlConfig(
                farm_id=farm_id,
                device_id=device.id if device else None,
                intelligence_mode=IntelligenceMode.SHADOW.value,
                automatic_irrigation_enabled=False,
                control_mode=(device.irrigation_mode if device and device.irrigation_mode else ControlMode.AUTO.value),
                decision_confidence_min=75,
                sensor_freshness_seconds=600,
                decision_validity_seconds=600,
                cooldown_seconds=1800,
                max_pump_runtime_seconds=300,
                default_duration_seconds=120,
                min_water_level_pct=15.0,
                require_esp32_ack=True,
                dry_run_mode=False,
                config_version="v1.0"
            )
            db.add(cfg)
            db.commit()
            db.refresh(cfg)
        else:
            # Sync control mode from device if device is linked
            if cfg.device_id:
                dev = db.query(Device).filter(Device.id == cfg.device_id).first()
                if dev and dev.irrigation_mode and dev.irrigation_mode != cfg.control_mode:
                    cfg.control_mode = dev.irrigation_mode
                    db.commit()
        return cfg

    @staticmethod
    def update_config(db: Session, farm_id: int, updates: Dict[str, Any]) -> IrrigationControlConfig:
        cfg = IrrigationConfigService.get_or_create_config(db, farm_id)
        
        allowed_fields = [
            "intelligence_mode",
            "automatic_irrigation_enabled",
            "decision_confidence_min",
            "sensor_freshness_seconds",
            "decision_validity_seconds",
            "cooldown_seconds",
            "max_pump_runtime_seconds",
            "default_duration_seconds",
            "min_water_level_pct",
            "min_water_level_liters",
            "require_esp32_ack",
            "dry_run_mode",
            "notes"
        ]
        
        for k, v in updates.items():
            if k in allowed_fields and v is not None:
                setattr(cfg, k, v)

        cfg.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cfg)
        return cfg
