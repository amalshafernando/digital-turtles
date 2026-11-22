import hmac
import time

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings, get_settings
from .errors import DomainError

_bearer = HTTPBearer(auto_error=False)


def check_credentials(settings: Settings, username: str, password: str) -> bool:
    u = hmac.compare_digest(username.encode(), settings.team_user.encode())
    p = hmac.compare_digest(password.encode(), settings.team_password.encode())
    return u & p  # constant-time, both always evaluated


def make_token(settings: Settings, subject: str) -> str:
    return jwt.encode({"sub": subject, "exp": int(time.time()) + settings.token_ttl_seconds},
                      settings.jwt_secret, algorithm="HS256")


def require_agent(creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
                  settings: Settings = Depends(get_settings)) -> str:
    if creds is None:
        raise DomainError(401, "unauthorized", "Please log in to continue.")
    try:
        return jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        raise DomainError(401, "unauthorized", "Your session expired. Please log in again.")
