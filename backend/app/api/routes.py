"""Thin HTTP layer: parse -> call service -> return. No business logic."""
import re

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from ..config import Settings, get_settings
from ..container import Container
from ..errors import DomainError
from ..schemas import (LoginRequest, Status, StatusUpdate, TicketCreate, TicketOut, TicketReceipt, TokenOut)
from ..security import check_credentials, make_token, require_agent
from ..services.ticket_service import TicketService
from .deps import get_container_dep, get_ticket_service

router = APIRouter(prefix="/api")
_CATEGORY = re.compile(r"^[A-Za-z_]{1,32}$")


@router.get("/health")
def health(c: Container = Depends(get_container_dep)):
    return {"status": "ok", "classifier": c.classifier_backend, "repository": c.repository}


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginRequest, settings: Settings = Depends(get_settings)):
    if not check_credentials(settings, body.username, body.password):
        raise DomainError(401, "invalid_credentials", "Incorrect username or password.")
    return {"access_token": make_token(settings, body.username)}


@router.post("/tickets", status_code=201, response_model=TicketReceipt)
def create_ticket(payload: TicketCreate, bg: BackgroundTasks, svc: TicketService = Depends(get_ticket_service)):
    ticket = svc.create(payload)
    bg.add_task(svc.run_draft, ticket["id"])   # the customer never waits for the LLM
    return {"id": ticket["id"], "message": "Thanks! We received your message and will get back to you soon."}


@router.get("/categories", response_model=list[str])
def categories(svc: TicketService = Depends(get_ticket_service), _: str = Depends(require_agent)):
    return svc.categories()


@router.get("/tickets", response_model=list[TicketOut])
def list_tickets(category: str | None = None, status: Status | None = None,
                 limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0),
                 svc: TicketService = Depends(get_ticket_service), _: str = Depends(require_agent)):
    if category is not None and not _CATEGORY.match(category):
        raise DomainError(400, "bad_category", "Category may only contain letters and underscores (max 32).")
    return svc.list_tickets(category.upper() if category else None, status, limit, offset)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, svc: TicketService = Depends(get_ticket_service), _: str = Depends(require_agent)):
    return svc.get(ticket_id)


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
def patch_ticket(ticket_id: int, body: StatusUpdate, svc: TicketService = Depends(get_ticket_service),
                 _: str = Depends(require_agent)):
    return svc.set_status(ticket_id, body.status)
