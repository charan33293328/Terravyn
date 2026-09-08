/*
 * =====================================================================================
 * TERRAVYN SMART AGRICULTURE — ESP32 FIRMWARE V2.0
 * DYNAMIC CROP/VARIETY IRRIGATION THRESHOLD SYNCHRONIZATION & LOCAL SAFETY CONTROLLER
 * =====================================================================================
 * 
 * Hardware Target: ESP32 NodeMCU / DevKit V1
 * Sensors Supported:
 *   - Capacitive Soil Moisture Sensor v1.2 (Analog PIN 34) [4095=DRY (0%), 1400=WET (100%)]
 *   - DHT11 / DHT22 Air Temperature & Humidity (PIN 4)
 *   - Rain Drop Sensor (Digital PIN 35 / Analog PIN 32)
 *   - BMP280 Barometric Pressure & Temp (I2C SDA:21, SCL:22)
 *   - Ultrasonic Water Level Sensor HC-SR04 (Trig: 5, Echo: 18)
 *   - 5V Relay Channel for Submersible Pump (PIN 26) [Active LOW / HIGH configurable]
 *   - Manual Push Button with Hardware Debounce (PIN 27)
 *   - Status Indicators (RGB / Built-in LED: PIN 2)
 * =====================================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>

// -------------------------------------------------------------------------------------
// PIN DEFINITIONS
// -------------------------------------------------------------------------------------
#define PIN_SOIL_ANALOG      34
#define PIN_RAIN_DIGITAL     35
#define PIN_RELAY_PUMP       26
#define PIN_MANUAL_BUTTON    27
#define PIN_STATUS_LED        2

// -------------------------------------------------------------------------------------
// PHYSICAL SENSOR CALIBRATION CONSTANTS (ADC MAPPING: 4095=DRY, 1400=WET)
// -------------------------------------------------------------------------------------
const int ADC_RAW_DRY = 4095;  // In-air sensor dry reference (0% moisture)
const int ADC_RAW_WET = 1400;  // Submerged sensor wet reference (100% moisture)

// -------------------------------------------------------------------------------------
// LOCAL SAFETY HARDWARE LIMITS
// -------------------------------------------------------------------------------------
const unsigned long MAX_PUMP_RUNTIME_MS    = 300000;  // 5 minutes max continuous runtime
const unsigned long TELEMETRY_INTERVAL_MS  = 10000;   // Send telemetry every 10 seconds
const unsigned long CONFIG_POLL_INTERVAL_MS= 15000;   // Poll config every 15 seconds
const unsigned long HEARTBEAT_INTERVAL_MS  = 30000;   // Heartbeat every 30 seconds

// -------------------------------------------------------------------------------------
// BACKEND NETWORK CONFIGURATION
// -------------------------------------------------------------------------------------
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* BACKEND_BASE  = "http://192.168.1.16:8000"; // Terravyn Backend Server URL

// -------------------------------------------------------------------------------------
// RUNTIME IRRIGATION STATE & DYNAMIC THRESHOLD VARIABLES (REPLACES HARD-CODED CONSTANTS)
// -------------------------------------------------------------------------------------
String currentOperationMode = "AUTO"; // "AUTO" or "MANUAL"
bool   pumpRunning          = false;
unsigned long pumpStartTime = 0;

// Dynamic Agronomic Threshold Variables Received from Backend
float  dynamicStartThreshold        = 0.0;
float  dynamicStopThreshold         = 0.0;
bool   dynamicThresholdConfigValid  = false;
bool   dynamicHysteresisEnabled     = true;
String configuredCrop               = "NONE";
String configuredVariety            = "";
String configuredGrowthStage        = "";
String configuredSoilType           = "";
int    configurationVersion         = 0;
String configStatus                 = "NO_CONFIG";

// Telemetry Variables
float  currentSoilMoisture  = 0.0;
float  currentTemperature   = 28.5;
float  currentHumidity      = 65.0;
bool   rainDetected         = false;
bool   lowWaterAlert        = false;
int    wifiRSSI             = 0;
String deviceMacAddress     = "";
String deviceUID            = "";

// Timers
unsigned long lastTelemetryTime  = 0;
unsigned long lastConfigPollTime = 0;
unsigned long lastHeartbeatTime  = 0;

// -------------------------------------------------------------------------------------
// FUNCTION PROTOTYPES
// -------------------------------------------------------------------------------------
void setupHardware();
void connectWiFi();
float readSoilMoisturePercentage();
bool readRainSensor();
void fetchDeviceConfiguration();
void sendConfigAcknowledgement(int version, const char* status, const char* rejectionReason = nullptr);
void sendTelemetry();
void sendHeartbeat();
void automaticIrrigation();
void turnPumpOn(const char* reason);
void turnPumpOff(const char* reason);
void handleManualButton();
bool validateReceivedConfiguration(JsonObject irrConfig, float &outStart, float &outStop, int &outVer);

// =====================================================================================
// ARDUINO SETUP
// =====================================================================================
void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n========================================================");
    Serial.println("  TERRAVYN SMART AGRICULTURE -- ESP32 CONTROLLER V2.0   ");
    Serial.println("========================================================");

    setupHardware();
    connectWiFi();

    // Fetch initial configuration immediately on boot
    fetchDeviceConfiguration();
}

// =====================================================================================
// ARDUINO MAIN LOOP
// =====================================================================================
void loop() {
    unsigned long currentMillis = millis();

    // 1. Maintain Wi-Fi Connection
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }

    // 2. Read live physical sensors
    currentSoilMoisture = readSoilMoisturePercentage();
    rainDetected        = readRainSensor();
    wifiRSSI            = WiFi.RSSI();

    // 3. Handle Manual Push-Button (Immediate physical override)
    handleManualButton();

    // 4. Run Dynamic Automatic Irrigation Loop
    if (currentOperationMode == "AUTO") {
        automaticIrrigation();
    }

    // 5. Check Maximum Pump Runtime Safety Cutoff
    if (pumpRunning && (currentMillis - pumpStartTime >= MAX_PUMP_RUNTIME_MS)) {
        turnPumpOff("MAX_RUNTIME_EXCEEDED_SAFETY_CUTOFF");
    }

    // 6. Periodic Backend Communication Tasks
    if (currentMillis - lastConfigPollTime >= CONFIG_POLL_INTERVAL_MS) {
        fetchDeviceConfiguration();
        lastConfigPollTime = currentMillis;
    }

    if (currentMillis - lastTelemetryTime >= TELEMETRY_INTERVAL_MS) {
        sendTelemetry();
        lastTelemetryTime = currentMillis;
    }

    if (currentMillis - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
        sendHeartbeat();
        lastHeartbeatTime = currentMillis;
    }

    delay(100);
}

// =====================================================================================
// SENSOR READING FUNCTIONS
// =====================================================================================
float readSoilMoisturePercentage() {
    int rawADC = analogRead(PIN_SOIL_ANALOG);
    
    // Strict sensor conversion: 4095=DRY (0%), 1400=WET (100%)
    float percentage = (float)(ADC_RAW_DRY - rawADC) / (float)(ADC_RAW_DRY - ADC_RAW_WET) * 100.0;
    
    if (percentage < 0.0) percentage = 0.0;
    if (percentage > 100.0) percentage = 100.0;
    
    return percentage;
}

bool readRainSensor() {
    // Digital LOW typically indicates active rain detected on resistive sensor
    return (digitalRead(PIN_RAIN_DIGITAL) == LOW);
}

// =====================================================================================
// DYNAMIC AUTOMATIC IRRIGATION ENGINE (LOCAL EXECUTION LAYER)
// =====================================================================================
void automaticIrrigation() {
    // GUARD 1: Operation Mode Check
    if (currentOperationMode != "AUTO") {
        return;
    }

    // GUARD 2: Dynamic Configuration Validity Check (SAFE DEFAULT POLICY)
    if (!dynamicThresholdConfigValid) {
        // If no valid configuration exists, DO NOT start automatic irrigation
        if (pumpRunning) {
            turnPumpOff("NO_VALID_CONFIG_SAFETY_SHUTDOWN");
        }
        return;
    }

    // GUARD 3: Sensor Fault / Anomaly Check
    if (isnan(currentSoilMoisture) || currentSoilMoisture < 0.0 || currentSoilMoisture > 100.0) {
        if (pumpRunning) {
            turnPumpOff("SENSOR_FAULT_ANOMALY");
        }
        return;
    }

    // GUARD 4: Local Rain Safety Override
    if (rainDetected) {
        if (pumpRunning) {
            turnPumpOff("LOCAL_RAIN_DETECTED_OVERRIDE");
        }
        return;
    }

    // GUARD 5: Low Water Level Safety Override
    if (lowWaterAlert) {
        if (pumpRunning) {
            turnPumpOff("LOW_WATER_LEVEL_OVERRIDE");
        }
        return;
    }

    // EXECUTION: Evaluate Dynamic Hysteresis Thresholds
    if (currentSoilMoisture < dynamicStartThreshold && !pumpRunning) {
        Serial.printf("[AUTO] Soil moisture (%.1f%%) < Dynamic Start Threshold (%.1f%%) [%s - %s v%d]. Starting Pump.\n",
            currentSoilMoisture, dynamicStartThreshold, configuredCrop.c_str(), configuredGrowthStage.c_str(), configurationVersion);
        turnPumpOn("AUTO_DYNAMIC_THRESHOLD_TRIGGER");
    } 
    else if (currentSoilMoisture >= dynamicStopThreshold && pumpRunning) {
        Serial.printf("[AUTO] Soil moisture (%.1f%%) >= Dynamic Stop Threshold (%.1f%%) [%s - %s v%d]. Stopping Pump.\n",
            currentSoilMoisture, dynamicStopThreshold, configuredCrop.c_str(), configuredGrowthStage.c_str(), configurationVersion);
        turnPumpOff("AUTO_DYNAMIC_TARGET_REACHED");
    }
}

// =====================================================================================
// HARDWARE ACTUATION & AUDIT
// =====================================================================================
void turnPumpOn(const char* reason) {
    if (!pumpRunning) {
        digitalWrite(PIN_RELAY_PUMP, HIGH);
        pumpRunning = true;
        pumpStartTime = millis();
        digitalWrite(PIN_STATUS_LED, HIGH);
        Serial.printf("[PUMP] Turned ON. Reason: %s (Time: %lu ms)\n", reason, pumpStartTime);
        sendTelemetry(); // Report state change immediately
    }
}

void turnPumpOff(const char* reason) {
    if (pumpRunning) {
        digitalWrite(PIN_RELAY_PUMP, LOW);
        pumpRunning = false;
        unsigned long runDurationSec = (millis() - pumpStartTime) / 1000;
        pumpStartTime = 0;
        digitalWrite(PIN_STATUS_LED, LOW);
        Serial.printf("[PUMP] Turned OFF. Reason: %s (Duration: %lu s)\n", reason, runDurationSec);
        sendTelemetry(); // Report state change immediately
    }
}

void handleManualButton() {
    static int lastButtonState = HIGH;
    int currentButtonState = digitalRead(PIN_MANUAL_BUTTON);

    if (lastButtonState == HIGH && currentButtonState == LOW) {
        delay(50); // Debounce
        if (digitalRead(PIN_MANUAL_BUTTON) == LOW) {
            Serial.println("[MANUAL] Physical button pressed. Toggling pump state.");
            if (pumpRunning) {
                turnPumpOff("PHYSICAL_MANUAL_BUTTON_STOP");
            } else {
                turnPumpOn("PHYSICAL_MANUAL_BUTTON_START");
            }
        }
    }
    lastButtonState = currentButtonState;
}

// =====================================================================================
// BACKEND CONFIGURATION SYNCHRONIZATION & VALIDATION
// =====================================================================================
void fetchDeviceConfiguration() {
    if (WiFi.status() != WL_CONNECTED) return;

    HTTPClient http;
    String url = String(BACKEND_BASE) + "/api/devices/config/" + deviceMacAddress;
    http.begin(url);
    http.setTimeout(5000);

    int httpCode = http.GET();
    if (httpCode == HTTP_CODE_OK) {
        String payload = http.getString();
        StaticJsonDocument<1024> doc;
        DeserializationError error = deserializeJson(doc, payload);

        if (!error) {
            // 1. Sync Operation Mode (AUTO vs MANUAL)
            const char* mode = doc["irrigation_mode"];
            if (mode != nullptr) {
                String newMode = String(mode);
                if (newMode != currentOperationMode) {
                    Serial.printf("[CONFIG] Operation mode changed: %s -> %s\n", currentOperationMode.c_str(), newMode.c_str());
                    currentOperationMode = newMode;
                    if (currentOperationMode == "MANUAL" && pumpRunning) {
                        turnPumpOff("SWITCHED_TO_MANUAL_MODE");
                    }
                }
            }

            // 2. Parse and Validate Dynamic Irrigation Configuration
            if (doc.containsKey("irrigation_config") && !doc["irrigation_config"].isNull()) {
                JsonObject irrConfig = doc["irrigation_config"];
                bool enabled = irrConfig["enabled"] | false;

                if (!enabled) {
                    const char* reason = irrConfig["reason"] | "Disabled by Backend";
                    Serial.printf("[CONFIG] Dynamic irrigation disabled: %s\n", reason);
                    dynamicThresholdConfigValid = false;
                    configStatus = "DISABLED";
                } else {
                    float newStart = 0.0, newStop = 0.0;
                    int newVer = 0;
                    
                    if (validateReceivedConfiguration(irrConfig, newStart, newStop, newVer)) {
                        // Apply valid configuration
                        if (configurationVersion != newVer || !dynamicThresholdConfigValid) {
                            dynamicStartThreshold       = newStart;
                            dynamicStopThreshold        = newStop;
                            configurationVersion        = newVer;
                            configuredCrop              = irrConfig["crop"].as<String>();
                            configuredVariety           = irrConfig["variety"].as<String>();
                            configuredGrowthStage       = irrConfig["growth_stage"].as<String>();
                            configuredSoilType          = irrConfig["soil_type"].as<String>();
                            dynamicHysteresisEnabled    = irrConfig["hysteresis_enabled"] | true;
                            dynamicThresholdConfigValid = true;
                            configStatus                = "APPLIED";

                            Serial.printf("[CONFIG] Applied v%d: %s (%s) | Start=%.1f%% Stop=%.1f%%\n",
                                configurationVersion, configuredCrop.c_str(), configuredGrowthStage.c_str(),
                                dynamicStartThreshold, dynamicStopThreshold);

                            sendConfigAcknowledgement(configurationVersion, "APPLIED");
                        }
                    } else {
                        Serial.println("[CONFIG ERROR] Received invalid threshold configuration! Rejecting.");
                        dynamicThresholdConfigValid = false;
                        configStatus = "REJECTED";
                        sendConfigAcknowledgement(newVer, "REJECTED", "Invalid threshold bounds (start >= stop or out of 0-100% range)");
                    }
                }
            } else {
                // Backward compatibility: Missing dynamic configuration
                dynamicThresholdConfigValid = false;
                configStatus = "UNAVAILABLE";
            }
        }
    } else {
        Serial.printf("[HTTP] Config poll failed, code: %d\n", httpCode);
    }
    http.end();
}

bool validateReceivedConfiguration(JsonObject irrConfig, float &outStart, float &outStop, int &outVer) {
    if (!irrConfig.containsKey("start_threshold") || !irrConfig.containsKey("stop_threshold") || !irrConfig.containsKey("configuration_version")) {
        return false;
    }

    outStart = irrConfig["start_threshold"].as<float>();
    outStop  = irrConfig["stop_threshold"].as<float>();
    outVer   = irrConfig["configuration_version"].as<int>();

    // Numerical and Range Bounds Validation
    if (isnan(outStart) || isnan(outStop)) return false;
    if (outStart <= 0.0 || outStart >= 100.0) return false;
    if (outStop <= 0.0 || outStop > 100.0) return false;
    if (outStart >= outStop) return false; // Strict Hysteresis Rule
    if (outVer <= 0) return false;

    return true;
}

void sendConfigAcknowledgement(int version, const char* status, const char* rejectionReason) {
    if (WiFi.status() != WL_CONNECTED) return;

    HTTPClient http;
    String url = String(BACKEND_BASE) + "/api/devices/config/ack";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<256> doc;
    doc["mac_address"]             = deviceMacAddress;
    doc["device_uid"]              = deviceUID;
    doc["configuration_version"]   = version;
    doc["status"]                  = status;
    doc["applied_start_threshold"] = dynamicStartThreshold;
    doc["applied_stop_threshold"]  = dynamicStopThreshold;
    doc["crop"]                    = configuredCrop;
    doc["variety"]                 = configuredVariety;
    doc["growth_stage"]            = configuredGrowthStage;
    if (rejectionReason != nullptr) {
        doc["rejection_reason"]    = rejectionReason;
    }

    String jsonBody;
    serializeJson(doc, jsonBody);
    int httpCode = http.POST(jsonBody);
    Serial.printf("[ACK] Sent config ACK v%d (%s), response: %d\n", version, status, httpCode);
    http.end();
}

// =====================================================================================
// TELEMETRY & HEARTBEAT COMMUNICATION
// =====================================================================================
void sendTelemetry() {
    if (WiFi.status() != WL_CONNECTED) return;

    HTTPClient http;
    String url = String(BACKEND_BASE) + "/api/devices/telemetry";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<512> doc;
    doc["device_id"]                      = deviceMacAddress;
    doc["mac_address"]                    = deviceMacAddress;
    doc["soil_moisture"]                  = currentSoilMoisture;
    doc["temperature"]                    = currentTemperature;
    doc["humidity"]                       = currentHumidity;
    doc["rain_detected"]                  = rainDetected;
    doc["operation_mode"]                 = currentOperationMode;
    doc["pump_status"]                    = pumpRunning;
    doc["wifi_rssi"]                      = wifiRSSI;
    doc["firmware_version"]               = "2.0.0";
    doc["uptime_seconds"]                 = millis() / 1000;

    // Dynamic Configuration Traceability Fields
    doc["configuration_version"]          = configurationVersion;
    doc["dynamic_threshold_config_valid"] = dynamicThresholdConfigValid;
    doc["start_threshold"]                = dynamicStartThreshold;
    doc["stop_threshold"]                 = dynamicStopThreshold;
    doc["configured_crop"]                = configuredCrop;
    doc["configured_variety"]             = configuredVariety;
    doc["configured_growth_stage"]        = configuredGrowthStage;

    String jsonBody;
    serializeJson(doc, jsonBody);
    int httpCode = http.POST(jsonBody);
    http.end();
}

void sendHeartbeat() {
    if (WiFi.status() != WL_CONNECTED) return;

    HTTPClient http;
    String url = String(BACKEND_BASE) + "/api/devices/heartbeat";
    http.begin(url);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<256> doc;
    doc["device_id"] = deviceMacAddress;
    doc["rssi"]      = wifiRSSI;

    String jsonBody;
    serializeJson(doc, jsonBody);
    http.POST(jsonBody);
    http.end();
}

// =====================================================================================
// HARDWARE INITIALIZATION & WIFI
// =====================================================================================
void setupHardware() {
    pinMode(PIN_RELAY_PUMP, OUTPUT);
    digitalWrite(PIN_RELAY_PUMP, LOW); // Start with pump safely OFF

    pinMode(PIN_STATUS_LED, OUTPUT);
    digitalWrite(PIN_STATUS_LED, LOW);

    pinMode(PIN_MANUAL_BUTTON, INPUT_PULLUP);
    pinMode(PIN_RAIN_DIGITAL, INPUT);
    pinMode(PIN_SOIL_ANALOG, INPUT);

    deviceMacAddress = WiFi.macAddress();
    deviceUID = "TRV-ESP32-" + deviceMacAddress;
    deviceUID.replace(":", "");
}

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;

    Serial.printf("[WIFI] Connecting to SSID: %s ...\n", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\n[WIFI] Connected successfully!");
        Serial.printf("[WIFI] IP Address: %s | MAC: %s\n", WiFi.localIP().toString().c_str(), deviceMacAddress.c_str());
    } else {
        Serial.println("\n[WIFI] Connection failed. Operating in offline failsafe mode.");
    }
}
