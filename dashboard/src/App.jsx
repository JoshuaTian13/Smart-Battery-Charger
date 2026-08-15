import { useEffect, useMemo, useState } from "react";
import { DEVICE_ID, fetchTelemetry } from "./api";

function formatPhase(phase = "unknown") {
  return phase
    .split("_")
    .map((word) => word[0].toUpperCase() + word.slice(1))
    .join(" ");
}

function Metric({ label, value, unit, accent }) {
  return (
    <article className="metric-card">
      <span className="metric-label">{label}</span>
      <div className="metric-value" style={{ color: accent }}>
        {value}
        <span>{unit}</span>
      </div>
    </article>
  );
}

function Sparkline({ items, field, color, label }) {
  const points = useMemo(() => {
    if (!items.length) return "";
    const values = items.map((item) => Number(item[field]));
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    const range = maximum - minimum || 1;
    return values
      .map((value, index) => {
        const x = (index / Math.max(values.length - 1, 1)) * 100;
        const y = 92 - ((value - minimum) / range) * 78;
        return x + "," + y;
      })
      .join(" ");
  }, [field, items]);

  return (
    <div className="chart-card">
      <div className="chart-heading">
        <span>{label}</span>
        <span>{items.at(-1)?.[field]?.toFixed?.(2) ?? "—"}</span>
      </div>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label={label}>
        <defs>
          <linearGradient id={"fill-" + field} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.28" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon
          points={"0,100 " + points + " 100,100"}
          fill={"url(#fill-" + field + ")"}
        />
        <polyline points={points} fill="none" stroke={color} strokeWidth="2.2" />
      </svg>
    </div>
  );
}

function HealthGauge({ value }) {
  const bounded = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className="health-card">
      <div
        className="health-ring"
        style={{ "--health": bounded * 3.6 + "deg" }}
      >
        <div>
          <strong>{bounded.toFixed(1)}%</strong>
          <span>estimated health</span>
        </div>
      </div>
      <p>
        Advisory model output from charge telemetry. Deterministic embedded
        limits remain authoritative.
      </p>
    </div>
  );
}

export default function App() {
  const [telemetry, setTelemetry] = useState([]);
  const [isDemo, setIsDemo] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    fetchTelemetry(controller.signal)
      .then(({ items, demo }) => {
        setTelemetry(items);
        setIsDemo(demo);
      })
      .catch((reason) => {
        if (reason.name !== "AbortError") setError(reason.message);
      });
    return () => controller.abort();
  }, []);

  const latest = telemetry.at(-1) || {};
  const maxTemperature = telemetry.length
    ? Math.max(...telemetry.map((item) => Number(item.temperature_c)))
    : 0;
  const energyWh = telemetry.reduce((sum, item, index) => {
    if (index === 0) return sum;
    const previous = telemetry[index - 1];
    const hours = (item.timestamp_ms - previous.timestamp_ms) / 3_600_000;
    const power = Number(item.voltage_v) * Number(item.current_ma) / 1000;
    return sum + power * hours;
  }, 0);

  return (
    <main>
      <header>
        <div>
          <span className="eyebrow">Connected charger telemetry</span>
          <h1>Battery intelligence,<br />from cell to cloud.</h1>
        </div>
        <div className="device-status">
          <span className={latest.fault === "none" ? "status-dot" : "status-dot fault"} />
          <div>
            <strong>{DEVICE_ID}</strong>
            <span>{formatPhase(latest.phase)}</span>
          </div>
        </div>
      </header>

      {isDemo && <div className="banner">Showing synthetic demonstration telemetry</div>}
      {error && <div className="banner error">{error}</div>}

      <section className="metrics">
        <Metric label="Cell voltage" value={latest.voltage_v?.toFixed?.(2) ?? "—"} unit="V" accent="#84f4bd" />
        <Metric label="Charge current" value={latest.current_ma?.toFixed?.(0) ?? "—"} unit="mA" accent="#69b7ff" />
        <Metric label="Temperature" value={latest.temperature_c?.toFixed?.(1) ?? "—"} unit="°C" accent="#ffb86b" />
        <Metric label="Delivered" value={latest.delivered_capacity_mah?.toFixed?.(0) ?? "—"} unit="mAh" accent="#d7a5ff" />
      </section>

      <section className="visuals">
        <div className="charts">
          <Sparkline items={telemetry} field="voltage_v" color="#84f4bd" label="Voltage profile" />
          <Sparkline items={telemetry} field="current_ma" color="#69b7ff" label="Current profile" />
          <Sparkline items={telemetry} field="temperature_c" color="#ffb86b" label="Thermal profile" />
        </div>
        <HealthGauge value={latest.predicted_health_pct} />
      </section>

      <section className="session">
        <div>
          <span>Peak temperature</span>
          <strong>{maxTemperature.toFixed(1)} °C</strong>
        </div>
        <div>
          <span>Estimated energy delivered</span>
          <strong>{energyWh.toFixed(2)} Wh</strong>
        </div>
        <div>
          <span>Cycle count</span>
          <strong>{latest.cycle_count ?? "—"}</strong>
        </div>
        <div>
          <span>Safety status</span>
          <strong>{latest.fault === "none" ? "Nominal" : formatPhase(latest.fault)}</strong>
        </div>
      </section>
    </main>
  );
}
