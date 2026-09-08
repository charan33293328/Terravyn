"""
Terravyn Dynamic Crop/Variety Irrigation Threshold Sync Service.
Calculates, versions, and prepares approved dynamic irrigation configurations for ESP32 devices
grounded in the Green Gram Knowledge Base, growth stages, soil physics, and active field calibrations.
"""
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session

from models.domain import Farm, Device, DeviceTelemetry, IrrigationLog
from schemas.domain import DynamicIrrigationConfigResponse, DeviceConfigAckRequest
from .green_gram_config import (
    determine_growth_stage,
    STAGE_MATURITY,
    STAGE_FLOWERING,
    STAGE_POD_FORMATION,
    STAGE_POD_FILLING,
    STAGE_VEGETATIVE,
    STAGE_SEEDLING,
    STAGE_GERMINATION,
    STAGE_SOWING
)
from .knowledge_base import knowledge_base
from services.validation_engine.calibration_manager import FieldCalibrationManager

logger = logging.getLogger(__name__)

SUPPORTED_GREEN_GRAM_NAMES = {
    "green gram",
    "green gram (moong)",
    "moong",
    "mung",
    "mung bean",
    "vigna radiata",
    "pesalu",
    "pasipayiru",
    "hesaru kaalu",
    "mug",
    "mug dal"
}


class DeviceConfigSyncService:
    """
    Manages calculation and synchronization of dynamic irrigation configurations
    between the Terravyn backend agricultural intelligence and ESP32 hardware.
    """

    @classmethod
    def is_green_gram(cls, crop_type: Optional[str]) -> bool:
        """Check whether the selected crop is Green Gram (Moong)."""
        if not crop_type:
            return True  # Default crop in Terravyn
        cleaned = crop_type.strip().lower()
        return any(name in cleaned for name in SUPPORTED_GREEN_GRAM_NAMES)

    @classmethod
    def calculate_device_irrigation_config(
        cls,
        db: Session,
        device: Device
    ) -> DynamicIrrigationConfigResponse:
        """
        Calculate the effective dynamic irrigation configuration for a device
        based on its associated farm, crop, variety, growth stage, soil type,
        and approved field calibrations.
        """
        if not device.farm_id:
            return DynamicIrrigationConfigResponse(
                enabled=False,
                crop=None,
                variety=None,
                growth_stage=None,
                soil_type=None,
                start_threshold=None,
                stop_threshold=None,
                hysteresis_enabled=False,
                configuration_version=0,
                source="NO_FARM_ASSIGNED",
                status="DISABLED",
                reason="Device is not assigned to any farm field."
            )

        farm = db.query(Farm).filter(Farm.id == device.farm_id).first()
        if not farm:
            return DynamicIrrigationConfigResponse(
                enabled=False,
                crop=None,
                variety=None,
                growth_stage=None,
                soil_type=None,
                start_threshold=None,
                stop_threshold=None,
                hysteresis_enabled=False,
                configuration_version=0,
                source="FARM_NOT_FOUND",
                status="DISABLED",
                reason=f"Assigned farm #{device.farm_id} does not exist in database."
            )

        # -------------------------------------------------------------
        # 1. Check for Unsupported Non-Green Gram Crops
        # -------------------------------------------------------------
        crop_raw = farm.crop_type or "Green Gram (Moong)"
        if not cls.is_green_gram(crop_raw):
            logger.info(
                f"[ConfigSync] Device {device.device_uid}: Selected crop '{crop_raw}' is unsupported. "
                "Returning dynamic configuration unavailable (zero Green Gram threshold leakage)."
            )
            return DynamicIrrigationConfigResponse(
                enabled=False,
                crop=crop_raw,
                variety=farm.crop_variety,
                growth_stage=None,
                soil_type=farm.soil_type,
                start_threshold=None,
                stop_threshold=None,
                hysteresis_enabled=False,
                configuration_version=0,
                source="UNSUPPORTED_CROP",
                status="UNAVAILABLE",
                reason=(
                    f"Dynamic irrigation configuration unavailable for unsupported crop: '{crop_raw}'. "
                    "Only Green Gram (Moong) is currently calibrated in the Terravyn Knowledge Base."
                )
            )

        # -------------------------------------------------------------
        # 2. Green Gram Stage & Variety Determination
        # -------------------------------------------------------------
        stage_info = determine_growth_stage(
            sowing_date=farm.sowing_date,
            variety_name=farm.crop_variety,
            manual_override=farm.growth_stage_override
        )
        stage = stage_info["stage"]
        variety = farm.crop_variety or "DEFAULT"
        soil_type = farm.soil_type or "Sandy Loam"

        # -------------------------------------------------------------
        # 3. Maturity / Harvest Stage Cease-Irrigation Rule
        # -------------------------------------------------------------
        if stage in [STAGE_MATURITY, "Maturity", "Harvest", "Maturity / Harvest"]:
            config_hash = cls._compute_signature(
                farm.id, "Green Gram (Moong)", variety, stage, soil_type, 0.0, 0.0, "ICAR-IIPR-2018"
            )
            version = cls._resolve_version(db, device, config_hash)
            return DynamicIrrigationConfigResponse(
                enabled=False,
                crop="Green Gram (Moong)",
                variety=farm.crop_variety,
                growth_stage=stage,
                soil_type=soil_type,
                start_threshold=0.0,
                stop_threshold=0.0,
                hysteresis_enabled=False,
                configuration_version=version,
                source="ICAR-IIPR-2018",
                status="APPROVED",
                reason=(
                    "Crop is in Maturity / Harvest stage. All irrigation must cease 10–12 days prior to harvest "
                    "to ensure uniform pod desiccation and prevent vivipary / pod shattering."
                )
            )

        # -------------------------------------------------------------
        # 4. Knowledge Base Base Thresholds by Growth Stage
        # -------------------------------------------------------------
        if stage in [STAGE_FLOWERING, STAGE_POD_FORMATION, "Flowering", "Pod Formation"]:
            base_threshold = 40.0
            stage_sensitivity = "CRITICAL"
        elif stage in [STAGE_POD_FILLING, "Pod Filling"]:
            base_threshold = 35.0
            stage_sensitivity = "HIGH"
        elif stage in [STAGE_VEGETATIVE, "Vegetative", "Branching"]:
            base_threshold = 30.0
            stage_sensitivity = "MODERATE"
        elif stage in [STAGE_SEEDLING, STAGE_GERMINATION, STAGE_SOWING, "Seedling", "Germination", "Sowing"]:
            base_threshold = 28.0
            stage_sensitivity = "MODERATE"
        else:
            base_threshold = 32.0
            stage_sensitivity = "MODERATE"

        # -------------------------------------------------------------
        # 5. Soil Profile Offset
        # -------------------------------------------------------------
        soil_prof = knowledge_base.get_soil(soil_type)
        soil_offset = soil_prof.capacitive_moisture_offset if soil_prof else 0.0
        effective_start = base_threshold + soil_offset
        hysteresis_delta = 10.0
        source = "GREEN_GRAM_KNOWLEDGE_BASE"
        status = "APPROVED"
        reason = (
            f"Green Gram {stage} stage ({stage_sensitivity} sensitivity) in {soil_type} "
            f"(base={base_threshold}%, soil offset={soil_offset:+.1f}%)."
        )

        # -------------------------------------------------------------
        # 6. Active Field Calibration Override Check
        # -------------------------------------------------------------
        try:
            active_cal = FieldCalibrationManager.get_active_calibration(
                db=db,
                field_id=farm.id,
                soil_type=soil_type,
                growth_stage=stage,
                crop="Green Gram (Moong)"
            )
            if active_cal and active_cal.value is not None:
                effective_start = float(active_cal.value)
                if active_cal.hysteresis_delta is not None and active_cal.hysteresis_delta > 0:
                    hysteresis_delta = float(active_cal.hysteresis_delta)
                source = f"FIELD_CALIBRATED_v{active_cal.version}"
                status = "APPROVED"
                reason = (
                    f"Approved field calibration v{active_cal.version} active for {stage} stage "
                    f"in {soil_type} (Scope: {active_cal.scope})."
                )
        except Exception as e:
            logger.warning(f"[ConfigSync] Field calibration lookup non-fatal error: {e}")

        effective_start = round(effective_start, 1)
        effective_stop = round(min(100.0, effective_start + hysteresis_delta), 1)

        # -------------------------------------------------------------
        # 7. Signature & Version Resolution
        # -------------------------------------------------------------
        config_hash = cls._compute_signature(
            farm.id, "Green Gram (Moong)", variety, stage, soil_type, effective_start, effective_stop, source
        )
        version = cls._resolve_version(db, device, config_hash)

        return DynamicIrrigationConfigResponse(
            enabled=True,
            crop="Green Gram (Moong)",
            variety=farm.crop_variety,
            growth_stage=stage,
            soil_type=soil_type,
            start_threshold=effective_start,
            stop_threshold=effective_stop,
            hysteresis_enabled=True,
            configuration_version=version,
            source=source,
            status=status,
            reason=reason
        )

    @classmethod
    def record_config_ack(
        cls,
        db: Session,
        ack_req: DeviceConfigAckRequest,
        device: Device
    ) -> Dict[str, Any]:
        """
        Record configuration acknowledgement or rejection from the ESP32.
        """
        now = datetime.utcnow()
        device.applied_config_version = ack_req.configuration_version
        device.config_ack_status = ack_req.status.upper()
        device.last_config_ack_at = now
        device.last_config_rejection_reason = ack_req.rejection_reason

        db.commit()
        db.refresh(device)

        logger.info(
            f"[ConfigSync] Device {device.device_uid} acknowledged configuration v{ack_req.configuration_version}: "
            f"Status={device.config_ack_status}"
        )

        return {
            "success": True,
            "device_uid": device.device_uid,
            "configuration_version": ack_req.configuration_version,
            "status": device.config_ack_status,
            "recorded_at": now
        }

    @classmethod
    def _compute_signature(
        cls,
        farm_id: int,
        crop: str,
        variety: Optional[str],
        stage: str,
        soil: str,
        start: float,
        stop: float,
        source: str
    ) -> str:
        """Create a deterministic SHA256 signature of the agronomic parameters."""
        raw = f"{farm_id}:{crop}:{variety or ''}:{stage}:{soil}:{start:.1f}:{stop:.1f}:{source}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _resolve_version(
        cls,
        db: Session,
        device: Device,
        current_hash: str
    ) -> int:
        """
        Increment configuration version only when effective parameters change.
        Ensures a valid positive version (>= 1) is always returned for approved configurations.
        """
        existing_ver = None
        if hasattr(device, "config_version") and device.config_version is not None and device.config_version > 0:
            existing_ver = device.config_version
        elif device.applied_config_version is not None and device.applied_config_version > 0:
            existing_ver = device.applied_config_version

        # 1. If hash matches existing configuration and we already have a positive version, keep it unchanged
        if device.current_config_hash == current_hash and existing_ver is not None and existing_ver >= 1:
            if hasattr(device, "config_version") and device.config_version != existing_ver:
                device.config_version = existing_ver
                db.commit()
            return existing_ver

        # 2. Hash has changed (or first initialization / legacy 0-version recovery)
        if existing_ver is None or existing_ver < 1:
            new_ver = 1
        else:
            new_ver = existing_ver + 1

        if hasattr(device, "config_version"):
            device.config_version = new_ver
        device.current_config_hash = current_hash
        device.config_ack_status = "PENDING"
        db.commit()
        db.refresh(device)
        return new_ver

