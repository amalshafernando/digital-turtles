"""Central settings. Values come from environment variables or a .env file (never commit secrets)."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

MESSAGE_MIN = 10
MESSAGE_MAX = 2000
NAME_MAX = 100


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    app_env: str = "dev"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    # --- team login (env-var fallback for dev / no-DB mode) ---
    team_user: str = "agent"
    team_password: str = "change-me"
    jwt_secret: str = "dev-only-secret-change-me"
    token_ttl_seconds: int = 8 * 3600

    # --- startup seed user (idempotent; created only if not already in DB) ---
    # Set both SEED_USER and SEED_PASSWORD to automatically create the first team member.
    seed_user: str = ""       # e.g. "admin"
    seed_password: str = ""   # plain-text; hashed with bcrypt before storing

    # --- database ---
    repository: Literal["supabase", "memory"] = "supabase"
    supabase_url: str = ""
    supabase_service_key: str = ""

    # --- classifier ---
    classifier_backend: Literal["auto", "onnx", "hf", "joblib", "none"] = "auto"
    model_dir: str = "models"
    unclear_below: float = 0.30

    # --- FAQ-grounded reply drafts ---
    faq_path: str = "data/faq.json"
    faq_min_score: float = 0.20
    llm_provider: Literal["mock", "ollama", "anthropic"] = "mock"
    llm_model: str = ""
    ollama_url: str = "http://localhost:11434"
    anthropic_api_key: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

