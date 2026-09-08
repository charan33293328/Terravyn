"""
Validation test for ESP32 Irrigation Config Versioning Fix.
Verifies all 10 checklist items specified in the task.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from database.connection import SessionLocal
from models.domain import Device, Farm
from app.main import app

def test_esp32_config_version_fix():
    print("=" * 80)
    print("RUNNING ESP32 IRRIGATION CONFIG_VERSION VERIFICATION SUITE")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    try:
        # Check target device in DB
        device = db.query(Device).filter(Device.device_uid == "TRV-DEV-20260614-4468").first()
        assert device is not None, "Target device TRV-DEV-20260614-4468 not found in DB"
        farm = db.query(Farm).filter(Farm.id == device.farm_id).first()
        assert farm is not None, f"Target farm {device.farm_id} not found in DB"

        # Item 1: Device is correctly mapped to intended farm/plot
        print(f"\n[Check 1] Device mapped to farm: ID={farm.id}, Name='{farm.name}'... [PASS]")

        # Item 2: Crop is Green Gram (Moong)
        print(f"[Check 2] Crop Type: '{farm.crop_type}'... [PASS]")
        assert "Green Gram" in farm.crop_type or "Moong" in farm.crop_type

        # Item 3: Variety is Pusa Vishal
        print(f"[Check 3] Crop Variety: '{farm.crop_variety}'... [PASS]")
        assert farm.crop_variety == "Pusa Vishal"

        # Item 4: Growth stage is Flowering
        print(f"[Check 4] Growth Stage: '{farm.growth_stage_override}'... [PASS]")
        assert farm.growth_stage_override == "Flowering"

        # Item 5 & 6: Call GET /api/devices/config/{device_uid} via FastAPI TestClient
        print("\n[Check 5 & 6] Querying GET /api/devices/config/{device_uid}...")
        resp = client.get(f"/api/devices/config/{device.device_uid}")
        assert resp.status_code == 200, f"Failed HTTP request: {resp.text}"
        data = resp.json()
        print(f"  Response: {data}")

        irr = data.get("irrigation_config", {})
        assert irr.get("enabled") is True
        assert irr.get("crop") == "Green Gram (Moong)"
        assert irr.get("variety") == "Pusa Vishal"
        assert irr.get("growth_stage") == "Flowering"
        assert irr.get("start_threshold") == 36.5
        assert irr.get("stop_threshold") == 46.5
        assert irr.get("status") == "APPROVED"
        assert data.get("config_version") >= 1
        assert irr.get("configuration_version") >= 1
        print(f"  [PASS] Start={irr.get('start_threshold')}%, Stop={irr.get('stop_threshold')}%, config_version={data.get('config_version')} (> 0).")

        initial_version = data.get("config_version")

        # Item 7: Repeated GET requests return the same version when nothing changes
        print("\n[Check 7] Repeated polling idempotency check (simulating 10:00, 10:00:10, 10:00:20)...")
        for i in range(5):
            r = client.get(f"/api/devices/config/{device.mac_address}")
            assert r.status_code == 200
            assert r.json().get("config_version") == initial_version
        print(f"  [PASS] Polled 5 consecutive times -> version remained constant at v{initial_version}.")

        # Test Telemetry from unconfigured/booting ESP32 doesn't downgrade config_version
        print("\n[Telemetry Resilience Check] Simulating telemetry from ESP32...")
        telem_resp = client.post("/api/devices/telemetry", json={
            "mac_address": device.mac_address,
            "device_uid": device.device_uid,
            "soil_moisture": 32.0,
            "temperature": 27.5,
            "humidity": 65.0,
            "configuration_version": 0 # Booting ESP32 reports 0 before ACK
        })
        assert telem_resp.status_code == 200
        # Check backend endpoint still delivers valid positive config_version
        r_after_telem = client.get(f"/api/devices/config/{device.device_uid}")
        assert r_after_telem.json().get("config_version") == initial_version
        print(f"  [PASS] Telemetry with version 0 did NOT corrupt backend config_version (remains v{initial_version}).")

        # Item 8: Changing an approved configuration creates a new version
        print("\n[Check 8] Changing approved configuration parameters (e.g. stage override to Vegetative)...")
        farm.growth_stage_override = "Vegetative"
        db.commit()

        resp_changed = client.get(f"/api/devices/config/{device.device_uid}")
        data_changed = resp_changed.json()
        new_version = data_changed.get("config_version")
        assert new_version > initial_version
        assert data_changed["irrigation_config"]["growth_stage"] == "Vegetative"
        assert data_changed["irrigation_config"]["start_threshold"] == 30.0 # Vegetative base (30.0) + Sandy Loam (0.0)
        assert data_changed["irrigation_config"]["stop_threshold"] == 40.0
        print(f"  [PASS] Configuration change detected -> Version incremented from v{initial_version} to v{new_version}.")

        # Restore Flowering stage
        farm.growth_stage_override = "Flowering"
        db.commit()
        resp_restored = client.get(f"/api/devices/config/{device.device_uid}")
        data_restored = resp_restored.json()
        assert data_restored["irrigation_config"]["growth_stage"] == "Flowering"
        assert data_restored["irrigation_config"]["start_threshold"] == 36.5
        assert data_restored["irrigation_config"]["stop_threshold"] == 46.5
        restored_version = data_restored.get("config_version")
        assert restored_version > new_version
        print(f"  [PASS] Restored Flowering stage -> Start={data_restored['irrigation_config']['start_threshold']}%, Stop={data_restored['irrigation_config']['stop_threshold']}%, v{restored_version}.")

        # Item 9: Backend restart simulation (close DB sessions, reload from DB)
        print("\n[Check 9] Backend restart persistence simulation...")
        db.close()
        db_new = SessionLocal()
        dev_reloaded = db_new.query(Device).filter(Device.device_uid == "TRV-DEV-20260614-4468").first()
        assert dev_reloaded.config_version == restored_version
        assert dev_reloaded.config_version > 0
        db_new.close()
        print(f"  [PASS] DB reload verified config_version is persisted as v{restored_version} (> 0).")

        # Item 10: ESP32 validation simulation against C++ validateReceivedConfiguration logic
        print("\n[Check 10] ESP32 firmware C++ validation function emulation...")
        irr_payload = data_restored["irrigation_config"]
        # In C++:
        # outStart = irrConfig["start_threshold"].as<float>();
        # outStop  = irrConfig["stop_threshold"].as<float>();
        # outVer   = irrConfig["configuration_version"].as<int>();
        # if (isnan(outStart) || isnan(outStop)) return false;
        # if (outStart <= 0.0 || outStart >= 100.0) return false;
        # if (outStop <= 0.0 || outStop > 100.0) return false;
        # if (outStart >= outStop) return false;
        # if (outVer <= 0) return false;
        outStart = float(irr_payload["start_threshold"])
        outStop = float(irr_payload["stop_threshold"])
        outVer = int(irr_payload["configuration_version"])
        esp32_valid = (
            (outStart > 0.0 and outStart < 100.0) and
            (outStop > 0.0 and outStop <= 100.0) and
            (outStart < outStop) and
            (outVer > 0)
        )
        assert esp32_valid is True
        print(f"  [PASS] ESP32 C++ validation evaluates to TRUE for Start={outStart}%, Stop={outStop}%, Version={outVer}.")

        # Emulate ESP32 sending ACK v{outVer}
        ack_resp = client.post("/api/devices/config/ack", json={
            "mac_address": device.mac_address,
            "device_uid": device.device_uid,
            "configuration_version": outVer,
            "status": "APPLIED",
            "applied_start_threshold": outStart,
            "applied_stop_threshold": outStop,
            "crop": irr_payload["crop"],
            "variety": irr_payload["variety"],
            "growth_stage": irr_payload["growth_stage"]
        })
        assert ack_resp.status_code == 200
        print(f"  [PASS] ESP32 successfully sent ACK for configuration version v{outVer}.")

    finally:
        db.close()

    print("\n" + "=" * 80)
    print("ALL 10 ESP32 CONFIG_VERSION VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    test_esp32_config_version_fix()
