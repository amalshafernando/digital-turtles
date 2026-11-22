import type { ReactNode } from "react";

export default function Alert({ kind = "error", title, children, onClose }:
  { kind?: "error" | "success" | "warning" | "info"; title?: string; children?: ReactNode; onClose?: () => void }) {
  const icon = { error: "!", success: "✓", warning: "▲", info: "i" }[kind];
  return (
    <div className={`alert alert-${kind}`} role={kind === "error" ? "alert" : "status"}>
      <span className="alert-icon">{icon}</span>
      <div className="alert-body">
        {title && <strong>{title}</strong>}
        {children && <div>{children}</div>}
      </div>
      {onClose && <button className="icon-btn" onClick={onClose} aria-label="Dismiss">×</button>}
    </div>
  );
}
