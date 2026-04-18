# DeepScan UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current bland cream/grey UI with a premium Forest Green on Cream aesthetic — stunning animations, split login layout, mesh-grid hero, dramatic result cards — while preserving all existing functionality.

**Architecture:** CSS-first redesign — no React component tree restructuring except Login.tsx (add left stats panel) and Home.tsx (add hero background wrapper). All JSX class names remain; we replace CSS rules for them in `index.css`. Framer Motion (already installed) added to Login, Home hero stagger, and ResultCard entrance.

**Tech Stack:** React 19, Framer Motion 11, CSS custom properties, Google Fonts CDN (Syne 700/800 + Plus Jakarta Sans 300–600 + JetBrains Mono 400/500)

---

## File Map

| File | What changes |
|------|-------------|
| `frontend/index.html` | Replace Google Fonts CDN link (Instrument Serif+Geist → Syne+Plus Jakarta Sans+JetBrains Mono) |
| `frontend/src/index.css` | Complete rewrite: new tokens, keyframes, all component styles |
| `frontend/src/pages/Login.tsx` | Add left stats panel JSX + Framer Motion form mount animation |
| `frontend/src/pages/Home.tsx` | Wrap hero in mesh-grid background div; add Framer Motion stagger |
| `frontend/src/components/FaceScan.tsx` | Recolor: dark/amber → forest green; update gradient stops and text |
| `frontend/src/components/ResultCard.tsx` | Add Framer Motion AnimatePresence + spring entrance + bar-grow animation |
| `frontend/src/components/VideoUpload.tsx` | Add Framer Motion scale on drag-over; update scan line to green |

---

## Task 1: Fonts and CSS Design Tokens

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/src/index.css` (lines 1–42 — tokens and body)

- [ ] **Step 1: Update index.html font CDN link**

Replace the existing `<link>` for Google Fonts with:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DeepScan — Deepfake Detection</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: Replace the `:root` token block in index.css**

Replace everything from line 1 through the closing `}` of `:root` (ends around line 42) with:

```css
@tailwind components;
@tailwind utilities;

/* ─── Tokens ────────────────────────────────────────────── */
:root {
  /* Backgrounds */
  --bg-base:      #f9f8f4;
  --bg-surface:   #f4f2ec;
  --bg-elevated:  #edeae0;

  /* Glass */
  --glass-bg:     rgba(255,255,255,0.72);
  --glass-border: rgba(26,74,46,0.10);
  --glass-hover:  rgba(255,255,255,0.88);

  /* Forest Green accent */
  --grad-start:   #1a4a2e;
  --grad-end:     #2d7a4f;
  --grad:         linear-gradient(135deg, #1a4a2e, #2d7a4f);
  --accent:       #1a4a2e;
  --accent-mid:   #2d7a4f;
  --accent-light: #d1ead9;
  --accent-glow:  rgba(26,74,46,0.12);

  /* Text */
  --text-primary:   #141a14;
  --text-secondary: #4a5e4a;
  --text-muted:     rgba(20,26,20,0.38);

  /* Semantic */
  --fake-color:  #c0392b;
  --fake-dim:    rgba(192,57,43,0.08);
  --real-color:  #1a4a2e;
  --real-dim:    rgba(26,74,46,0.08);

  /* Borders */
  --border:      rgba(26,74,46,0.10);
  --border-mid:  rgba(26,74,46,0.18);

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

  --shadow-xs: 0 1px 2px rgba(26,74,46,0.05);
  --shadow-sm: 0 2px 8px rgba(26,74,46,0.07), 0 1px 2px rgba(26,74,46,0.04);
  --shadow-md: 0 4px 20px rgba(26,74,46,0.09), 0 1px 4px rgba(26,74,46,0.05);
  --shadow-lg: 0 12px 40px rgba(26,74,46,0.11), 0 2px 8px rgba(26,74,46,0.06);
}
```

- [ ] **Step 3: Update body rule**

Find the `body {` block in index.css and replace it with:

```css
body {
  background: var(--bg-base);
  color: var(--text-primary);
  font-family: var(--font-ui);
  font-size: 15px;
  line-height: 1.55;
  min-height: 100dvh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

- [ ] **Step 4: Verify in browser**

Run `npm run dev` in `frontend/`. Open `http://localhost:5173`. Page background should be warm cream `#f9f8f4` and text should use Plus Jakarta Sans (check browser DevTools > Fonts). No other layout should change yet.

- [ ] **Step 5: Commit**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
git add index.html src/index.css
git commit -m "style: forest green/cream tokens + Syne font CDN"
```

---

## Task 2: Keyframes + Global Animations

**Files:**
- Modify: `frontend/src/index.css` (keyframes section, lines ~60–96)

- [ ] **Step 1: Replace keyframes block**

Find the `/* ─── Keyframes ─────────────────────────────────────────── */` section (lines ~60–96) and replace with:

```css
/* ─── Keyframes ─────────────────────────────────────────── */
@keyframes fade-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes fade-in {
  from { opacity: 0; }
  to   { opacity: 1; }
}
@keyframes scale-in {
  from { opacity: 0; transform: scale(0.94); }
  to   { opacity: 1; transform: scale(1); }
}
@keyframes bar-grow {
  from { width: 0%; }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 0 0 rgba(26,74,46,0.5); }
  50%       { box-shadow: 0 0 0 5px rgba(26,74,46,0); }
}
@keyframes scan-line {
  0%   { transform: translateY(-100%); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 1; }
  100% { transform: translateY(520px); opacity: 0; }
}
@keyframes orbit {
  from { transform: rotate(0deg) translateX(130px) rotate(0deg); }
  to   { transform: rotate(360deg) translateX(130px) rotate(-360deg); }
}
@keyframes corner-draw {
  from { stroke-dashoffset: 40; }
  to   { stroke-dashoffset: 0; }
}
@keyframes grid-pulse {
  0%, 100% { opacity: 0.4; }
  50%       { opacity: 0.75; }
}
@keyframes shimmer {
  0%   { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
@keyframes orb-drift {
  0%   { transform: translate(0, 0) scale(1); }
  50%  { transform: translate(20px, -15px) scale(1.06); }
  100% { transform: translate(-10px, 10px) scale(0.97); }
}
@keyframes leaf-drift {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%       { transform: translateY(-8px) rotate(2deg); }
}
@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(192,57,43,0); }
  50%       { box-shadow: 0 0 16px 2px rgba(192,57,43,0.18); }
}
```

- [ ] **Step 2: Commit**

```bash
git add src/index.css
git commit -m "style: add forest-green keyframes (grid-pulse, shimmer, orb-drift, pulse-border)"
```

---

## Task 3: Navigation Styles

**Files:**
- Modify: `frontend/src/index.css` (Nav section, lines ~98–191)

- [ ] **Step 1: Replace the Nav CSS block**

Find the `/* ─── Navigation ────────────────────────────────────────── */` section and replace everything up to (but not including) `/* ─── Buttons */` with:

```css
/* ─── Navigation ────────────────────────────────────────── */
.nav {
  height: var(--nav-h);
  display: flex;
  align-items: center;
  padding: 0 28px;
  background: rgba(249,248,244,0.88);
  backdrop-filter: saturate(160%) blur(20px);
  -webkit-backdrop-filter: saturate(160%) blur(20px);
  border-bottom: 1px solid var(--border);
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
  color: var(--accent);
  font-weight: 500;
}
.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 12px;
  right: 12px;
  height: 2px;
  background: var(--accent);
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
  color: var(--accent);
  background: var(--accent-light);
  border: 1px solid rgba(26,74,46,0.25);
  padding: 1px 6px;
  border-radius: 4px;
}
```

- [ ] **Step 2: Verify nav in browser**

Nav should show cream frosted glass bg, green badge for role, green underline on active link. "DeepScan" wordmark uses Syne font.

- [ ] **Step 3: Commit**

```bash
git add src/index.css
git commit -m "style: nav forest-green tokens — frosted cream, green role badge"
```

---

## Task 4: Button Styles

**Files:**
- Modify: `frontend/src/index.css` (Buttons section)

- [ ] **Step 1: Replace the Buttons CSS block**

Find `/* ─── Buttons */` and replace all button rules until the next section comment with:

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
  opacity: 0.88;
  box-shadow: 0 4px 20px rgba(26,74,46,0.30);
}
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-mid);
}
.btn-ghost:hover {
  background: var(--accent-glow);
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

- [ ] **Step 2: Verify**

The "Analyze a video" CTA button on Home should now show forest-green gradient. Ghost buttons (Sign out, feedback) have green-tinted border.

- [ ] **Step 3: Commit**

```bash
git add src/index.css
git commit -m "style: button forest-green gradient primary, ghost with green border"
```

---

## Task 5: Login Page — Split Layout with Stats Panel

**Files:**
- Modify: `frontend/src/pages/Login.tsx` (full rewrite of JSX + add Framer Motion)
- Modify: `frontend/src/index.css` (login section)

- [ ] **Step 1: Install Framer Motion import in Login.tsx**

Replace the entire contents of `frontend/src/pages/Login.tsx` with:

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
          {/* Logo */}
          <div className="login-logo">
            <div className="login-logo-mark">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
              </svg>
            </div>
            <span className="login-logo-name">DeepScan</span>
          </div>

          {/* Tagline */}
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

          {/* Stat cards */}
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
              <input
                id="u"
                type="text"
                className="login-input"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
                autoFocus
                required
                placeholder="e.g. admin"
              />
            </div>

            <div className="login-field">
              <label htmlFor="p" className="login-label">Password</label>
              <input
                id="p"
                type="password"
                className="login-input"
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            <AnimatePresence>
              {error && (
                <motion.p
                  className="login-error"
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>

            <button type="submit" className="login-submit">Continue →</button>
          </form>

          {/* Role hints */}
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

- [ ] **Step 2: Add Login CSS to index.css**

Find the existing login styles (search for `.login-outer`) and replace the entire login section with:

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
  background: linear-gradient(160deg, #e8f0ea 0%, #f9f8f4 55%, #eef5ef 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.login-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  pointer-events: none;
  animation: orb-drift 10s ease-in-out infinite alternate;
}
.login-orb-1 {
  width: 320px; height: 320px;
  background: radial-gradient(circle, rgba(26,74,46,0.18) 0%, transparent 70%);
  top: -80px; left: -60px;
}
.login-orb-2 {
  width: 280px; height: 280px;
  background: radial-gradient(circle, rgba(45,122,79,0.12) 0%, transparent 70%);
  bottom: -60px; right: -40px;
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

.login-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.login-logo-mark {
  width: 32px; height: 32px;
  background: var(--grad);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
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
.login-stat-unit {
  font-size: 18px;
}
.login-stat-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}
.login-stat-desc {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-top: 2px;
}

/* Right form panel */
.login-right {
  width: 440px;
  flex-shrink: 0;
  background: rgba(255,255,255,0.90);
  border-left: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}

.login-form-wrap {
  width: 100%;
  max-width: 300px;
}

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
  background: rgba(26,74,46,0.04);
  border: 1px solid var(--border-mid);
  border-radius: var(--r-sm);
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--text-primary);
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
}
.login-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(26,74,46,0.10);
}
.login-input::placeholder { color: var(--text-muted); }

.login-error {
  font-size: 12.5px;
  color: var(--fake-color);
  background: var(--fake-dim);
  border: 1px solid rgba(192,57,43,0.20);
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
  opacity: 0.88;
  box-shadow: 0 4px 20px rgba(26,74,46,0.28);
}

.login-divider {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 24px 0 14px;
  color: var(--text-muted);
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.login-divider::before,
.login-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.login-role-pills { display: flex; gap: 8px; }
.login-role-pill {
  flex: 1;
  padding: 10px 12px;
  border-radius: var(--r-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.login-role-pill.admin {
  background: var(--accent-light);
  border: 1px solid rgba(26,74,46,0.20);
}
.login-role-pill.user {
  background: rgba(209,234,217,0.4);
  border: 1px solid rgba(26,74,46,0.12);
}
.login-role-name {
  font-size: 11px;
  font-family: var(--font-mono);
  font-weight: 500;
  color: var(--accent);
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
  .login-right { width: 100%; border-left: none; border-top: 1px solid var(--border); padding: 36px 28px 48px; }
}
```

- [ ] **Step 3: Verify in browser**

Login page should show: left panel with green gradient orbs drifting, "Every frame holds a **secret.**" in gradient shimmer, 3 glass stat cards; right panel with form. Framer Motion fades form up on mount. Error pill appears animated.

- [ ] **Step 4: Commit**

```bash
git add src/pages/Login.tsx src/index.css
git commit -m "feat: login split layout — stats panel, gradient tagline, Framer Motion form"
```

---

## Task 6: Hero Section — Mesh Grid Background + Framer Motion Stagger

**Files:**
- Modify: `frontend/src/pages/Home.tsx`
- Modify: `frontend/src/index.css` (hero section)

- [ ] **Step 1: Update Home.tsx with mesh hero wrapper and Framer Motion stagger**

Replace the entire contents of `frontend/src/pages/Home.tsx` with:

```tsx
import type React from "react";
import { useRef, useState } from "react";
import { motion } from "framer-motion";
import { predictVideo } from "../api/client";
import type { PredictResponse } from "../api/client";
import { FaceScan } from "../components/FaceScan";
import { ResultCard } from "../components/ResultCard";
import { VideoUpload } from "../components/VideoUpload";

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
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<PredictResponse | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const [requestId, setRequestId] = useState("");
  const uploadRef = useRef<HTMLDivElement>(null);

  const handleFile = async (file: File) => {
    setLoading(true);
    setResult(null);
    setError(null);
    try {
      const data = await predictVideo(file);
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

  return (
    <>
      {/* ── Hero ── */}
      <div className="hero-wrap">
        {/* Animated mesh grid background */}
        <div className="hero-bg">
          <div className="hero-bg-grid" />
          <div className="hero-bg-glow" />
          <div className="hero-bg-vignette" />
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
                className="btn btn-primary btn-lg"
                onClick={scroll}
              >
                Analyze a video
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </button>
            </motion.div>
          </motion.div>

          {/* Right: FaceScan */}
          <motion.div
            className="hero-right"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.16,1,0.3,1], delay: 0.2 }}
          >
            <FaceScan />
          </motion.div>
        </div>
      </div>

      {/* ── Analyze ── */}
      <div className="analyze-section" ref={uploadRef}>
        <p className="section-label">Upload &amp; Analyze</p>

        <VideoUpload onFile={handleFile} disabled={loading} />

        {loading && (
          <div className="analyzing-card">
            <div className="analyzing-spinner" />
            <div>
              <p className="analyzing-title">Analyzing video…</p>
              <p className="analyzing-sub">EXTRACTING FRAMES · RUNNING INFERENCE</p>
            </div>
          </div>
        )}

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

        {result && <ResultCard result={result} requestId={requestId} />}
      </div>
    </>
  );
};
```

- [ ] **Step 2: Add/update hero CSS in index.css**

Find the hero section in index.css (search for `.hero-wrap`) and replace all hero rules with:

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
    radial-gradient(ellipse at 50% 0%, #dceede 0%, #f9f8f4 60%),
    linear-gradient(rgba(26,74,46,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(26,74,46,0.06) 1px, transparent 1px);
  background-size: 100% 100%, 40px 40px, 40px 40px;
  animation: grid-pulse 5s ease infinite;
}
.hero-bg-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 40%, rgba(26,74,46,0.14) 0%, transparent 65%);
}
.hero-bg-vignette {
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 50% 50%, transparent 40%, rgba(249,248,244,0.55) 100%);
}

.hero {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  padding: 80px 32px 80px;
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
  background: var(--accent-light);
  border: 1px solid rgba(26,74,46,0.20);
  border-radius: 99px;
  padding: 5px 12px;
  font-size: 10px;
  font-family: var(--font-mono);
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
  width: fit-content;
}

.hero-eyebrow-dot {
  width: 6px;
  height: 6px;
  background: #22c55e;
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

.hero-right {
  display: flex;
  justify-content: center;
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 60px 24px;
    text-align: center;
  }
  .hero-eyebrow { margin: 0 auto; }
  .hero-body { max-width: 100%; }
  .hero-cta { justify-content: center; }
  .hero-right { display: none; }
}
```

- [ ] **Step 3: Verify in browser**

Hero shows cream background with subtle green grid lines pulsing, radial glow at center. Headline staggers in line by line. "deepfakes." word shows green gradient shimmer. FaceScan visible on right.

- [ ] **Step 4: Commit**

```bash
git add src/pages/Home.tsx src/index.css
git commit -m "feat: hero mesh-grid animated bg + Framer Motion text stagger"
```

---

## Task 7: FaceScan Component Recolor

**Files:**
- Modify: `frontend/src/components/FaceScan.tsx`
- Modify: `frontend/src/index.css` (FaceScan styles)

- [ ] **Step 1: Recolor FaceScan.tsx SVG elements**

Replace the entire contents of `frontend/src/components/FaceScan.tsx` with:

```tsx
import type React from "react";

// Face mesh vertices — 440×480 viewBox
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
          <stop offset="0%"   stopColor="#e8f0ea" />
          <stop offset="50%"  stopColor="#dce8de" />
          <stop offset="100%" stopColor="#ccdacc" />
        </radialGradient>
        <radialGradient id="hg" cx="50%" cy="18%" r="52%">
          <stop offset="0%"   stopColor="#d4e0d4" />
          <stop offset="100%" stopColor="#c4d4c4" />
        </radialGradient>
        <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stopColor="#1a4a2e" stopOpacity="0" />
          <stop offset="48%"  stopColor="#1a4a2e" stopOpacity="0.06" />
          <stop offset="50%"  stopColor="#2d7a4f" stopOpacity="0.5" />
          <stop offset="52%"  stopColor="#1a4a2e" stopOpacity="0.06" />
          <stop offset="100%" stopColor="#1a4a2e" stopOpacity="0" />
        </linearGradient>
        <filter id="dg" x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="3" result="b"/>
          <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
        <clipPath id="fc">
          <ellipse cx={CX} cy={CY} rx="108" ry="168" />
        </clipPath>
      </defs>

      {/* Outer ring */}
      <circle cx={CX} cy={CY} r="188"
        stroke="#1a4a2e" strokeOpacity="0.07" strokeWidth="1"
        strokeDasharray="4 6" />
      <circle cx={CX} cy={CY} r="158"
        stroke="#1a4a2e" strokeOpacity="0.12" strokeWidth="0.75" />

      {/* Orbiting mark */}
      <circle r="4" fill="#2d7a4f" fillOpacity="0.7"
        className="face-orbit-dot"
        style={{ filter: "drop-shadow(0 0 6px rgba(26,74,46,0.8))" }} />

      {/* Face volume */}
      <ellipse cx={CX} cy={175} rx="112" ry="140" fill="url(#hg)" />
      <ellipse cx={CX} cy={CY} rx="107" ry="166" fill="url(#fv)" />

      {/* Mesh */}
      {EDGES.map(([a,b],i) => (
        <line key={i}
          x1={V[a][0]} y1={V[a][1]}
          x2={V[b][0]} y2={V[b][1]}
          stroke="#2d7a4f" strokeOpacity="0.15" strokeWidth="0.75"
        />
      ))}

      {/* Dots */}
      {V.map(([x,y],i) => {
        const big = MAJOR.has(i);
        return (
          <circle key={i} cx={x} cy={y}
            r={big ? 3.5 : 2}
            fill="#1a4a2e"
            fillOpacity={big ? 0.55 : 0.28}
            filter={big ? "url(#dg)" : undefined}
            className="face-mesh-dot"
            style={{ animationDelay: `${(i * 0.08) % 2}s` }}
          />
        );
      })}

      {/* Scan beam */}
      <rect x="112" y="-20" width="216" height="32"
        fill="url(#beam)"
        clipPath="url(#fc)"
        className="face-scan-beam"
      />
      <line x1="112" y1="0" x2="328" y2="0"
        stroke="#2d7a4f" strokeWidth="0.75" strokeOpacity="0.7"
        clipPath="url(#fc)"
        className="face-scan-beam"
      />

      {/* Corner marks */}
      <path d="M 28 64 L 28 40 L 52 40" className="face-corner-line" />
      <path d="M 388 40 L 412 40 L 412 64" className="face-corner-line" />
      <path d="M 28 416 L 28 440 L 52 440" className="face-corner-line" />
      <path d="M 388 440 L 412 440 L 412 416" className="face-corner-line" />

      {/* Status */}
      <circle cx="46" cy="24" r="3.5" fill="#1a4a2e" opacity="0.85"
        className="face-mesh-dot" />
      <text x="56" y="28" fontFamily="'JetBrains Mono', monospace" fontSize="9"
        letterSpacing="0.12em" fill="#4a5e4a">BIOMETRIC SCAN · ACTIVE</text>

      <text x="220" y="468" textAnchor="middle"
        fontFamily="'JetBrains Mono', monospace" fontSize="8"
        letterSpacing="0.1em" fill="#4a5e4a" fillOpacity="0.6">
        36 LANDMARKS · CNN+LSTM
      </text>
    </svg>
  </div>
);
```

- [ ] **Step 2: Update FaceScan CSS in index.css**

Find the `.face-wrap` / `.face-corner-line` / `.face-scan-beam` / `.face-orbit-dot` / `.face-mesh-dot` block and replace with:

```css
/* ─── FaceScan ───────────────────────────────────────────── */
.face-wrap {
  width: 100%;
  max-width: 360px;
  opacity: 0.92;
}
.face-wrap svg { width: 100%; height: auto; overflow: visible; }

.face-corner-line {
  stroke: rgba(26,74,46,0.55);
  stroke-width: 1.5;
  fill: none;
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  animation: corner-draw 0.6s ease 0.4s forwards;
}

.face-scan-beam {
  animation: scan-line 2.4s ease-in-out infinite;
}

.face-orbit-dot {
  animation: orbit 5s linear infinite;
  transform-origin: 220px 210px;
}

.face-mesh-dot {
  animation: pulse-dot 2s ease-in-out infinite;
}
```

- [ ] **Step 3: Verify**

FaceScan on Home hero should show forest-green mesh lines, green orbiting dot with glow, green scan beam, and green corner brackets animating in. No amber or dark grey.

- [ ] **Step 4: Commit**

```bash
git add src/components/FaceScan.tsx src/index.css
git commit -m "style: FaceScan recolored to forest green — mesh, beam, orbit dot"
```

---

## Task 8: Upload Zone Styles

**Files:**
- Modify: `frontend/src/index.css` (upload section)
- Modify: `frontend/src/components/VideoUpload.tsx` (add Framer Motion scale on drag-over)

- [ ] **Step 1: Update VideoUpload.tsx to use Framer Motion on drag-over**

Replace the entire contents of `frontend/src/components/VideoUpload.tsx` with:

```tsx
import type React from "react";
import { useCallback, useState } from "react";
import { motion } from "framer-motion";

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export const VideoUpload: React.FC<Props> = ({ onFile, disabled }) => {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = (file: File): string | null => {
    if (!file.name.endsWith(".mp4")) return "Only MP4 files are accepted.";
    if (file.size > 100 * 1024 * 1024) return "File must be under 100 MB.";
    return null;
  };

  const handleFile = useCallback((file: File) => {
    const err = validate(file);
    if (err) { setError(err); return; }
    setError(null);
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
```

- [ ] **Step 2: Update upload CSS in index.css**

Find the upload zone styles (`.upload-zone`) and replace the entire block with:

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
  background: var(--glass-bg);
  border: 1.5px dashed var(--border-mid);
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
  border-color: rgba(26,74,46,0.40);
  border-style: solid;
  background: rgba(26,74,46,0.04);
  box-shadow: 0 0 40px rgba(26,74,46,0.10);
}
.upload-zone.drag-over {
  border-color: rgba(26,74,46,0.6);
  box-shadow: 0 0 60px rgba(26,74,46,0.15);
}
.upload-zone.scanning { pointer-events: none; }

.upload-scan-line {
  position: absolute;
  left: 0; right: 0;
  height: 1.5px;
  background: linear-gradient(90deg, transparent, #1a4a2e, #2d7a4f, #1a4a2e, transparent);
  top: 0;
  opacity: 0;
  pointer-events: none;
}
.upload-zone.scanning .upload-scan-line {
  animation: scan-line 2.4s ease-in-out infinite;
}

.upload-icon-wrap {
  width: 48px; height: 48px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  color: var(--text-secondary);
  transition: color 0.15s, background 0.15s;
}
.upload-zone:hover .upload-icon-wrap,
.upload-zone.drag-over .upload-icon-wrap {
  color: var(--accent);
  background: var(--accent-light);
}

.upload-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}
.upload-hint {
  font-size: 13.5px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.upload-link {
  color: var(--accent);
  font-weight: 500;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.upload-spec {
  font-size: 10.5px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.upload-err {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 14px;
  font-size: 12.5px;
  color: var(--fake-color);
  background: var(--fake-dim);
  border: 1px solid rgba(192,57,43,0.18);
  padding: 8px 12px;
  border-radius: var(--r-sm);
}
```

- [ ] **Step 3: Commit**

```bash
git add src/components/VideoUpload.tsx src/index.css
git commit -m "style: upload zone green hover/scan + Framer Motion drag-scale"
```

---

## Task 9: Result Card — Framer Motion Entrance + Updated Styles

**Files:**
- Modify: `frontend/src/components/ResultCard.tsx`
- Modify: `frontend/src/index.css` (result section)

- [ ] **Step 1: Add Framer Motion to ResultCard.tsx**

Replace the entire contents of `frontend/src/components/ResultCard.tsx` with:

```tsx
import type React from "react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { PredictResponse } from "../api/client";
import { submitFeedback } from "../api/client";

interface Props {
  result: PredictResponse;
  requestId: string;
}

export const ResultCard: React.FC<Props> = ({ result, requestId }) => {
  const isFake  = result.prediction === "fake";
  const pct     = Math.round(result.confidence * 100);
  const cls     = isFake ? "fake" : "real";
  const verdict = isFake ? "DEEPFAKE" : "AUTHENTIC";
  const desc    = isFake
    ? "AI-generated or manipulated content detected in this video."
    : "No manipulation artifacts detected. This video appears authentic.";

  const [feedbackSent, setFeedbackSent] = useState(false);

  const sendFeedback = async (correct: boolean) => {
    const ground_truth: "real" | "fake" = correct
      ? result.prediction
      : result.prediction === "fake" ? "real" : "fake";
    try {
      await submitFeedback({ request_id: requestId, predicted: result.prediction, ground_truth });
      setFeedbackSent(true);
    } catch { /* silent */ }
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
            <div className="conf-fill" style={{ width: `${pct}%` }} />
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
            </div>
          )}

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
        </div>
      </motion.div>
    </AnimatePresence>
  );
};
```

- [ ] **Step 2: Update result card CSS in index.css**

Find the result card styles (`.result`, `.result-hero`, etc.) and replace the entire result section with:

```css
/* ─── Result Card ────────────────────────────────────────── */
.result {
  border-radius: var(--r-xl);
  overflow: hidden;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-lg);
}

.result-hero {
  padding: 28px 28px 24px;
}
.result-hero.fake {
  background: var(--fake-dim);
  border-bottom: 1px solid rgba(192,57,43,0.18);
  animation: pulse-border 2s ease infinite;
}
.result-hero.real {
  background: var(--real-dim);
  border-bottom: 1px solid rgba(26,74,46,0.18);
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
  font-size: 13.5px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.result-body {
  padding: 24px 28px;
  background: var(--glass-bg);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Confidence bar */
.conf-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.conf-label {
  font-size: 11px;
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.conf-pct {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 18px;
  color: var(--text-primary);
}
.conf-track {
  height: 6px;
  background: var(--bg-elevated);
  border-radius: 99px;
  overflow: hidden;
}
.conf-fill {
  height: 100%;
  border-radius: 99px;
  animation: bar-grow 0.9s cubic-bezier(0.25,1,0.5,1) both;
}
.result-body.fake .conf-fill {
  background: linear-gradient(90deg, #c0392b, #e74c3c);
  box-shadow: 0 0 8px rgba(192,57,43,0.4);
}
.result-body.real .conf-fill {
  background: var(--grad);
  box-shadow: 0 0 8px rgba(26,74,46,0.3);
}

/* Meta grid */
.meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.meta-cell {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.meta-cell-label {
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.meta-cell-value {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 22px;
  color: var(--text-primary);
  line-height: 1.1;
}
.meta-cell-unit {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary);
  margin-left: 2px;
}

/* Grad-CAM */
.gradcam-wrap { display: flex; flex-direction: column; gap: 8px; }
.gradcam-label {
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.gradcam-wrap img {
  width: 100%;
  border-radius: var(--r-md);
  border: 1px solid var(--border);
}

/* Feedback */
.feedback-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 4px;
  border-top: 1px solid var(--border);
}
.feedback-q {
  font-size: 13px;
  color: var(--text-secondary);
  flex: 1;
}
.feedback-ok {
  font-size: 13px;
  color: var(--real-color);
}
```

- [ ] **Step 3: Verify**

Upload a test video. Result card springs in with scale animation. Verdict "DEEPFAKE" or "AUTHENTIC" in Syne 800. Fake: red dim header with pulse border. Real: green dim header. Confidence bar grows with animation.

- [ ] **Step 4: Commit**

```bash
git add src/components/ResultCard.tsx src/index.css
git commit -m "feat: result card Framer spring entrance + forest-green AUTHENTIC verdict"
```

---

## Task 10: Analyzing/Error Card + Remaining Page Sections

**Files:**
- Modify: `frontend/src/index.css` (analyzing card, error card, pipeline, admin)

- [ ] **Step 1: Add analyzing/error card styles in index.css**

Find the `.analyzing-card` block and replace through to the pipeline section (or end of file if pipeline styles aren't present) with:

```css
/* ─── Analyzing / Error Cards ────────────────────────────── */
.analyzing-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: var(--glass-bg);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-sm);
}
.analyzing-spinner {
  width: 20px; height: 20px;
  border: 2px solid var(--accent-light);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
.analyzing-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 2px;
}
.analyzing-sub {
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.error-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: var(--fake-dim);
  border: 1px solid rgba(192,57,43,0.20);
  border-radius: var(--r-lg);
  padding: 16px 20px;
}
.error-card-icon { color: var(--fake-color); flex-shrink: 0; margin-top: 1px; }
.error-card-title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--fake-color);
  margin-bottom: 3px;
}
.error-card-msg {
  font-size: 13px;
  color: var(--text-secondary);
}

/* ─── Pipeline Dashboard ─────────────────────────────────── */
.pipeline-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 40px 32px 80px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.pipeline-header h1 {
  font-family: var(--font-display);
  font-weight: 800;
  font-style: italic;
  font-size: 28px;
  letter-spacing: -0.5px;
  color: var(--text-primary);
  margin-bottom: 4px;
}
.pipeline-header p {
  font-size: 13.5px;
  color: var(--text-secondary);
}

.stat-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
.stat-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg);
  padding: 20px;
  transition: box-shadow 0.15s, border-color 0.15s, transform 0.15s;
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-mid);
  transform: translateY(-2px);
}
.stat-card-label {
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.stat-card-value {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 26px;
  color: var(--text-primary);
  line-height: 1.1;
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
  border-radius: var(--r-lg);
  overflow: hidden;
}
.pipeline-table { width: 100%; border-collapse: collapse; }
.pipeline-table th {
  background: var(--bg-elevated);
  padding: 10px 14px;
  text-align: left;
  font-size: 10px;
  font-family: var(--font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}
.pipeline-table td {
  padding: 12px 14px;
  font-size: 13px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border);
}
.pipeline-table tr:last-child td { border-bottom: none; }
.pipeline-table tr:hover td { background: rgba(26,74,46,0.04); }
.pipeline-table .val-gradient {
  background: var(--grad);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-weight: 600;
}

.pipeline-terminal {
  background: #f0ede4;
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  max-height: 280px;
  overflow-y: auto;
  color: var(--text-primary);
}

/* ─── Admin Page ─────────────────────────────────────────── */
.admin-page {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 32px 80px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.admin-page h1 {
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 26px;
  letter-spacing: -0.5px;
  color: var(--text-primary);
}
.admin-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--r-lg);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.admin-card h2 {
  font-family: var(--font-display);
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}
.admin-input {
  width: 100%;
  padding: 9px 12px;
  background: rgba(26,74,46,0.04);
  border: 1px solid var(--border-mid);
  border-radius: var(--r-sm);
  font-family: var(--font-ui);
  font-size: 14px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.admin-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(26,74,46,0.10);
}
.admin-status {
  font-size: 13px;
  padding: 10px 14px;
  border-radius: var(--r-sm);
}
.admin-status.success {
  background: var(--real-dim);
  border: 1px solid rgba(26,74,46,0.18);
  color: var(--real-color);
}
.admin-status.error {
  background: var(--fake-dim);
  border: 1px solid rgba(192,57,43,0.18);
  color: var(--fake-color);
}
```

- [ ] **Step 2: Commit**

```bash
git add src/index.css
git commit -m "style: analyzing/error cards, pipeline table, admin page — forest-green tokens"
```

---

## Task 11: Remove Unused UI Components + App.css Cleanup

**Files:**
- Modify: `frontend/src/App.css` (clear out conflicting styles)

- [ ] **Step 1: Clear App.css**

Read `frontend/src/App.css` to see its contents. If it contains conflicting styles (old color vars, button overrides, etc.), replace the entire file with just:

```css
/* App-level layout */
#root {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}
```

- [ ] **Step 2: Verify no import of background-gradient-animation in active pages**

Check `frontend/src/pages/Home.tsx` — the `background-gradient-animation` import should NOT be present. (It was removed in earlier tasks when Home.tsx was rewritten.) If it appears, remove the import.

Run: `grep -r "background-gradient-animation" frontend/src/pages/`
Expected: no output (no matches).

- [ ] **Step 3: Build check**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npm run build 2>&1 | tail -20
```

Expected: `✓ built in` with no errors. TypeScript errors about missing types are acceptable only if pre-existing.

- [ ] **Step 4: Commit**

```bash
git add src/App.css
git commit -m "style: clear App.css conflicts, confirm bg-gradient unused"
```

---

## Task 12: Final Polish + Smoke Test

**Files:**
- No code changes — verification only

- [ ] **Step 1: Start dev server**

```bash
cd "f:/mlops project/deepfake-detection/frontend"
npm run dev
```

Open `http://localhost:5173` in browser.

- [ ] **Step 2: Login page check**

- [ ] Left panel visible with two green orbs drifting
- [ ] "Every frame holds a **secret.**" with shimmer animation on "secret."
- [ ] Three stat cards with glass border, green gradient numbers
- [ ] Right panel: form fades up on load
- [ ] Submit with wrong password → red error pill animates in
- [ ] Submit with admin/admin123 → redirects to home with Nav

- [ ] **Step 3: Home hero check**

- [ ] Cream background with subtle green grid lines (pulsing opacity)
- [ ] Radial green glow at center
- [ ] Text staggers in (each line 0.08s apart)
- [ ] "deepfakes." shows green gradient shimmer
- [ ] FaceScan on right: green mesh, green beam, green orbit dot
- [ ] Eyebrow chip: green background, pulsing green dot

- [ ] **Step 4: Upload zone check**

- [ ] Glass card with dashed green border
- [ ] Drag a file over: card scales 1.01, border solidifies green
- [ ] Drop an MP4: scan line sweeps green while analyzing

- [ ] **Step 5: Result card check**

- [ ] Card springs in with scale animation
- [ ] FAKE: red dim header, pulse-border shadow, red confidence bar with glow
- [ ] REAL (or test with authentic video): green header, "AUTHENTIC" in forest green, green bar
- [ ] Confidence bar grows with `bar-grow` animation
- [ ] Framer Motion verdict slides in from left

- [ ] **Step 6: Nav check**

- [ ] Admin role: role badge shows "ADMIN" in green pill
- [ ] Active link: green underline
- [ ] Sign out → returns to login

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "style: forest-green/cream UI redesign complete — all smoke tests passing"
```
