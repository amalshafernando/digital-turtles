"""In-memory repository: used by unit tests and for quick local demos (REPOSITORY=memory)."""
import threading
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryTicketRepository:
    def __init__(self) -> None:
        self._rows: dict[int, dict] = {}
        self._next = 1
        self._lock = threading.Lock()

    def create(self, data: dict) -> dict:
        with self._lock:
            row = {"id": self._next, "created_at": _now(), "updated_at": _now(),
                   "draft_reply": None, "draft_sources": None, "draft_flags": None, **data}
            self._rows[self._next] = row
            self._next += 1
            return dict(row)

    def get(self, ticket_id: int) -> dict | None:
        row = self._rows.get(ticket_id)
        return dict(row) if row else None

    def list(self, category, status, limit, offset) -> list[dict]:
        rows = sorted(self._rows.values(), key=lambda r: r["id"], reverse=True)
        if category:
            rows = [r for r in rows if r["category"] == category]
        if status:
            rows = [r for r in rows if r["status"] == status]
        return [dict(r) for r in rows[offset: offset + limit]]

    def update(self, ticket_id: int, fields: dict) -> dict | None:
        with self._lock:
            row = self._rows.get(ticket_id)
            if row is None:
                return None
            row.update(fields)
            row["updated_at"] = _now()
            return dict(row)
