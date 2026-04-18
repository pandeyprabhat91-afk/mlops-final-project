import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { fetchHistory } from "../api/client";
import type { HistoryRecord } from "../api/client";

function ConfidenceChart({ records }: { records: HistoryRecord[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || records.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth;
    const H = canvas.offsetHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);

    const isDark = document.documentElement.getAttribute("data-theme") !== "light";
    const textColor = isDark ? "rgba(255,255,255,0.35)" : "rgba(0,0,0,0.35)";
    const gridColor = isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)";

    const PAD = { top: 12, right: 12, bottom: 28, left: 36 };
    const cW = W - PAD.left - PAD.right;
    const cH = H - PAD.top - PAD.bottom;

    // Oldest first for left-to-right time flow
    const data = [...records].reverse();
    const n = data.length;

    const xOf = (i: number) => PAD.left + (i / Math.max(n - 1, 1)) * cW;
    const yOf = (v: number) => PAD.top + (1 - v) * cH;

    // Grid lines at 0, 25%, 50%, 75%, 100%
    ctx.font = "10px system-ui, sans-serif";
    ctx.fillStyle = textColor;
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    [0, 0.25, 0.5, 0.75, 1].forEach((v) => {
      const y = yOf(v);
      ctx.beginPath();
      ctx.moveTo(PAD.left, y);
      ctx.lineTo(PAD.left + cW, y);
      ctx.stroke();
      ctx.fillText(`${Math.round(v * 100)}%`, 2, y + 4);
    });

    // Gradient fill under line
    const grad = ctx.createLinearGradient(0, PAD.top, 0, PAD.top + cH);
    grad.addColorStop(0, "rgba(52,168,90,0.18)");
    grad.addColorStop(1, "rgba(52,168,90,0)");
    ctx.beginPath();
    data.forEach((r, i) => {
      const x = xOf(i);
      const y = yOf(r.confidence);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.lineTo(xOf(n - 1), PAD.top + cH);
    ctx.lineTo(xOf(0), PAD.top + cH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.strokeStyle = "rgba(52,168,90,0.7)";
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";
    data.forEach((r, i) => {
      const x = xOf(i);
      const y = yOf(r.confidence);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots colored by prediction
    data.forEach((r, i) => {
      const x = xOf(i);
      const y = yOf(r.confidence);
      ctx.beginPath();
      ctx.arc(x, y, n > 20 ? 2.5 : 4, 0, Math.PI * 2);
      ctx.fillStyle = r.prediction === "fake" ? "#f87171" : "#34a85a";
      ctx.fill();
    });
  }, [records]);

  if (records.length < 2) return null;

  return (
    <div className="sparkline-wrap">
      <p className="sparkline-label">Confidence over time</p>
      <canvas ref={canvasRef} className="sparkline-canvas" aria-label="Confidence trend chart" />
      <div className="sparkline-legend">
        <span className="sparkline-legend-dot" style={{ background: "#f87171" }} aria-hidden="true" />
        <span>Deepfake</span>
        <span className="sparkline-legend-dot" style={{ background: "#34a85a", marginLeft: 12 }} aria-hidden="true" />
        <span>Authentic</span>
      </div>
    </div>
  );
}

type FilterType = "all" | "fake" | "real";

export const History: React.FC = () => {
  const { username } = useAuth();
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");

  useEffect(() => {
    if (!username) return;
    fetchHistory(username)
      .then(setRecords)
      .catch(() => setError("Failed to load history."))
      .finally(() => setLoading(false));
  }, [username]);

  const visible = records.filter((r) => {
    if (filter !== "all" && r.prediction !== filter) return false;
    if (search && !r.filename.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="page-wrap">
      <h1 className="page-title">Prediction History</h1>
      <p className="page-sub">Your last 50 analyses, newest first.</p>

      {loading && <p className="history-loading">Loading…</p>}
      {error && <p className="history-error">{error}</p>}

      {!loading && !error && records.length === 0 && (
        <div className="empty-state">
          <svg className="empty-state-icon" viewBox="0 0 80 80" fill="none" aria-hidden="true">
            <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" strokeDasharray="6 4" opacity="0.3"/>
            <rect x="22" y="28" width="36" height="24" rx="4" stroke="currentColor" strokeWidth="2" opacity="0.5"/>
            <path d="M34 36l4 4 8-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.5"/>
            <circle cx="55" cy="25" r="8" fill="var(--accent)" opacity="0.15"/>
            <path d="M55 22v6M52 25h6" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <h3 className="empty-state-title">No analyses yet</h3>
          <p className="empty-state-body">Upload a video on the Analyze page and your results will appear here.</p>
          <a href="/" className="btn empty-state-cta">Start analyzing</a>
        </div>
      )}

      {records.length > 0 && (
        <>
          <div className="history-controls">
            <div className="history-search-wrap">
              <svg className="history-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
              </svg>
              <input
                type="search"
                className="history-search"
                placeholder="Search filename…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                aria-label="Search by filename"
              />
            </div>
            <div className="history-filter-pills" role="group" aria-label="Filter by verdict">
              {(["all", "fake", "real"] as FilterType[]).map((f) => (
                <button
                  key={f}
                  type="button"
                  className={`history-pill${filter === f ? " active" : ""} ${f}`}
                  onClick={() => setFilter(f)}
                >
                  {f === "all" ? "All" : f === "fake" ? "Deepfake" : "Authentic"}
                </button>
              ))}
            </div>
          </div>

          <ConfidenceChart records={records} />

          {visible.length === 0 ? (
            <p className="history-empty">No results match your search.</p>
          ) : (
            <div className="history-table-wrap">
              <table className="history-table">
                <thead>
                  <tr>
                    <th scope="col">Time</th>
                    <th scope="col">File</th>
                    <th scope="col">Verdict</th>
                    <th scope="col">Confidence</th>
                    <th scope="col">Latency</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((r) => (
                    <tr key={r.id}>
                      <td className="history-ts">
                        {new Date(r.timestamp).toLocaleString()}
                      </td>
                      <td className="history-filename">{r.filename}</td>
                      <td>
                        <span className={`history-badge ${r.prediction}`}>
                          {r.prediction === "fake" ? "DEEPFAKE" : "AUTHENTIC"}
                        </span>
                      </td>
                      <td>{Math.round(r.confidence * 100)}%</td>
                      <td>{r.inference_latency_ms.toFixed(0)} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};
