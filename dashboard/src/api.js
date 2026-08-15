const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;
export const DEVICE_ID = import.meta.env.VITE_DEVICE_ID || "charger-001";

const demoItems = [
  { timestamp_ms: 0, voltage_v: 3.08, current_ma: 155, temperature_c: 25.1, phase: "precharge", fault: "none", delivered_capacity_mah: 12, cycle_count: 83, predicted_health_pct: 93.4 },
  { timestamp_ms: 300000, voltage_v: 3.42, current_ma: 798, temperature_c: 27.8, phase: "constant_current", fault: "none", delivered_capacity_mah: 78, cycle_count: 83, predicted_health_pct: 93.5 },
  { timestamp_ms: 600000, voltage_v: 3.69, current_ma: 805, temperature_c: 30.2, phase: "constant_current", fault: "none", delivered_capacity_mah: 145, cycle_count: 83, predicted_health_pct: 93.2 },
  { timestamp_ms: 900000, voltage_v: 3.96, current_ma: 792, temperature_c: 32.1, phase: "constant_current", fault: "none", delivered_capacity_mah: 211, cycle_count: 83, predicted_health_pct: 93.1 },
  { timestamp_ms: 1200000, voltage_v: 4.13, current_ma: 510, temperature_c: 31.4, phase: "constant_voltage", fault: "none", delivered_capacity_mah: 254, cycle_count: 83, predicted_health_pct: 93.3 },
  { timestamp_ms: 1500000, voltage_v: 4.19, current_ma: 272, temperature_c: 29.6, phase: "constant_voltage", fault: "none", delivered_capacity_mah: 277, cycle_count: 83, predicted_health_pct: 93.4 },
  { timestamp_ms: 1800000, voltage_v: 4.2, current_ma: 74, temperature_c: 27.2, phase: "complete", fault: "none", delivered_capacity_mah: 283, cycle_count: 83, predicted_health_pct: 93.5 },
];

export async function fetchTelemetry(signal) {
  if (!API_BASE_URL) {
    return { items: demoItems, demo: true };
  }
  const base = API_BASE_URL.replace(/\/$/, "");
  const response = await fetch(
    base + "/devices/" + DEVICE_ID + "/telemetry?limit=200",
    { signal },
  );
  if (!response.ok) {
    throw new Error("telemetry API returned " + response.status);
  }
  const payload = await response.json();
  return {
    items: [...payload.items].sort((left, right) => left.timestamp_ms - right.timestamp_ms),
    demo: false,
  };
}
