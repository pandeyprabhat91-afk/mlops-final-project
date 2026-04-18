import type React from "react";
import { useEffect, useState } from "react";
import { apiClient } from "../api/client";

interface StatusPill {
  label: string;
  value: string;
  ok: boolean;
}

function timeAgo(isoString: string): string {
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 2) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export const PipelineStatusBar: React.FC = () => {
  const [pills, setPills] = useState<StatusPill[] | null>(null);

  const load = () => {
    Promise.all([
      apiClient.get("/pipeline/airflow-runs").catch(() => null),
      apiClient.get("/pipeline/mlflow-runs").catch(() => null),
    ]).then(([airflowRes, mlflowRes]) => {
      if (!airflowRes && !mlflowRes) {
        setPills(null); // hide bar silently
        return;
      }

      const newPills: StatusPill[] = [];

      if (airflowRes?.data) {
        const runs: Array<{ state: string; execution_date: string }> = airflowRes.data.dag_runs ?? [];
        const latest = runs[0];
        newPills.push({
          label: "Pipeline",
          value: latest ? `${latest.state} · ${timeAgo(latest.execution_date)}` : "no runs",
          ok: latest?.state === "success",
        });
      }

      if (mlflowRes?.data) {
        const runs: Array<{ run_id: string; metrics?: { val_f1?: number } }> = mlflowRes.data.runs ?? [];
        const latest = runs[0];
        const f1 = latest?.metrics?.val_f1;
        newPills.push({
          label: "Model",
          value: latest ? `run ${latest.run_id.slice(0, 6)} · F1 ${f1 !== undefined ? f1.toFixed(2) : "n/a"}` : "no runs",
          ok: true,
        });
      }

      newPills.push({ label: "System", value: "Online", ok: true });
      setPills(newPills);
    });
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 60_000);
    return () => clearInterval(interval);
  }, []);

  if (!pills) return null;

  return (
    <div className="pipeline-status-bar">
      {pills.map((pill) => (
        <div key={pill.label} className={`psb-pill ${pill.ok ? "ok" : "warn"}`}>
          <span className="psb-dot" />
          <span className="psb-label">{pill.label}</span>
          <span className="psb-value">{pill.value}</span>
        </div>
      ))}
    </div>
  );
};
