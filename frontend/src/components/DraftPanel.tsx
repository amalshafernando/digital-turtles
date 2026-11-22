import { useState } from "react";
import type { Ticket } from "../lib/types";
import Alert from "./Alert";

export default function DraftPanel({ ticket }: { ticket: Ticket }) {
  const [copied, setCopied] = useState(false);
  const { draft_status: st, draft_reply: reply, draft_sources: sources, draft_flags: flags } = ticket;

  const copy = async () => {
    if (!reply) return;
    await navigator.clipboard?.writeText(reply);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section className="panel draft">
      <div className="panel-head">
        <h3><span className="spark">✦</span> AI reply draft</h3>
        <span className="hint">Suggestion only. Review before sending.</span>
      </div>

      {flags?.includes("possible_prompt_injection") && (
        <Alert kind="warning" title="Possible prompt-injection attempt">
          The message contains instructions aimed at the AI. They were ignored; the draft is based on the FAQ only.
        </Alert>
      )}

      {st === "pending" && <div className="skeleton-lines" aria-busy="true"><i /><i /><i /><span className="hint">Generating draft…</span></div>}
      {st === "failed" && <Alert kind="error" title="Draft unavailable">The AI service failed. Please reply manually.</Alert>}
      {st === "no_match" && (
        <>
          <Alert kind="warning" title="No matching FAQ">
            The answer cannot be verified from our FAQ, so no information was invented. Needs a human reply.
          </Alert>
          {reply && <blockquote className="draft-text muted">{reply}</blockquote>}
        </>
      )}
      {st === "ready" && reply && (
        <>
          <blockquote className="draft-text">{reply}</blockquote>
          <button className="btn btn-ghost" onClick={copy}>{copied ? "Copied ✓" : "Copy draft"}</button>
        </>
      )}

      <div className="sources">
        <h4>Used FAQ entries</h4>
        {sources && sources.length > 0 ? (
          <ul>
            {sources.map((s) => (
              <li key={s.id} className="faq-badge" title={`Match score ${s.score}`}>
                <code>{s.id}</code><span>{s.title}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="hint">{st === "pending" ? "Waiting for the draft…" : "None. No FAQ entry was used."}</p>
        )}
      </div>
    </section>
  );
}
