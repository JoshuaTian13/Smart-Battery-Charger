#pragma once

#include <cstdint>

namespace charger {

enum class Phase : std::uint8_t {
    idle,
    precharge,
    constant_current,
    constant_voltage,
    complete,
    fault,
};

enum class Fault : std::uint8_t {
    none,
    invalid_sensor,
    over_temperature,
    over_voltage,
};

struct Telemetry {
    std::uint64_t timestamp_ms;
    float voltage_v;
    float current_ma;
    float temperature_c;
    bool battery_present;
};

struct Limits {
    float minimum_valid_voltage_v = 0.0F;
    float maximum_valid_voltage_v = 5.5F;
    float precharge_voltage_v = 3.0F;
    float regulation_voltage_v = 4.2F;
    float maximum_temperature_c = 45.0F;
    float precharge_current_ma = 150.0F;
    float charge_current_ma = 800.0F;
    float termination_current_ma = 80.0F;
    std::uint8_t termination_samples = 3;
};

struct Command {
    Phase phase;
    Fault fault;
    bool charge_enabled;
    float requested_current_ma;
};

class ChargerController {
public:
    explicit ChargerController(Limits limits = {});

    Command update(const Telemetry& sample);
    void reset();

private:
    bool valid(const Telemetry& sample) const;
    Command fail(Fault fault);

    Limits limits_;
    Phase phase_ = Phase::idle;
    Fault fault_ = Fault::none;
    std::uint8_t termination_count_ = 0;
};

const char* to_string(Phase phase);
const char* to_string(Fault fault);

}  // namespace charger
