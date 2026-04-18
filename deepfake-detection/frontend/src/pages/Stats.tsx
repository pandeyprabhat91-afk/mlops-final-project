import type React from "react";
import { useEffect, useState } from "react";
import { fetchHistory } from "../api/client";
import type { HistoryRecord } from "../api/client";
import { useAuth } from "../auth/AuthContext";

function msAgo(ms: number) {
  if (ms < 60_000) return `${Math.round(ms / 1000)}s ago`;
  if (ms < 3_600_000) return `${Math.round(ms / 60_000)}m ago`;
  if (ms < 86_400_000) return `${Math.round(ms / 3_600_000)}h ago`;
  return `${Math.round(ms / 86_400_000)}d ago`;
}

export const Stats: React.FC = () => {
  const { username } = useAuth();
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!username) return;
    fetchHistory(username)
      .then(setRecords)
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) return <div className="page-wrap"><p className="history-loading">Loading stats…</p></div>;

  const total = records.length;
  const fakeCount = records.filter((r) => r.prediction === "fake").length;
  const realCount = total - fakeCount;
  const avgConf = total === 0 ? 0 : Math.round(records.reduce((s, r) => s + r.confidence, 0) / total * 100);
  const avgLatency = total === 0 ? 0 : Math.round(records.reduce((s, r) => s + r.inference_latency_ms, 0) / total);
  const now = Date.now();
  const thisWeek = records.filter((r) => now - new Date(r.timestamp).getTime() < 7 * 86_400_000).length;
  const lastAnalysis = records[0] ? msAgo(now - new Date(records[0].timestamp).getTime()) : "—";

  const fakeRatio = total === 0 ? 0 : fakeCount / total;
  const CIRC = 2 * Math.PI * 36;
  const fakeDash = fakeRatio * CIRC;
  const realDash = CIRC - fakeDash;

  return (
    <div className="page-wrap">
      <h1 className="page-title">Your Stats</h1>
      <p className="page-sub">Personal usage summary based on your last 50 analyses.</p>

      {total === 0 ? (
        <div className="empty-state">
          <svg className="empty-state-icon" viewBox="0 0 80 80" fill="none" aria-hidden="true">
            <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" strokeDasharray="6 4" opacity="0.3"/>
            <path d="M25 58V42M35 58V30M45 58V46M55 58V34" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity="0.5"/>
            <circle cx="55" cy="25" r="8" fill="var(--accent)" opacity="0.15"/>
            <path d="M55 22v6M52 25h6" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <h3 className="empty-state-title">No data yet</h3>
          <p className="empty-state-body">Run your first analysis and your personal stats will appear here.</p>
          <a href="/" className="btn empty-state-cta">Analyze a video</a>
        </div>
      ) : (
        <>
          <div className="stats-kpi-row">
            <div className="stats-kpi">
              <span className="stats-kpi-value">{total}</span>
              <span className="stats-kpi-label">Total analyses</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{thisWeek}</span>
              <span className="stats-kpi-label">This week</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{avgConf}%</span>
              <span className="stats-kpi-label">Avg confidence</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{avgLatency}ms</span>
              <span className="stats-kpi-label">Avg latency</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{lastAnalysis}</span>
              <span className="stats-kpi-label">Last analysis</span>
            </div>
          </div>

          <div className="stats-donut-wrap">
            <svg className="stats-donut" viewBox="0 0 88 88" width="120" height="120" aria-label={`${fakeCount} deepfakes, ${realCount} authentic`}>
              <circle cx="44" cy="44" r="36" fill="none" stroke="var(--bg-elevated)" strokeWidth="10"/>
              <circle
                cx="44" cy="44" r="36" fill="none"
                stroke="var(--real-color)" strokeWidth="10"
                strokeDasharray={`${realDash} ${fakeDash}`}
                strokeDashoffset={CIRC * 0.25}
                strokeLinecap="round"
              />
              <circle
                cx="44" cy="44" r="36" fill="none"
                stroke="var(--fake-color)" strokeWidth="10"
                strokeDasharray={`${fakeDash} ${realDash}`}
                strokeDashoffset={CIRC * 0.25 - realDash}
                strokeLinecap="round"
              />
              <text x="44" y="48" textAnchor="middle" fontSize="12" fill="var(--text-primary)" fontWeight="600">{total}</text>
              <text x="44" y="58" textAnchor="middle" fontSize="7" fill="var(--text-muted)">total</text>
            </svg>
            <div className="stats-legend">
              <div className="stats-legend-item">
                <span className="stats-legend-dot" style={{ background: "var(--fake-color)" }} />
                <span>{fakeCount} deepfake{fakeCount !== 1 ? "s" : ""} ({Math.round(fakeRatio * 100)}%)</span>
              </div>
              <div className="stats-legend-item">
                <span className="stats-legend-dot" style={{ background: "var(--real-color)" }} />
                <span>{realCount} authentic ({Math.round((1 - fakeRatio) * 100)}%)</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
