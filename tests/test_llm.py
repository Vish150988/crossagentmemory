"""Tests for LLM client."""

from __future__ import annotations

from crossagentmemory.llm import LLMClient, get_llm_client


def test_llm_client_without_keys() -> None:
    client = LLMClient()
    assert client.provider == "none"
    assert client.is_available() is False


def test_llm_client_chat_returns_empty_when_unavailable() -> None:
    client = LLMClient(provider="none")
    resp = client.chat("hello")
    assert resp.text == ""
    assert resp.provider == "none"


def test_llm_client_summarize_fallback() -> None:
    client = LLMClient(provider="none")
    result = client.summarize_text("some text")
    assert result == ""


def test_get_llm_client() -> None:
    client = get_llm_client()
    assert isinstance(client, LLMClient)
