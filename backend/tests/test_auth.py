"""Auth-related tests: login, JWT token, protected route, seed-user helpers."""
import os
import time

os.environ.update({"REPOSITORY": "memory", "CLASSIFIER_BACKEND": "none", "LLM_PROVIDER": "mock",
                   "TEAM_USER": "agent", "TEAM_PASSWORD": "pw", "JWT_SECRET": "test-secret"})

import pytest
from app.security import check_credentials, hash_password, make_token
from app.config import get_settings


@pytest.fixture(scope="module")
def settings():
    return get_settings()


# ─── Password hashing ────────────────────────────────────────────────────────

def test_hash_and_verify_password():
    pw = "super-secret-123!"
    hashed = hash_password(pw)
    assert hashed != pw                                        # never stored plain
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")  # bcrypt marker


def test_verify_correct_password(settings):
    hashed = hash_password("correct-horse")
    assert check_credentials(settings, "agent", "correct-horse", password_hash=hashed)


def test_reject_wrong_password(settings):
    hashed = hash_password("correct-horse")
    assert not check_credentials(settings, "agent", "wrong-pass", password_hash=hashed)


def test_env_var_fallback_correct(settings):
    """Without a DB hash, falls back to TEAM_USER / TEAM_PASSWORD env vars."""
    assert check_credentials(settings, "agent", "pw", password_hash=None)


def test_env_var_fallback_wrong(settings):
    assert not check_credentials(settings, "agent", "bad", password_hash=None)


# ─── JWT token ───────────────────────────────────────────────────────────────

def test_make_token_contains_required_claims(settings):
    import jwt as pyjwt
    token = make_token(settings, "alice", role="team_member")
    payload = pyjwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    assert payload["sub"] == "alice"
    assert payload["role"] == "team_member"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_token_expires(settings):
    import jwt as pyjwt
    # Build a token that expired 1 second ago
    now = int(time.time())
    expired = pyjwt.encode({"sub": "x", "exp": now - 1}, settings.jwt_secret, algorithm="HS256")
    with pytest.raises(pyjwt.ExpiredSignatureError):
        pyjwt.decode(expired, settings.jwt_secret, algorithms=["HS256"])


# ─── Login endpoint ──────────────────────────────────────────────────────────

def test_login_with_valid_env_credentials(client):
    r = client.post("/api/auth/login", json={"username": "agent", "password": "pw"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_wrong_password_returns_401(client):
    r = client.post("/api/auth/login", json={"username": "agent", "password": "wrong"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_credentials"


def test_protected_route_without_token_returns_401(client):
    r = client.get("/api/tickets")
    assert r.status_code == 401


def test_protected_route_with_valid_token(client):
    login = client.post("/api/auth/login", json={"username": "agent", "password": "pw"})
    token = login.json()["access_token"]
    r = client.get("/api/tickets", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_protected_route_with_bad_token_returns_401(client):
    r = client.get("/api/tickets", headers={"Authorization": "Bearer not.a.real.token"})
    assert r.status_code == 401
