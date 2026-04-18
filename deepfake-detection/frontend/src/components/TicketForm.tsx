import { useState } from "react";
import { submitTicket } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface Props {
  onClose: () => void;
}

export function TicketForm({ onClose }: Props) {
  const { username } = useAuth();
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [ticketId, setTicketId] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    try {
      const ticket = await submitTicket(subject, description, username);
      setTicketId(ticket.id);
      setStatus("success");
    } catch {
      setStatus("error");
    }
  };

  if (status === "success") {
    return (
      <div className="ticket-modal-overlay" onClick={onClose}>
        <div className="ticket-modal" onClick={(e) => e.stopPropagation()}>
          <div className="ticket-success">
            <div className="ticket-success-icon">✓</div>
            <h3>Ticket Submitted</h3>
            <p>Your ticket <strong>{ticketId}</strong> has been created. Our team will respond shortly.</p>
            <button type="button" className="ticket-btn-primary" onClick={onClose}>Done</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="ticket-modal-overlay" onClick={onClose}>
      <div className="ticket-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ticket-header">
          <h3>Report an Issue</h3>
          <button type="button" className="ticket-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <form onSubmit={handleSubmit} className="ticket-form">
          <label className="ticket-label" htmlFor="subject">Subject</label>
          <input
            id="subject"
            className="ticket-input"
            type="text"
            placeholder="Short summary of the issue"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
            minLength={1}
          />

          <label className="ticket-label" htmlFor="description">Description</label>
          <textarea
            id="description"
            className="ticket-textarea"
            placeholder="Describe what happened, what you expected, and any error messages you saw"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            minLength={1}
            rows={5}
          />

          {status === "error" && (
            <p className="ticket-error">Failed to submit ticket. Please try again.</p>
          )}

          <div className="ticket-actions">
            <button type="button" className="ticket-btn-secondary" onClick={onClose}>Cancel</button>
            <button type="submit" className="ticket-btn-primary" disabled={status === "loading"}>
              {status === "loading" ? "Submitting…" : "Submit Ticket"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
