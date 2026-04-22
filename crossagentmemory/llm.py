"""Pluggable LLM client for CrossAgentMemory.

Supports OpenAI, Anthropic, Ollama (local), and graceful fallback.
Configure via environment variables:
  OPENAI_API_KEY=sk-...       → Use OpenAI
  ANTHROPIC_API_KEY=sk-ant... → Use Anthropic
  OLLAMA_HOST=http://localhost:11434 → Use local Ollama

If no provider is configured, LLM features fall back to extractive methods.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


def _has_openai() -> bool:
    try:
        import openai  # noqa: F401

        return True
    except ImportError:
        return False


def _has_anthropic() -> bool:
    try:
        import anthropic  # noqa: F401

        return True
    except ImportError:
        return False


def _has_httpx() -> bool:
    try:
        import httpx  # noqa: F401

        return True
    except ImportError:
        return False


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str


class LLMClient:
    """Unified LLM client with provider auto-detection."""

    def __init__(self, provider: str = "auto", model: str | None = None):
        self.provider = self._resolve_provider(provider)
        self.model = model or self._default_model()
        self._client: Any | None = None

    def _resolve_provider(self, provider: str) -> str:
        if provider != "auto":
            return provider
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        if os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        if os.environ.get("OLLAMA_HOST"):
            return "ollama"
        return "none"

    def _default_model(self) -> str:
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-haiku-20240307",
            "ollama": "llama3.2",
            "none": "none",
        }
        return defaults.get(self.provider, "none")

    def is_available(self) -> bool:
        return self.provider != "none"

    def _get_openai_client(self) -> Any:
        if self._client is None:
            import openai

            self._client = openai.OpenAI()
        return self._client

    def _get_anthropic_client(self) -> Any:
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def chat(self, prompt: str, system: str = "") -> LLMResponse:
        """Send a chat prompt and return the response."""
        if not self.is_available():
            return LLMResponse(text="", model="none", provider="none")

        if self.provider == "openai":
            return self._chat_openai(prompt, system)
        if self.provider == "anthropic":
            return self._chat_anthropic(prompt, system)
        if self.provider == "ollama":
            return self._chat_ollama(prompt, system)

        return LLMResponse(text="", model="none", provider="none")

    def _chat_openai(self, prompt: str, system: str) -> LLMResponse:
        client = self._get_openai_client()
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        text = resp.choices[0].message.content or ""
        return LLMResponse(text=text, model=self.model, provider="openai")

    def _chat_anthropic(self, prompt: str, system: str) -> LLMResponse:
        client = self._get_anthropic_client()
        resp = client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.3,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text if resp.content else ""
        return LLMResponse(text=text, model=self.model, provider="anthropic")

    def _chat_ollama(self, prompt: str, system: str) -> LLMResponse:
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0.3},
        }
        try:
            import httpx

            r = httpx.post(f"{host}/api/chat", json=payload, timeout=60.0)
            data = r.json()
            text = data.get("message", {}).get("content", "")
            return LLMResponse(text=text, model=self.model, provider="ollama")
        except Exception:
            return LLMResponse(text="", model=self.model, provider="ollama")

    def summarize_text(self, text: str, instruction: str = "Summarize concisely.") -> str:
        """Summarize text using the LLM."""
        prompt = f"{instruction}\n\n{text}"
        resp = self.chat(prompt, system="You summarize technical content accurately.")
        return resp.text

    def generate_tags(self, content: str, existing_tags: list[str] | None = None) -> list[str]:
        """Generate tags for a memory entry."""
        prompt = (
            f"Generate 3-5 relevant tags for this technical memory. "
            f"Return ONLY a JSON array of strings.\n\n{content}"
        )
        resp = self.chat(
            prompt,
            system="You generate concise tags for technical notes. Output valid JSON only.",
        )
        try:
            tags = json.loads(resp.text.strip())
            if isinstance(tags, list):
                return [str(t).lower().replace(" ", "-") for t in tags[:5]]
        except (json.JSONDecodeError, ValueError):
            pass
        return []

    def detect_contradictions(self, memories: list[str]) -> list[tuple[int, int, str]]:
        """Detect contradictions between memories.

        Returns list of (index_a, index_b, explanation) tuples.
        """
        if len(memories) < 2:
            return []

        lines = "\n".join(f"{i}. {m}" for i, m in enumerate(memories))
        prompt = (
            f"Analyze these memories and find any contradictions. "
            f"Return ONLY a JSON array of objects with keys: "
            f"'a' (int), 'b' (int), 'reason' (string). "
            f"If no contradictions, return [].\n\n{lines}"
        )
        resp = self.chat(
            prompt,
            system="You detect logical contradictions in technical decisions.",
        )
        try:
            data = json.loads(resp.text.strip())
            if isinstance(data, list):
                return [
                    (int(item["a"]), int(item["b"]), str(item["reason"]))
                    for item in data
                    if isinstance(item, dict)
                ]
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        return []


def get_llm_client() -> LLMClient:
    """Get a configured LLM client."""
    return LLMClient()
