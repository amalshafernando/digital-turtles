import type { Ticket } from "../lib/types";
import { CategoryBadge, PriorityBadge, StatusBadge } from "./Badges";

const fmt = (iso: string) => new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });

export default function TicketTable({ tickets, selectedId, onSelect }:
  { tickets: Ticket[]; selectedId: number | null; onSelect: (id: number) => void }) {
  if (tickets.length === 0) {
    return <div className="empty"><div className="empty-icon">📭</div><p>No tickets match these filters.</p></div>;
  }
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr><th>#</th><th>Customer</th><th>Category</th><th>Priority</th><th>Status</th><th>Message</th><th>Received</th></tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr key={t.id} className={t.id === selectedId ? "selected" : ""} tabIndex={0}
                onClick={() => onSelect(t.id)} onKeyDown={(e) => e.key === "Enter" && onSelect(t.id)}>
              <td className="mono">#{t.id}</td>
              <td><div className="cust">{t.name}</div><div className="sub">{t.email}</div></td>
              <td><CategoryBadge category={t.category} confidence={t.category_confidence} /></td>
              <td><PriorityBadge priority={t.priority} /></td>
              <td><StatusBadge status={t.status} /></td>
              <td className="preview">{t.message}</td>
              <td className="sub nowrap">{fmt(t.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
