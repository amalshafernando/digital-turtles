"""API contracts (Pydantic). Validation rules live here, once, for the server side."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from .config import MESSAGE_MAX, MESSAGE_MIN, NAME_MAX

Status = Literal["open", "in_progress", "resolved", "closed"]
STATUSES = ("open", "in_progress", "resolved", "closed")


class TicketCreate(BaseModel):
    name: str = Field(min_length=1, max_length=NAME_MAX)
    email: EmailStr
    message: str = Field(min_length=MESSAGE_MIN, max_length=MESSAGE_MAX)

    @field_validator("name", "message", "email", mode="before")
    @classmethod
    def _strip(cls, v):
        # strip BEFORE length checks so "      " counts as empty
        return v.strip() if isinstance(v, str) else v


class TicketReceipt(BaseModel):
    """What the CUSTOMER gets back: no category / priority / draft (internal data)."""
    id: int
    message: str


class StatusUpdate(BaseModel):
    status: Status


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DraftSource(BaseModel):
    id: str
    title: str
    score: float


class TicketOut(BaseModel):
    id: int
    name: str
    email: str
    message: str
    category: str
    category_confidence: float
    priority: str
    status: str
    draft_status: str
    draft_reply: str | None = None
    draft_sources: list[DraftSource] | None = None
    draft_flags: list[str] | None = None
    created_at: datetime
    updated_at: datetime
