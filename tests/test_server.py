"""Tests for REST API server."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from crossagentmemory.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_api_list_memories(client: TestClient) -> None:
    resp = client.get("/api/memories?project=server-test")
    assert resp.status_code == 200
    assert "memories" in resp.json()


def test_api_create_and_get_memory(client: TestClient) -> None:
    payload = {
        "project": "server-test",
        "content": "API test memory",
        "category": "fact",
    }
    create = client.post("/api/memories", json=payload)
    assert create.status_code == 200
    memory_id = create.json()["id"]

    get_resp = client.get(f"/api/memories/{memory_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["content"] == "API test memory"


def test_api_create_with_tenant_and_temporal(client: TestClient) -> None:
    payload = {
        "project": "server-test",
        "content": "Tenant-scoped memory",
        "category": "decision",
        "user_id": "user-42",
        "tenant_id": "tenant-99",
        "valid_from": "2024-01-01T00:00:00Z",
        "valid_until": "2025-12-31T23:59:59Z",
    }
    create = client.post("/api/memories", json=payload)
    assert create.status_code == 200
    memory_id = create.json()["id"]

    get_resp = client.get(f"/api/memories/{memory_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["user_id"] == "user-42"
    assert data["tenant_id"] == "tenant-99"
    assert data["valid_from"] == "2024-01-01T00:00:00Z"
    assert data["valid_until"] == "2025-12-31T23:59:59Z"


def test_api_search(client: TestClient) -> None:
    client.post(
        "/api/memories",
        json={
            "project": "search-api",
            "content": "unique api keyword xyz",
            "category": "fact",
        },
    )
    resp = client.get("/api/search?q=xyz")
    assert resp.status_code == 200
    data = resp.json()
    assert any("xyz" in r["content"] for r in data["results"])


def test_api_search_with_tenant_filter(client: TestClient) -> None:
    client.post(
        "/api/memories",
        json={
            "project": "search-api",
            "content": "tenant alpha keyword abc",
            "category": "fact",
            "tenant_id": "alpha",
        },
    )
    client.post(
        "/api/memories",
        json={
            "project": "search-api",
            "content": "tenant beta keyword abc",
            "category": "fact",
            "tenant_id": "beta",
        },
    )
    resp = client.get("/api/search?q=abc&tenant_id=alpha")
    assert resp.status_code == 200
    data = resp.json()
    assert all(r["tenant_id"] == "alpha" for r in data["results"])


def test_api_stats(client: TestClient) -> None:
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_memories" in data


def test_api_projects(client: TestClient) -> None:
    resp = client.get("/api/projects")
    assert resp.status_code == 200
    assert "projects" in resp.json()


def test_api_graph(client: TestClient) -> None:
    resp = client.get("/api/graph?project=graph-api")
    assert resp.status_code == 200
    data = resp.json()
    assert "nodes" in data
    assert "edges" in data


def test_api_tag(client: TestClient) -> None:
    resp = client.post("/api/tag", json={"content": "auth system with JWT"})
    assert resp.status_code == 200
    assert "tags" in resp.json()
