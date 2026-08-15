#include "charger_controller.hpp"

#include <cassert>
#include <iostream>

namespace {

charger::Telemetry sample(
    const float voltage,
    const float current,
    const float temperature,
    const bool present = true
) {
    return {1'000U, voltage, current, temperature, present};
}

}  // namespace

int main() {
    charger::ChargerController controller;

    auto command = controller.update(sample(0.0F, 0.0F, 25.0F, false));
    assert(command.phase == charger::Phase::idle);
    assert(!command.charge_enabled);

    command = controller.update(sample(2.8F, 120.0F, 25.0F));
    assert(command.phase == charger::Phase::precharge);
    assert(command.requested_current_ma == 150.0F);

    command = controller.update(sample(3.7F, 790.0F, 29.0F));
    assert(command.phase == charger::Phase::constant_current);
    assert(command.requested_current_ma == 800.0F);

    command = controller.update(sample(4.19F, 300.0F, 32.0F));
    assert(command.phase == charger::Phase::constant_voltage);
    assert(command.charge_enabled);

    command = controller.update(sample(4.20F, 70.0F, 32.0F));
    assert(command.phase == charger::Phase::constant_voltage);
    command = controller.update(sample(4.20F, 65.0F, 32.0F));
    assert(command.phase == charger::Phase::constant_voltage);
    command = controller.update(sample(4.20F, 60.0F, 32.0F));
    assert(command.phase == charger::Phase::complete);
    assert(!command.charge_enabled);

    controller.reset();
    command = controller.update(sample(3.8F, 500.0F, 48.0F));
    assert(command.phase == charger::Phase::fault);
    assert(command.fault == charger::Fault::over_temperature);
    assert(!command.charge_enabled);

    command = controller.update(sample(3.8F, 500.0F, 25.0F));
    assert(command.phase == charger::Phase::fault);

    controller.reset();
    command = controller.update(sample(4.3F, 100.0F, 25.0F));
    assert(command.fault == charger::Fault::over_voltage);

    std::cout << "PASS: charger phases, termination debounce, and latched faults\n";
    return 0;
}
