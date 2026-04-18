import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

function fmtBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const VideoUpload: React.FC<Props> = ({ onFile, disabled }) => {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ url: string; name: string; size: string } | null>(null);
  const prevUrlRef = useRef<string | null>(null);

  // Revoke object URL on cleanup or when preview changes
  useEffect(() => {
    return () => {
      if (prevUrlRef.current) URL.revokeObjectURL(prevUrlRef.current);
    };
  }, []);

  const validate = (file: File): string | null => {
    if (!file.name.endsWith(".mp4")) return "Only MP4 files are accepted.";
    if (file.size > 100 * 1024 * 1024) return "File must be under 100 MB.";
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const err = validate(file);
    if (err) { setError(err); setPreview(null); return; }
    setError(null);
    // Revoke previous URL
    if (prevUrlRef.current) URL.revokeObjectURL(prevUrlRef.current);
    const url = URL.createObjectURL(file);
    prevUrlRef.current = url;
    setPreview({ url, name: file.name, size: fmtBytes(file.size) });
    onFile(file);
  }, [onFile]);

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const cls = [
    "upload-zone",
    dragOver   ? "drag-over" : "",
    disabled   ? "scanning"  : "",
  ].filter(Boolean).join(" ");

  return (
    <motion.div
      className={cls}
      animate={{ scale: dragOver ? 1.01 : 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      onDrop={onDrop}
      onDragOver={e => { e.preventDefault(); if (!disabled) setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
    >
      <div className="upload-scan-line" />

      <div className="upload-icon-wrap">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z"/>
        </svg>
      </div>

      <p className="upload-title">
        {dragOver ? "Release to analyze" : "Drop a video to analyze"}
      </p>

      {preview ? (
        <div className="upload-preview">
          <video
            className="upload-preview-video"
            src={preview.url}
            muted
            preload="metadata"
            aria-label={`Preview of ${preview.name}`}
          />
          <div className="upload-preview-meta">
            <span className="upload-preview-name">{preview.name}</span>
            <span className="upload-preview-size">{preview.size}</span>
          </div>
          <label className="upload-link upload-preview-change">
            Change file
            <input
              type="file"
              accept=".mp4"
              hidden
              disabled={disabled}
              onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
            />
          </label>
        </div>
      ) : (
        <>
          <p className="upload-hint">
            Drag & drop an MP4, or{" "}
            <label className="upload-link">
              select a file
              <input
                type="file"
                accept=".mp4"
                hidden
                disabled={disabled}
                onChange={e => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </label>
          </p>
          <p className="upload-spec">MP4 · max 100 MB · CNN+LSTM analysis</p>
        </>
      )}

      {error && (
        <div className="upload-err">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {error}
        </div>
      )}
    </motion.div>
  );
};
