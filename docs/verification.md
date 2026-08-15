# Verification matrix

## Automated repository checks

| Layer | Automated checks |
| --- | --- |
| Firmware | Host-tested idle/precharge/CC/CV/completion/fault logic plus a full PlatformIO ESP32 application build |
| Cloud validation | Valid storage, strict Boolean/range checks, derived power, duplicate detection, seven-feature prediction contract, and model suppression during faults |
| Query API | Newest-first query configuration and bounded result limits |
| ML features/inference | Cloud/training feature-order parity, derived power, phase encoding, non-finite input rejection, and bounded endpoint output |
| ML training in CI | Synthetic dataset generation, cycle-grouped cross-validation, model comparison, holdout evaluation, and artifact creation |
| Dashboard | Clean production build with React and Vite |

Run the portable suite:

```bash
make test
```

## Hardware validation plan

| Stage | Instruments | Representative checks |
| --- | --- | --- |
| Unpowered PCB | Multimeter | Rail shorts, connector polarity, continuity, shunt routing |
| Current-limited bring-up | Bench supply, multimeter | Input current, 3.3 V stability, ESP32 boot, safe default enable |
| Sensor validation | Reference DMM, thermometer | INA219 voltage/current accuracy, DS18B20 response and disconnect behavior |
| Charger-stage test | Electronic load/test cell, scope | Precharge current, regulation voltage, current taper, enable response |
| Fault injection | Heat source, sensor disconnect, voltage sweep | Over-temperature, invalid-sensor, and over-voltage latch behavior |
| Cloud integration | MQTT test client, CloudWatch | Certificate policy, payload validation, duplicates, disconnect/reconnect |
| End-to-end cycle | Protected test cell, logged instrumentation | Phase transitions, accumulated capacity, DynamoDB records, dashboard curves |

## ML validation boundary

The demonstration generator proves that the code path is reproducible; it does not establish real-world model accuracy. A deployable model requires measured labeled cycles spanning cells, temperatures, charge rates, ages, and sensor variation. Evaluation must split by battery or cycle group to prevent leakage, report error across operating subgroups, and preserve deterministic hardware limits regardless of prediction.
