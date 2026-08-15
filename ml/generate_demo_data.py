from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path


PHASES = (
    ("precharge", 2.85, 150.0),
    ("constant_current", 3.35, 800.0),
    ("constant_current", 3.65, 800.0),
    ("constant_current", 3.95, 760.0),
    ("constant_voltage", 4.12, 520.0),
    ("constant_voltage", 4.18, 280.0),
    ("constant_voltage", 4.20, 130.0),
    ("complete", 4.20, 65.0),
)


def generate(destination: Path, cycles: int, seed: int) -> None:
    rng = random.Random(seed)
    fieldnames = [
        "cycle_id",
        "cycle_count",
        "sample_index",
        "voltage_v",
        "current_ma",
        "temperature_c",
        "phase",
        "delivered_capacity_mah",
        "health_pct",
    ]

    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for cycle in range(cycles):
            base_health = max(68.0, 100.0 - 0.055 * cycle - 0.00035 * cycle**1.6)
            thermal_penalty = max(0.0, rng.gauss(0.8, 0.45))
            health = max(60.0, base_health - thermal_penalty)
            nominal_capacity = 2_200.0
            delivered_total = nominal_capacity * health / 100.0
            for index, (phase, voltage, current) in enumerate(PHASES):
                progress = (index + 1) / len(PHASES)
                temperature = (
                    24.0
                    + 8.5 * math.sin(progress * math.pi)
                    + (100.0 - health) * 0.06
                    + rng.gauss(0.0, 0.35)
                )
                writer.writerow(
                    {
                        "cycle_id": f"demo-{cycle:04d}",
                        "cycle_count": cycle,
                        "sample_index": index,
                        "voltage_v": round(voltage + rng.gauss(0.0, 0.012), 4),
                        "current_ma": round(max(0.0, current + rng.gauss(0.0, 18.0)), 3),
                        "temperature_c": round(temperature, 3),
                        "phase": phase,
                        "delivered_capacity_mah": round(delivered_total * progress, 3),
                        "health_pct": round(health, 3),
                    }
                )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an explicitly synthetic charger dataset")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--cycles", type=int, default=240)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    generate(args.destination, args.cycles, args.seed)
    print(f"wrote {args.cycles * len(PHASES)} synthetic rows to {args.destination}")


if __name__ == "__main__":
    main()
