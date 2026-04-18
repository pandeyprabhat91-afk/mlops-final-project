import type React from "react";

export interface LogEntry {
  id: string;
  timestamp: string;
  type: "success" | "error" | "warning";
  message: string;
}

interface Props {
  entries: LogEntry[];
}

const TYPE_CLASS: Record<LogEntry["type"], string> = {
  success: "log-success",
  error:   "log-error",
  warning: "log-warn",
};

const TYPE_LABEL: Record<LogEntry["type"], string> = {
  success: "OK ",
  error:   "ERR",
  warning: "WRN",
};

export const ErrorConsole: React.FC<Props> = ({ entries }) => (
  <div className="terminal">
    <div className="terminal-bar">
      <div className="t-dot t-dot-r" />
      <div className="t-dot t-dot-y" />
      <div className="t-dot t-dot-g" />
      <span className="terminal-title">pipeline · console</span>
    </div>
    <div className="terminal-body">
      {entries.length === 0 && (
        <span className="log-empty">No recent pipeline runs.</span>
      )}
      {entries.map((e) => (
        <div key={e.id} className="log-row">
          <span className="log-ts">{e.timestamp.slice(0, 19).replace("T", " ")}</span>
          <span className={TYPE_CLASS[e.type]}>[{TYPE_LABEL[e.type]}]</span>
          <span className="log-txt">{e.message}</span>
        </div>
      ))}
    </div>
  </div>
);
