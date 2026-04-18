import { useState } from "react";
import { TicketForm } from "../components/TicketForm";

const FAQ: { q: string; a: string }[] = [
  {
    q: "What file formats does DeepScan accept?",
    a: "DeepScan accepts MP4 video files only. Maximum file size is 100MB. Other formats (AVI, MOV, MKV) are not supported.",
  },
  {
    q: "How long does analysis take?",
    a: "Most videos are analyzed in 5–30 seconds. Longer videos (>2 minutes) may take up to 60 seconds. The progress indicator will update you in real time.",
  },
  {
    q: "What does the confidence score mean?",
    a: "The confidence score (0–100%) shows how certain the model is about its prediction. A score above 80% indicates high confidence. Scores near 50% mean the video has mixed signals — treat those results with caution.",
  },
  {
    q: "What is the Grad-CAM heatmap?",
    a: "The Grad-CAM heatmap highlights the facial regions the model focused on when making its prediction. Brighter areas had more influence on the result. This helps you understand why the model made its decision.",
  },
  {
    q: "The prediction seems wrong. What should I do?",
    a: "Use the Feedback button on the result card to report incorrect predictions — this helps improve the model over time. If you encounter a technical error (crash, timeout), use the 'Report Issue' button to raise a support ticket.",
  },
  {
    q: "Is my video stored after analysis?",
    a: "No. Uploaded videos are processed in memory and are not saved to disk. Only the extracted frame features are temporarily stored during analysis and discarded immediately after.",
  },
  {
    q: "What is the Pipeline Dashboard?",
    a: "The Pipeline Dashboard (admin only) shows the status of the Airflow data pipeline, recent MLflow training runs, and live Prometheus metrics. It is used by administrators to monitor system health.",
  },
  {
    q: "How do I raise a support ticket?",
    a: "Click the 'Report Issue' button at the bottom of this page. Describe what happened and what you expected. Our team will respond via the admin console.",
  },
];

export function Help() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [showTicket, setShowTicket] = useState(false);

  return (
    <main className="help-page">
      <div className="help-hero">
        <h1 className="help-title">Help & Support</h1>
        <p className="help-subtitle">
          Everything you need to use DeepScan. Can't find your answer?
          Use the chat assistant or raise a ticket below.
        </p>
      </div>

      <section className="help-section">
        <h2 className="help-section-title">Frequently Asked Questions</h2>
        <div className="faq-list">
          {FAQ.map((item, i) => (
            <div
              key={i}
              className={`faq-item ${openIndex === i ? "faq-item--open" : ""}`}
            >
              <button
                type="button"
                className="faq-question"
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                aria-expanded={openIndex === i}
              >
                <span>{item.q}</span>
                <svg
                  className="faq-chevron"
                  width="16" height="16" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" strokeWidth="2.5"
                >
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </button>
              {openIndex === i && (
                <div className="faq-answer">{item.a}</div>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="help-section help-cta-row">
        <div className="help-cta-card">
          <div className="help-cta-icon">💬</div>
          <h3>Ask the AI Assistant</h3>
          <p>Get instant answers from our support bot. Available 24/7 — click the chat button in the bottom right.</p>
        </div>
        <div className="help-cta-card">
          <div className="help-cta-icon">🎫</div>
          <h3>Raise a Support Ticket</h3>
          <p>Experiencing a bug or unexpected behaviour? Submit a ticket and our team will investigate.</p>
          <button
            type="button"
            className="ticket-btn-primary"
            style={{ marginTop: "12px" }}
            onClick={() => setShowTicket(true)}
          >
            Report an Issue
          </button>
        </div>
      </section>

      {showTicket && <TicketForm onClose={() => setShowTicket(false)} />}
    </main>
  );
}
