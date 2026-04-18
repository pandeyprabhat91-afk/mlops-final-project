import type React from "react";
import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

interface ModelInfo {
  model_version: string;
  run_id: string;
  model_loaded: boolean;
}

export const Admin: React.FC = () => {
  const [modelInfo, setModelInfo]           = useState<ModelInfo | null>(null);
  const [rollbackVersion, setRollbackVersion] = useState("");
  const [rollbackStatus, setRollbackStatus]   = useState<string | null>(null);
  const [loading, setLoading]               = useState(false);
  const [reloading, setReloading]           = useState(false);

  const fetchInfo = () => {
    apiClient.get<ModelInfo>("/admin/model-info")
      .then(r => setModelInfo(r.data))
      .catch(() => setModelInfo(null));
  };

  useEffect(() => { fetchInfo(); }, []);

  const handleRollback = async () => {
    if (!rollbackVersion.trim()) return;
    setLoading(true);
    setRollbackStatus(null);
    try {
      const r = await apiClient.post("/admin/rollback", { version: rollbackVersion.trim() });
      setRollbackStatus(`Rolled back to ${r.data.model_version}`);
      fetchInfo();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setRollbackStatus(`Error: ${err?.response?.data?.detail ?? "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReload = async () => {
    setReloading(true);
    try {
      await apiClient.post("/admin/reload-model");
      fetchInfo();
      setRollbackStatus("Model reloaded.");
    } catch {
      setRollbackStatus("Reload failed.");
    } finally {
      setReloading(false);
    }
  };

  return (
    <div className="page">
      <p className="page-eyebrow">System</p>
      <h1 className="page-title">Admin</h1>
      <p className="page-sub">Manage the deployed model and monitor system health.</p>

      {/* Model info */}
      <div className="sh" style={{ marginTop: 0 }}>
        <h2>Current Model</h2>
        <div className="sh-line" />
      </div>

      <div className="card" style={{ marginBottom: 28 }}>
        {modelInfo ? (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <tbody>
              {([
                ["Status",     modelInfo.model_loaded ? "Loaded" : "Not loaded"],
                ["Version",    modelInfo.model_version],
                ["Run ID",     modelInfo.run_id],
              ] as [string, string][]).map(([k, v]) => (
                <tr key={k} style={{ borderBottom: "1px solid var(--border-light)" }}>
                  <td style={{ padding: "12px 20px", color: "var(--ink-3)", width: 140, fontSize: 13.5 }}>{k}</td>
                  <td style={{ padding: "12px 20px", fontFamily: "var(--font-mono)", fontSize: 12.5, color: "var(--ink)" }}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ padding: "20px", color: "var(--ink-3)", fontSize: 13.5 }}>
            Could not fetch model info — is the API running?
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="sh">
        <h2>Model Actions</h2>
        <div className="sh-line" />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 28 }}>
        {/* Reload */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={handleReload}
            disabled={reloading}
          >
            {reloading ? "Reloading…" : "Reload model"}
          </button>
          <span style={{ fontSize: 13, color: "var(--ink-4)" }}>
            Reloads the current checkpoint from disk
          </span>
        </div>

        {/* Rollback */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <input
            type="text"
            className="admin-input"
            value={rollbackVersion}
            onChange={e => setRollbackVersion(e.target.value)}
            placeholder="MLflow version number, e.g. 2"
          />
          <button
            type="button"
            className="btn btn-ghost"
            onClick={handleRollback}
            disabled={loading || !rollbackVersion.trim()}
          >
            {loading ? "Rolling back…" : "Rollback"}
          </button>
        </div>
      </div>

      {rollbackStatus && (
        <p style={{ fontSize: 13, color: "var(--ink-3)", fontFamily: "var(--font-mono)", marginBottom: 28 }}>
          {rollbackStatus}
        </p>
      )}

      {/* Monitoring links */}
      <div className="sh">
        <h2>Monitoring</h2>
        <div className="sh-line" />
      </div>

      <div className="ext-links">
        {([
          ["MLflow",      "http://localhost:5000"],
          ["Grafana",     "http://localhost:3001"],
          ["Prometheus",  "http://localhost:9090"],
          ["Airflow",     "http://localhost:8080"],
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
