# DeepScan UI Redesign — Implementation Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current bland light-UI with a dramatic glass/gradient aesthetic — vivid, animated, stunning — while preserving all existing functionality (auth, predict, pipeline, admin).

**Architecture:** Pure CSS + Framer Motion (already installed). No new dependencies except two Google Fonts. All logic stays in existing files; only `index.css`, `index.html`, and component JSX/TSX change.

**Tech Stack:** React 19, Framer Motion 11, Tailwind (utility fallback), CSS custom properties, Google Fonts (Syne + Plus Jakarta Sans + JetBrains Mono via CDN)

**Color Direction:** Dark dramatic glass — near-black base with **forest green** accent gradient replacing the original violet/rose. Everything else (dark backgrounds, glass cards, bright accents, animations) stays from the original dramatic spec.

---

## Design Tokens

```css
/* Background palette */
--bg-deep:     #0d0f0d          /* near-black with green undertone */
--bg-mid:      #111a13          /* card surface */
--bg-elevated: #182019          /* hover/elevated */

/* Glass surfaces */
--glass-bg:    rgba(255,255,255,0.05)
--glass-border:rgba(255,255,255,0.08)
--glass-hover: rgba(255,255,255,0.08)

/* Accent gradient — Forest Green */
--grad-start:  #1a5c35          /* deep forest green */
--grad-end:    #34a85a          /* vivid emerald */
--grad:        linear-gradient(135deg, #1a5c35, #34a85a)

/* Text */
--text-primary:  #ffffff
--text-secondary:rgba(255,255,255,0.55)
--text-muted:    rgba(255,255,255,0.28)

/* Semantic */
--fake-color:  #fb7185          /* rose-400 */
--fake-dim:    rgba(251,113,133,0.12)
--real-color:  #4ade80          /* green-400 */
--real-dim:    rgba(74,222,128,0.12)

/* Fonts */
--font-display: 'Syne', sans-serif
--font-ui:      'Plus Jakarta Sans', sans-serif
--font-mono:    'JetBrains Mono', monospace
```

---

## Section 1 — Global Styles (`index.css` + `index.html`)

### Fonts
Load in `index.html` via Google Fonts CDN:
- `Syne` (weights 700,800) — hero headline, verdict text, stat numbers, nav wordmark
- `Plus Jakarta Sans` (weights 300,400,500,600) — all UI body text
- `JetBrains Mono` (weights 400,500) — metadata, badges, code

CDN URL:
```
https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap
```

### Body
```css
body {
  background: var(--bg-deep);
  color: var(--text-primary);
  font-family: var(--font-ui);
}
```

### Keyframe animations required
- `@keyframes grid-pulse` — opacity 0.5→0.8→0.5, 4s ease infinite (grid glow)
- `@keyframes shimmer` — background-position 0%→200%, 3s linear infinite (gradient text shimmer)
- `@keyframes pulse-dot` — box-shadow grows/shrinks, 2s ease infinite (status dot)
- `@keyframes spin` — 360deg, 0.7s linear infinite (loader)
- `@keyframes scan-sweep` — translateY(-100%)→translateY(600px), 2s ease-in-out infinite (upload scanning beam)
- `@keyframes corner-draw` — stroke-dashoffset 40→0, 0.6s ease forwards (face corner brackets)
- `@keyframes fade-up` — opacity 0 + translateY(16px) → 1 + 0, 0.5s (used sparingly for non-Framer elements)
- `@keyframes bar-grow` — width 0→final, 0.9s cubic-bezier(0.25,1,0.5,1) (confidence bar)
- `@keyframes orb-drift` — translate + scale, 10s ease-in-out infinite alternate (login bg orbs)
- `@keyframes orbit` — 360deg around center point, 5s linear infinite (FaceScan orbit dot)

---

## Section 2 — Navigation

**File:** `src/App.tsx` (Nav component) + `index.css`

### Layout
- Height: 56px, sticky top, `z-index: 200`
- Background: `rgba(13,15,13,0.85)` + `backdrop-filter: blur(20px)` + `saturate(180%)`
- Bottom border: `1px solid rgba(255,255,255,0.07)`
- Padding: `0 32px`

### Logo mark
- 28×28px, `background: var(--grad)`, border-radius 8px, shield icon in white
- Wordmark "DeepScan" in Syne 700

### Nav links
- Color: `var(--text-secondary)`, transition to white on hover
- Active: gradient underline `2px`, text white
- Admin-only links (Pipeline, Admin) hidden for user role

### Nav right
- Role badge: `rgba(26,92,53,0.20)` bg, `rgba(52,168,90,0.35)` border, `#4ade80` text, Mono font 10px uppercase
- Username in `var(--text-secondary)`
- Sign out: ghost button, border `rgba(255,255,255,0.12)`, hover `rgba(255,255,255,0.08)` bg

---

## Section 3 — Login Page

**File:** `src/pages/Login.tsx` + styles in `index.css`

### Layout: Full-viewport split (50/50 on desktop, stacked on mobile)

#### Left panel — Stats & Branding
- Background: `radial-gradient(ellipse at 30% 30%, #0d3318 0%, #0d0f0d 65%)`
- Two animated orbs (forest green top-left, emerald bottom-right) — `position:absolute`, blurred radial gradients, slow `orb-drift` via CSS keyframes
- **Top:** Logo row (gradient mark + "DeepScan" in Syne 700)
- **Middle:** Tagline in Syne 800, ~28px: `"Every frame holds a secret."` — "secret" in gradient text (`shimmer` animation)
- Body text in Plus Jakarta Sans, muted: CNN+LSTM description
- **Bottom:** 3 glass stat cards stacked:
  - `99%` — Detection Rate / on SDFVD test set
  - `~2s` — Inference Time / per video analysis
  - `30` — Frames Sampled / CNN feature extraction
  - Each: `rgba(255,255,255,0.05)` bg, `rgba(255,255,255,0.08)` border, 10px border-radius, gradient value number

#### Right panel — Form
- Background: `rgba(13,15,13,0.95)`
- Left border: `1px solid rgba(255,255,255,0.06)`
- Centered in panel, max-width 320px

**Form elements:**
- Title "Welcome back" in Syne 700, 24px
- Subtitle "Sign in to your account" muted
- Fields: dark glass inputs (`rgba(255,255,255,0.05)` bg, `rgba(255,255,255,0.10)` border), on focus: border `rgba(52,168,90,0.6)` + `box-shadow: 0 0 0 3px rgba(52,168,90,0.15)`
- Labels: mono uppercase 9px muted
- **Submit button:** full-width, `background: var(--grad)`, border-radius 10px, Syne 700, hover: `opacity 0.9` + `box-shadow: 0 0 24px rgba(52,168,90,0.4)`
- Divider "ACCOUNTS" with lines
- Two role hint pills: Admin (forest green) / User (dark glass)

**Framer Motion:** Form fades up on mount (`initial: {opacity:0, y:20}`, `animate: {opacity:1, y:0}`, `transition: {duration:0.5, ease:[0.16,1,0.3,1]}`)

**Error state:** Red glass banner (`var(--fake-dim)` bg, rose border), slides in from top with Framer Motion

---

## Section 4 — Home Page

**File:** `src/pages/Home.tsx` + components

### 4a — Hero Section

**Background: Mesh Grid + Glow**
- Base: `radial-gradient(ellipse at 50% 0%, #0d2e18 0%, #0d0f0d 60%)`
- Grid layer: `background-image: linear-gradient(rgba(52,168,90,0.07) 1px, transparent 1px), linear-gradient(90deg, rgba(52,168,90,0.07) 1px, transparent 1px)`, `background-size: 40px 40px`
- Center radial glow: `radial-gradient(ellipse at 50% 40%, rgba(26,92,53,0.25) 0%, transparent 65%)` — subtle `grid-pulse` animation
- Full viewport height on desktop

**Hero content layout:** 2-column grid (text left, FaceScan right)

**Left — text:**
- Eyebrow chip: glass pill, pulsing green dot + "Model active · CNN+LSTM" in mono uppercase, `#4ade80` text
- Headline in Syne 800, `clamp(42px, 5vw, 68px)`, line-height 1.0:
  - Line 1: "Detect" (white)
  - Line 2: "deepfakes." (gradient text with shimmer animation)
  - Line 3: "instantly." (white)
- Body text: Plus Jakarta Sans 16px, `var(--text-secondary)`, max-width 420px
- CTA button: `background: var(--grad)`, large (14px, padding 12px 28px), border-radius 10px, Syne 700, arrow icon, hover glow shadow
- Framer Motion stagger: `{opacity:0,y:24}→{opacity:1,y:0}` with 0.08s between children

**Right — FaceScan:**
- Recolor all mesh/dots to `#34a85a` (vivid emerald)
- Scan beam: forest green → emerald gradient
- Orbiting dot: `var(--grad)` fill + green drop-shadow glow
- Corner brackets: `stroke: rgba(52,168,90,0.7)`
- Status dot: emerald with glow
- Face volume gradients: dark green tones (not cream)

### 4b — Upload Section

Below hero, `max-width: 620px`, centered, `padding: 56px 24px 80px`

**Upload zone glass card:**
- Background: `rgba(255,255,255,0.04)`, border: `1.5px dashed rgba(255,255,255,0.12)`, border-radius 20px, padding 52px 32px
- Hover: border solid `rgba(52,168,90,0.4)`, bg `rgba(52,168,90,0.05)`, `box-shadow: 0 0 40px rgba(52,168,90,0.15)`
- Drag-over: border `rgba(52,168,90,0.7)`, stronger glow, card scales to `1.01` via Framer Motion
- Scanning state: green scan line sweeps top-to-bottom

### 4c — Result Card

Use Framer Motion `AnimatePresence` + spring entrance.

**FAKE result:**
- Header bg: `var(--fake-dim)`, border `rgba(251,113,133,0.25)`
- Verdict "DEEPFAKE" in Syne 800, 56px, `#fb7185`
- Pulsing red border glow animation
- Confidence bar: rose gradient

**REAL result:**
- Header bg: `var(--real-dim)`, border `rgba(74,222,128,0.20)`
- Verdict "AUTHENTIC" in Syne 800, 56px, `#4ade80`
- Confidence bar: green gradient

**Body (both):**
- Background `rgba(255,255,255,0.04)`, border `rgba(255,255,255,0.08)`
- Meta grid: 2 glass cells

---

## Section 5 — Pipeline Dashboard

- Page background: `var(--bg-deep)`
- Page header: Syne 800 italic for title
- **Stat cards:** glass `rgba(255,255,255,0.05)` bg, `rgba(255,255,255,0.08)` border, hover lifts. Best val F1 gets gradient text.
- **Table:** dark glass container, header row `rgba(255,255,255,0.04)` bg, row hover `rgba(52,168,90,0.05)`. Val F1 ≥ 0.9 gets gradient text.
- **Terminal:** near-black bg `#060d07`, green/red log colors

---

## Section 6 — Admin Page

Same dark glass card language. Inputs: dark glass style. Buttons: gradient primary, ghost secondary. Status messages in colored glass banners.

---

## Implementation Notes

1. **No new npm packages** — Framer Motion already installed
2. **Font loading** — update `index.html` with Google Fonts CDN for Syne + Plus Jakarta Sans + JetBrains Mono
3. **Framer Motion** — `motion.div` for: hero text stagger, result card entrance, login form mount, upload zone drag state
4. **CSS-only for:** background animations (orbs, grid pulse, shimmer, scan line, corner-draw, pulse-dot)
5. **FaceScan** — replace all dark/amber colors with forest green (`#1a5c35`, `#34a85a`)
6. **Preserve:** All API calls, auth logic, role-based routing, feedback submission, admin reload/rollback
7. **Remove:** all old cream/light-theme tokens from `index.css` (the incorrectly-implemented light theme must be fully replaced)
