import React from "react";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ChatBot } from "./components/ChatBot";
import { ToastProvider } from "./components/Toast";
import { Login } from "./pages/Login";
import { Admin } from "./pages/Admin";
import { Home } from "./pages/Home";
import { PipelineDashboard } from "./pages/PipelineDashboard";
import { Help } from "./pages/Help";
import { TicketAdmin } from "./pages/TicketAdmin";
import { History } from "./pages/History";
import { Batch } from "./pages/Batch";
import { ModelCard } from "./pages/ModelCard";
import { Stats } from "./pages/Stats";
import Dashboard from "./pages/Dashboard";
import { AnimatePresence, motion } from "framer-motion";
import "./App.css";

function Nav() {
  const { pathname } = useLocation();
  const { role, username, logout } = useAuth();

  const [theme, setTheme] = React.useState<"dark" | "light">(
    document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark"
  );

  const toggleTheme = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    if (next === "light") {
      document.documentElement.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
    } else {
      document.documentElement.removeAttribute("data-theme");
      localStorage.setItem("theme", "dark");
    }
  };

  return (
    <div className="nav-float-wrap">
      <nav className="nav">
        <Link to="/" className="nav-logo">
          <span className="nav-logo-mark">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <path d="M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-9-5z" />
            </svg>
          </span>
          DeepScan
        </Link>

        <div className="nav-divider" />

        <div className="nav-links">
          <Link to="/" className={`nav-link ${pathname === "/" ? "active" : ""}`}>Analyze</Link>
          <Link to="/batch" className={`nav-link ${pathname === "/batch" ? "active" : ""}`}>Batch</Link>
          <Link to="/stats" className={`nav-link ${pathname === "/stats" ? "active" : ""}`}>Stats</Link>
          <Link to="/history" className={`nav-link ${pathname === "/history" ? "active" : ""}`}>History</Link>
          <Link id="help-nav-link" to="/help" className={`nav-link ${pathname === "/help" ? "active" : ""}`}>Help</Link>
          <Link to="/model" className={`nav-link ${pathname === "/model" ? "active" : ""}`}>Model</Link>
          {role === "admin" && (
            <>
              <Link to="/dashboard" className={`nav-link ${pathname === "/dashboard" ? "active" : ""}`}>Dashboard</Link>
              <Link to="/pipeline"  className={`nav-link ${pathname === "/pipeline"  ? "active" : ""}`}>Pipeline</Link>
              <Link to="/admin"     className={`nav-link ${pathname === "/admin"     ? "active" : ""}`}>Admin</Link>
              <Link to="/tickets"   className={`nav-link ${pathname === "/tickets"   ? "active" : ""}`}>Tickets</Link>
            </>
          )}
        </div>

        <div className="nav-divider" />

        <div className="nav-actions">
          <span className="nav-user-role-pill">{role}</span>
          <span className="nav-username">{username}</span>
          <button
            type="button"
            className="nav-theme-toggle"
            onClick={toggleTheme}
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
              </svg>
            )}
          </button>
          <button type="button" className="nav-signout" onClick={logout}>Sign out</button>
        </div>
      </nav>
    </div>
  );
}

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

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { role } = useAuth();
  return role === "admin" ? <>{children}</> : <Navigate to="/" replace />;
}

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
          <Route path="/dashboard" element={<AdminRoute><PageWrap><Dashboard /></PageWrap></AdminRoute>} />
          <Route path="/pipeline" element={<AdminRoute><PageWrap><PipelineDashboard /></PageWrap></AdminRoute>} />
          <Route path="/admin"    element={<AdminRoute><PageWrap><Admin /></PageWrap></AdminRoute>} />
          <Route path="/tickets"  element={<AdminRoute><PageWrap><TicketAdmin /></PageWrap></AdminRoute>} />
          <Route path="*"         element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AuthProvider>
          <AppShell />
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}

export default App;
