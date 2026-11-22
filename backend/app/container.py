"""Composition root: builds the object graph once. Tests build their own with fakes."""
from dataclasses import dataclass
from functools import lru_cache

from .config import Settings, get_settings
from .repositories.base import TicketRepository
from .services.classification_service import ClassificationService
from .services.classifier.base import Classifier
from .services.classifier.factory import build_classifier
from .services.draft_service import DraftService
from .services.faq_retriever import FaqRetriever
from .services.llm import LLM, build_llm
from .services.ticket_service import TicketService


@dataclass
class Container:
    tickets: TicketService
    classifier_backend: str
    repository: str


def build_container(settings: Settings, repo: TicketRepository | None = None,
                    classifier: Classifier | None = None, llm: LLM | None = None) -> Container:
    if repo is None:
        if settings.repository == "supabase":
            from .repositories.supabase_repo import SupabaseTicketRepository
            repo = SupabaseTicketRepository(settings.supabase_url, settings.supabase_service_key)
        else:
            from .repositories.memory_repo import MemoryTicketRepository
            repo = MemoryTicketRepository()
    classifier = classifier or build_classifier(settings.classifier_backend, settings.model_dir)
    llm = llm or build_llm(settings.llm_provider, settings.llm_model, settings.ollama_url, settings.anthropic_api_key)
    service = TicketService(
        repo,
        ClassificationService(classifier, settings.unclear_below),
        DraftService(FaqRetriever(settings.faq_path), llm, settings.faq_min_score),
    )
    return Container(service, classifier.name, settings.repository)


@lru_cache
def get_container() -> Container:
    return build_container(get_settings())
