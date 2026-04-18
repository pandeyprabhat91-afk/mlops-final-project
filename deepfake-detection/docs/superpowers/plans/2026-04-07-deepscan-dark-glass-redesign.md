# DeepScan Dark Glass UI Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the incorrectly-implemented light cream UI with the intended dramatic dark glass aesthetic — near-black backgrounds, forest green accent gradient, vivid animations — while preserving all functionality.

**Architecture:** Complete overwrite of `index.css` tokens/global styles + update component JSX where needed. Framer Motion already installed. The previous light implementation must be fully replaced.

**Tech Stack:** React 19, Framer Motion 11, CSS custom properties, Google Fonts (Syne 700/800 + Plus Jakarta Sans 300–600 + JetBrains Mono 400/500 — already in index.html)

---

## File Map

| File | What changes |
|------|-------------|
| `frontend/src/index.css` | Full rewrite: dark tokens, dark keyframes, dark component styles throughout |
| `frontend/src/pages/Login.tsx` | Dark glass left panel with green orbs; dark form panel |
| `frontend/src/pages/Home.tsx` | Dark mesh-grid hero (already has correct JSX structure, needs dark CSS) |
| `frontend/src/components/FaceScan.tsx` | Dark green tones replacing light cream face volume |
| `frontend/src/components/ResultCard.tsx` | Dark glass body, bright verdict colors on dark bg |
| `frontend/src/components/VideoUpload.tsx` | Dark glass card, green scan line |

---

## Task 1: Dark Design Tokens + Body

**Files:**
- Modify: `frontend/src/index.css` (`:root` block and `body` rule)

- [ ] **Step 1: Replace the entire `:root` block**

Find the `:root {` block at the top of `frontend/src/index.css` and replace it (and the `body` rule) with:

```css
@tailwind components;
@tailwind utilities;

/* ─── Tokens ────────────────────────────────────────────── */
:root {
  /* Dark backgrounds */
  --bg-deep:      #0d0f0d;
  --bg-mid:       #111a13;
  --bg-elevated:  #182019;

  /* Dark glass */
  --glass-bg:     rgba(255,255,255,0.05);
  --glass-border: rgba(255,255,255,0.08);
  --glass-hover:  rgba(255,255,255,0.08);

  /* Forest Green accent */
  --grad-start:   #1a5c35;
  --grad-end:     #34a85a;
  --grad:         linear-gradient(135deg, #1a5c35, #34a85a);
  --accent:       #34a85a;
  --accent-light: rgba(52,168,90,0.15);
  --accent-glow:  rgba(52,168,90,0.20);

  /* Text — on dark bg */
  --text-primary:   #ffffff;
  --text-secondary: rgba(255,255,255,0.55);
  --text-muted:     rgba(255,255,255,0.28);

  /* Semantic */
  --fake-color:  #fb7185;
  --fake-dim:    rgba(251,113,133,0.12);
  --real-color:  #4ade80;
  --real-dim:    rgba(74,222,128,0.12);

  /* Borders */
  --border:      rgba(255,255,255,0.08);
  --border-mid:  rgba(255,255,255,0.12);

  /* Fonts */
  --font-display: 'Syne', sans-serif;
  --font-ui:      'Plus Jakarta Sans', sans-serif;
  --font-mono:    'JetBrains Mono', monospace;

  /* Misc */
  --nav-h:     52px;
  --r-sm:      8px;
  --r-md:      12px;
  --r-lg:      18px;
  --r-xl:      24px;

  --shadow-xs: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 20px rgba(0,0,0,0.5), 0 1px 4px rgba(0,0,0,0.3);
  --shadow-lg: 0 12px 40px rgba(0,0,0,0.6), 0 2px 8px rgba(0,0,0,0.4);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  background: var(--bg-deep);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 15px;
  line-height: 1.55;
  min-height: 100dvh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#root { min-height: 100dvh; display: flex; flex-direction: column; }
```

- [ ] **Step 2: Verify the existing keyframes are correct**

The keyframes block should already have `grid-pulse`, `shimmer`, `orb-drift`, `pulse-border`, `bar-grow`, `spin`, `scan-line`, `orbit`, `corner-draw`, `pulse-dot` from the previous implementation. If any are missing, add them. Do NOT change keyframe content.

- [ ] **Step 3: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/index.css
git commit -m "style: dark glass tokens — near-black bg, forest green accent"
```

---

## Task 2: Dark Navigation

**Files:**
- Modify: `frontend/src/index.css` (Nav section)

- [ ] **Step 1: Replace the Nav CSS block**

Find `/* ─── Navigation` and replace everything up to (not including) `/* ─── Buttons` with:

```css
/* ─── Navigation ────────────────────────────────────────── */
.nav {
  height: var(--nav-h);
  display: flex;
  align-items: center;
  padding: 0 28px;
  background: rgba(13,15,13,0.85);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.07);
  position: sticky;
  top: 0;
  z-index: 200;
  gap: 6px;
}

.nav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 15px;
  letter-spacing: -0.3px;
  color: var(--text-primary);
  text-decoration: none;
  margin-right: 28px;
  flex-shrink: 0;
}

.nav-logo-mark {
  width: 26px;
  height: 26px;
  background: var(--grad);
  border-radius: 7px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.nav-links { display: flex; align-items: center; flex: 1; }

.nav-link {
  padding: 0 12px;
  height: var(--nav-h);
  display: flex;
  align-items: center;
  font-size: 13.5px;
  font-weight: 400;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.15s;
  position: relative;
}
.nav-link:hover { color: var(--text-primary); }
.nav-link.active {
  color: white;
  font-weight: 500;
}
.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 12px;
  right: 12px;
  height: 2px;
  background: var(--grad);
  border-radius: 1px;
}

.nav-actions { display: flex; align-items: center; gap: 8px; margin-left: auto; }

.nav-user {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.nav-user-role {
  font-size: 10px;
  font-family: var(--font-mono);
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--real-color);
  background: rgba(26,92,53,0.20);
  border: 1px solid rgba(52,168,90,0.35);
  padding: 1px 6px;
  border-radius: 4px;
}
```

- [ ] **Step 2: Replace the Buttons CSS block**

Find `/* ─── Buttons` and replace up to the next section with:

```css
/* ─── Buttons ───────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  font-family: var(--font-ui);
  font-size: 13.5px;
  font-weight: 500;
  border-radius: var(--r-sm);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.15s;
  border: none;
  line-height: 1;
}

.btn-primary {
  background: var(--grad);
  color: white;
  border: none;
}
.btn-primary:hover {
  opacity: 0.9;
  box-shadow: 0 0 24px rgba(52,168,90,0.4);
}
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid rgba(255,255,255,0.12);
}
.btn-ghost:hover {
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
}

.btn-lg {
  padding: 11px 24px;
  font-size: 14px;
  font-family: var(--font-display);
  font-weight: 700;
  border-radius: var(--r-md);
}
```

- [ ] **Step 3: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/index.css
git commit -m "style: dark nav + buttons — translucent dark bg, green gradient active"
```

---

## Task 3: Dark Login Page

**Files:**
- Modify: `frontend/src/pages/Login.tsx`
- Modify: `frontend/src/index.css` (login section)

- [ ] **Step 1: Rewrite Login.tsx**

Replace the entire contents of `frontend/src/pages/Login.tsx`:

```tsx
import type React from "react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../auth/AuthContext";

export const Login: React.FC = () => {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!login(username, password)) setError("Incorrect username or password.");
  };

  return (
    <div className="login-outer">
      {/* ── Left: Branding + Stats ── */}
      <div className="login-left">
        <div className="login-orb login-orb-1" />
        <div className="login-orb login-orb-2" />

        <div className="login-left-content">
          <div className="login-logo">
            <div className="login-logo-mark">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
              </svg>
            </div>
            <span className="login-logo-name">DeepScan</span>
          </div>

          <div className="login-tagline">
            <h2 className="login-tagline-text">
              Every frame holds a{" "}
              <span className="login-gradient-word">secret.</span>
            </h2>
            <p className="login-tagline-sub">
              CNN + LSTM neural network trained on the SDFVD dataset.
              Detects AI-generated faces with clinical precision.
            </p>
          </div>

          <div className="login-stats">
            <div className="login-stat-card">
              <span className="login-stat-value">99<span className="login-stat-unit">%</span></span>
              <div>
                <p className="login-stat-name">Detection Rate</p>
                <p className="login-stat-desc">on SDFVD test set</p>
              </div>
            </div>
            <div className="login-stat-card">
              <span className="login-stat-value">~2<span className="login-stat-unit">s</span></span>
              <div>
                <p className="login-stat-name">Inference Time</p>
                <p className="login-stat-desc">per video analysis</p>
              </div>
            </div>
            <div className="login-stat-card">
              <span className="login-stat-value">30</span>
              <div>
                <p className="login-stat-name">Frames Sampled</p>
                <p className="login-stat-desc">CNN feature extraction</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right: Form ── */}
      <div className="login-right">
        <motion.div
          className="login-form-wrap"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        >
          <h1 className="login-heading">Welcome back</h1>
          <p className="login-sub">Sign in to your account</p>

          <form onSubmit={handleSubmit}>
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
                  exit={{ opacity: 0 }} transition={{ duration: 0.25 }}>
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <button type="submit" className="login-submit">Continue →</button>
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
  );
};
```

- [ ] **Step 2: Replace login CSS section**

Find `/* ─── Login` and replace the entire section with:

```css
/* ─── Login ─────────────────────────────────────────────── */
.login-outer {
  display: flex;
  min-height: 100dvh;
}

.login-left {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: radial-gradient(ellipse at 30% 30%, #0d3318 0%, #0d0f0d 65%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.login-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  animation: orb-drift 10s ease-in-out infinite alternate;
}
.login-orb-1 {
  width: 360px; height: 360px;
  background: radial-gradient(circle, rgba(26,92,53,0.35) 0%, transparent 70%);
  top: -100px; left: -80px;
}
.login-orb-2 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, rgba(52,168,90,0.20) 0%, transparent 70%);
  bottom: -80px; right: -60px;
  animation-delay: -5s;
  animation-direction: alternate-reverse;
}

.login-left-content {
  position: relative;
  z-index: 1;
  max-width: 360px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.login-logo { display: flex; align-items: center; gap: 10px; }
.login-logo-mark {
  width: 32px; height: 32px;
  background: var(--grad);
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  color: white;
}
.login-logo-name {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 18px;
  color: var(--text-primary);
  letter-spacing: -0.4px;
}

.login-tagline { display: flex; flex-direction: column; gap: 12px; }
.login-tagline-text {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: clamp(24px, 3.5vw, 34px);
  line-height: 1.1;
  color: var(--text-primary);
  letter-spacing: -0.6px;
}
.login-gradient-word {
  background: var(--grad);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 3s linear infinite;
}
.login-tagline-sub {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  max-width: 320px;
}

.login-stats { display: flex; flex-direction: column; gap: 8px; }
.login-stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-md);
  padding: 14px 18px;
  backdrop-filter: blur(8px);
}
.login-stat-value {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 28px;
  line-height: 1;
  background: var(--grad);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  min-width: 52px;
  flex-shrink: 0;
}
.login-stat-unit { font-size: 18px; }
.login-stat-name {
  font-size: 13px; font-weight: 600;
  color: var(--text-primary); line-height: 1.3;
}
.login-stat-desc {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-top: 2px;
}

.login-right {
  width: 440px;
  flex-shrink: 0;
  background: rgba(13,15,13,0.95);
  border-left: 1px solid rgba(255,255,255,0.06);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.login-form-wrap { width: 100%; max-width: 300px; }

.login-heading {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  letter-spacing: -0.5px;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.login-sub {
  font-size: 13.5px;
  color: var(--text-secondary);
  margin-bottom: 28px;
}

.login-field { display: flex; flex-direction: column; gap: 5px; margin-bottom: 16px; }
.login-label {
  font-size: 9px;
  font-family: var(--font-mono);
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.login-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: var(--r-sm);
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--text-primary);
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
}
.login-input:focus {
  border-color: rgba(52,168,90,0.6);
  box-shadow: 0 0 0 3px rgba(52,168,90,0.15);
}
.login-input::placeholder { color: var(--text-muted); }

.login-error {
  font-size: 12.5px;
  color: var(--fake-color);
  background: var(--fake-dim);
  border: 1px solid rgba(251,113,133,0.25);
  padding: 8px 12px;
  border-radius: var(--r-sm);
  margin-bottom: 12px;
}

.login-submit {
  width: 100%;
  padding: 11px;
  background: var(--grad);
  color: white;
  border: none;
  border-radius: var(--r-md);
  font-family: var(--font-display);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.15s, box-shadow 0.15s;
  margin-top: 4px;
}
.login-submit:hover {
  opacity: 0.9;
  box-shadow: 0 0 24px rgba(52,168,90,0.4);
}

.login-divider {
  display: flex; align-items: center; gap: 10px;
  margin: 24px 0 14px;
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.login-divider::before, .login-divider::after {
  content: ''; flex: 1; height: 1px;
  background: rgba(255,255,255,0.08);
}

.login-role-pills { display: flex; gap: 8px; }
.login-role-pill {
  flex: 1; padding: 10px 12px;
  border-radius: var(--r-sm);
  display: flex; flex-direction: column; gap: 2px;
}
.login-role-pill.admin {
  background: rgba(26,92,53,0.20);
  border: 1px solid rgba(52,168,90,0.30);
}
.login-role-pill.user {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
}
.login-role-name {
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--real-color);
}
.login-role-access {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

@media (max-width: 768px) {
  .login-outer { flex-direction: column; }
  .login-left { padding: 40px 28px 32px; }
  .login-right { width: 100%; border-left: none; border-top: 1px solid rgba(255,255,255,0.06); padding: 36px 28px 48px; }
}
```

- [ ] **Step 3: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/pages/Login.tsx frontend/src/index.css
git commit -m "style: dark glass login — near-black bg, green orbs, glass stat cards"
```

---

## Task 4: Dark Hero Section

**Files:**
- Modify: `frontend/src/index.css` (hero section)

Note: `Home.tsx` JSX structure is already correct (hero-bg, hero-bg-grid, etc.) from the previous implementation. Only the CSS colors need updating.

- [ ] **Step 1: Replace hero CSS section**

Find `/* ─── Hero` and replace the entire section with:

```css
/* ─── Hero ──────────────────────────────────────────────── */
.hero-wrap {
  position: relative;
  overflow: hidden;
  min-height: 100svh;
  display: flex;
  align-items: center;
}

.hero-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
}
.hero-bg-grid {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 50% 0%, #0d2e18 0%, #0d0f0d 60%),
    linear-gradient(rgba(52,168,90,0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(52,168,90,0.07) 1px, transparent 1px);
  background-size: 100% 100%, 40px 40px, 40px 40px;
  animation: grid-pulse 4s ease infinite;
}
.hero-bg-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 40%, rgba(26,92,53,0.25) 0%, transparent 65%);
}
.hero-bg-vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(13,15,13,0.6) 100%);
}

.hero {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 80px 32px;
  display: grid;
  grid-template-columns: 1fr 420px;
  align-items: center;
  gap: 48px;
}

.hero-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 520px;
}

.hero-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(52,168,90,0.10);
  border: 1px solid rgba(52,168,90,0.25);
  border-radius: 99px;
  padding: 5px 12px;
  font-size: 10px;
  font-family: var(--font-mono);
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--real-color);
  width: fit-content;
}

.hero-eyebrow-dot {
  width: 6px; height: 6px;
  background: var(--real-color);
  border-radius: 50%;
  animation: pulse-dot 2s ease infinite;
}

.hero-title {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: clamp(42px, 5vw, 68px);
  line-height: 1.0;
  letter-spacing: -1.5px;
  color: var(--text-primary);
}

.hero-title-gradient {
  display: block;
  background: var(--grad);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 3s linear infinite;
  font-style: normal;
}

.hero-body {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.65;
  max-width: 420px;
}

.hero-cta { display: flex; gap: 12px; }

.hero-right { display: flex; justify-content: center; }

@media (max-width: 900px) {
  .hero { grid-template-columns: 1fr; padding: 60px 24px; text-align: center; }
  .hero-eyebrow { margin: 0 auto; }
  .hero-body { max-width: 100%; }
  .hero-cta { justify-content: center; }
  .hero-right { display: none; }
}
```

- [ ] **Step 2: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/index.css
git commit -m "style: dark hero — near-black mesh grid, green glow, shimmer headline"
```

---

## Task 5: Dark FaceScan

**Files:**
- Modify: `frontend/src/components/FaceScan.tsx`
- Modify: `frontend/src/index.css` (FaceScan section)

- [ ] **Step 1: Rewrite FaceScan.tsx with dark green tones**

Replace the entire contents of `frontend/src/components/FaceScan.tsx`:

```tsx
import type React from "react";

const V: [number, number][] = [
  [220,46],[143,73],[297,73],[103,141],[337,141],
  [125,164],[168,148],[220,146],[272,148],[315,164],
  [125,184],[161,176],[193,184],[247,184],[279,176],[315,184],
  [114,229],[326,229],[175,209],[265,209],[220,210],
  [196,243],[244,243],[220,254],[120,275],[320,275],
  [165,280],[275,280],[197,268],[243,268],
  [220,293],[128,322],[312,322],[167,354],[273,354],[220,378],
];

const EDGES: [number,number][] = [
  [0,1],[0,2],[1,2],[1,3],[2,4],[3,5],[4,9],[3,6],[4,8],
  [0,7],[6,7],[7,8],[1,6],[2,8],[5,6],[8,9],
  [5,10],[6,12],[9,15],[8,13],
  [10,11],[11,12],[13,14],[14,15],
  [10,16],[15,17],[12,18],[13,19],[11,18],[14,19],
  [16,18],[17,19],[18,20],[19,20],[16,24],[17,25],
  [20,21],[20,22],[21,22],[21,23],[22,23],
  [23,26],[23,27],[21,26],[22,27],
  [26,28],[28,29],[29,27],[26,30],[27,30],[28,30],[29,30],
  [24,26],[25,27],[24,31],[25,32],
  [30,31],[30,32],[31,33],[32,34],[33,35],[34,35],[33,34],[30,35],
];

const MAJOR = new Set([0,3,4,10,15,16,17,20,23,26,27,30,31,32,35]);
const CX = 220, CY = 210;

export const FaceScan: React.FC = () => (
  <div className="face-wrap" aria-hidden="true">
    <svg viewBox="0 0 440 480" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="fv" cx="50%" cy="42%" r="52%">
          <stop offset="0%"   stopColor="#1a3d1e" />
          <stop offset="50%"  stopColor="#142e17" />
          <stop offset="100%" stopColor="#0e1f10" />
        </radialGradient>
        <radialGradient id="hg" cx="50%" cy="18%" r="52%">
          <stop offset="0%"   stopColor="#122a15" />
          <stop offset="100%" stopColor="#0c1a0e" />
        </radialGradient>
        <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#1a5c35" stopOpacity="0" />
          <stop offset="48%"  stopColor="#1a5c35" stopOpacity="0.08" />
          <stop offset="50%"  stopColor="#34a85a" stopOpacity="0.6" />
          <stop offset="52%"  stopColor="#1a5c35" stopOpacity="0.08" />
          <stop offset="100%" stopColor="#1a5c35" stopOpacity="0" />
        </linearGradient>
        <filter id="dg" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <clipPath id="fc">
          <ellipse cx={CX} cy={CY} rx="108" ry="168" />
        </clipPath>
      </defs>

      <circle cx={CX} cy={CY} r="188"
        stroke="#34a85a" strokeOpacity="0.10" strokeWidth="1"
        strokeDasharray="4 6" />
      <circle cx={CX} cy={CY} r="158"
        stroke="#34a85a" strokeOpacity="0.15" strokeWidth="0.75" />

      <circle r="4" fill="#34a85a" fillOpacity="0.9"
        className="face-orbit-dot"
        style={{ filter: "drop-shadow(0 0 6px rgba(52,168,90,0.9))" }} />

      <ellipse cx={CX} cy={175} rx="112" ry="140" fill="url(#hg)" />
      <ellipse cx={CX} cy={CY} rx="107" ry="166" fill="url(#fv)" />

      {EDGES.map(([a,b],i) => (
        <line key={i}
          x1={V[a][0]} y1={V[a][1]} x2={V[b][0]} y2={V[b][1]}
          stroke="#34a85a" strokeOpacity="0.20" strokeWidth="0.75" />
      ))}

      {V.map(([x,y],i) => {
        const big = MAJOR.has(i);
        return (
          <circle key={i} cx={x} cy={y}
            r={big ? 3.5 : 2}
            fill="#34a85a"
            fillOpacity={big ? 0.70 : 0.35}
            filter={big ? "url(#dg)" : undefined}
            className="face-mesh-dot"
            style={{ animationDelay: `${(i * 0.08) % 2}s` }} />
        );
      })}

      <rect x="112" y="-20" width="216" height="32"
        fill="url(#beam)" clipPath="url(#fc)"
        className="face-scan-beam" />
      <line x1="112" y1="0" x2="328" y2="0"
        stroke="#34a85a" strokeWidth="1" strokeOpacity="0.8"
        clipPath="url(#fc)" className="face-scan-beam" />

      <path d="M 28 64 L 28 40 L 52 40" className="face-corner-line" />
      <path d="M 388 40 L 412 40 L 412 64" className="face-corner-line" />
      <path d="M 28 416 L 28 440 L 52 440" className="face-corner-line" />
      <path d="M 388 440 L 412 440 L 412 416" className="face-corner-line" />

      <circle cx="46" cy="24" r="3.5" fill="#4ade80" opacity="0.9"
        className="face-mesh-dot" />
      <text x="56" y="28" fontFamily="'JetBrains Mono', monospace" fontSize="9"
        letterSpacing="0.12em" fill="rgba(255,255,255,0.45)">BIOMETRIC SCAN · ACTIVE</text>

      <text x="220" y="468" textAnchor="middle"
        fontFamily="'JetBrains Mono', monospace" fontSize="8"
        letterSpacing="0.1em" fill="rgba(255,255,255,0.25)">
        36 LANDMARKS · CNN+LSTM
      </text>
    </svg>
  </div>
);
```

- [ ] **Step 2: Replace FaceScan CSS section**

Find `/* ─── FaceScan` and replace:

```css
/* ─── FaceScan ───────────────────────────────────────────── */
.face-wrap { width: 100%; max-width: 360px; }
.face-wrap svg { width: 100%; height: auto; overflow: visible; }

.face-corner-line {
  stroke: rgba(52,168,90,0.7);
  stroke-width: 1.5;
  fill: none;
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  animation: corner-draw 0.6s ease 0.4s forwards;
}

.face-scan-beam { animation: scan-line 2.4s ease-in-out infinite; }

.face-orbit-dot {
  animation: orbit 5s linear infinite;
  transform-origin: 220px 210px;
}

.face-mesh-dot { animation: pulse-dot 2s ease-in-out infinite; }
```

- [ ] **Step 3: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/components/FaceScan.tsx frontend/src/index.css
git commit -m "style: FaceScan dark green — deep tones, vivid emerald mesh and beam"
```

---

## Task 6: Dark Upload Zone + Analyze Section

**Files:**
- Modify: `frontend/src/index.css` (analyze/upload section)

Note: `VideoUpload.tsx` JSX is already correct (motion.div, correct classes). Only CSS needs updating.

- [ ] **Step 1: Replace analyze/upload CSS section**

Find `/* ─── Analyze Section` and replace:

```css
/* ─── Analyze Section ────────────────────────────────────── */
.analyze-section {
  max-width: 620px;
  margin: 0 auto;
  padding: 56px 24px 80px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-label {
  font-size: 10px;
  font-family: var(--font-mono);
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  text-align: center;
  margin-bottom: 4px;
}

.upload-zone {
  background: rgba(255,255,255,0.04);
  border: 1.5px dashed rgba(255,255,255,0.12);
  border-radius: var(--r-xl);
  padding: 52px 32px;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
}
.upload-zone:hover,
.upload-zone.drag-over {
  border-color: rgba(52,168,90,0.45);
  border-style: solid;
  background: rgba(52,168,90,0.05);
  box-shadow: 0 0 40px rgba(52,168,90,0.15);
}
.upload-zone.drag-over {
  border-color: rgba(52,168,90,0.7);
  box-shadow: 0 0 60px rgba(52,168,90,0.20);
}
.upload-zone.scanning { pointer-events: none; }

.upload-scan-line {
  position: absolute;
  left: 0; right: 0;
  height: 1.5px;
  background: linear-gradient(90deg, transparent, #1a5c35, #34a85a, #1a5c35, transparent);
  top: 0;
  opacity: 0;
  pointer-events: none;
}
.upload-zone.scanning .upload-scan-line {
  animation: scan-line 2.4s ease-in-out infinite;
}

.upload-icon-wrap {
  width: 48px; height: 48px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: var(--r-md);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
  color: var(--text-secondary);
  transition: color 0.15s, background 0.15s;
}
.upload-zone:hover .upload-icon-wrap,
.upload-zone.drag-over .upload-icon-wrap {
  color: var(--real-color);
  background: rgba(52,168,90,0.12);
}

.upload-title {
  font-size: 15px; font-weight: 600;
  color: var(--text-primary); margin-bottom: 6px;
}
.upload-hint {
  font-size: 13.5px; color: var(--text-secondary); margin-bottom: 8px;
}
.upload-link {
  color: var(--real-color);
  font-weight: 500; cursor: pointer;
  text-decoration: underline; text-underline-offset: 2px;
}
.upload-spec {
  font-size: 10.5px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.upload-err {
  display: flex; align-items: center; gap: 6px;
  margin-top: 14px; font-size: 12.5px;
  color: var(--fake-color);
  background: var(--fake-dim);
  border: 1px solid rgba(251,113,133,0.20);
  padding: 8px 12px;
  border-radius: var(--r-sm);
}
```

- [ ] **Step 2: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/index.css
git commit -m "style: dark upload zone — glass dark, green hover glow and scan line"
```

---

## Task 7: Dark Result Card

**Files:**
- Modify: `frontend/src/index.css` (result card section)

Note: `ResultCard.tsx` JSX is already correct. Only CSS needs updating.

- [ ] **Step 1: Replace result card CSS section**

Find `/* ─── Result Card` and replace:

```css
/* ─── Result Card ────────────────────────────────────────── */
.result {
  border-radius: var(--r-xl);
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: var(--shadow-lg);
}

.result-hero { padding: 28px 28px 24px; }
.result-hero.fake {
  background: var(--fake-dim);
  border-bottom: 1px solid rgba(251,113,133,0.25);
  animation: pulse-border 2s ease infinite;
}
.result-hero.real {
  background: var(--real-dim);
  border-bottom: 1px solid rgba(74,222,128,0.20);
}

.result-eyebrow {
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.result-verdict {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: clamp(36px, 7vw, 56px);
  line-height: 1.0;
  letter-spacing: -1px;
  margin-bottom: 8px;
}
.result-hero.fake .result-verdict { color: var(--fake-color); }
.result-hero.real .result-verdict { color: var(--real-color); }

.result-desc {
  font-size: 13.5px; color: var(--text-secondary); line-height: 1.5;
}

.result-body {
  padding: 24px 28px;
  background: rgba(255,255,255,0.04);
  display: flex; flex-direction: column; gap: 20px;
}

.conf-row { display: flex; justify-content: space-between; align-items: baseline; }
.conf-label {
  font-size: 11px; font-family: var(--font-mono);
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted);
}
.conf-pct {
  font-family: var(--font-display); font-weight: 700;
  font-size: 18px; color: var(--text-primary);
}
.conf-track {
  height: 6px; background: rgba(255,255,255,0.08);
  border-radius: 99px; overflow: hidden;
}
.conf-fill {
  height: 100%; border-radius: 99px;
  animation: bar-grow 0.9s cubic-bezier(0.25,1,0.5,1) both;
}
.result-body.fake .conf-fill {
  background: linear-gradient(90deg, #be123c, #fb7185);
  box-shadow: 0 0 8px rgba(251,113,133,0.5);
}
.result-body.real .conf-fill {
  background: linear-gradient(90deg, #1a5c35, #4ade80);
  box-shadow: 0 0 8px rgba(74,222,128,0.4);
}

.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.meta-cell {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--r-md);
  padding: 12px 14px;
  display: flex; flex-direction: column; gap: 3px;
}
.meta-cell-label {
  font-size: 10px; font-family: var(--font-mono);
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted);
}
.meta-cell-value {
  font-family: var(--font-display); font-weight: 700;
  font-size: 22px; color: var(--text-primary); line-height: 1.1;
}
.meta-cell-unit {
  font-size: 13px; font-weight: 400;
  color: var(--text-secondary); margin-left: 2px;
}

.gradcam-wrap { display: flex; flex-direction: column; gap: 8px; }
.gradcam-label {
  font-size: 10px; font-family: var(--font-mono);
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-muted);
}
.gradcam-wrap img {
  width: 100%; border-radius: var(--r-md);
  border: 1px solid rgba(255,255,255,0.08);
}

.feedback-wrap {
  display: flex; align-items: center; gap: 8px;
  padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.08);
}
.feedback-q { font-size: 13px; color: var(--text-secondary); flex: 1; }
.feedback-ok { font-size: 13px; color: var(--real-color); }
```

- [ ] **Step 2: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/index.css
git commit -m "style: dark result card — glass dark body, vivid DEEPFAKE/AUTHENTIC verdict"
```

---

## Task 8: Dark Analyzing/Error Cards + Pipeline + Admin

**Files:**
- Modify: `frontend/src/index.css` (remaining sections)

- [ ] **Step 1: Replace Analyzing/Error card CSS**

Find `/* ─── Analyzing / Error Cards` and replace:

```css
/* ─── Analyzing / Error Cards ────────────────────────────── */
.analyzing-card {
  display: flex; align-items: center; gap: 16px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
}
.analyzing-spinner {
  width: 20px; height: 20px;
  border: 2px solid rgba(52,168,90,0.20);
  border-top-color: var(--real-color);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
.analyzing-title {
  font-size: 14px; font-weight: 600;
  color: var(--text-primary); margin-bottom: 2px;
}
.analyzing-sub {
  font-size: 10px; font-family: var(--font-mono);
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted);
}

.error-card {
  display: flex; align-items: flex-start; gap: 12px;
  background: var(--fake-dim);
  border: 1px solid rgba(251,113,133,0.20);
  border-radius: var(--r-lg);
  padding: 16px 20px;
}
.error-card-icon { color: var(--fake-color); flex-shrink: 0; margin-top: 1px; }
.error-card-title {
  font-size: 13.5px; font-weight: 600;
  color: var(--fake-color); margin-bottom: 3px;
}
.error-card-msg { font-size: 13px; color: var(--text-secondary); }
```

- [ ] **Step 2: Replace Pipeline CSS section**

Find `/* ─── Pipeline Dashboard` and replace:

```css
/* ─── Pipeline Dashboard ─────────────────────────────────── */
.pipeline-page {
  max-width: 1100px; margin: 0 auto;
  padding: 40px 32px 80px;
  display: flex; flex-direction: column; gap: 32px;
}
.pipeline-header h1 {
  font-family: var(--font-display);
  font-weight: 800; font-style: italic;
  font-size: 28px; letter-spacing: -0.5px;
  color: var(--text-primary); margin-bottom: 4px;
}
.pipeline-header p { font-size: 13.5px; color: var(--text-secondary); }

.stat-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.stat-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg); padding: 20px;
  transition: box-shadow 0.15s, border-color 0.15s, transform 0.15s;
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  border-color: rgba(52,168,90,0.25);
  transform: translateY(-2px);
}
.stat-card-label {
  font-size: 10px; font-family: var(--font-mono);
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 6px;
}
.stat-card-value {
  font-family: var(--font-display); font-weight: 700;
  font-size: 26px; color: var(--text-primary); line-height: 1.1;
}
.stat-card-value.gradient {
  background: var(--grad);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.pipeline-table-wrap {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg); overflow: hidden;
}
.pipeline-table { width: 100%; border-collapse: collapse; }
.pipeline-table th {
  background: rgba(255,255,255,0.04);
  padding: 10px 14px; text-align: left;
  font-size: 10px; font-family: var(--font-mono);
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-muted);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.pipeline-table td {
  padding: 12px 14px; font-size: 13px;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.pipeline-table tr:last-child td { border-bottom: none; }
.pipeline-table tr:hover td { background: rgba(52,168,90,0.05); }
.pipeline-table .val-gradient {
  background: var(--grad);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text; font-weight: 600;
}

.pipeline-terminal {
  background: #060d07;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: var(--r-md); padding: 16px;
  font-family: var(--font-mono); font-size: 12px;
  line-height: 1.6; max-height: 280px;
  overflow-y: auto; color: rgba(255,255,255,0.7);
}
```

- [ ] **Step 3: Replace Admin CSS section**

Find `/* ─── Admin Page` and replace:

```css
/* ─── Admin Page ─────────────────────────────────────────── */
.admin-page {
  max-width: 760px; margin: 0 auto;
  padding: 40px 32px 80px;
  display: flex; flex-direction: column; gap: 28px;
}
.admin-page h1 {
  font-family: var(--font-display); font-weight: 800;
  font-size: 26px; letter-spacing: -0.5px;
  color: var(--text-primary);
}
.admin-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg); padding: 24px;
  display: flex; flex-direction: column; gap: 16px;
}
.admin-card h2 {
  font-family: var(--font-display); font-size: 15px;
  font-weight: 700; color: var(--text-primary);
}
.admin-input {
  width: 100%; padding: 9px 12px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: var(--r-sm);
  font-family: var(--font-ui); font-size: 14px;
  color: var(--text-primary); outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.admin-input:focus {
  border-color: rgba(52,168,90,0.6);
  box-shadow: 0 0 0 3px rgba(52,168,90,0.15);
}
.admin-status { font-size: 13px; padding: 10px 14px; border-radius: var(--r-sm); }
.admin-status.success {
  background: var(--real-dim);
  border: 1px solid rgba(74,222,128,0.20);
  color: var(--real-color);
}
.admin-status.error {
  background: var(--fake-dim);
  border: 1px solid rgba(251,113,133,0.20);
  color: var(--fake-color);
}
```

- [ ] **Step 4: Commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add frontend/src/index.css
git commit -m "style: dark glass analyzing/pipeline/admin sections"
```

---

## Task 9: Build Verification

**Files:** No code changes — verification only

- [ ] **Step 1: Run TypeScript check**

```bash
export PATH="/c/Program Files/nodejs:$PATH"
cd "f:/mlops project/deepfake-detection/frontend"
npx tsc --noEmit 2>&1 | head -20
```

Expected: no output (0 errors)

- [ ] **Step 2: Run production build**

```bash
export PATH="/c/Program Files/nodejs:$PATH"
cd "f:/mlops project/deepfake-detection/frontend"
npm run build 2>&1 | tail -10
```

Expected: `✓ built in` with no errors

- [ ] **Step 3: Visual smoke check list**

Start dev server: `npm run dev`

- [ ] Page background is **near-black** (#0d0f0d), NOT cream/white
- [ ] Login: dark background with green glowing orbs, glass stat cards with dark bg
- [ ] Hero: dark background with subtle green grid lines
- [ ] FaceScan: vivid green mesh/dots/beam on dark face volume
- [ ] Upload zone: dark glass card, green hover glow
- [ ] Result FAKE: dark glass body, bright #fb7185 "DEEPFAKE"
- [ ] Result REAL: dark glass body, bright #4ade80 "AUTHENTIC"
- [ ] Nav: dark translucent bar, green gradient badge for role

- [ ] **Step 4: Final commit**

```bash
cd "f:/mlops project/deepfake-detection"
git add -A
git commit -m "style: dark glass redesign complete — forest green on near-black"
```
