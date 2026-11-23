"""JWT authentication + password hashing.

Flow:
  1. POST /auth/login  → verify password via bcrypt → issue JWT (sub, role, iat, exp)
  2. Protected routes  → require_agent() extracts Bearer token → decode → return username

Security notes:
  - Passwords are stored as bcrypt hashes; plain-text is NEVER persisted.
  - JWT payload is Base64URL-encoded, NOT encrypted — do NOT put secrets in it.
  - JWT signing secret must come from the JWT_SECRET env var (never hardcode).
  - Falls back to env-var credentials when no users table row is found,
    so the app still works without a DB (memory repo / tests).
"""
import time
from typing import Optional

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings
from .errors import DomainError

_bearer = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Password hashing (bcrypt via passlib)
# ---------------------------------------------------------------------------
try:
    from passlib.context import CryptContext
    _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(plain: str) -> str:
        """Return a bcrypt hash for *plain*.  Use this when creating/seeding users."""
        return _pwd_ctx.hash(plain)

    def _verify_bcrypt(plain: str, hashed: str) -> bool:
        return _pwd_ctx.verify(plain, hashed)

except ImportError:  # passlib not installed (should not happen in production)
    import hashlib, hmac as _hmac

    def hash_password(plain: str) -> str:  # type: ignore[misc]
        raise RuntimeError("passlib[bcrypt] is required — pip install passlib[bcrypt]")

    def _verify_bcrypt(plain: str, hashed: str) -> bool:  # type: ignore[misc]
        return False


# ---------------------------------------------------------------------------
# Credential verification
# ---------------------------------------------------------------------------

def check_credentials(settings: Settings, username: str, password: str,
                       password_hash: Optional[str] = None) -> bool:
    """Verify credentials.

    If *password_hash* is provided (looked up from the users table), we use
    bcrypt comparison.  Otherwise we fall back to constant-time comparison
    against the TEAM_USER / TEAM_PASSWORD env vars (dev / no-DB mode).
    """
    if password_hash is not None:
        # DB-backed path: bcrypt verify
        return _verify_bcrypt(password, password_hash)

    # Fallback: env-var mode (dev / test, no DB needed)
    import hmac as _hmac
    u_ok = _hmac.compare_digest(username.encode(), settings.team_user.encode())
    p_ok = _hmac.compare_digest(password.encode(), settings.team_password.encode())
    return u_ok and p_ok  # constant-time; both always evaluated


# ---------------------------------------------------------------------------
# JWT token creation & verification
# ---------------------------------------------------------------------------

def make_token(settings: Settings, subject: str, role: str = "team_member") -> str:
    """Create a signed JWT.

    Payload fields:
      sub  — username / email (identifies the user, NOT secret)
      role — 'team_member' | 'admin'
      iat  — issued-at timestamp (Unix seconds)
      exp  — expiry timestamp (Unix seconds)
    """
    now = int(time.time())
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + settings.token_ttl_seconds,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def require_agent(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    """FastAPI dependency: validates the Bearer JWT and returns the subject (username).

    Raises DomainError 401 when:
      - No Authorization header is present
      - Signature is invalid
      - Token has expired (exp in the past)
    """
    if creds is None:
        raise DomainError(401, "unauthorized", "Please log in to continue.")
    try:
        payload = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise DomainError(401, "token_expired", "Your session has expired. Please log in again.")
    except jwt.PyJWTError:
        raise DomainError(401, "unauthorized", "Invalid token. Please log in again.")
