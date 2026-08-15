#include <Adafruit_INA219.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <ctime>
#include <DallasTemperature.h>
#include <OneWire.h>
#include <Preferences.h>
#include <PubSubClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <sys/time.h>

#include "charger_controller.hpp"
#if __has_include("credentials.hpp")
#include "credentials.hpp"
#else
#include "credentials.example.hpp"
#endif

namespace {

constexpr int kTemperaturePin = 4;
constexpr int kBatteryPresentPin = 27;
constexpr int kChargerEnablePin = 26;
constexpr std::uint32_t kSamplePeriodMs = 5'000U;
constexpr std::time_t kMinimumValidEpoch = 1'704'067'200;

Adafruit_INA219 power_sensor;
OneWire one_wire(kTemperaturePin);
DallasTemperature temperature_sensor(&one_wire);
WiFiClientSecure tls_client;
PubSubClient mqtt_client(tls_client);
charger::ChargerController controller;
std::uint32_t last_sample_ms = 0;
float delivered_capacity_mah = 0.0F;
std::uint32_t cycle_count = 0;
charger::Phase previous_phase = charger::Phase::idle;
Preferences preferences;

void connect_wifi() {
    WiFi.begin(kWifiSsid, kWifiPassword);
    while (WiFi.status() != WL_CONNECTED) {
        delay(250);
    }
}

void synchronize_clock() {
    configTime(0, 0, "pool.ntp.org", "time.nist.gov");
    for (int attempt = 0; attempt < 40; ++attempt) {
        if (std::time(nullptr) >= kMinimumValidEpoch) {
            return;
        }
        delay(500);
    }
    // Valid wall time is required for TLS certificate checks and unique records.
    digitalWrite(kChargerEnablePin, LOW);
    ESP.restart();
}

std::uint64_t unix_time_ms() {
    timeval now{};
    gettimeofday(&now, nullptr);
    return static_cast<std::uint64_t>(now.tv_sec) * 1'000ULL +
           static_cast<std::uint64_t>(now.tv_usec) / 1'000ULL;
}

void connect_mqtt() {
    while (!mqtt_client.connected()) {
        mqtt_client.connect(kDeviceId);
        if (!mqtt_client.connected()) {
            delay(1'000);
        }
    }
}

charger::Telemetry read_telemetry() {
    temperature_sensor.requestTemperatures();
    const float bus_voltage_v = power_sensor.getBusVoltage_V();
    const float shunt_voltage_v = power_sensor.getShuntVoltage_mV() / 1'000.0F;
    return {
        unix_time_ms(),
        bus_voltage_v + shunt_voltage_v,
        power_sensor.getCurrent_mA(),
        temperature_sensor.getTempCByIndex(0),
        digitalRead(kBatteryPresentPin) == HIGH,
    };
}

void apply_command(const charger::Command& command) {
    // The ESP32 only enables or inhibits an external regulated charger stage.
    // Cell-current and voltage limits must also be enforced in charger hardware.
    digitalWrite(kChargerEnablePin, command.charge_enabled ? HIGH : LOW);
}

void publish(
    const charger::Telemetry& telemetry,
    const charger::Command& command
) {
    JsonDocument document;
    document["schema_version"] = 1;
    document["device_id"] = kDeviceId;
    document["timestamp_ms"] = telemetry.timestamp_ms;
    document["voltage_v"] = telemetry.voltage_v;
    document["current_ma"] = telemetry.current_ma;
    document["temperature_c"] = telemetry.temperature_c;
    document["battery_present"] = telemetry.battery_present;
    document["phase"] = charger::to_string(command.phase);
    document["fault"] = charger::to_string(command.fault);
    document["charge_enabled"] = command.charge_enabled;
    document["requested_current_ma"] = command.requested_current_ma;
    document["delivered_capacity_mah"] = delivered_capacity_mah;
    document["cycle_count"] = cycle_count;

    char payload[384];
    const std::size_t length = serializeJson(document, payload);
    const String topic = String("battery-charger/") + kDeviceId + "/telemetry";
    mqtt_client.publish(topic.c_str(), payload, length);
}

}  // namespace

void setup() {
    Serial.begin(115200);
    pinMode(kBatteryPresentPin, INPUT_PULLDOWN);
    pinMode(kChargerEnablePin, OUTPUT);
    digitalWrite(kChargerEnablePin, LOW);

    power_sensor.begin();
    temperature_sensor.begin();
    preferences.begin("charger", false);
    cycle_count = preferences.getUInt("cycles", 0);
    connect_wifi();
    synchronize_clock();

    tls_client.setCACert(kRootCa);
    tls_client.setCertificate(kDeviceCertificate);
    tls_client.setPrivateKey(kPrivateKey);
    mqtt_client.setServer(kAwsIotEndpoint, 8883);
}

void loop() {
    if (WiFi.status() != WL_CONNECTED) {
        digitalWrite(kChargerEnablePin, LOW);
        connect_wifi();
    }
    if (!mqtt_client.connected()) {
        digitalWrite(kChargerEnablePin, LOW);
        connect_mqtt();
    }
    mqtt_client.loop();

    const std::uint32_t now = millis();
    if (now - last_sample_ms < kSamplePeriodMs) {
        return;
    }
    const std::uint32_t elapsed_ms =
        last_sample_ms == 0 ? 0 : now - last_sample_ms;
    last_sample_ms = now;

    const auto telemetry = read_telemetry();
    const auto command = controller.update(telemetry);
    if (previous_phase == charger::Phase::idle &&
        command.phase != charger::Phase::idle) {
        delivered_capacity_mah = 0.0F;
    }
    const float elapsed_hours =
        static_cast<float>(elapsed_ms) / 3'600'000.0F;
    if (telemetry.battery_present && telemetry.current_ma > 0.0F) {
        delivered_capacity_mah += telemetry.current_ma * elapsed_hours;
    }
    if (previous_phase != charger::Phase::complete &&
        command.phase == charger::Phase::complete) {
        ++cycle_count;
        preferences.putUInt("cycles", cycle_count);
    }
    previous_phase = command.phase;
    apply_command(command);
    publish(telemetry, command);
}
