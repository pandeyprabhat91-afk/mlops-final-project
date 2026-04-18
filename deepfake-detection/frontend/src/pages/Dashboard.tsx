import { useEffect, useState, useCallback } from "react";

const PROM = "http://localhost:9090/api/v1/query";

async function pq(query: string): Promise<number | null> {
  try {
    const r = await fetch(`${PROM}?query=${encodeURIComponent(query)}`);
    if (!r.ok) return null;
    const d = await r.json();
    const v = d?.data?.result?.[0]?.value?.[1];
    return v != null ? parseFloat(v) : null;
  } catch {
    return null;
  }
}

interface PlatformStats {
  total_scans: number;
  fake_count: number;
  real_count: number;
  mlflow_val_f1: number | null;
  mlflow_val_accuracy: number | null;
  mlflow_train_f1: number | null;
  mlflow_val_loss: number | null;
  detection_rate: number;
  avg_inference_ms: number;
  total_users: number;
  dau: number;
  mau: number;
  feedback_samples: number;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  fpr: number | null;
}

function StatusDot({ up }: { up: boolean }) {
  return (
    <span style={{
      display: "inline-block", width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
      background: up ? "var(--real-color)" : "var(--fake-color)",
      boxShadow: up ? "0 0 6px rgba(74,222,128,0.5)" : "0 0 6px rgba(251,113,133,0.5)",
    }} />
  );
}

type Status = "ok" | "warn" | "bad" | "neutral" | "info";

const STATUS_COLOR: Record<Status, string> = {
  ok:      "var(--real-color)",
  warn:    "#f59e0b",
  bad:     "var(--fake-color)",
  neutral: "var(--accent)",
  info:    "#60a5fa",
};

function KpiCard({
  label, value, sub, status = "neutral", icon, extra,
}: {
  label: string; value: string; sub: string; status?: Status; icon: string; extra?: React.ReactNode;
}) {
  return (
    <div style={{
      background: "var(--glass-bg)",
      border: `1px solid var(--border)`,
      borderLeft: `3px solid ${STATUS_COLOR[status]}`,
      borderRadius: "var(--r-md)",
      padding: "1.1rem 1.25rem",
      display: "flex", flexDirection: "column", gap: "0.2rem",
      transition: "border-color 0.15s, box-shadow 0.15s",
    }}
      onMouseEnter={e => (e.currentTarget.style.boxShadow = "var(--shadow-sm)")}
      onMouseLeave={e => (e.currentTarget.style.boxShadow = "none")}
    >
      <div style={{ fontSize: "1rem", color: STATUS_COLOR[status], lineHeight: 1, marginBottom: "0.2rem" }}>{icon}</div>
      <div style={{ fontSize: "1.6rem", fontFamily: "var(--font-mono)", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.1 }}>
        {value}
      </div>
      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
        {label}
      </div>
      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>{sub}</div>
      {extra}
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: "0.75rem",
      marginBottom: "0.9rem", marginTop: "0.25rem",
    }}>
      <span style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--text-muted)" }}>
        {children}
      </span>
      <div style={{ flex: 1, height: 1, background: "var(--border)" }} />
    </div>
  );
}

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div style={{ marginTop: "0.5rem", background: "var(--glass-bg)", borderRadius: 4, height: 4, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.5s ease" }} />
    </div>
  );
}

function NullKpi({ label, icon }: { label: string; icon: string }) {
  return (
    <div style={{
      background: "var(--glass-bg)", border: "1px solid var(--border)", borderLeft: "3px solid var(--border-mid)",
      borderRadius: "var(--r-md)", padding: "1.1rem 1.25rem", display: "flex", flexDirection: "column", gap: "0.2rem",
    }}>
      <div style={{ fontSize: "1rem", color: "var(--text-muted)", lineHeight: 1 }}>{icon}</div>
      <div style={{ fontSize: "1.2rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>—</div>
      <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.15rem" }}>No feedback data yet</div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [modelInfo, setModelInfo] = useState<{ version: string; run_id: string; loaded: boolean } | null>(null);
  const [sysMetrics, setSysMetrics] = useState<{
    driftScore: number | null; modelMem: number | null; procMem: number | null;
    cpu: number | null; activeReqs: number | null; backendUp: boolean; airflowUp: boolean;
  }>({ driftScore: null, modelMem: null, procMem: null, cpu: null, activeReqs: null, backendUp: false, airflowUp: false });
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const [platformRes, modelRes, driftScore, modelMem, procMemBytes, cpu, activeReqs, backendUp, airflowUp] = await Promise.all([
      fetch("/api/admin/platform-stats").then(r => r.ok ? r.json() : null).catch(() => null),
      fetch("/api/admin/model-info").then(r => r.ok ? r.json() : null).catch(() => null),
      pq("deepfake_drift_score"),
      pq("deepfake_model_memory_mb"),
      pq('process_resident_memory_bytes{job="backend"}'),
      pq('rate(process_cpu_seconds_total{job="backend"}[1m])'),
      pq("deepfake_active_requests"),
      pq('up{job="backend"}'),
      pq('up{job="airflow"}'),
    ]);
    if (platformRes) setStats(platformRes);
    if (modelRes) setModelInfo({ version: modelRes.model_version, run_id: modelRes.run_id, loaded: modelRes.model_loaded });
    setSysMetrics({
      driftScore, modelMem, procMem: procMemBytes != null ? procMemBytes / (1024 * 1024) : null,
      cpu, activeReqs, backendUp: backendUp === 1, airflowUp: airflowUp === 1,
    });
    setLastRefresh(new Date());
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); const id = setInterval(fetchAll, 30_000); return () => clearInterval(id); }, [fetchAll]);

  const s = stats;
  const m = sysMetrics;

  return (
    <div className="page-wide" style={{ paddingTop: "2rem", paddingBottom: "3rem" }}>

      {/* ── Header ── */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "1.75rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <h1 style={{ fontFamily: "var(--font-display)", fontSize: "1.6rem", fontWeight: 700, margin: 0, color: "var(--text-primary)" }}>
            System Dashboard
          </h1>
          <p style={{ color: "var(--text-secondary)", margin: "0.3rem 0 0", fontSize: "0.83rem" }}>
            Platform analytics · all users · live system health
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ fontSize: "0.76rem", color: "var(--text-muted)" }}>
            Updated {lastRefresh.toLocaleTimeString()}
          </span>
          <button onClick={fetchAll} disabled={loading} style={{
            background: "var(--glass-bg)", border: "1px solid var(--border)", borderRadius: "var(--r-sm)",
            color: "var(--text-secondary)", padding: "0.4rem 0.9rem", fontSize: "0.8rem",
            cursor: loading ? "wait" : "pointer", opacity: loading ? 0.5 : 1, transition: "all 0.15s",
          }}>
            {loading ? "Loading…" : "↻ Refresh"}
          </button>
        </div>
      </div>

      {/* ── Model strip ── */}
      {modelInfo && (
        <div style={{
          background: "var(--glass-bg)", border: "1px solid var(--border)", borderRadius: "var(--r-md)",
          padding: "0.7rem 1.25rem", marginBottom: "1.75rem",
          display: "flex", alignItems: "center", gap: "2rem", flexWrap: "wrap",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <StatusDot up={modelInfo.loaded} />
            <span style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>Model</span>
            <span style={{ fontSize: "0.82rem", fontFamily: "var(--font-mono)", color: "var(--text-primary)" }}>{modelInfo.version}</span>
          </div>
          <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
            Run: <span style={{ fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>{modelInfo.run_id.slice(0, 12)}…</span>
          </div>
          <div style={{ fontSize: "0.82rem", color: modelInfo.loaded ? "var(--real-color)" : "var(--fake-color)" }}>
            {modelInfo.loaded ? "● Loaded" : "○ Not loaded"}
          </div>
          {m.driftScore != null && (
            <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Drift</span>
              <span style={{
                fontFamily: "var(--font-mono)", fontSize: "0.82rem",
                color: m.driftScore > 3 ? "var(--fake-color)" : m.driftScore > 1 ? "#f59e0b" : "var(--real-color)",
              }}>{m.driftScore.toFixed(3)}</span>
            </div>
          )}
        </div>
      )}

      {/* ── 1. Usage & Adoption ── */}
      <SectionHeader>Usage & Adoption</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.75rem" }}>
        <KpiCard
          label="Videos Analyzed" icon="◈" status="neutral"
          value={s ? s.total_scans.toLocaleString() : "—"}
          sub="total uploads processed"
        />
        <KpiCard
          label="Total Users" icon="◎" status="info"
          value={s ? s.total_users.toString() : "—"}
          sub={s ? `${s.dau} active today · ${s.mau} this month` : "loading…"}
        />
        <KpiCard
          label="Daily Active Users" icon="↑" status={s && s.dau > 0 ? "ok" : "neutral"}
          value={s ? s.dau.toString() : "—"}
          sub="users in last 24 hours"
          extra={s && s.mau > 0 ? <MiniBar value={s.dau} max={s.mau} color="var(--accent)" /> : undefined}
        />
        <KpiCard
          label="Monthly Active" icon="◉" status="info"
          value={s ? s.mau.toString() : "—"}
          sub="users in last 30 days"
        />
      </div>

      {/* ── 2. Detection ── */}
      <SectionHeader>Detection Results</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.75rem" }}>
        <KpiCard
          label="Deepfake Detection Rate" icon="⚠" status={s && s.detection_rate > 70 ? "warn" : "ok"}
          value={s ? `${s.detection_rate.toFixed(1)}%` : "—"}
          sub={s ? `${s.fake_count} flagged · ${s.real_count} authentic` : "loading…"}
          extra={s ? <MiniBar value={s.fake_count} max={s.total_scans} color="var(--fake-color)" /> : undefined}
        />
        <KpiCard
          label="Authentic Videos" icon="✓" status="ok"
          value={s ? s.real_count.toLocaleString() : "—"}
          sub={s && s.total_scans > 0 ? `${(100 - s.detection_rate).toFixed(1)}% of scans` : "no data"}
        />
        <KpiCard
          label="Deepfakes Flagged" icon="✗" status="bad"
          value={s ? s.fake_count.toLocaleString() : "—"}
          sub={s ? `${s.detection_rate.toFixed(1)}% of scans` : "no data"}
        />
      </div>

      {/* ── 3. Model Quality ── */}
      <SectionHeader>Model Quality · training validation metrics</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", marginBottom: "0.75rem" }}>
        <KpiCard
          label="Val F1 Score" icon="◆"
          status={s?.mlflow_val_f1 != null ? (s.mlflow_val_f1 >= 90 ? "ok" : s.mlflow_val_f1 >= 75 ? "warn" : "bad") : "neutral"}
          value={s?.mlflow_val_f1 != null ? `${s.mlflow_val_f1.toFixed(1)}%` : "—"}
          sub="validation set · current run"
        />
        <KpiCard
          label="Val Accuracy" icon="▣"
          status={s?.mlflow_val_accuracy != null ? (s.mlflow_val_accuracy >= 90 ? "ok" : s.mlflow_val_accuracy >= 75 ? "warn" : "bad") : "neutral"}
          value={s?.mlflow_val_accuracy != null ? `${s.mlflow_val_accuracy.toFixed(1)}%` : "—"}
          sub="validation set · current run"
        />
        <KpiCard
          label="Train F1 Score" icon="▤"
          status={s?.mlflow_train_f1 != null ? (s.mlflow_train_f1 >= 90 ? "ok" : "warn") : "neutral"}
          value={s?.mlflow_train_f1 != null ? `${s.mlflow_train_f1.toFixed(1)}%` : "—"}
          sub="training set · current run"
        />
        <KpiCard
          label="Val Loss" icon="~"
          status={s?.mlflow_val_loss != null ? (s.mlflow_val_loss < 0.1 ? "ok" : s.mlflow_val_loss < 0.5 ? "warn" : "bad") : "neutral"}
          value={s?.mlflow_val_loss != null ? s.mlflow_val_loss.toFixed(4) : "—"}
          sub="cross-entropy · current run"
        />
      </div>

      {/* Live feedback metrics (shown only when feedback data exists) */}
      {s && s.feedback_samples > 0 && (
        <>
          <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginBottom: "0.75rem", paddingLeft: "0.1rem" }}>
            Live production metrics · {s.feedback_samples} ground-truth labels submitted
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.75rem" }}>
            <KpiCard label="Live F1 Score" icon="◆" status={s.f1_score! >= 90 ? "ok" : s.f1_score! >= 75 ? "warn" : "bad"}
              value={`${s.f1_score!.toFixed(1)}%`} sub="based on user feedback" />
            <KpiCard label="Precision" icon="▣" status={s.precision! >= 90 ? "ok" : s.precision! >= 75 ? "warn" : "bad"}
              value={`${s.precision!.toFixed(1)}%`} sub="of flagged, truly fake" />
            <KpiCard label="Recall" icon="▤" status={s.recall! >= 90 ? "ok" : s.recall! >= 75 ? "warn" : "bad"}
              value={`${s.recall!.toFixed(1)}%`} sub="fakes correctly caught" />
            <KpiCard label="False Positive Rate" icon="!" status={s.fpr! <= 2 ? "ok" : s.fpr! <= 5 ? "warn" : "bad"}
              value={`${s.fpr!.toFixed(2)}%`} sub="authentic wrongly flagged" />
          </div>
        </>
      )}
      {s && s.feedback_samples === 0 && (
        <div style={{
          fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "1.75rem",
          padding: "0.6rem 1rem", background: "var(--glass-bg)", border: "1px solid var(--border)",
          borderRadius: "var(--r-sm)",
        }}>
          Live precision/recall/FPR will appear here once users submit ground-truth feedback via the Feedback button after a scan.
        </div>
      )}

      {/* ── 4. Performance ── */}
      <SectionHeader>Performance</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem", marginBottom: "1.75rem" }}>
        <KpiCard
          label="Avg Inference Time" icon="⏱"
          status={s && s.avg_inference_ms > 5000 ? "warn" : s && s.avg_inference_ms > 0 ? "ok" : "neutral"}
          value={s && s.avg_inference_ms > 0 ? `${(s.avg_inference_ms / 1000).toFixed(1)}s` : "—"}
          sub="per video (end-to-end)"
        />
        <KpiCard
          label="Active Requests" icon="↻"
          status={m.activeReqs != null && m.activeReqs > 3 ? "warn" : "ok"}
          value={m.activeReqs != null ? m.activeReqs.toFixed(0) : "0"}
          sub="in-flight predictions"
        />
        <KpiCard
          label="Process Memory" icon="▤"
          status={m.procMem != null && m.procMem > 1800 ? "warn" : "ok"}
          value={m.procMem != null ? `${m.procMem.toFixed(0)} MB` : "—"}
          sub="backend resident memory"
          extra={m.procMem != null ? <MiniBar value={m.procMem} max={2048} color={m.procMem > 1800 ? "#f59e0b" : "var(--accent)"} /> : undefined}
        />
        <KpiCard
          label="CPU Rate" icon="◉"
          status={m.cpu != null && m.cpu > 0.8 ? "warn" : "ok"}
          value={m.cpu != null ? `${(m.cpu * 100).toFixed(2)}%` : "—"}
          sub="1-minute average"
        />
      </div>

      {/* ── 5. Service Health ── */}
      <SectionHeader>Service Health</SectionHeader>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(175px, 1fr))", gap: "0.75rem", marginBottom: "1.75rem" }}>
        {[
          { name: "Backend API", up: m.backendUp, url: "http://localhost:8000/health" },
          { name: "Prometheus",  up: m.driftScore !== null, url: "http://localhost:9090" },
          { name: "Grafana",     up: true, url: "http://localhost:3001" },
          { name: "MLflow",      up: true, url: "http://localhost:5000" },
          { name: "Airflow",     up: m.airflowUp, url: "http://localhost:8080" },
        ].map(svc => (
          <a key={svc.name} href={svc.url} target="_blank" rel="noreferrer" style={{
            display: "flex", alignItems: "center", gap: "0.6rem",
            padding: "0.75rem 1rem", background: "var(--glass-bg)",
            border: "1px solid var(--border)", borderRadius: "var(--r-md)",
            textDecoration: "none", transition: "border-color 0.15s",
          }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--border-mid)")}
            onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
          >
            <StatusDot up={svc.up} />
            <div>
              <div style={{ fontSize: "0.84rem", fontWeight: 600, color: "var(--text-primary)" }}>{svc.name}</div>
              <div style={{ fontSize: "0.72rem", color: svc.up ? "var(--real-color)" : "var(--fake-color)" }}>
                {svc.up ? "Operational" : "Down"}
              </div>
            </div>
            <span style={{ marginLeft: "auto", fontSize: "0.7rem", color: "var(--text-muted)" }}>↗</span>
          </a>
        ))}
      </div>

      {/* ── Grafana CTA ── */}
      <div style={{
        background: "var(--glass-bg)", border: "1px solid var(--border)", borderRadius: "var(--r-lg)",
        padding: "1.25rem 1.5rem", display: "flex", alignItems: "center",
        justifyContent: "space-between", flexWrap: "wrap", gap: "1rem",
      }}>
        <div>
          <div style={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--text-primary)", marginBottom: "0.25rem" }}>
            Full Time-Series Dashboard
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            Histograms, latency percentiles, alert panels in Grafana
          </div>
        </div>
        <a href="http://localhost:3001/d/deepfake-combined/deepfake-detection-overview"
          target="_blank" rel="noreferrer" style={{
            display: "inline-flex", alignItems: "center", gap: "0.4rem",
            background: "var(--grad)", color: "#fff", fontWeight: 600, fontSize: "0.84rem",
            padding: "0.55rem 1.2rem", borderRadius: "var(--r-sm)", textDecoration: "none",
            boxShadow: "var(--shadow-sm)",
          }}>
          Open Grafana ↗
        </a>
      </div>
    </div>
  );
}
