import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import Settings, get_settings
from .container import get_container
from .errors import install_error_handlers

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("startup")


def _seed_team_user(settings: Settings) -> None:
    """Idempotently create the seed team-member user in the users table.

    Only runs when SEED_USER and SEED_PASSWORD env vars are both set.
    If the user already exists the insert is skipped (no duplicate created).
    Requires REPOSITORY=supabase; silently skipped for memory mode (no DB).
    """
    if not settings.seed_user or not settings.seed_password:
        return
    if settings.repository != "supabase":
        log.info("Seed user skipped: REPOSITORY=%s (no users table)", settings.repository)
        return
    if not settings.supabase_url or not settings.supabase_service_key:
        log.warning("Seed user skipped: SUPABASE_URL / SUPABASE_SERVICE_KEY not set")
        return

    try:
        from supabase import create_client
        from .security import hash_password

        client = create_client(settings.supabase_url, settings.supabase_service_key)
        # Check if user already exists (idempotent)
        existing = client.table("users").select("id").eq("username", settings.seed_user).limit(1).execute()
        if existing.data:
            log.info("Seed user '%s' already exists — skipping creation", settings.seed_user)
            return

        hashed = hash_password(settings.seed_password)
        client.table("users").insert({
            "username": settings.seed_user,
            "password_hash": hashed,
            "role": "admin",
        }).execute()
        log.info("Seed user '%s' created successfully (role=admin)", settings.seed_user)
    except Exception as exc:  # noqa: BLE001
        log.warning("Seed user creation failed (non-fatal): %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    get_container()          # load model + FAQ + DB client at startup -> fail fast, first request is fast
    _seed_team_user(settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Smart Support Desk API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_methods=["*"], allow_headers=["*"])
    install_error_handlers(app)
    app.include_router(router)
    app.add_api_route("/health", lambda: {"status": "ok"}, methods=["GET"], include_in_schema=False)
    return app


app = create_app()
