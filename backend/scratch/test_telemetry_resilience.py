"""
Comprehensive test for ESP32 Telemetry endpoint resilience.
Tests multiple URL routes, payload formats, header formats, and identifier schemes.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from database.connection import SessionLocal
from models.domain import Device, DeviceTelemetry
from app.main import app

def test_telemetry():
    client = TestClient(app)
    db = SessionLocal()

    try:
        device = db.query(Device).filter(Device.device_uid == "TRV-DEV-20260614-4468").first()
        assert device is not None

        routes = [
            "/api/devices/telemetry",
            "/api/devices/data",
            "/devices/telemetry",
            "/device/telemetry",
            "/api/device/telemetry",
            "/telemetry",
            "/data",
            "/api/sensors/data",
            "/api/sensors/telemetry"
        ]

        test_payloads = [
            # 1. Standard ESP32 payload
            {
                "device_id": device.mac_address,
                "mac_address": device.mac_address,
                "soil_moisture": 34.2,
                "temperature": 28.5,
                "humidity": 62.0,
                "rain_detected": False,
                "operation_mode": "AUTO",
                "pump_status": False,
                "wifi_rssi": -65,
                "firmware_version": "2.0.0",
                "uptime_seconds": 300,
                "configuration_version": 5,
                "dynamic_threshold_config_valid": True,
                "start_threshold": 36.5,
                "stop_threshold": 46.5,
                "configured_crop": "Green Gram (Moong)",
                "configured_variety": "Pusa Vishal",
                "configured_growth_stage": "Flowering"
            },
            # 2. Firmware generated deviceUID format (TRV-ESP32-B0CBD8CA2818)
            {
                "device_id": "TRV-ESP32-B0CBD8CA2818",
                "device_uid": "TRV-ESP32-B0CBD8CA2818",
                "soil_moisture": 35.0,
                "temperature": 29.1,
                "humidity": 58.0,
                "rain_detected": False,
                "operation_mode": "AUTO",
                "pump_status": False
            },
            # 3. Clean MAC without colons
            {
                "device_id": "B0CBD8CA2818",
                "soil_moisture": 33.8,
                "temperature": 27.9,
                "humidity": 64.0
            },
            # 4. Backend Device UID
            {
                "device_uid": "TRV-DEV-20260614-4468",
                "soil_moisture": 36.0,
                "temperature": 28.0,
                "humidity": 60.0
            },
            # 5. Nested sensor payload format (v1.0 ESP32)
            {
                "mac_address": device.mac_address,
                "sensors": {
                    "soil_moisture": 32.5,
                    "temperature": 28.2,
                    "humidity": 61.0,
                    "rain_detected": False,
                    "water_level": 85.0,
                    "bmp280": {
                        "temperature": 28.1,
                        "pressure": 1012.5,
                        "altitude": 150.0
                    }
                },
                "pump_status": {
                    "is_running": False,
                    "mode": "AUTO",
                    "last_run_duration": 0
                }
            }
        ]

        print("=" * 80)
        print("RUNNING ESP32 TELEMETRY RESILIENCE TEST")
        print("=" * 80)

        for route in routes:
            for i, p in enumerate(test_payloads):
                resp = client.post(route, json=p)
                assert resp.status_code == 200, f"Failed on route {route}, payload {i}: {resp.status_code} {resp.text}"
                data = resp.json()
                assert data.get("success") is True or "message" in data
                print(f"  [PASS] Route: {route:25} | Payload #{i+1} -> HTTP 200 (device_uid: {data.get('device_uid')})")

        # Test heartbeat endpoint
        hb_resp = client.post("/api/devices/heartbeat", json={"device_id": "TRV-ESP32-B0CBD8CA2818", "rssi": -62})
        assert hb_resp.status_code == 200
        print("\n  [PASS] Heartbeat with generated device UID -> HTTP 200")

        # Test ACK endpoint
        ack_resp = client.post("/api/devices/config/ack", json={
            "mac_address": "TRV-ESP32-B0CBD8CA2818",
            "configuration_version": 5,
            "status": "APPLIED"
        })
        assert ack_resp.status_code == 200
        print("  [PASS] Config ACK with generated device UID -> HTTP 200")

    finally:
        db.close()

    print("\n" + "=" * 80)
    print("ALL TELEMETRY, HEARTBEAT & ACK RESILIENCE TESTS PASSED (HTTP 200)!")
    print("=" * 80)

if __name__ == "__main__":
    test_telemetry()
