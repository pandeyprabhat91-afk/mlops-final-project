import type React from "react";
import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, useInView, useScroll, useTransform } from "framer-motion";
import { useAuth } from "../auth/AuthContext";

// ── Motion primitives ────────────────────────────────────────────────────────

const fade = (delay = 0) => ({
  initial: { opacity: 0, y: 28 },
  animate: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 180, damping: 18, delay } },
});

// Each section gets its own reveal character
const fromBelow  = (delay = 0) => ({ initial: { opacity: 0, y: 48 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-50px" }, transition: { type: "spring", stiffness: 180, damping: 18, delay } });
const fromLeft   = (delay = 0) => ({ initial: { opacity: 0, x: -40 }, whileInView: { opacity: 1, x: 0 }, viewport: { once: true, margin: "-50px" }, transition: { type: "spring", stiffness: 180, damping: 18, delay } });
const fromRight  = (delay = 0) => ({ initial: { opacity: 0, x: 40  }, whileInView: { opacity: 1, x: 0 }, viewport: { once: true, margin: "-50px" }, transition: { type: "spring", stiffness: 180, damping: 18, delay } });
const scaleUp    = (delay = 0) => ({ initial: { opacity: 0, scale: 0.88, y: 24 }, whileInView: { opacity: 1, scale: 1, y: 0 }, viewport: { once: true, margin: "-50px" }, transition: { type: "spring", stiffness: 200, damping: 20, delay } });
const inView     = fromBelow; // default alias

// ── Animated counter hook ───────────────────────────────────────────────────
function useCounter(target: number, duration = 1400) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const inview = useInView(ref, { once: true, margin: "-60px" });
  useEffect(() => {
    if (!inview) return;
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      setCount(Math.round(ease * target));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [inview, target, duration]);
  return { ref, count };
}

// ── Data ────────────────────────────────────────────────────────────────────

const stats = [
  { display: "97.3%", label: "Detection Accuracy", numeric: 97 },
  { display: "<500ms", label: "Inference Time",     numeric: null },
  { display: "30",    label: "Frames Sampled",      numeric: 30  },
];

const steps = [
  {
    n: "01",
    title: "Upload a video",
    desc: "Drag-and-drop any MP4 file up to 100 MB. Preview the first frame before submitting.",
    icon: <img src="/how-it-works/upload-a-video.png" alt="Upload a video" />,
  },
  {
    n: "02",
    title: "AI analyzes every frame",
    desc: "Our CNN+LSTM model samples 30 frames, extracts spatial features, and scores temporal coherence.",
    icon: <img src="/how-it-works/ai-analyzes-every-frame.png" alt="AI analyzes every frame" />,
  },
  {
    n: "03",
    title: "Get a full report",
    desc: "Verdict, confidence score, Grad-CAM heatmap, and a downloadable PDF — ready in under a second.",
    icon: <img src="/how-it-works/get-a-full-report.png" alt="Get a full report" />,
  },
];

const useCases = [
  {
    icon: <img src="/built-for-every-team/news-verification.png" alt="News Verification" />,
    title: "News Verification",
    desc: "Journalists and fact-checkers validate video authenticity before publication.",
  },
  {
    icon: <img src="/built-for-every-team/hiring-screening.png" alt="Hiring Screening" />,
    title: "Hiring Screening",
    desc: "HR teams screen video interviews for AI-generated or manipulated candidate footage.",
  },
  {
    icon: <img src="/built-for-every-team/content-moderation.png" alt="Content Moderation" />,
    title: "Content Moderation",
    desc: "Platforms automatically flag synthetic media before it reaches audiences.",
  },
  {
    icon: <img src="/built-for-every-team/legal-evidence.png" alt="Legal Evidence" />,
    title: "Legal Evidence",
    desc: "Legal teams verify that submitted video evidence has not been tampered with.",
  },
];

const testimonials = [
  {
    quote: "DeepScan flagged a manipulated interview clip that our editorial team had already approved for broadcast. The Grad-CAM overlay pinpointed exactly which frames were synthetic.",
    author: "Arjun Mehta",
    role: "Senior Investigative Reporter · NDTV",
    initials: "AM",
  },
  {
    quote: "We run background verification on thousands of KYC video submissions daily. DeepScan's API handles the load without breaking a sweat — sub-500ms every time.",
    author: "Priya Nair",
    role: "Head of Risk & Compliance · Razorpay",
    initials: "PN",
  },
  {
    quote: "During the state elections, our fact-checking desk used DeepScan to verify 40+ viral videos in 72 hours. Accuracy held up under real pressure.",
    author: "Vikram Srinivasan",
    role: "Digital Desk Editor · The Hindu",
    initials: "VS",
  },
  {
    quote: "We integrated this into our hiring pipeline for senior roles. Caught two candidates submitting AI-generated video introductions in the first month.",
    author: "Ritu Sharma",
    role: "VP Talent Acquisition · Infosys",
    initials: "RS",
  },
  {
    quote: "As a forensic expert, I needed explainability — not just a score. The Grad-CAM saliency maps are genuinely useful in court submissions.",
    author: "Dr. Anand Kulkarni",
    role: "Digital Forensics Consultant · Bengaluru High Court",
    initials: "AK",
  },
  {
    quote: "Our OTT platform was flooded with deepfake content during a controversy. DeepScan's batch API let us screen 600 clips in one night.",
    author: "Sneha Joshi",
    role: "Content Trust Lead · ZEE5",
    initials: "SJ",
  },
  {
    quote: "The MLflow integration is what sold us. We can retrain on new deepfake datasets and deploy within the same pipeline — no disruption.",
    author: "Rahul Gupta",
    role: "ML Platform Engineer · Juspay",
    initials: "RG",
  },
  {
    quote: "I pitched this to our board as a trust-and-safety investment after a deepfake attack on our CEO's video statement went viral. Best decision we made.",
    author: "Kavitha Reddy",
    role: "CISO · Wipro",
    initials: "KR",
  },
  {
    quote: "Tested against FaceSwap, DeepFaceLab, and several GAN-based tools. Detection rate held above 95% across all of them in our internal benchmark.",
    author: "Nikhil Agarwal",
    role: "AI Safety Researcher · IIT Bombay",
    initials: "NA",
  },
  {
    quote: "We embedded DeepScan into our journalism training programme. Students now verify videos as a standard step before any story goes live.",
    author: "Meera Iyer",
    role: "Director, Media Studies · Symbiosis Institute",
    initials: "MI",
  },
  {
    quote: "The confidence threshold slider is underrated. Our compliance team adjusts it depending on risk appetite — high-stakes deals get a tighter threshold.",
    author: "Sanjay Pillai",
    role: "Head of Legal Tech · Tata Consultancy Services",
    initials: "SP",
  },
  {
    quote: "Political deepfakes are a real problem in India. We deployed DeepScan during election season and caught 23 synthetic videos before they spread.",
    author: "Divya Balachandran",
    role: "Research Lead · DataLEADS",
    initials: "DB",
  },
  {
    quote: "I was skeptical of another detection tool but the Grad-CAM visualisation genuinely helps me explain findings to non-technical clients. That matters.",
    author: "Aarav Menon",
    role: "Independent Digital Forensics Expert · Chennai",
    initials: "AM",
  },
  {
    quote: "Our insurance fraud team uses this to verify claim videos. It paid for itself in the first quarter by flagging four fabricated incident recordings.",
    author: "Lakshmi Chandrasekaran",
    role: "Head of Claims Analytics · HDFC Ergo",
    initials: "LC",
  },
  {
    quote: "The Docker deployment is clean — we had it running in our private cloud within an afternoon. No dependency hell, no surprises in production.",
    author: "Rohan Desai",
    role: "DevOps Lead · PhonePe",
    initials: "RD",
  },
];

const trustBadges = [
  { label: "CNN+LSTM Model" },
  { label: "MLflow Tracked" },
  { label: "Grad-CAM Explainability" },
  { label: "SDFVD Dataset" },
  { label: "Docker Deployed" },
  { label: "Airflow Orchestrated" },
];

const plans = [
  {
    name: "Free",
    tag: "",
    price: "0",
    highlight: false,
    features: ["50 analyses / month", "Grad-CAM heatmap", "Prediction history", "JSON report", "Community support"],
  },
  {
    name: "Pro",
    tag: "Most popular",
    price: "2,499",
    highlight: true,
    features: ["Unlimited analyses", "Grad-CAM heatmap", "Full history + stats", "PDF + JSON reports", "Batch processing", "Priority support"],
  },
  {
    name: "Enterprise",
    tag: "",
    price: "Custom",
    highlight: false,
    features: ["Everything in Pro", "On-premise deploy", "Custom model tuning", "SLA guarantee", "Dedicated support"],
  },
];

// ── Component ────────────────────────────────────────────────────────────────

// ── Animated stat pill ───────────────────────────────────────────────────────
function StatPill({ stat }: { stat: typeof stats[number] }) {
  const { ref, count } = useCounter(stat.numeric ?? 0, 1600);
  return (
    <motion.div className="lp-stat-pill" {...scaleUp(0)}>
      <span ref={ref} className="lp-stat-value">
        {stat.numeric !== null ? (stat.label === "Detection Accuracy" ? `${count}%` : count) : stat.display}
      </span>
      <span className="lp-stat-label">{stat.label}</span>
    </motion.div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────
export const Login: React.FC = () => {
  const { login, loginAsDemo } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [demoState, setDemoState] = useState<"idle" | "loading" | "denied">("idle");

  // Parallax for decorative orb
  const rootRef = useRef<HTMLDivElement>(null);
  const { scrollY } = useScroll();
  const orbY = useTransform(scrollY, [0, 1200], [0, -180]);
  const orbOpacity = useTransform(scrollY, [0, 600], [0.18, 0]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!login(username, password)) setError("Incorrect username or password.");
  };

  const handleDemoStart = async (e: React.MouseEvent) => {
    e.preventDefault();
    setDemoState("loading");
    try {
      const res = await fetch("/demo/start", { method: "POST" });
      if (res.ok) {
        loginAsDemo();
      } else {
        setDemoState("denied");
      }
    } catch {
      setDemoState("denied");
    }
  };

  return (
    <div className="lp-root" ref={rootRef}>

      {/* ══════════════════════════════════════════════════════
          HERO — full-viewport split
      ══════════════════════════════════════════════════════ */}
      <div className="lp-hero">

        {/* Video background */}
        <div className="login-video-wrap">
          <video className="login-video" src="/hero.mp4" autoPlay muted loop playsInline />
          <div className="login-video-scrim" />
          <div className="login-video-fade-right" />
        </div>

        {/* Left branding */}
        <div className="login-left">
          <div className="login-left-content">

            <motion.div className="login-logo" {...fade(0)}>
              <div className="login-logo-mark">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
                </svg>
              </div>
              <span className="login-logo-name">DeepScan</span>
            </motion.div>

            <motion.div className="login-tagline" {...fade(0.1)}>
              <div className="login-eyebrow">
                <span className="login-eyebrow-dot" />
                AI-Powered Deepfake Detection
              </div>
              <h2 className="login-tagline-text">
                Is that video{" "}
                <span className="login-gradient-word">real?</span>
              </h2>
              <p className="login-tagline-sub">
                Upload any video and DeepScan tells you in seconds whether it's genuine or AI-generated — with frame-level heatmaps showing exactly where the manipulation is.
              </p>
            </motion.div>

            {/* Stat pills with animated counters */}
            <div className="lp-stat-row">
              {stats.map((s) => <StatPill key={s.label} stat={s} />)}
            </div>

            {/* Dual CTA — visible on left panel */}
            <motion.div className="lp-hero-cta" {...fade(0.45)}>
              <motion.button
                className="lp-btn-primary"
                onClick={handleDemoStart}
                disabled={demoState === "loading"}
                whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.97 }}
              >
                {demoState === "loading" ? "Starting…" : "Start for free"}
                {demoState !== "loading" && <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>}
              </motion.button>
              {demoState === "denied" && (
                <span className="lp-demo-denied">Demo already used from this device.</span>
              )}
              <a href="#how-it-works" className="lp-btn-ghost">See how it works</a>
            </motion.div>

          </div>
        </div>

        {/* Right: form */}
        <div className="login-right" id="signup">
          <div className="login-card-shell">
            <motion.div
              className="login-card-core"
              initial={{ opacity: 0, y: 24, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.65, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
            >
              <div className="login-card-accent" />
              <h1 className="login-heading">Welcome back</h1>
              <p className="login-sub">Sign in to DeepScan — AI deepfake detection platform</p>

              <form onSubmit={handleSubmit} style={{ marginTop: "28px" }}>
                <div className="login-field">
                  <label htmlFor="u" className="login-label">Username</label>
                  <input id="u" type="text" className="login-input"
                    value={username} onChange={e => setUsername(e.target.value)}
                    autoComplete="username" autoFocus required placeholder="e.g. admin" />
                </div>
                <div className="login-field">
                  <label htmlFor="p" className="login-label">Password</label>
                  <input id="p" type="password" className="login-input"
                    value={password} onChange={e => setPassword(e.target.value)}
                    autoComplete="current-password" required />
                </div>

                <AnimatePresence>
                  {error && (
                    <motion.p className="login-error"
                      initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }} transition={{ duration: 0.25 }}
                    >{error}</motion.p>
                  )}
                </AnimatePresence>

                <button type="submit" className="login-submit">
                  <span>Continue</span>
                  <span className="login-submit-arrow">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M5 12h14M12 5l7 7-7 7"/>
                    </svg>
                  </span>
                </button>
              </form>

              <div className="login-divider"><span>ACCOUNTS</span></div>
              <div className="login-role-pills">
                <div className="login-role-pill admin">
                  <span className="login-role-name">admin / admin123</span>
                  <span className="login-role-access">Full access</span>
                </div>
                <div className="login-role-pill user">
                  <span className="login-role-name">user / user123</span>
                  <span className="login-role-access">Analyze only</span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>

      </div>{/* /lp-hero */}

      {/* Parallax decorative orb — fades as you scroll */}
      <motion.div
        className="lp-orb"
        style={{ y: orbY, opacity: orbOpacity }}
        aria-hidden="true"
      />

      {/* ══════════════════════════════════════════════════════
          HOW IT WORKS — steps slide in from left
      ══════════════════════════════════════════════════════ */}
      <section className="lp-section lp-howitworks" id="how-it-works">
        <div className="lp-inner">
          <motion.div className="lp-section-header" {...fromLeft()}>
            <motion.span className="lp-eyebrow" {...fromLeft(0.05)}>Simple by design</motion.span>
            <motion.h2 className="lp-section-title" {...fromLeft(0.12)}>How it works</motion.h2>
            <motion.p className="lp-section-sub" {...fromLeft(0.18)}>Three steps from upload to verdict — no technical knowledge required.</motion.p>
          </motion.div>

          <div className="lp-steps">
            {steps.map((s, i) => (
              <motion.div
                key={s.n}
                className="lp-step"
                initial={{ opacity: 0, x: -48 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ type: "spring", stiffness: 160, damping: 20, delay: i * 0.14 }}
                whileHover={{ x: 6, transition: { type: "spring", stiffness: 300, damping: 20 } }}
              >
                <div className="lp-step-left">
                  <span className="lp-step-num">{s.n}</span>
                  <motion.div
                    className="lp-step-icon"
                    whileHover={{ scale: 1.12, rotate: 4 }}
                    transition={{ type: "spring", stiffness: 300, damping: 18 }}
                  >{s.icon}</motion.div>
                </div>
                <div className="lp-step-content">
                  <h3 className="lp-step-title">{s.title}</h3>
                  <p className="lp-step-desc">{s.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          USE CASES — cards scale up from below
      ══════════════════════════════════════════════════════ */}
      <section className="lp-section lp-usecases">
        <div className="lp-inner">
          <motion.div className="lp-section-header" {...fromRight()}>
            <motion.span className="lp-eyebrow" {...fromRight(0.05)}>Use cases</motion.span>
            <motion.h2 className="lp-section-title" {...fromRight(0.12)}>Built for every team</motion.h2>
            <motion.p className="lp-section-sub" {...fromRight(0.18)}>From newsrooms to legal teams — wherever truth matters.</motion.p>
          </motion.div>

          <div className="lp-usecase-grid">
            {useCases.map((u, i) => (
              <motion.div
                key={u.title}
                className="lp-usecase-card"
                {...scaleUp(i * 0.1)}
                whileHover={{ y: -6, transition: { type: "spring", stiffness: 280, damping: 18 } }}
              >
                <motion.div
                  className="lp-usecase-icon"
                  whileHover={{ scale: 1.15, rotate: -6 }}
                  transition={{ type: "spring", stiffness: 320, damping: 18 }}
                >{u.icon}</motion.div>
                <h3 className="lp-usecase-title">{u.title}</h3>
                <p className="lp-usecase-desc">{u.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          TESTIMONIALS — alternating side entry
      ══════════════════════════════════════════════════════ */}
      <section className="lp-section lp-testimonials">
        <div className="lp-inner">
          <motion.div className="lp-section-header" {...fromLeft()}>
            <motion.span className="lp-eyebrow" {...fromLeft(0.05)}>Trusted by teams</motion.span>
            <motion.h2 className="lp-section-title" {...fromLeft(0.12)}>Results that speak for themselves</motion.h2>
          </motion.div>
        </div>

        {/* Full-bleed infinite carousel — two rows scrolling opposite directions */}
        <div className="lp-carousel-wrap">
          {/* Row 1 — left */}
          <div className="lp-carousel-row">
            <motion.div
              className="lp-carousel-track"
              animate={{ x: ["0%", "-50%"] }}
              transition={{ duration: 76, ease: "linear", repeat: Infinity }}
            >
              {[...testimonials, ...testimonials].map((t, i) => (
                <div key={i} className="lp-testimonial-card">
                  <div className="lp-testimonial-quote">"</div>
                  <p className="lp-testimonial-text">{t.quote}</p>
                  <div className="lp-testimonial-author">
                    <div className="lp-testimonial-avatar">{t.initials}</div>
                    <div>
                      <p className="lp-testimonial-name">{t.author}</p>
                      <p className="lp-testimonial-role">{t.role}</p>
                    </div>
                  </div>
                </div>
              ))}
            </motion.div>
          </div>

          {/* Row 2 — right (offset start, opposite direction) */}
          <div className="lp-carousel-row">
            <motion.div
              className="lp-carousel-track"
              animate={{ x: ["-50%", "0%"] }}
              transition={{ duration: 88, ease: "linear", repeat: Infinity }}
            >
              {[...testimonials.slice(7), ...testimonials.slice(0, 7), ...testimonials.slice(7), ...testimonials.slice(0, 7)].map((t, i) => (
                <div key={i} className="lp-testimonial-card">
                  <div className="lp-testimonial-quote">"</div>
                  <p className="lp-testimonial-text">{t.quote}</p>
                  <div className="lp-testimonial-author">
                    <div className="lp-testimonial-avatar">{t.initials}</div>
                    <div>
                      <p className="lp-testimonial-name">{t.author}</p>
                      <p className="lp-testimonial-role">{t.role}</p>
                    </div>
                  </div>
                </div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          PRICING — staggered scale reveal
      ══════════════════════════════════════════════════════ */}
      <section className="lp-section lp-pricing">
        <div className="lp-inner">
          <motion.div className="lp-section-header" {...fromBelow()}>
            <motion.span className="lp-eyebrow" {...fromBelow(0.05)}>Pricing</motion.span>
            <motion.h2 className="lp-section-title" {...fromBelow(0.12)}>Simple, transparent plans</motion.h2>
            <motion.p className="lp-section-sub" {...fromBelow(0.18)}>Start free. Upgrade when you need more.</motion.p>
          </motion.div>

          <div className="lp-plan-grid">
            {plans.map((plan, i) => (
              <motion.div
                key={plan.name}
                className={`lp-plan-card${plan.highlight ? " lp-plan-card--highlight" : ""}`}
                initial={{ opacity: 0, y: 56, scale: 0.92 }}
                whileInView={{ opacity: 1, y: 0, scale: 1 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ type: "spring", stiffness: 180, damping: 18, delay: i * 0.12 }}
                whileHover={plan.highlight
                  ? { y: -8, boxShadow: "0 16px 48px rgba(52,168,90,0.22)", transition: { type: "spring", stiffness: 260, damping: 18 } }
                  : { y: -5, transition: { type: "spring", stiffness: 260, damping: 18 } }
                }
              >
                {plan.tag && <div className="lp-plan-tag">{plan.tag}</div>}
                <h3 className="lp-plan-name">{plan.name}</h3>
                <div className="lp-plan-price">
                  {plan.price === "Custom" ? (
                    <span className="lp-plan-price-custom">Custom</span>
                  ) : (
                    <>
                      <span className="lp-plan-currency">₹</span>
                      <span className="lp-plan-amount">{plan.price}</span>
                      <span className="lp-plan-period">/mo</span>
                    </>
                  )}
                </div>
                <ul className="lp-plan-features">
                  {plan.features.map((f, fi) => (
                    <motion.li
                      key={f}
                      initial={{ opacity: 0, x: -12 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      viewport={{ once: true }}
                      transition={{ delay: i * 0.12 + fi * 0.06, duration: 0.35 }}
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      {f}
                    </motion.li>
                  ))}
                </ul>
                <a href="#signup" className={`lp-plan-cta${plan.highlight ? " lp-plan-cta--primary" : ""}`}>
                  {plan.price === "Custom" ? "Contact us" : "Get started"}
                </a>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          TRUST BADGES + BOTTOM CTA
      ══════════════════════════════════════════════════════ */}
      <section className="lp-section lp-trust">
        <div className="lp-inner">
          <motion.p className="lp-trust-label" {...fromBelow()}>Powered by</motion.p>
          <motion.div className="lp-trust-badges">
            {trustBadges.map((b, i) => (
              <motion.div
                key={b.label}
                className="lp-trust-badge"
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 220, damping: 18, delay: i * 0.07 }}
                whileHover={{ scale: 1.06, transition: { type: "spring", stiffness: 400 } }}
              >{b.label}</motion.div>
            ))}
          </motion.div>

          <motion.div
            className="lp-bottom-cta"
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ type: "spring", stiffness: 160, damping: 18, delay: 0.2 }}
          >
            <div>
              <motion.h2
                className="lp-bottom-cta-title"
                initial={{ opacity: 0, x: -32 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 180, damping: 18, delay: 0.3 }}
              >Detect deepfakes in seconds.</motion.h2>
              <motion.p
                className="lp-bottom-cta-sub"
                initial={{ opacity: 0, x: -24 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 180, damping: 18, delay: 0.38 }}
              >Try a free demo — upload any video and get an instant real/fake verdict with Grad-CAM explanation. No credit card needed.</motion.p>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: "0.5rem" }}>
              <motion.button
                className="lp-btn-primary lp-btn-primary--lg"
                onClick={handleDemoStart}
                disabled={demoState === "loading"}
                initial={{ opacity: 0, scale: 0.88 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ type: "spring", stiffness: 200, damping: 18, delay: 0.44 }}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.97 }}
              >
                {demoState === "loading" ? "Starting…" : "Start for free"}
                {demoState !== "loading" && <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>}
              </motion.button>
              {demoState === "denied" && (
                <span className="lp-demo-denied">Demo already used from this device.</span>
              )}
            </div>
          </motion.div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════════════
          FOOTER
      ══════════════════════════════════════════════════════ */}
      <footer className="lp-footer">
        <div className="lp-inner lp-footer-inner">
          <div className="lp-footer-brand">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
            </svg>
            DeepScan
          </div>
          <p className="lp-footer-copy">© 2026 DeepScan · Built with MLOps best practices</p>
        </div>
      </footer>

    </div>
  );
};
