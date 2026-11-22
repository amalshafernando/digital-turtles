"""Use-cases. No HTTP / FastAPI imports here -> trivial to unit test."""
import logging

from ..errors import DomainError
from ..repositories.base import TicketRepository
from ..schemas import STATUSES, TicketCreate
from .classification_service import ClassificationService
from .draft_service import Draft, DraftService
from .priority import score_priority

log = logging.getLogger("tickets")


class TicketService:
    def __init__(self, repo: TicketRepository, classifier: ClassificationService, drafts: DraftService) -> None:
        self.repo, self.classifier, self.drafts = repo, classifier, drafts

    def create(self, payload: TicketCreate) -> dict:
        category, conf = self.classifier.classify(payload.message)
        return self.repo.create({
            "name": payload.name, "email": payload.email, "message": payload.message,
            "category": category, "category_confidence": round(conf, 4),
            "priority": score_priority(payload.message, category),
            "status": "open", "draft_status": "pending",
        })

    def run_draft(self, ticket_id: int) -> None:
        """Background job: generate the AI reply draft and store it on the ticket."""
        ticket = self.repo.get(ticket_id)
        if ticket is None:
            return
        try:
            d = self.drafts.generate(ticket["message"])
        except Exception:  # noqa: BLE001
            log.exception("unexpected draft error")
            d = Draft(None, [], "failed", [], "exception")
        self.repo.update(ticket_id, {"draft_reply": d.text, "draft_sources": d.sources,
                                     "draft_status": d.status, "draft_flags": d.flags})

    def get(self, ticket_id: int) -> dict:
        t = self.repo.get(ticket_id)
        if t is None:
            raise DomainError(404, "not_found", f"Ticket #{ticket_id} was not found.")
        return t

    def list_tickets(self, category: str | None, status: str | None, limit: int, offset: int) -> list[dict]:
        return self.repo.list(category, status, limit, offset)

    def set_status(self, ticket_id: int, status: str) -> dict:
        if status not in STATUSES:
            raise DomainError(422, "validation_error", f"Status must be one of: {', '.join(STATUSES)}")
        updated = self.repo.update(ticket_id, {"status": status})
        if updated is None:
            raise DomainError(404, "not_found", f"Ticket #{ticket_id} was not found.")
        return updated

    def categories(self) -> list[str]:
        return self.classifier.categories()
