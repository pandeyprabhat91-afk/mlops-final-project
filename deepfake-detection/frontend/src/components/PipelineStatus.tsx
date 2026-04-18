import type { FC } from "react";

interface AirflowRun {
  dag_id: string;
  state: string;
  start_date: string;
  end_date: string | null;
}

interface Props {
  runs: AirflowRun[];
  loading?: boolean;
}

const STATE_COLOR: Record<string, string> = {
  success: "#16a34a",
  failed: "#dc2626",
  running: "#2563eb",
  queued: "#d97706",
};

export const PipelineStatus: FC<Props> = ({ runs, loading }) => {
  if (loading) {
    return <p style={{ color: "#6b7280" }}>Loading pipeline status...</p>;
  }

  if (runs.length === 0) {
    return (
      <p style={{ color: "#9ca3af" }}>
        No recent DAG runs. Trigger a run from the{" "}
        <a href="http://localhost:8080" target="_blank" rel="noreferrer">
          Airflow UI
        </a>
        .
      </p>
    );
  }

  return (
    <div>
      {runs.map((run) => (
        <div
          key={run.dag_id + run.start_date}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            padding: "8px 0",
            borderBottom: "1px solid #f3f4f6",
          }}
        >
          <span
            style={{
              display: "inline-block",
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: STATE_COLOR[run.state] ?? "#9ca3af",
              flexShrink: 0,
            }}
          />
          <span style={{ fontFamily: "monospace", fontSize: 13, flex: 1 }}>
            {run.dag_id}
          </span>
          <span
            style={{
              color: STATE_COLOR[run.state] ?? "#6b7280",
              fontSize: 12,
              fontWeight: 600,
              textTransform: "uppercase",
            }}
          >
            {run.state}
          </span>
          <span style={{ fontSize: 12, color: "#9ca3af" }}>
            {run.start_date ? new Date(run.start_date).toLocaleString() : "—"}
          </span>
        </div>
      ))}
    </div>
  );
};
