"""Thin HTTP layer: parse -> call service -> return. No business logic."""
import logging
import re

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from ..config import Settings, get_settings
from ..container import Container
from ..errors import DomainError
from ..schemas import (LoginRequest, Status, StatusUpdate, TicketCreate, TicketOut, TicketReceipt, TokenOut)
from ..auth.security import check_credentials, make_token, require_agent
from ..services.ticket_service import TicketService
from .deps import get_container_dep, get_ticket_service

router = APIRouter(prefix="/api")
_CATEGORY = re.compile(r"^[A-Za-z_]{1,32}$")
log = logging.getLogger("routes")


def _lookup_user_hash(settings: Settings, username: str) -> str | None:
    """Try to look up the bcrypt password_hash for *username* from the users table.

    Returns None when:
      - REPOSITORY != supabase, OR
      - Supabase credentials not configured, OR
      - User not found in DB (fall back to env-var mode)
    """
    if settings.repository != "supabase" or not settings.supabase_url or not settings.supabase_service_key:
        return None
    try:
        from supabase import create_client
        client = create_client(settings.supabase_url, settings.supabase_service_key)
        res = client.table("users").select("password_hash, role").eq("username", username).limit(1).execute()
        if res.data:
            return res.data[0]["password_hash"]
    except Exception as exc:  # noqa: BLE001
        log.warning("DB user lookup failed, falling back to env-var auth: %s", exc)
    return None


@router.get("/health")
def health(c: Container = Depends(get_container_dep)):
    return {"status": "ok", "classifier": c.classifier_backend, "repository": c.repository}


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginRequest, settings: Settings = Depends(get_settings)):
    """Authenticate a team member and return a signed JWT.

    1. Try to look up the user in the DB (bcrypt verify).
    2. Fall back to TEAM_USER / TEAM_PASSWORD env vars (dev / no-DB mode).
    """
    password_hash = _lookup_user_hash(settings, body.username)
    if not check_credentials(settings, body.username, body.password, password_hash):
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
                 limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                 svc: TicketService = Depends(get_ticket_service), _: str = Depends(require_agent)):
    if category is not None and not _CATEGORY.match(category):
        raise DomainError(400, "bad_category", "Category may only contain letters and underscores (max 32).")
    return svc.list_tickets(category.upper() if category else None, status, limit, offset)


@router.get("/tickets/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, svc: TicketService = Depends(get_ticket_service), _: str = Depends(require_agent)):
    return svc.get(ticket_id)


@router.patch("/tickets/{ticket_id}", response_model=TicketOut)
@router.patch("/tickets/{ticket_id}/status", response_model=TicketOut, include_in_schema=False)   # alias used in the guide
def patch_ticket(ticket_id: int, body: StatusUpdate, svc: TicketService = Depends(get_ticket_service),
                 _: str = Depends(require_agent)):
    return svc.set_status(ticket_id, body.status)
