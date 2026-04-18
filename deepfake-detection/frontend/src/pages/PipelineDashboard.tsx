import type React from "react";
import { useEffect, useState } from "react";
import { apiClient } from "../api/client";
import { ErrorConsole } from "../components/ErrorConsole";
import type { LogEntry } from "../components/ErrorConsole";

interface MLflowRun {
  run_id: string;
  run_name: string;
  status: string;
  start_time: number;
  metrics: Record<string, number>;
  params: Record<string, string>;
  tags: Record<string, string>;
}

interface AirflowRun {
  dag_id: string;
  state: string;
  start_date: string;
  end_date: string | null;
}

function StatusBadge({ status }: { status: string }) {
  const s = status.toLowerCase();
  const cls =
    s === "finished" || s === "success" ? "badge-green"
    : s === "running"                    ? "badge-blue"
    : s === "failed"                     ? "badge-red"
    : "badge-muted";
  return (
    <span className={`badge ${cls}`}>
      <span className="badge-dot" />
      {status}
    </span>
  );
}

const f4 = (v: number | undefined) => v !== undefined ? v.toFixed(4) : "—";
const fDate = (ts: number) => !ts ? "—" : new Date(ts).toLocaleString("en-GB", {
  day: "2-digit", month: "short", year: "2-digit", hour: "2-digit", minute: "2-digit"
});

export const PipelineDashboard: React.FC = () => {
  const [runs, setRuns]           = useState<MLflowRun[]>([]);
  const [airflow, setAirflow]     = useState<AirflowRun[]>([]);
  const [throughput, setThroughput] = useState<number | null>(null);
  const [expanded, setExpanded]   = useState<string | null>(null);

  useEffect(() => {
    apiClient.get<MLflowRun[]>("/pipeline/mlflow-runs").then(r => setRuns(r.data)).catch(() => {});
    apiClient.get<AirflowRun[]>("/pipeline/airflow-runs").then(r => setAirflow(r.data)).catch(() => {});
    apiClient.get<{ videos_per_minute: number }>("/pipeline/throughput").then(r => setThroughput(r.data.videos_per_minute)).catch(() => {});
  }, []);

  const finished = runs.filter(r => r.status === "FINISHED");
  const bestRun  = finished.reduce<MLflowRun | null>((b, r) =>
    !b || (r.metrics?.val_f1 ?? 0) > (b.metrics?.val_f1 ?? 0) ? r : b, null);
  const avgF1    = finished.length
    ? (finished.reduce((a, r) => a + (r.metrics?.val_f1 ?? 0), 0) / finished.length)
    : null;

  const logEntries: LogEntry[] = airflow.map(r => ({
    id: r.dag_id + r.start_date,
    timestamp: r.start_date,
    type: r.state === "success" ? "success" : r.state === "failed" ? "error" : "warning",
    message: `${r.dag_id} — ${r.state}`,
  }));

  return (
    <div className="page-wide">
      <p className="page-eyebrow">MLOps</p>
      <h1 className="page-title">Pipeline</h1>
      <p className="page-sub">Experiment runs, training metrics, and Airflow DAG status.</p>

      {/* Stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <span className="stat-label">Throughput</span>
          <div className="stat-value">{throughput !== null ? throughput.toFixed(1) : "—"}</div>
          <div className="stat-unit">videos / min</div>
        </div>
        <div className="stat-card">
          <span className="stat-label">Total runs</span>
          <div className="stat-value">{runs.length}</div>
          <div className="stat-unit">MLflow experiments</div>
        </div>
        <div className="stat-card">
          <span className="stat-label">Best val F1</span>
          <div className="stat-value" style={{ color: "var(--green)" }}>
            {bestRun ? f4(bestRun.metrics.val_f1) : "—"}
          </div>
          <div className="stat-unit">{bestRun?.run_id.slice(0,8) ?? "—"}</div>
        </div>
        <div className="stat-card">
          <span className="stat-label">Avg val F1</span>
          <div className="stat-value">{avgF1 !== null ? avgF1.toFixed(3) : "—"}</div>
          <div className="stat-unit">finished runs</div>
        </div>
      </div>

      {/* MLflow runs */}
      <div className="sh">
        <h2>MLflow Runs</h2>
        <div className="sh-line" />
      </div>

      <div className="tbl-wrap">
        <table className="tbl">
          <thead>
            <tr>
              <th>Run</th>
              <th>Date</th>
              <th>Status</th>
              <th>Val F1</th>
              <th>Val Acc</th>
              <th>Val Loss</th>
              <th>LR</th>
              <th>Epochs</th>
            </tr>
          </thead>
          <tbody>
            {runs.map(run => (
              <>
                <tr
                  key={run.run_id}
                  style={{ cursor: "pointer" }}
                  onClick={() => setExpanded(expanded === run.run_id ? null : run.run_id)}
                >
                  <td>
                    <span className="tbl-mono">{run.run_id.slice(0,8)}</span>
                    {run.run_name && (
                      <span style={{ color: "var(--ink-4)", fontSize: 11, marginLeft: 6, fontFamily: "var(--font-mono)" }}>
                        {run.run_name}
                      </span>
                    )}
                  </td>
                  <td className="tbl-mono" style={{ fontSize: 11 }}>{fDate(run.start_time)}</td>
                  <td><StatusBadge status={run.status} /></td>
                  <td className="tbl-mono" style={{ color: (run.metrics?.val_f1 ?? 0) >= 0.9 ? "var(--green)" : undefined, fontWeight: 500 }}>
                    {f4(run.metrics?.val_f1)}
                  </td>
                  <td className="tbl-mono">{f4(run.metrics?.val_accuracy)}</td>
                  <td className="tbl-mono">{f4(run.metrics?.val_loss)}</td>
                  <td className="tbl-mono">{run.params?.lr ?? "—"}</td>
                  <td className="tbl-mono">{run.params?.epochs ?? "—"}</td>
                </tr>

                {expanded === run.run_id && (
                  <tr key={`${run.run_id}-d`}>
                    <td colSpan={8} style={{ padding: 0 }}>
                      <div className="run-detail">
                        <div className="run-detail-grid">
                          <div>
                            <p className="run-detail-section-label">All metrics (final epoch)</p>
                            {Object.entries(run.metrics).map(([k, v]) => (
                              <div className="run-kv" key={k}>
                                <span className="run-kv-key">{k}</span>
                                <span className="run-kv-val">{typeof v === "number" ? v.toFixed(6) : v}</span>
                              </div>
                            ))}
                          </div>
                          <div>
                            <p className="run-detail-section-label">Hyperparameters</p>
                            {Object.entries(run.params).map(([k, v]) => (
                              <div className="run-kv" key={k}>
                                <span className="run-kv-key">{k}</span>
                                <span className="run-kv-val">{v}</span>
                              </div>
                            ))}
                            {run.tags?.git_commit && (
                              <p style={{ marginTop: 10, fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--ink-4)" }}>
                                git {run.tags.git_commit.slice(0,7)} · {run.tags?.device ?? "cpu"}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
            {runs.length === 0 && (
              <tr><td colSpan={8} className="tbl-empty">No runs yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Airflow */}
      <div className="sh">
        <h2>Airflow DAG Status</h2>
        <div className="sh-line" />
      </div>
      <ErrorConsole entries={logEntries} />

      {/* External tools */}
      <div className="sh">
        <h2>External Tools</h2>
        <div className="sh-line" />
      </div>
      <div className="ext-links">
        {([
          ["MLflow",     "http://localhost:5000"],
          ["Airflow",    "http://localhost:8080"],
          ["Grafana",    "http://localhost:3001/d/deepfake-combined/deepfake-detection-overview"],
          ["Prometheus", "http://localhost:9090"],
        ] as [string, string][]).map(([label, url]) => (
          <a key={label} href={url} target="_blank" rel="noreferrer" className="ext-link">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
              <polyline points="15 3 21 3 21 9"/>
              <line x1="10" y1="14" x2="21" y2="3"/>
            </svg>
            {label}
          </a>
        ))}
      </div>
    </div>
  );
};
