import type React from "react";
import { useRef, useState } from "react";
import { batchPredict } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface BatchResult {
  filename: string;
  prediction: "real" | "fake";
  confidence: number;
  inference_latency_ms: number;
  error: string;
}

export const Batch: React.FC = () => {
  const { username } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [results, setResults] = useState<BatchResult[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<{ total: number; succeeded: number } | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const handleFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(Array.from(e.target.files ?? []));
    setResults(null);
    setSummary(null);
    setFetchError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) return;
    setLoading(true);
    setFetchError(null);
    try {
      const resp = await batchPredict(files, username || "anonymous");
      setResults(resp.results);
      setSummary({ total: resp.total, succeeded: resp.succeeded });
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setFetchError(ax?.response?.data?.detail ?? "Batch request failed. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-wrap">
      <h1 className="page-title">Batch Upload</h1>
      <p className="page-sub">Upload up to 10 MP4 files at once. Each is analyzed independently.</p>

      <form onSubmit={handleSubmit} className="batch-form">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".mp4"
          onChange={handleFiles}
          className="batch-file-input"
          id="batch-file"
        />
        <label htmlFor="batch-file" className="batch-file-label">
          {files.length > 0
            ? `${files.length} file${files.length > 1 ? "s" : ""} selected`
            : "Choose MP4 files…"}
        </label>
        <button
          type="submit"
          className="btn batch-submit-btn"
          disabled={files.length === 0 || loading}
        >
          {loading ? "Analyzing…" : "Analyze All"}
        </button>
      </form>

      {fetchError && (
        <div style={{ color: "#f87171", fontSize: "0.875rem", marginBottom: "1rem" }}>
          {fetchError}
        </div>
      )}

      {summary && (
        <div className="batch-summary">
          {summary.succeeded} of {summary.total} succeeded
        </div>
      )}

      {results !== null && results.length === 0 && (
        <div className="empty-state" style={{ marginTop: "2rem" }}>
          <svg className="empty-state-icon" viewBox="0 0 80 80" fill="none" aria-hidden="true">
            <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" strokeDasharray="6 4" opacity="0.3"/>
            <path d="M28 44l8-8 8 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" opacity="0.5"/>
            <path d="M40 36v16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5"/>
            <rect x="26" y="26" width="28" height="4" rx="2" fill="currentColor" opacity="0.15"/>
          </svg>
          <h3 className="empty-state-title">No results returned</h3>
          <p className="empty-state-body">All files may have errored or the batch was empty. Try uploading again.</p>
        </div>
      )}

      {results && results.length > 0 && (
        <div className="history-table-wrap" style={{ marginTop: "1.5rem" }}>
          <table className="history-table">
            <thead>
              <tr>
                <th scope="col">File</th>
                <th scope="col">Verdict</th>
                <th scope="col">Confidence</th>
                <th scope="col">Latency</th>
                <th scope="col">Error</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td className="history-filename">{r.filename}</td>
                  <td>
                    {r.error ? (
                      <span style={{ color: "var(--text-muted)" }}>—</span>
                    ) : (
                      <span className={`history-badge ${r.prediction}`}>
                        {r.prediction === "fake" ? "DEEPFAKE" : "AUTHENTIC"}
                      </span>
                    )}
                  </td>
                  <td>{r.error ? "—" : `${Math.round(r.confidence * 100)}%`}</td>
                  <td>{r.error ? "—" : `${r.inference_latency_ms.toFixed(0)} ms`}</td>
                  <td style={{ color: "#f87171", fontSize: "0.78rem" }}>{r.error || ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
