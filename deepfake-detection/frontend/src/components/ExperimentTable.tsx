import type { FC } from "react";

interface MLflowRun {
  run_id: string;
  status: string;
  metrics: Record<string, number>;
  tags: Record<string, string>;
}

interface Props {
  runs: MLflowRun[];
  loading?: boolean;
}

export const ExperimentTable: FC<Props> = ({ runs, loading }) => {
  if (loading) {
    return <p style={{ color: "#6b7280" }}>Loading experiments...</p>;
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr style={{ background: "#f3f4f6" }}>
          {["Run ID", "Status", "Val F1", "Val Accuracy", "Git Commit"].map((h) => (
            <th
              key={h}
              style={{
                padding: "8px 12px",
                textAlign: "left",
                fontSize: 13,
                fontWeight: 600,
                color: "#374151",
              }}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {runs.map((run) => (
          <tr
            key={run.run_id}
            style={{ borderBottom: "1px solid #e5e7eb" }}
          >
            <td
              style={{
                padding: "8px 12px",
                fontFamily: "monospace",
                fontSize: 12,
                color: "#4f46e5",
              }}
            >
              {run.run_id.slice(0, 8)}...
            </td>
            <td style={{ padding: "8px 12px", fontSize: 13 }}>{run.status}</td>
            <td style={{ padding: "8px 12px", fontSize: 13 }}>
              {run.metrics?.val_f1 != null
                ? run.metrics.val_f1.toFixed(4)
                : "—"}
            </td>
            <td style={{ padding: "8px 12px", fontSize: 13 }}>
              {run.metrics?.val_accuracy != null
                ? run.metrics.val_accuracy.toFixed(4)
                : "—"}
            </td>
            <td
              style={{
                padding: "8px 12px",
                fontFamily: "monospace",
                fontSize: 12,
                color: "#6b7280",
              }}
            >
              {run.tags?.git_commit?.slice(0, 7) ?? "—"}
            </td>
          </tr>
        ))}
        {runs.length === 0 && (
          <tr>
            <td
              colSpan={5}
              style={{ padding: 16, color: "#9ca3af", textAlign: "center" }}
            >
              No experiments yet. Run training to see results here.
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
};
