"""Tests for web dashboard."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmemory.core import MemoryEngine, MemoryEntry

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from agentmemory.dashboard import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_index_returns_html(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AgentMemory Dashboard" in response.text


def test_api_stats_structure(client: TestClient) -> None:
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_memories" in data
    assert "projects" in data
    assert "sessions" in data
    assert "by_category" in data


def test_api_capture_and_recall(client: TestClient) -> None:
    payload = {
        "project": "dash-test",
        "content": "Dashboard capture test",
        "category": "fact",
        "confidence": 0.9,
    }
    resp = client.post("/api/capture", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "stored"

    # Now recall
    resp = client.get("/api/memories?project=dash-test")
    assert resp.status_code == 200
    data = resp.json()
    assert any(m["content"] == "Dashboard capture test" for m in data["memories"])


def test_api_search(client: TestClient) -> None:
    client.post("/api/capture", json={
        "project": "search-test",
        "content": "unique search term xyz123",
        "category": "fact",
    })
    resp = client.get("/api/search?project=search-test&keyword=xyz123")
    assert resp.status_code == 200
    data = resp.json()
    assert any("xyz123" in r["content"] for r in data["results"])


def test_api_projects(client: TestClient) -> None:
    client.post("/api/capture", json={
        "project": "proj-a",
        "content": "memory a",
        "category": "fact",
    })
    client.post("/api/capture", json={
        "project": "proj-b",
        "content": "memory b",
        "category": "fact",
    })
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert "proj-a" in data["projects"]
    assert "proj-b" in data["projects"]
