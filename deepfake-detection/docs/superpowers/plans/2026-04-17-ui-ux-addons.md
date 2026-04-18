# UI/UX Addons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add five high-impact UI/UX features: global toast notifications, result permalink sharing, personal stats dashboard, confidence trend chart on History page, and animated page transitions.

**Architecture:** All features are pure frontend — no new backend endpoints required. Toast system uses a React context + fixed overlay so any component can trigger it. Stats page reads from the existing `/history` API. Charts use the Canvas API directly (no new deps). Animated transitions wrap `<Routes>` with framer-motion's `AnimatePresence`. Permalink encodes result JSON into a URL hash.

**Tech Stack:** React 18, TypeScript, Vite, framer-motion (already installed), CSS custom properties, Canvas API, Web Crypto / btoa for URL encoding.

---

## File Structure

| File | Action | Purpose |
|---|---|---|
| `frontend/src/components/Toast.tsx` | Create | Toast context, provider, hook, and overlay renderer |
| `frontend/src/index.css` | Modify | Toast styles, stats page styles, chart styles, light-mode overrides |
| `frontend/src/App.tsx` | Modify | Wrap app in `ToastProvider`; wrap `<Routes>` with `AnimatePresence` + route key for transitions |
| `frontend/src/components/ResultCard.tsx` | Modify | Add "Copy link" button that encodes result to URL hash and fires toast |
| `frontend/src/pages/Home.tsx` | Modify | Read URL hash on mount and pre-populate result if present (permalink restore) |
| `frontend/src/pages/Stats.tsx` | Create | Personal dashboard: totals, fake/real donut, avg confidence, analyses this week |
| `frontend/src/pages/History.tsx` | Modify | Add confidence-over-time sparkline chart above the table |

---

## Task 1: Toast notification system

**Files:**
- Create: `frontend/src/components/Toast.tsx`
- Modify: `frontend/src/index.css` (toast styles)
- Modify: `frontend/src/App.tsx` (wrap with ToastProvider)

- [ ] **Step 1: Create `Toast.tsx`**

```tsx
// frontend/src/components/Toast.tsx
import React, { createContext, useCallback, useContext, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastCtx {
  toast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastCtx>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

let _id = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: ToastType = "success") => {
    const id = ++_id;
    setToasts((t) => [...t, { id, message, type }]);
    setTimeout(() => {
      setToasts((t) => t.filter((x) => x.id !== id));
    }, 3500);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="toast-stack" aria-live="polite">
        <AnimatePresence>
          {toasts.map((t) => (
            <motion.div
              key={t.id}
              className={`toast toast--${t.type}`}
              initial={{ opacity: 0, y: 24, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.96 }}
              transition={{ type: "spring", stiffness: 340, damping: 24 }}
            >
              {t.type === "success" && (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              )}
              {t.type === "error" && (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
              )}
              {t.type === "info" && (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
              )}
              <span>{t.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
```

- [ ] **Step 2: Add toast CSS to `index.css`**

Add this block anywhere after the chatbot styles (around line 1750):

```css
/* ─── Toast notifications ──────────────────────────────────── */
.toast-stack {
  position: fixed;
  bottom: 88px; /* above chatbot FAB */
  right: 24px;
  z-index: 900;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 10px;
  font-size: 13.5px;
  font-weight: 500;
  font-family: var(--font-ui);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 4px 24px rgba(0,0,0,0.35), 0 1px 0 rgba(255,255,255,0.06) inset;
  pointer-events: all;
  max-width: 320px;
  line-height: 1.4;
}

.toast--success {
  background: rgba(26,92,53,0.90);
  border: 1px solid rgba(52,168,90,0.35);
  color: #d1fae5;
}
.toast--error {
  background: rgba(127,29,29,0.90);
  border: 1px solid rgba(248,113,113,0.35);
  color: #fee2e2;
}
.toast--info {
  background: rgba(13,15,13,0.88);
  border: 1px solid rgba(255,255,255,0.12);
  color: var(--text-primary);
}

[data-theme="light"] .toast--success {
  background: rgba(240,253,244,0.97);
  border-color: rgba(22,101,52,0.25);
  color: #166534;
  box-shadow: 0 4px 24px rgba(0,0,0,0.12);
}
[data-theme="light"] .toast--error {
  background: rgba(254,242,242,0.97);
  border-color: rgba(220,38,38,0.25);
  color: #991b1b;
  box-shadow: 0 4px 24px rgba(0,0,0,0.12);
}
[data-theme="light"] .toast--info {
  background: rgba(255,255,255,0.97);
  border-color: rgba(0,0,0,0.12);
  color: #111827;
  box-shadow: 0 4px 24px rgba(0,0,0,0.12);
}
```

- [ ] **Step 3: Wrap app with `ToastProvider` in `App.tsx`**

In `frontend/src/App.tsx`, add the import and wrap `<AuthProvider>`:

```tsx
import { ToastProvider } from "./components/Toast";

// inside App():
return (
  <BrowserRouter>
    <ToastProvider>
      <AuthProvider>
        <AppShell />
      </AuthProvider>
    </ToastProvider>
  </BrowserRouter>
);
```

- [ ] **Step 4: Verify toast renders — add a temporary test call**

In `AppShell`, temporarily add after `<Nav />`:
```tsx
// TEMP — remove after verifying
React.useEffect(() => { toast("Toast system working!"); }, []);
```
Import `useToast` and call it. Run `npm run dev` in the frontend directory. Confirm toast appears bottom-right and auto-dismisses after 3.5s. Then remove the temporary code.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/Toast.tsx frontend/src/index.css frontend/src/App.tsx
git commit -m "feat: add global toast notification system"
```

---

## Task 2: Result permalink (share link)

**Files:**
- Modify: `frontend/src/components/ResultCard.tsx` (add "Copy link" button, use toast)
- Modify: `frontend/src/pages/Home.tsx` (read hash on mount, restore result)

The permalink encodes the `PredictResponse` as base64 JSON in the URL hash: `/#result=<base64>`. No backend needed — the result is self-contained.

- [ ] **Step 1: Add permalink encode/decode helpers inline in `ResultCard.tsx`**

At the top of `ResultCard.tsx`, after imports, add:

```tsx
function encodeResult(result: PredictResponse): string {
  // Exclude gradcam_image (too large for URL); include everything else
  const { gradcam_image: _, ...slim } = result;
  return btoa(JSON.stringify(slim));
}
```

- [ ] **Step 2: Add "Copy link" button to `ResultCard.tsx`**

Import `useToast`:
```tsx
import { useToast } from "./Toast";
```

Inside the component body, add:
```tsx
const { toast } = useToast();

const copyLink = () => {
  const encoded = encodeResult(result);
  const url = `${window.location.origin}/#result=${encoded}`;
  navigator.clipboard.writeText(url).then(() => {
    toast("Link copied to clipboard!", "success");
  }).catch(() => {
    toast("Could not copy — try manually: " + url, "error");
  });
};
```

Add the button inside `result-body`, right after the download report button div:

```tsx
<div className="report-wrap" style={{ marginTop: "8px" }}>
  <button type="button" className="btn btn-ghost report-btn" onClick={copyLink}>
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/>
      <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>
    </svg>
    Copy Link
  </button>
</div>
```

- [ ] **Step 3: Restore result from URL hash in `Home.tsx`**

In `frontend/src/pages/Home.tsx`, add a `useEffect` after the existing state declarations:

```tsx
// Restore permalink result from URL hash on mount
useEffect(() => {
  const hash = window.location.hash;
  const match = hash.match(/[#&]result=([^&]+)/);
  if (!match) return;
  try {
    const decoded = JSON.parse(atob(match[1]));
    // Restore as PredictResponse — gradcam_image will be empty string
    setResult({ gradcam_image: "", ...decoded });
    setRequestId(crypto.randomUUID());
    // Clean up the hash so sharing again produces a fresh URL
    window.history.replaceState(null, "", window.location.pathname);
  } catch {
    // malformed hash — ignore silently
  }
}, []);
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ResultCard.tsx frontend/src/pages/Home.tsx
git commit -m "feat: add result permalink copy-link sharing"
```

---

## Task 3: Animated page transitions

**Files:**
- Modify: `frontend/src/App.tsx` (wrap Routes with AnimatePresence)
- Modify: `frontend/src/index.css` (page-transition class)

framer-motion's `AnimatePresence` is already installed. The approach: wrap `<Routes>` with `AnimatePresence`, and each route renders a `motion.div` wrapper. To avoid adding `motion.div` to every page component, we use a `PageWrap` wrapper component inside `AppShell`.

- [ ] **Step 1: Add `AnimatePresence` import and `PageWrap` to `App.tsx`**

Add to imports:
```tsx
import { AnimatePresence, motion } from "framer-motion";
```

Add this component above `AppShell`:
```tsx
const pageVariants = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.32, ease: [0.16, 1, 0.3, 1] } },
  exit:    { opacity: 0, y: -8, transition: { duration: 0.18, ease: [0.4, 0, 1, 1] } },
};

function PageWrap({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {children}
    </motion.div>
  );
}
```

- [ ] **Step 2: Wrap Routes with AnimatePresence in `AppShell`**

Replace the Routes block in `AppShell`:

```tsx
function AppShell() {
  const { role } = useAuth();
  const location = useLocation();
  if (!role) return <Login />;

  return (
    <>
      <Nav />
      <ChatBot />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<PageWrap><Home /></PageWrap>} />
          <Route path="/help" element={<PageWrap><Help /></PageWrap>} />
          <Route path="/history" element={<PageWrap><History /></PageWrap>} />
          <Route path="/batch" element={<PageWrap><Batch /></PageWrap>} />
          <Route path="/model" element={<PageWrap><ModelCard /></PageWrap>} />
          <Route path="/stats" element={<PageWrap><Stats /></PageWrap>} />
          <Route path="/pipeline" element={<AdminRoute><PageWrap><PipelineDashboard /></PageWrap></AdminRoute>} />
          <Route path="/admin"    element={<AdminRoute><PageWrap><Admin /></PageWrap></AdminRoute>} />
          <Route path="/tickets"  element={<AdminRoute><PageWrap><TicketAdmin /></PageWrap></AdminRoute>} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </>
  );
}
```

Note: `useLocation` is already imported from react-router-dom. Add `Stats` import (created in Task 4).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: add animated page transitions with framer-motion"
```

---

## Task 4: Personal stats dashboard (`/stats`)

**Files:**
- Create: `frontend/src/pages/Stats.tsx`
- Modify: `frontend/src/App.tsx` (add `/stats` route + nav link)
- Modify: `frontend/src/index.css` (stats page styles)

Stats are derived entirely from the existing `GET /history` API — no new backend endpoint.

- [ ] **Step 1: Create `Stats.tsx`**

```tsx
// frontend/src/pages/Stats.tsx
import type React from "react";
import { useEffect, useState } from "react";
import { fetchHistory } from "../api/client";
import type { HistoryRecord } from "../api/client";
import { useAuth } from "../auth/AuthContext";

function msAgo(ms: number) {
  if (ms < 60_000) return `${Math.round(ms / 1000)}s ago`;
  if (ms < 3_600_000) return `${Math.round(ms / 60_000)}m ago`;
  if (ms < 86_400_000) return `${Math.round(ms / 3_600_000)}h ago`;
  return `${Math.round(ms / 86_400_000)}d ago`;
}

export const Stats: React.FC = () => {
  const { username } = useAuth();
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!username) return;
    fetchHistory(username)
      .then(setRecords)
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) return <div className="page-wrap"><p className="history-loading">Loading stats…</p></div>;

  const total = records.length;
  const fakeCount = records.filter((r) => r.prediction === "fake").length;
  const realCount = total - fakeCount;
  const avgConf = total === 0 ? 0 : Math.round(records.reduce((s, r) => s + r.confidence, 0) / total * 100);
  const avgLatency = total === 0 ? 0 : Math.round(records.reduce((s, r) => s + r.inference_latency_ms, 0) / total);

  const now = Date.now();
  const thisWeek = records.filter((r) => now - new Date(r.timestamp).getTime() < 7 * 86_400_000).length;

  const lastAnalysis = records[0]
    ? msAgo(now - new Date(records[0].timestamp).getTime())
    : "—";

  // Donut SVG helper
  const fakeRatio = total === 0 ? 0 : fakeCount / total;
  const CIRC = 2 * Math.PI * 36; // r=36
  const fakeDash = fakeRatio * CIRC;
  const realDash = CIRC - fakeDash;

  return (
    <div className="page-wrap">
      <h1 className="page-title">Your Stats</h1>
      <p className="page-sub">Personal usage summary based on your last 50 analyses.</p>

      {total === 0 ? (
        <div className="stats-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3">
            <path d="M18 20V10M12 20V4M6 20v-6"/>
          </svg>
          <p>No analyses yet. Upload a video to see your stats.</p>
        </div>
      ) : (
        <>
          {/* KPI row */}
          <div className="stats-kpi-row">
            <div className="stats-kpi">
              <span className="stats-kpi-value">{total}</span>
              <span className="stats-kpi-label">Total analyses</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{thisWeek}</span>
              <span className="stats-kpi-label">This week</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{avgConf}%</span>
              <span className="stats-kpi-label">Avg confidence</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{avgLatency}ms</span>
              <span className="stats-kpi-label">Avg latency</span>
            </div>
            <div className="stats-kpi">
              <span className="stats-kpi-value">{lastAnalysis}</span>
              <span className="stats-kpi-label">Last analysis</span>
            </div>
          </div>

          {/* Donut + breakdown */}
          <div className="stats-donut-wrap">
            <svg className="stats-donut" viewBox="0 0 88 88" width="120" height="120">
              <circle cx="44" cy="44" r="36" fill="none" stroke="var(--bg-elevated)" strokeWidth="10"/>
              {/* Real segment */}
              <circle
                cx="44" cy="44" r="36" fill="none"
                stroke="var(--real-color)" strokeWidth="10"
                strokeDasharray={`${realDash} ${fakeDash}`}
                strokeDashoffset={CIRC * 0.25}
                strokeLinecap="round"
              />
              {/* Fake segment */}
              <circle
                cx="44" cy="44" r="36" fill="none"
                stroke="var(--fake-color)" strokeWidth="10"
                strokeDasharray={`${fakeDash} ${realDash}`}
                strokeDashoffset={CIRC * 0.25 - realDash}
                strokeLinecap="round"
              />
              <text x="44" y="48" textAnchor="middle" className="stats-donut-label" fontSize="12" fill="var(--text-primary)" fontWeight="600">
                {total}
              </text>
              <text x="44" y="58" textAnchor="middle" fontSize="7" fill="var(--text-muted)">
                total
              </text>
            </svg>
            <div className="stats-legend">
              <div className="stats-legend-item">
                <span className="stats-legend-dot" style={{ background: "var(--fake-color)" }} />
                <span>{fakeCount} deepfake{fakeCount !== 1 ? "s" : ""} ({total === 0 ? 0 : Math.round(fakeRatio * 100)}%)</span>
              </div>
              <div className="stats-legend-item">
                <span className="stats-legend-dot" style={{ background: "var(--real-color)" }} />
                <span>{realCount} authentic ({total === 0 ? 0 : Math.round((1 - fakeRatio) * 100)}%)</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
```

- [ ] **Step 2: Add stats CSS to `index.css`**

Add after the history styles (after `.history-badge.real` block, around line 1955):

```css
/* ─── Stats page ────────────────────────────────────────────── */
.stats-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 0;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.stats-kpi-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 32px;
}

.stats-kpi {
  flex: 1 1 120px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stats-kpi-value {
  font-size: 1.6rem;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--text-primary);
  letter-spacing: -0.02em;
}

.stats-kpi-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 500;
}

.stats-donut-wrap {
  display: flex;
  align-items: center;
  gap: 28px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 24px 28px;
  max-width: 360px;
}

.stats-donut { flex-shrink: 0; }

.stats-legend { display: flex; flex-direction: column; gap: 10px; }

.stats-legend-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.85rem; color: var(--text-secondary);
}

.stats-legend-dot {
  width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0;
}

[data-theme="light"] .stats-kpi {
  background: #ffffff;
  border-color: rgba(0,0,0,0.08);
}
[data-theme="light"] .stats-donut-wrap {
  background: #ffffff;
  border-color: rgba(0,0,0,0.08);
}
```

- [ ] **Step 3: Add `/stats` route and nav link**

In `App.tsx`, add the import:
```tsx
import { Stats } from "./pages/Stats";
```

Add the nav link (after the `Model` link):
```tsx
<Link to="/stats" className={`nav-link ${pathname === "/stats" ? "active" : ""}`}>Stats</Link>
```

The route is already planned in Task 3's `AppShell` block. Verify it's present.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/Stats.tsx frontend/src/index.css frontend/src/App.tsx
git commit -m "feat: add personal stats dashboard at /stats"
```

---

## Task 5: Confidence trend sparkline on History page

**Files:**
- Modify: `frontend/src/pages/History.tsx` (add canvas sparkline above table)
- Modify: `frontend/src/index.css` (sparkline wrapper styles)

Use the Canvas API — no charting library. The chart draws a confidence-over-time line for the last 50 records (oldest left, newest right). Points are colored by prediction (green = real, red = fake).

- [ ] **Step 1: Add sparkline component inline in `History.tsx`**

Add this component at the top of `History.tsx`, before the `History` function:

```tsx
import { useEffect, useRef } from "react";

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
    const yOf = (v: number) => PAD.top + (1 - v) * cH; // confidence 0-1

    // Grid lines at 25%, 50%, 75%, 100%
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
      <canvas ref={canvasRef} className="sparkline-canvas" />
      <div className="sparkline-legend">
        <span className="sparkline-legend-dot" style={{ background: "#f87171" }} /> Deepfake
        <span className="sparkline-legend-dot" style={{ background: "#34a85a", marginLeft: 12 }} /> Authentic
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Render `ConfidenceChart` in `History` component**

Inside the `History` function's return, add the chart right before the `history-table-wrap` div:

```tsx
{records.length > 0 && <ConfidenceChart records={records} />}

{records.length > 0 && (
  <div className="history-table-wrap">
    ...
  </div>
)}
```

Also update the imports at the top of `History.tsx`:

```tsx
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { fetchHistory } from "../api/client";
import type { HistoryRecord } from "../api/client";
```

- [ ] **Step 3: Add sparkline CSS to `index.css`**

Add after the stats styles:

```css
/* ─── Sparkline chart ───────────────────────────────────────── */
.sparkline-wrap {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 16px 20px 12px;
  margin-bottom: 20px;
}

.sparkline-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.sparkline-canvas {
  display: block;
  width: 100%;
  height: 120px;
  border-radius: 6px;
}

.sparkline-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.sparkline-legend-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

[data-theme="light"] .sparkline-wrap {
  background: #ffffff;
  border-color: rgba(0,0,0,0.08);
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/History.tsx frontend/src/index.css
git commit -m "feat: add confidence trend sparkline chart to history page"
```

---

## Self-Review

**Spec coverage:**
1. ✅ Toast system — `Toast.tsx` + `ToastProvider` wrapping app, CSS styles, `useToast` hook
2. ✅ Result permalink — `encodeResult` + `copyLink` in `ResultCard.tsx`, hash restore in `Home.tsx`, fires toast
3. ✅ Animated page transitions — `AnimatePresence` + `PageWrap` in `AppShell`, `mode="wait"`, keyed by `location.pathname`
4. ✅ Stats dashboard — `Stats.tsx` with KPI cards + donut SVG, `/stats` route + nav link, CSS
5. ✅ Confidence sparkline — `ConfidenceChart` canvas component in `History.tsx`, gradient + colored dots, CSS

**Placeholder scan:** No TBD/TODO found. All code blocks are complete.

**Type consistency:**
- `HistoryRecord` type imported from `api/client` in both `History.tsx` and `Stats.tsx` ✅
- `PredictResponse` imported from `api/client` in `ResultCard.tsx` ✅
- `ToastType` and `useToast` exported from `Toast.tsx` and consumed in `ResultCard.tsx` ✅
- `PageWrap` is defined in `App.tsx` and used only in `App.tsx` ✅
- `ConfidenceChart` props use `HistoryRecord[]` matching the `records` state type ✅
