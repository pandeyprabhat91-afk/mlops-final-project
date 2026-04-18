import type React from "react";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { predictVideo } from "../api/client";
import type { PredictResponse } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { Features } from "../components/Features";
import { Testimonials } from "../components/Testimonials";
import { ResultCard } from "../components/ResultCard";
import { VideoUpload } from "../components/VideoUpload";
import { PipelineStatusBar } from "../components/PipelineStatusBar";
import { ProgressBar } from "../components/ProgressBar";
import { OnboardingTour } from "../components/OnboardingTour";

const stagger = {
  container: {
    animate: { transition: { staggerChildren: 0.08 } },
  },
  item: {
    initial: { opacity: 0, y: 24 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.16,1,0.3,1] } },
  },
};

export const Home: React.FC = () => {
  const { username } = useAuth();
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<PredictResponse | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const [requestId, setRequestId] = useState("");
  const uploadRef = useRef<HTMLDivElement>(null);

  // Restore permalink result from URL hash on mount
  useEffect(() => {
    const hash = window.location.hash;
    const match = hash.match(/[#&]result=([^&]+)/);
    if (!match) return;
    try {
      const decoded = JSON.parse(decodeURIComponent(escape(atob(match[1]))));
      setResult({ gradcam_image: "", ...decoded });
      setRequestId(crypto.randomUUID());
      window.history.replaceState(null, "", window.location.pathname);
    } catch {
      // malformed hash — ignore
    }
  }, []);

  const handleFile = async (file: File) => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await predictVideo(file, username || "anonymous");
      setResult(data);
      setRequestId(crypto.randomUUID());
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { detail?: string } } };
      setError(ax?.response?.data?.detail ?? "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const scroll = () =>
    uploadRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });

  const handleReset = () => {
    setResult(null);
    setError(null);
    setRequestId("");
    scroll();
  };

  return (
    <>
      <PipelineStatusBar />
      {/* ── Hero ── */}
      <div className="hero-wrap">
        {/* Video background */}
        <div className="hero-video-wrap">
          <video
            className="hero-video"
            src="/hero.mp4"
            autoPlay
            muted
            loop
            playsInline
          />
          <div className="hero-video-mask" />
        </div>

        {/* Subtle grid overlay on top of video */}
        <div className="hero-bg">
          <div className="hero-bg-grid" />
        </div>

        <div className="hero">
          {/* Left: text stagger */}
          <motion.div
            className="hero-left"
            variants={stagger.container}
            initial="initial"
            animate="animate"
          >
            <motion.div variants={stagger.item} className="hero-eyebrow">
              <span className="hero-eyebrow-dot" />
              Model active · CNN+LSTM
            </motion.div>

            <motion.h1 variants={stagger.item} className="hero-title">
              Detect <em className="hero-title-gradient">deepfakes.</em>
              <br />
              instantly.
            </motion.h1>

            <motion.p variants={stagger.item} className="hero-body">
              Upload any MP4 and our CNN&nbsp;+&nbsp;LSTM neural network — trained on the SDFVD dataset — classifies it as authentic or AI-generated.
            </motion.p>

            <motion.div variants={stagger.item} className="hero-cta">
              <button
                type="button"
                className="hero-cta-btn"
                onClick={scroll}
              >
                <span>Analyze a video</span>
                <span className="hero-cta-arrow">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </span>
              </button>
            </motion.div>
          </motion.div>

        </div>
      </div>

      {/* ── Analyze ── */}
      <div className="analyze-section" id="upload-area" ref={uploadRef}>
        <p className="section-label">Upload &amp; Analyze</p>

        <VideoUpload onFile={handleFile} disabled={loading} />

        <ProgressBar loading={loading} error={error} />

        {error && (
          <div className="error-card">
            <svg className="error-card-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            <div>
              <p className="error-card-title">Prediction failed</p>
              <p className="error-card-msg">{error}</p>
            </div>
          </div>
        )}

        {result && <ResultCard key={requestId} result={result} requestId={requestId} onReset={handleReset} />}
        <div id="result-card-anchor" />
        <div id="gradcam-anchor" />
      </div>

      {/* ── Features ── */}
      <Features />

      {/* ── Testimonials ── */}
      <Testimonials />

      {/* ── Footer ── */}
      <footer className="site-footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <span className="footer-logo">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
              </svg>
              DeepScan
            </span>
            <span className="footer-copy">&copy; 2026 DeepScan. Built with MLOps best practices.</span>
          </div>
          <div className="footer-links">
            <a href="https://github.com" className="footer-link" target="_blank" rel="noopener noreferrer">GitHub</a>
            <a href="#" className="footer-link">Docs</a>
            <a href="#" className="footer-link">API</a>
          </div>
        </div>
      </footer>

      <OnboardingTour />
    </>
  );
};
