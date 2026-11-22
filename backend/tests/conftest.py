import os

# Must be set BEFORE the app is imported
os.environ.update({"REPOSITORY": "memory", "CLASSIFIER_BACKEND": "none", "LLM_PROVIDER": "mock",
                   "TEAM_USER": "agent", "TEAM_PASSWORD": "pw", "JWT_SECRET": "test-secret"})

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_ticket_service
from app.config import get_settings
from app.container import build_container
from app.main import create_app
from app.repositories.memory_repo import MemoryTicketRepository
from app.services.classifier.base import Prediction


class StubClassifier:
    """Keyword classifier standing in for the real DistilBERT model (fast, deterministic)."""
    name = "stub"

    def labels(self):
        return ["ACCOUNT", "INVOICE", "ORDER", "REFUND"]

    def predict(self, text):
        t = text.lower()
        for kw, label in (("refund", "REFUND"), ("invoice", "INVOICE"), ("password", "ACCOUNT"), ("order", "ORDER")):
            if kw in t:
                return Prediction(label, 0.95)
        return Prediction("ORDER", 0.10)   # low confidence -> UNCLEAR


@pytest.fixture
def service():
    return build_container(get_settings(), repo=MemoryTicketRepository(), classifier=StubClassifier()).tickets


@pytest.fixture
def client(service):
    app = create_app()
    app.dependency_overrides[get_ticket_service] = lambda: service
    return TestClient(app)


@pytest.fixture
def auth(client):
    r = client.post("/api/auth/login", json={"username": "agent", "password": "pw"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
