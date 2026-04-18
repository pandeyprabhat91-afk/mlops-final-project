import type React from "react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { PredictResponse } from "../api/client";
import { submitFeedback } from "../api/client";
import { useToast } from "./Toast";

function encodeResult(result: PredictResponse): string {
  // Exclude gradcam_image (too large for URL)
  const { gradcam_image: _, ...slim } = result;
  return btoa(unescape(encodeURIComponent(JSON.stringify(slim))));
}

interface Props {
  result: PredictResponse;
  requestId: string;
  onReset?: () => void;
}

export const ResultCard: React.FC<Props> = ({ result, requestId, onReset }) => {
  const pct = Math.round(result.confidence * 100);

  const { toast } = useToast();
  const [threshold, setThreshold] = useState(50);
  const [feedbackSent, setFeedbackSent] = useState(false);

  const copyLink = () => {
    const encoded = encodeResult(result);
    const url = `${window.location.origin}/#result=${encoded}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(() => {
        toast("Link copied to clipboard!", "success");
      }).catch(() => {
        toast("Could not copy link", "error");
      });
    } else {
      // Fallback for non-secure contexts
      try {
        const ta = document.createElement("textarea");
        ta.value = url;
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        toast("Link copied to clipboard!", "success");
      } catch {
        toast("Could not copy link", "error");
      }
    }
  };

  // Re-evaluate verdict client-side based on threshold
  const effectivePrediction: "real" | "fake" = pct >= threshold ? "fake" : "real";
  const isFake  = effectivePrediction === "fake";
  const cls     = isFake ? "fake" : "real";
  const verdict = isFake ? "DEEPFAKE" : "AUTHENTIC";
  const desc    = isFake
    ? "AI-generated or manipulated content detected in this video."
    : "No manipulation artifacts detected. This video appears authentic.";

  const sendFeedback = async (correct: boolean) => {
    const ground_truth: "real" | "fake" = correct
      ? result.prediction
      : result.prediction === "fake" ? "real" : "fake";
    try {
      await submitFeedback({ request_id: requestId, predicted: result.prediction, ground_truth });
      setFeedbackSent(true);
    } catch { /* silent */ }
  };

  const downloadReport = () => {
    const report = {
      generated_at: new Date().toISOString(),
      filename: "uploaded_video.mp4",
      prediction: effectivePrediction,
      confidence: result.confidence,
      threshold_used: threshold,
      inference_latency_ms: result.inference_latency_ms,
      mlflow_run_id: result.mlflow_run_id,
      frames_analyzed: result.frames_analyzed,
      gradcam_base64: result.gradcam_image,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `deepscan-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const printReport = () => {
    const gradcamSrc = result.gradcam_image
      ? `data:image/png;base64,${result.gradcam_image}`
      : null;
    const win = window.open("", "_blank", "width=800,height=900");
    if (!win) return;
    win.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>DeepScan Report — ${new Date().toLocaleDateString()}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; color: #111; padding: 2.5rem; max-width: 720px; margin: auto; }
    .logo { display: flex; align-items: center; gap: 0.5rem; font-size: 1.1rem; font-weight: 700; color: #111; margin-bottom: 0.25rem; }
    .logo svg { opacity: 0.8; }
    .subtitle { font-size: 0.8rem; color: #666; margin-bottom: 2rem; }
    h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem; }
    .verdict-fake { color: #dc2626; }
    .verdict-real { color: #16a34a; }
    .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 1.5rem; }
    .badge-fake { background: #fee2e2; color: #dc2626; }
    .badge-real { background: #dcfce7; color: #16a34a; }
    .section { margin-bottom: 1.5rem; }
    .section-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: #888; margin-bottom: 0.5rem; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    td { padding: 0.45rem 0.6rem; border-bottom: 1px solid #f0f0f0; }
    td:first-child { color: #666; width: 45%; }
    td:last-child { font-weight: 500; }
    .conf-track { height: 8px; background: #f0f0f0; border-radius: 4px; margin: 0.5rem 0; overflow: hidden; }
    .conf-fill { height: 100%; border-radius: 4px; background: ${isFake ? "#dc2626" : "#16a34a"}; width: ${pct}%; }
    .gradcam { width: 100%; max-width: 400px; border-radius: 8px; border: 1px solid #e5e7eb; display: block; margin: 0.5rem 0; }
    .explainer { background: #f9fafb; border-radius: 8px; padding: 1rem; font-size: 0.82rem; line-height: 1.6; color: #555; border: 1px solid #e5e7eb; }
    .explainer strong { color: #111; }
    .footer { margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; font-size: 0.75rem; color: #aaa; display: flex; justify-content: space-between; }
    @media print { body { padding: 1.5rem; } button { display: none; } }
  </style>
</head>
<body>
  <div class="logo">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z"/>
    </svg>
    DeepScan
  </div>
  <div class="subtitle">Deepfake Detection Report · Generated ${new Date().toLocaleString()}</div>

  <h1 class="verdict-${effectivePrediction}">${verdict}</h1>
  <div class="badge badge-${effectivePrediction}">${isFake ? "AI manipulation detected" : "No manipulation detected"}</div>

  <div class="section">
    <div class="section-title">Confidence Score</div>
    <div style="font-size:1.6rem;font-weight:700;color:${isFake ? "#dc2626" : "#16a34a"}">${pct}%</div>
    <div class="conf-track"><div class="conf-fill"></div></div>
    <div style="font-size:0.78rem;color:#888">Threshold used: ${threshold}% · ${pct >= threshold ? "Exceeds" : "Below"} threshold → classified as ${effectivePrediction.toUpperCase()}</div>
  </div>

  <div class="section">
    <div class="section-title">Analysis Details</div>
    <table>
      <tr><td>MLflow Run ID</td><td>${result.mlflow_run_id}</td></tr>
      <tr><td>Frames analyzed</td><td>${result.frames_analyzed}</td></tr>
      <tr><td>Inference latency</td><td>${result.inference_latency_ms.toFixed(0)} ms</td></tr>
      <tr><td>Threshold</td><td>${threshold}%</td></tr>
      <tr><td>Effective verdict</td><td>${verdict}</td></tr>
    </table>
  </div>

  ${gradcamSrc ? `
  <div class="section">
    <div class="section-title">Grad-CAM Saliency Map</div>
    <img class="gradcam" src="${gradcamSrc}" alt="Grad-CAM heatmap"/>
    <div class="explainer" style="margin-top:0.75rem">
      <strong>How to read this heatmap:</strong> Warmer colors (red/yellow) indicate regions the model weighted most heavily.
      Key signals include <strong>face boundary artifacts</strong>, <strong>unnatural eye/lip blending</strong>,
      <strong>lighting inconsistencies</strong>, and <strong>compression noise patterns</strong> introduced by generative models.
    </div>
  </div>` : ""}

  <div class="footer">
    <span>DeepScan · CNN+LSTM deepfake classifier</span>
    <span>Report ID: ${requestId.slice(0, 8).toUpperCase()}</span>
  </div>
  <script>window.onload = () => window.print();<\/script>
</body>
</html>`);
    win.document.close();
  };

  return (
    <AnimatePresence>
      <motion.div
        className="result"
        key={requestId}
        initial={{ scale: 0.92, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.96, opacity: 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
      >
        {/* Verdict hero */}
        <div className={`result-hero ${cls}`}>
          <p className="result-eyebrow">Analysis Result</p>
          <motion.h2
            className="result-verdict"
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.1 }}
          >
            {verdict}
          </motion.h2>
          <p className="result-desc">{desc}</p>
        </div>

        {/* Details */}
        <div className={`result-body ${cls}`}>
          {/* Confidence */}
          <div className="conf-row">
            <span className="conf-label">Confidence</span>
            <span className="conf-pct">{pct}%</span>
          </div>
          <div className="conf-track">
            <motion.div
              className="conf-fill"
              initial={{ width: "0%" }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 1.1, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
            />
          </div>

          {/* Threshold slider */}
          <div className="threshold-wrap">
            <label className="threshold-label" htmlFor="threshold-slider">
              Threshold: {threshold}%
            </label>
            <input
              id="threshold-slider"
              type="range"
              min={0}
              max={100}
              step={1}
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="threshold-slider"
            />
            <div className="threshold-verdict-row">
              <span className={`threshold-verdict-badge ${effectivePrediction}`}>
                {pct >= threshold ? "Exceeds" : "Below"} threshold
                {" — "}classified as <strong>{verdict}</strong>
              </span>
            </div>
            <p className="threshold-hint">
              Drag to re-evaluate verdict client-side. Default: 50%.
            </p>
          </div>

          {/* Meta */}
          <div className="meta-grid">
            <div className="meta-cell">
              <span className="meta-cell-label">Frames analyzed</span>
              <span className="meta-cell-value">{result.frames_analyzed}</span>
            </div>
            <div className="meta-cell">
              <span className="meta-cell-label">Inference time</span>
              <span className="meta-cell-value">
                {result.inference_latency_ms.toFixed(0)}
                <span className="meta-cell-unit">ms</span>
              </span>
            </div>
          </div>

          {/* Grad-CAM */}
          {result.gradcam_image && (
            <div className="gradcam-wrap">
              <p className="gradcam-label">Grad-CAM Saliency Map</p>
              <img
                src={`data:image/png;base64,${result.gradcam_image}`}
                alt="Grad-CAM heatmap highlighting manipulated regions"
              />
              <div className="gradcam-explainer">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true" style={{ flexShrink: 0, marginTop: "1px" }}>
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <span>
                  Warmer regions (red/yellow) show where the model detected anomalies —
                  typically <strong>face boundary blending</strong>, <strong>unnatural eye &amp; lip movement</strong>,
                  and <strong>lighting inconsistencies</strong> introduced by generative models.
                </span>
              </div>
            </div>
          )}

          {/* Export actions */}
          <div className="report-actions">
            <button type="button" className="btn btn-ghost report-btn" onClick={downloadReport}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              JSON Report
            </button>
            <button type="button" className="btn btn-ghost report-btn" onClick={printReport}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <polyline points="6 9 6 2 18 2 18 9"/>
                <path d="M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2"/>
                <rect x="6" y="14" width="12" height="8"/>
              </svg>
              PDF Report
            </button>
            <button type="button" className="btn btn-ghost report-btn" onClick={copyLink}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>
              </svg>
              Copy Link
            </button>
          </div>

          {/* Feedback */}
          <div className="feedback-wrap">
            {feedbackSent ? (
              <span className="feedback-ok">✓ Feedback recorded — thank you</span>
            ) : (
              <>
                <span className="feedback-q">Was this prediction correct?</span>
                <button type="button" className="btn btn-ghost" onClick={() => sendFeedback(true)}>Yes</button>
                <button type="button" className="btn btn-ghost" onClick={() => sendFeedback(false)}>No</button>
              </>
            )}
          </div>

          {/* Analyze another */}
          {onReset && (
            <div className="analyze-another-wrap">
              <button type="button" className="btn analyze-another-btn" onClick={onReset}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                  <polyline points="1 4 1 10 7 10"/>
                  <path d="M3.51 15a9 9 0 102.13-9.36L1 10"/>
                </svg>
                Analyze another video
              </button>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
