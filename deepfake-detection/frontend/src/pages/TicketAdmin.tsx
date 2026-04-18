import { useEffect, useState } from "react";
import { fetchTickets, resolveTicket, type Ticket } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function TicketAdmin() {
  const { role, username } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState<string | null>(null);
  const [resolution, setResolution] = useState<Record<string, string>>({});
  const [filter, setFilter] = useState<"all" | "open" | "resolved">("open");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTickets(role ?? "user", username)
      .then(setTickets)
      .catch(() => setError("Failed to load tickets. Please refresh."))
      .finally(() => setLoading(false));
  }, [role, username]);

  const handleResolve = async (ticketId: string) => {
    const text = resolution[ticketId]?.trim();
    if (!text) return;
    setResolving(ticketId);
    try {
      const updated = await resolveTicket(ticketId, text, role ?? "admin");
      setTickets((ts) => ts.map((t) => (t.id === updated.id ? updated : t)));
    } catch {
      setError("Failed to resolve ticket. Please try again.");
    } finally {
      setResolving(null);
    }
  };

  const displayed = tickets.filter((t) => filter === "all" || t.status === filter);

  return (
    <main className="ticket-admin-page">
      <div className="ticket-admin-header">
        <h1 className="ticket-admin-title">Support Tickets</h1>
        <div className="ticket-filter-row">
          {(["all", "open", "resolved"] as const).map((f) => (
            <button
              key={f}
              type="button"
              className={`ticket-filter-btn ${filter === f ? "active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
              {f !== "all" && (
                <span className="ticket-filter-count">
                  {tickets.filter((t) => t.status === f).length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="ticket-admin-loading">Loading tickets…</p>}
      {error && <p className="ticket-admin-error">{error}</p>}

      {!loading && displayed.length === 0 && (
        <div className="ticket-admin-empty">
          No {filter === "all" ? "" : filter} tickets.
        </div>
      )}

      <div className="ticket-list">
        {displayed.map((t) => (
          <div key={t.id} className={`ticket-card ticket-card--${t.status}`}>
            <div className="ticket-card-top">
              <div>
                <span className="ticket-id">{t.id}</span>
                <span className={`ticket-status-badge ticket-status-badge--${t.status}`}>
                  {t.status}
                </span>
              </div>
              <span className="ticket-meta">
                {t.username} · {new Date(t.created_at).toLocaleDateString()}
              </span>
            </div>

            <h3 className="ticket-subject">{t.subject}</h3>
            <p className="ticket-description">{t.description}</p>

            {t.status === "resolved" && (
              <div className="ticket-resolution-box">
                <span className="ticket-resolution-label">Resolution:</span> {t.resolution}
              </div>
            )}

            {t.status === "open" && role === "admin" && (
              <div className="ticket-resolve-row">
                <input
                  className="ticket-input"
                  type="text"
                  placeholder="Enter resolution…"
                  value={resolution[t.id] ?? ""}
                  onChange={(e) =>
                    setResolution((r) => ({ ...r, [t.id]: e.target.value }))
                  }
                />
                <button
                  type="button"
                  className="ticket-btn-primary"
                  disabled={!resolution[t.id]?.trim() || resolving === t.id}
                  onClick={() => handleResolve(t.id)}
                >
                  {resolving === t.id ? "Resolving…" : "Resolve"}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}
