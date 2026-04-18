import { motion } from "framer-motion";

const features = [
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
        <path d="M9 12l2 2 4-4" />
      </svg>
    ),
    title: "CNN + LSTM Detection",
    description:
      "Dual-stage neural network combining spatial feature extraction with temporal sequence analysis for frame-level deepfake detection.",
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="2" y="3" width="20" height="14" rx="2" />
        <path d="M8 21h8M12 17v4" />
        <path d="M7 8l3 3-3 3M12 14h4" />
      </svg>
    ),
    title: "MLOps Pipeline",
    description:
      "End-to-end automated pipeline with Airflow orchestration, DVC versioning, and MLflow experiment tracking.",
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <circle cx="12" cy="10" r="3" />
      </svg>
    ),
    title: "Biometric Analysis",
    description:
      "36-point facial landmark mesh with real-time scan visualization and Grad-CAM explainability overlays.",
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
      </svg>
    ),
    title: "Real-time Monitoring",
    description:
      "Grafana dashboards and Prometheus metrics for inference latency, model drift, and system health.",
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" />
        <path d="M3.27 6.96L12 12.01l8.73-5.05M12 22.08V12" />
      </svg>
    ),
    title: "Containerized Deploy",
    description:
      "Docker Compose orchestration with Nginx reverse proxy, isolated services, and one-command deployment.",
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z" />
      </svg>
    ),
    title: "SDFVD Dataset",
    description:
      "Trained on the curated Synthetic Deepfake Face Video Dataset with balanced real and AI-generated samples.",
  },
];

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1], delay: i * 0.08 },
  }),
};

export const Features: React.FC = () => (
  <section className="features-section">
    <div className="features-inner">

      {/* Header — left-aligned, asymmetric */}
      <motion.div
        className="features-header"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      >
        <span className="features-eyebrow">Capabilities</span>
        <h2 className="features-title">
          Built for <em className="features-title-gradient">production</em>
        </h2>
        <p className="features-subtitle">
          A complete MLOps stack — from data ingestion to model serving —<br className="features-br" /> engineered for reliability and scale.
        </p>
      </motion.div>

      {/* Asymmetric bento grid */}
      <div className="features-bento">
        {/* Hero card — spans 2 cols */}
        <motion.div
          className="feature-card feature-card-hero"
          custom={0} variants={cardVariants} initial="hidden"
          whileInView="visible" viewport={{ once: true, margin: "-60px" }}
        >
          <div className="feature-card-hero-accent" />
          <div className="feature-icon feature-icon-lg">{features[0].icon}</div>
          <h3 className="feature-card-title feature-card-title-lg">{features[0].title}</h3>
          <p className="feature-card-desc">{features[0].description}</p>
          <div className="feature-card-tag">Core Model</div>
        </motion.div>

        {/* Remaining 5 cards in 2-col sub-grid */}
        {features.slice(1).map((f, i) => (
          <motion.div
            key={f.title}
            className="feature-card"
            custom={i + 1} variants={cardVariants} initial="hidden"
            whileInView="visible" viewport={{ once: true, margin: "-60px" }}
          >
            <div className="feature-icon">{f.icon}</div>
            <h3 className="feature-card-title">{f.title}</h3>
            <p className="feature-card-desc">{f.description}</p>
          </motion.div>
        ))}
      </div>

    </div>
  </section>
);
