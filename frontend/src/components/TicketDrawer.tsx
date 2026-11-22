import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../lib/api";
import { STATUSES, STATUS_LABEL, type Status, type Ticket } from "../lib/types";
import Alert from "./Alert";
import { CategoryBadge, PriorityBadge } from "./Badges";
import DraftPanel from "./DraftPanel";

interface Props {
  ticketId: number;
  onClose: () => void;
  onUpdated: (t: Ticket) => void;
  onUnauthorized: () => void;
}

export default function TicketDrawer({ ticketId, onClose, onUpdated, onUnauthorized }: Props) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const tries = useRef(0);

  // Load the ticket; while the AI draft is still "pending", poll every 2s (max ~40s).
  useEffect(() => {
    let alive = true;
    let timer: number | undefined;
    tries.current = 0;
    setTicket(null);
    setError(null);

    const load = async () => {
      try {
        const t = await api.getTicket(ticketId);
        if (!alive) return;
        setTicket(t);
        onUpdated(t);
        if (t.draft_status === "pending" && tries.current++ < 20) timer = window.setTimeout(load, 2000);
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401) return onUnauthorized();
        setError(e instanceof Error ? e.message : "Could not load the ticket.");
      }
    };
    load();
    return () => { alive = false; window.clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketId]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const changeStatus = async (status: Status) => {
    if (!ticket || status === ticket.status) return;
    setSaving(true); setError(null); setSaved(false);
    try {
      const updated = await api.updateStatus(ticket.id, status);   // PATCH /api/tickets/{id}
      setTicket(updated); onUpdated(updated); setSaved(true);
      window.setTimeout(() => setSaved(false), 1800);
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return onUnauthorized();
      setError(e instanceof Error ? e.message : "Could not update the status.");
    } finally { setSaving(false); }
  };

  return (
    <>
      <div className="overlay" onClick={onClose} />
      <aside className="drawer" role="dialog" aria-modal="true" aria-label={`Ticket ${ticketId}`}>
        <div className="drawer-head">
          <div>
            <div className="mono sub">Ticket</div>
            <h2>#{ticketId}</h2>
          </div>
          <button className="icon-btn big" onClick={onClose} aria-label="Close">×</button>
        </div>

        {error && <Alert kind="error" onClose={() => setError(null)}>{error}</Alert>}
        {!ticket && !error && <div className="skeleton-lines"><i /><i /><i /></div>}

        {ticket && (
          <div className="drawer-body">
            <div className="meta-row">
              <CategoryBadge category={ticket.category} confidence={ticket.category_confidence} />
              <PriorityBadge priority={ticket.priority} />
              <span className="sub">{new Date(ticket.created_at).toLocaleString()}</span>
            </div>

            <section className="panel">
              <div className="who">
                <div className="avatar">{ticket.name.slice(0, 1).toUpperCase()}</div>
                <div><div className="cust">{ticket.name}</div><a className="sub" href={`mailto:${ticket.email}`}>{ticket.email}</a></div>
              </div>
              <h4>Full message</h4>
              <p className="message">{ticket.message}</p>
            </section>

            <section className="panel">
              <label htmlFor="status-select" className="label-inline">Status</label>
              <div className="status-row">
                <select id="status-select" className="input select" value={ticket.status} disabled={saving}
                        onChange={(e) => changeStatus(e.target.value as Status)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABEL[s]}</option>)}
                </select>
                {saving && <span className="hint">Saving…</span>}
                {saved && <span className="saved">Saved ✓</span>}
              </div>
            </section>

            <DraftPanel ticket={ticket} />
          </div>
        )}
      </aside>
    </>
  );
}
