import json
import re
from typing import Protocol

import httpx


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class MockLLM:
    """Deterministic, key-free. Echoes the top <faq> entry. For tests/demos ONLY - it is not a real LLM."""

    def complete(self, system: str, user: str) -> str:
        m = re.search(r'<faq id="([^"]+)"[^>]*>(.*?)</faq>', user, re.S)
        if not m:
            return json.dumps({"answer": None, "used_faq_ids": []})
        text = m.group(2).replace("&lt;", "<").replace("&gt;", ">").strip()
        return json.dumps({"answer": f"Hi! {text}", "used_faq_ids": [m.group(1)]})


class OllamaLLM:
    def __init__(self, url: str, model: str) -> None:
        self.url, self.model = url, model

    def complete(self, system: str, user: str) -> str:
        r = httpx.post(f"{self.url}/api/chat", timeout=90, json={
            "model": self.model, "stream": False, "format": "json", "options": {"temperature": 0},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        r.raise_for_status()
        return r.json()["message"]["content"]


class AnthropicLLM:
    def __init__(self, api_key: str, model: str) -> None:
        import anthropic  # optional dependency: pip install anthropic
        self.client, self.model = anthropic.Anthropic(api_key=api_key), model

    def complete(self, system: str, user: str) -> str:
        msg = self.client.messages.create(model=self.model, max_tokens=400, temperature=0, timeout=30,
                                          system=system, messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in msg.content if b.type == "text")


def build_llm(provider: str, model: str, ollama_url: str, api_key: str) -> LLM:
    if provider == "ollama":
        return OllamaLLM(ollama_url, model or "llama3.2:3b")
    if provider == "anthropic":
        if not api_key or not model:
            raise RuntimeError("LLM_PROVIDER=anthropic needs ANTHROPIC_API_KEY and LLM_MODEL")
        return AnthropicLLM(api_key, model)
    return MockLLM()
