import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import get_settings
from .container import get_container
from .errors import install_error_handlers

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_container()          # load model + FAQ + DB client at startup -> fail fast, first request is fast
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Smart Support Desk API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_methods=["*"], allow_headers=["*"])
    install_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
