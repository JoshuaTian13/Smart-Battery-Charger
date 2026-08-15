#include "charger_controller.hpp"

#include <algorithm>
#include <cmath>

namespace charger {

ChargerController::ChargerController(const Limits limits) : limits_(limits) {}

bool ChargerController::valid(const Telemetry& sample) const {
    return std::isfinite(sample.voltage_v) &&
           std::isfinite(sample.current_ma) &&
           std::isfinite(sample.temperature_c) &&
           sample.voltage_v >= limits_.minimum_valid_voltage_v &&
           sample.voltage_v <= limits_.maximum_valid_voltage_v &&
           sample.current_ma >= -50.0F &&
           sample.temperature_c >= -20.0F &&
           sample.temperature_c <= 100.0F;
}

Command ChargerController::fail(const Fault fault) {
    phase_ = Phase::fault;
    fault_ = fault;
    termination_count_ = 0;
    return {phase_, fault_, false, 0.0F};
}

Command ChargerController::update(const Telemetry& sample) {
    if (phase_ == Phase::fault) {
        return {phase_, fault_, false, 0.0F};
    }
    if (!valid(sample)) {
        return fail(Fault::invalid_sensor);
    }
    if (sample.temperature_c > limits_.maximum_temperature_c) {
        return fail(Fault::over_temperature);
    }
    if (sample.voltage_v > limits_.regulation_voltage_v + 0.05F) {
        return fail(Fault::over_voltage);
    }
    if (!sample.battery_present) {
        phase_ = Phase::idle;
        termination_count_ = 0;
        return {phase_, Fault::none, false, 0.0F};
    }

    if (sample.voltage_v < limits_.precharge_voltage_v) {
        phase_ = Phase::precharge;
        termination_count_ = 0;
        return {phase_, Fault::none, true, limits_.precharge_current_ma};
    }

    if (sample.voltage_v < limits_.regulation_voltage_v - 0.03F) {
        phase_ = Phase::constant_current;
        termination_count_ = 0;
        return {phase_, Fault::none, true, limits_.charge_current_ma};
    }

    if (sample.current_ma <= limits_.termination_current_ma) {
        termination_count_ = static_cast<std::uint8_t>(
            std::min<int>(termination_count_ + 1, limits_.termination_samples)
        );
    } else {
        termination_count_ = 0;
    }

    if (termination_count_ >= limits_.termination_samples) {
        phase_ = Phase::complete;
        return {phase_, Fault::none, false, 0.0F};
    }

    phase_ = Phase::constant_voltage;
    const float taper_ratio = std::clamp(
        sample.current_ma / limits_.charge_current_ma,
        0.1F,
        1.0F
    );
    return {
        phase_,
        Fault::none,
        true,
        limits_.charge_current_ma * taper_ratio,
    };
}

void ChargerController::reset() {
    phase_ = Phase::idle;
    fault_ = Fault::none;
    termination_count_ = 0;
}

const char* to_string(const Phase phase) {
    switch (phase) {
        case Phase::idle: return "idle";
        case Phase::precharge: return "precharge";
        case Phase::constant_current: return "constant_current";
        case Phase::constant_voltage: return "constant_voltage";
        case Phase::complete: return "complete";
        case Phase::fault: return "fault";
    }
    return "unknown";
}

const char* to_string(const Fault fault) {
    switch (fault) {
        case Fault::none: return "none";
        case Fault::invalid_sensor: return "invalid_sensor";
        case Fault::over_temperature: return "over_temperature";
        case Fault::over_voltage: return "over_voltage";
    }
    return "unknown";
}

}  // namespace charger
