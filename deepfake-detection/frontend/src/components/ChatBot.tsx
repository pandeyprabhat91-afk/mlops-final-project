import { useState, useRef, useEffect } from "react";
import { sendChat } from "../api/client";
import type { ChatReply } from "../api/client";

// ── Message types ────────────────────────────────────────────────────────────

interface BotMessage {
  role: "bot";
  text: string;
  follow_up?: string | null;
  suggestions?: string[] | null;
  // detail + escalate stored so the NEXT user message can trigger them
  detail?: string | null;
  escalate?: boolean;
}

interface UserMessage {
  role: "user";
  text: string;
}

type Message = BotMessage | UserMessage;

// ── Lightweight markdown renderer ────────────────────────────────────────────

function renderMessage(text: string): React.ReactNode {
  const lines = text.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim().startsWith("```")) {
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      nodes.push(
        <pre key={`code-${i}`} className="cm-code-block">
          <code>{codeLines.join("\n")}</code>
        </pre>
      );
      i++;
      continue;
    }

    if (line.trim() === "") {
      if (nodes.length > 0) nodes.push(<div key={`sp-${i}`} className="cm-spacer" />);
      i++;
      continue;
    }

    const bulletMatch = line.match(/^([•\-\*]|\d+\.) (.+)/);
    if (bulletMatch) {
      const isOrdered = /^\d+\./.test(line);
      const items: string[] = [];
      while (i < lines.length && lines[i].match(/^([•\-\*]|\d+\.) (.+)/)) {
        const m = lines[i].match(/^([•\-\*]|\d+\.) (.+)/)!;
        items.push(m[2]);
        i++;
      }
      const Tag = isOrdered ? "ol" : "ul";
      nodes.push(
        <Tag key={`list-${i}`} className="cm-list">
          {items.map((item, idx) => <li key={idx}>{inlineFmt(item)}</li>)}
        </Tag>
      );
      continue;
    }

    nodes.push(<p key={`p-${i}`} className="cm-para">{inlineFmt(line)}</p>);
    i++;
  }

  return <>{nodes}</>;
}

function inlineFmt(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**"))
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`"))
      return <code key={i} className="cm-inline-code">{part.slice(1, -1)}</code>;
    return part;
  });
}

// ────────────────────────────────────────────────────────────────────────────

export function ChatBot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "bot",
      text: "Hi! 👋 I'm the DeepScan support assistant.",
      follow_up: "What can I help you with today?",
      suggestions: ["How do I analyze a video?", "What is DeepScan?", "I have a problem"],
      detail: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Track the last bot turn's detail + escalate so next user message can trigger them
  const lastDetailRef = useRef<string | null>(null);
  const lastEscalateRef = useRef<boolean>(false);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;

    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const reply: ChatReply = await sendChat(text, lastDetailRef.current, lastEscalateRef.current);

      // Update the last-detail context for next turn
      lastDetailRef.current = reply.detail ?? null;
      lastEscalateRef.current = false; // reset; backend already appended escalation to detail

      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: reply.reply,
          follow_up: reply.follow_up,
          suggestions: reply.suggestions,
          detail: reply.detail,
        } as BotMessage,
      ]);
    } catch {
      lastDetailRef.current = null;
      lastEscalateRef.current = false;
      setMessages((m) => [
        ...m,
        {
          role: "bot",
          text: "Sorry, I'm unavailable right now.",
          follow_up: "Please raise a support ticket on the Help page and our team will help you.",
          suggestions: ["How do I raise a ticket?"],
          detail: null,
        } as BotMessage,
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
  };

  return (
    <>
      {!open && (
        <div className="chatbot-help-video-wrap">
          <video
            className="chatbot-help-video"
            autoPlay
            loop
            muted
            playsInline
          >
            <source src="/help_animate.webm" type="video/webm" />
            <source src="/help_animate.mp4" type="video/mp4" />
          </video>
          <span className="chatbot-help-label">Chat for Help</span>
        </div>
      )}
      <div className="chatbot-fab-group">
        <button
          type="button"
          className="chatbot-fab"
          onClick={() => setOpen((o) => !o)}
          aria-label="Open support chat"
        >
          {open ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
            </svg>
          )}
        </button>
      </div>

      {open && (
        <div className="chatbot-window">
          <div className="chatbot-header">
            <span className="chatbot-title">DeepScan Support</span>
            <span className="chatbot-online-dot" />
          </div>

          <div className="chatbot-messages">
            {messages.map((m, i) => (
              <div key={i}>
                {/* Message bubble */}
                <div className={`chatbot-msg chatbot-msg--${m.role}`}>
                  {m.role === "bot" ? renderMessage(m.text) : m.text}
                </div>

                {/* Follow-up question (bot only) */}
                {m.role === "bot" && (m as BotMessage).follow_up && (
                  <div className="chatbot-followup">
                    {(m as BotMessage).follow_up}
                  </div>
                )}

                {/* Quick-reply suggestion chips (bot only, last bot message only) */}
                {m.role === "bot" &&
                  (m as BotMessage).suggestions &&
                  i === messages.length - 1 && (
                    <div className="chatbot-chips">
                      {(m as BotMessage).suggestions!.map((s, si) => (
                        <button
                          key={si}
                          type="button"
                          className="chatbot-chip"
                          onClick={() => send(s)}
                          disabled={loading}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
              </div>
            ))}

            {loading && (
              <div className="chatbot-msg chatbot-msg--bot chatbot-typing">
                <span /><span /><span />
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="chatbot-input-row">
            <textarea
              className="chatbot-input"
              placeholder="Ask a question…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              rows={1}
            />
            <button
              type="button"
              className="chatbot-send"
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              aria-label="Send"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
