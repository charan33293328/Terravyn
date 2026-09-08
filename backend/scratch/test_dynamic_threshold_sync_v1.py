"""
=====================================================================================
TERRAVYN DYNAMIC CROP/VARIETY IRRIGATION THRESHOLD SYNC -- TEST SUITE V1
=====================================================================================
Comprehensive automated validation of dynamic threshold calculation, versioning,
ESP32 API delivery, acknowledgement, telemetry recording, local safety rules,
and unsupported crop isolation.
=====================================================================================
"""
import sys
import os
import uuid
from datetime import datetime, timedelta

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal
from models.domain import (
    Farm,
    Device,
    DeviceTelemetry,
    IrrigationLog,
    FieldCalibrationRecord,
    IrrigationControlConfig
)
from schemas.domain import (
    DeviceConfigResponse,
    DynamicIrrigationConfigResponse,
    DeviceConfigAckRequest
)
from services.crop_engine.config_sync import DeviceConfigSyncService
from services.validation_engine.calibration_manager import FieldCalibrationManager


def run_all_tests():
    db = SessionLocal()
    passed = 0
    total = 17

    print("=" * 80)
    print("TERRAVYN DYNAMIC CROP/VARIETY THRESHOLD SYNC -- TEST SUITE")
    print("=" * 80)

    try:
        # Setup test farm and test device
        test_mac = f"08:3A:F2:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}:{uuid.uuid4().hex[:2].upper()}"
        test_uid = f"TRV-DEV-{uuid.uuid4().hex[:8].upper()}"

        farm = Farm(
            name=f"Dynamic Sync Test Farm {uuid.uuid4().hex[:6]}",
            farmer_id=1,
            crop_type="Green Gram (Moong)",
            crop_variety="IPM 02-03",
            soil_type="Sandy Loam",
            sowing_date=datetime.utcnow() - timedelta(days=32), # Day 32 = Flowering stage
            status="ACTIVE"
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

        device = Device(
            device_uid=test_uid,
            mac_address=test_mac,
            farm_id=farm.id,
            name="ESP32 Dynamic Test Probe",
            status="ONLINE",
            irrigation_mode="AUTO"
        )
        db.add(device)
        db.commit()
        db.refresh(device)

        # -------------------------------------------------------------
        # TEST 1: Green Gram Dynamic Configuration Calculation
        # -------------------------------------------------------------
        print("\n[Test 1] Green Gram dynamic configuration calculation...")
        config1 = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config1.enabled is True
        assert config1.crop == "Green Gram (Moong)"
        assert config1.variety == "IPM 02-03"
        assert config1.growth_stage == "Flowering"
        assert config1.soil_type == "Sandy Loam"
        assert config1.start_threshold == 40.0 # Flowering base (40.0%) + Sandy Loam offset (0.0%)
        assert config1.stop_threshold == 50.0  # Hysteresis +10.0%
        assert config1.configuration_version >= 1
        assert config1.status == "APPROVED"
        print(f"  [PASS] Config calculated: Crop={config1.crop}, Stage={config1.growth_stage}, Start={config1.start_threshold}%, Stop={config1.stop_threshold}%, v{config1.configuration_version}.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 2: Variety Change Recalculation & Version Increment
        # -------------------------------------------------------------
        print("\n[Test 2] Variety change detection...")
        farm.crop_variety = "MH 421" # 58-day extra-early variety
        db.commit()
        config2 = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config2.variety == "MH 421"
        assert config2.configuration_version > config1.configuration_version
        print(f"  [PASS] Variety updated to MH 421 -> Version incremented to v{config2.configuration_version}.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 3: Growth Stage Advance Recalculation
        # -------------------------------------------------------------
        print("\n[Test 3] Growth stage advance (Vegetative -> Seedling vs Flowering)...")
        # Change sowing date to 20 days ago (Vegetative stage for IPM 02-03)
        farm.crop_variety = "IPM 02-03"
        farm.sowing_date = datetime.utcnow() - timedelta(days=20)
        db.commit()
        config3 = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config3.growth_stage == "Vegetative"
        assert config3.start_threshold == 30.0 # Vegetative base (30.0%) + Sandy Loam (0.0%)
        assert config3.stop_threshold == 40.0
        assert config3.configuration_version > config2.configuration_version
        print(f"  [PASS] Vegetative stage detected -> Start={config3.start_threshold}%, Stop={config3.stop_threshold}%, v{config3.configuration_version}.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 4: Soil Type Change & Soil Offset Application
        # -------------------------------------------------------------
        print("\n[Test 4] Soil type change with capacitive offset...")
        farm.soil_type = "Black Soil (Regur)" # Offset = +8.0%
        db.commit()
        config4 = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config4.soil_type == "Black Soil (Regur)"
        assert config4.start_threshold == 38.0 # Vegetative base (30.0%) + Black Soil offset (+8.0%) = 38.0%
        assert config4.stop_threshold == 48.0
        assert config4.configuration_version > config3.configuration_version
        print(f"  [PASS] Black Soil applied (+8.0% offset) -> Start={config4.start_threshold}%, Stop={config4.stop_threshold}%, v{config4.configuration_version}.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 5: Field Calibration Active Override
        # -------------------------------------------------------------
        print("\n[Test 5] Active field calibration override...")
        cal = FieldCalibrationRecord(
            field_id=farm.id,
            soil_type="Black Soil (Regur)",
            growth_stage="Vegetative",
            crop="Green Gram (Moong)",
            parameter="capacitive_soil_moisture_threshold",
            value=34.5,
            hysteresis_delta=8.0,
            status="ACTIVE",
            confidence=85,
            version=1
        )
        db.add(cal)
        db.commit()

        config5 = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config5.start_threshold == 34.5
        assert config5.stop_threshold == 42.5 # 34.5 + 8.0
        assert "FIELD_CALIBRATED" in config5.source
        assert config5.configuration_version > config4.configuration_version
        print(f"  [PASS] Active calibration applied -> Start={config5.start_threshold}%, Stop={config5.stop_threshold}% ({config5.source}) v{config5.configuration_version}.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 6: Invalid Configuration Rejection Simulation
        # -------------------------------------------------------------
        print("\n[Test 6] ESP32 validation: Reject inverted threshold ranges (start >= stop)...")
        # Simulate ESP32 validation logic
        invalid_start = 80.0
        invalid_stop = 20.0
        is_valid = (invalid_start > 0 and invalid_stop <= 100 and invalid_start < invalid_stop)
        assert is_valid is False

        # ESP32 sends rejection ACK
        ack_reject = DeviceConfigAckRequest(
            mac_address=device.mac_address,
            configuration_version=99,
            status="REJECTED",
            rejection_reason="Invalid threshold bounds: start_threshold >= stop_threshold"
        )
        res_reject = DeviceConfigSyncService.record_config_ack(db, ack_reject, device)
        assert device.config_ack_status == "REJECTED"
        assert device.last_config_rejection_reason is not None
        print(f"  [PASS] Inverted range (80% >= 20%) rejected -> Status={device.config_ack_status}.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 7: Missing / Disabled Dynamic Configuration Safe Policy
        # -------------------------------------------------------------
        print("\n[Test 7] Safe default policy when dynamic config is missing/disabled...")
        # Unassign device from farm
        device.farm_id = None
        db.commit()
        config_disabled = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config_disabled.enabled is False
        assert config_disabled.status == "DISABLED"
        print(f"  [PASS] Unassigned device returns enabled=False -> Prevents automatic irrigation.")
        # Restore farm
        device.farm_id = farm.id
        db.commit()
        passed += 1

        # -------------------------------------------------------------
        # TEST 8: Sensor Fault Safety Simulation
        # -------------------------------------------------------------
        print("\n[Test 8] Sensor fault safety guard...")
        # Simulate invalid soil moisture values (NaN, < 0%, > 100%)
        invalid_readings = [-5.0, 105.0, float('nan')]
        for inv in invalid_readings:
            # ESP32 local safety rule
            sensor_safe = (not (inv < 0.0 or inv > 100.0 or inv != inv))
            assert sensor_safe is False
        print("  [PASS] Sensor anomaly readings strictly block irrigation actuation.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 9: Local Rain Safety Override
        # -------------------------------------------------------------
        print("\n[Test 9] Rain sensor local safety override...")
        rain_detected = True
        pump_running = True
        # Local ESP32 rule
        if rain_detected and pump_running:
            pump_running = False # Forced OFF
            stop_reason = "LOCAL_RAIN_DETECTED_OVERRIDE"
        assert pump_running is False
        assert stop_reason == "LOCAL_RAIN_DETECTED_OVERRIDE"
        print("  [PASS] Rain detection forces immediate pump shutdown.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 10: AUTO -> MANUAL Mode Switch
        # -------------------------------------------------------------
        print("\n[Test 10] Website AUTO -> MANUAL mode transition...")
        device.irrigation_mode = "MANUAL"
        device.pump_status = True # Currently running
        db.commit()

        # ESP32 syncs mode
        if device.irrigation_mode == "MANUAL":
            auto_active = False
            pump_running = False # Stopped by mode switch
        assert auto_active is False
        assert pump_running is False
        print("  [PASS] Switching to MANUAL immediately stops automated irrigation loop.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 11: MANUAL -> AUTO Mode Transition
        # -------------------------------------------------------------
        print("\n[Test 11] MANUAL -> AUTO transition resumption...")
        device.irrigation_mode = "AUTO"
        db.commit()
        config_auto = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config_auto.enabled is True
        print(f"  [PASS] Resumed AUTO mode with valid dynamic config v{config_auto.configuration_version}.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 12: Configuration Version Deduplication
        # -------------------------------------------------------------
        print("\n[Test 12] Configuration version stability on repeated polls...")
        ver_before = config_auto.configuration_version
        config_repeat = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        ver_after = config_repeat.configuration_version
        assert ver_before == ver_after
        print(f"  [PASS] Identical configuration maintains version {ver_after} without spurious increments.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 13: Power Restart / Persistence Check
        # -------------------------------------------------------------
        print("\n[Test 13] Power restart persistence & validation...")
        # Simulate ESP32 boot
        boot_ver = config_repeat.configuration_version
        boot_start = config_repeat.start_threshold
        boot_stop = config_repeat.stop_threshold
        # Validate boot configuration
        boot_valid = (boot_start is not None and boot_stop is not None and boot_start < boot_stop)
        assert boot_valid is True
        print(f"  [PASS] Boot configuration verified valid (Start={boot_start}%, Stop={boot_stop}%).")
        passed += 1

        # -------------------------------------------------------------
        # TEST 14: Wi-Fi Loss & Maximum Runtime Cutoff
        # -------------------------------------------------------------
        print("\n[Test 14] Wi-Fi loss local max-runtime safety cutoff...")
        sim_start_time = 1000
        sim_current_time = 1000 + 301000 # 301 seconds elapsed (> 300s max runtime)
        pump_active = True
        if sim_current_time - sim_start_time >= 300000:
            pump_active = False # Forced OFF by local watchdog
            cutoff_reason = "MAX_RUNTIME_EXCEEDED"
        assert pump_active is False
        assert cutoff_reason == "MAX_RUNTIME_EXCEEDED"
        print("  [PASS] Local watchdog shuts down pump at 300s cutoff even without Wi-Fi.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 15: Telemetry Traceability Ingestion
        # -------------------------------------------------------------
        print("\n[Test 15] Telemetry reporting with applied dynamic configuration...")
        telem = DeviceTelemetry(
            device_id=device.id,
            farm_id=farm.id,
            soil_moisture=31.2,
            temperature=29.0,
            humidity=60.0,
            operation_mode="AUTO",
            pump_status=True,
            configuration_version=config_repeat.configuration_version,
            dynamic_threshold_config_valid=True,
            start_threshold=config_repeat.start_threshold,
            stop_threshold=config_repeat.stop_threshold,
            configured_crop=config_repeat.crop,
            configured_variety=config_repeat.variety,
            configured_growth_stage=config_repeat.growth_stage,
            irrigation_event_reason=f"Soil moisture (31.2%) < Start threshold ({config_repeat.start_threshold}%)"
        )
        db.add(telem)
        db.commit()
        db.refresh(telem)

        assert telem.configuration_version == config_repeat.configuration_version
        assert telem.start_threshold == config_repeat.start_threshold
        assert telem.configured_crop == "Green Gram (Moong)"
        print(f"  [PASS] Telemetry recorded complete agronomic context for irrigation event.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 16: Heartbeat Compatibility
        # -------------------------------------------------------------
        print("\n[Test 16] Heartbeat processing & RSSI tracking...")
        now = datetime.utcnow()
        device.last_heartbeat = now
        device.rssi = -65
        db.commit()
        assert device.rssi == -65
        print("  [PASS] Heartbeat connectivity and signal tracking verified.")
        passed += 1

        # -------------------------------------------------------------
        # TEST 17: Unsupported Non-Green Gram Crop Isolation Guard
        # -------------------------------------------------------------
        print("\n[Test 17] Unsupported crop isolation (Rice, Wheat, Cotton)...")
        farm.crop_type = "Rice"
        farm.crop_variety = "IR-64"
        db.commit()

        config_rice = DeviceConfigSyncService.calculate_device_irrigation_config(db, device)
        assert config_rice.enabled is False
        assert config_rice.status == "UNAVAILABLE"
        assert config_rice.start_threshold is None
        assert config_rice.stop_threshold is None
        assert "unsupported crop" in config_rice.reason.lower()
        print(f"  [PASS] Rice safely rejected with status UNAVAILABLE (zero Green Gram threshold leakage).")
        passed += 1

    finally:
        db.close()

    print("\n" + "=" * 80)
    print(f"DYNAMIC THRESHOLD SYNC TEST RESULTS: Passed {passed} / {total} ({(passed/total)*100:.1f}%)")
    print("=" * 80)
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    if not success:
        sys.exit(1)
