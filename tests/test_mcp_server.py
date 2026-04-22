"""Tests for MCP server."""

from __future__ import annotations

import json

import pytest

pytest.importorskip("fastmcp")

from crossagentmemory.mcp_server import (
    memory_capture,
    memory_recall,
    memory_search,
    memory_stats,
)


def test_mcp_memory_capture_and_recall() -> None:
    result = memory_capture("mcp-test", "MCP captured this", category="decision")
    data = json.loads(result)
    assert data["status"] == "stored"
    assert "memory_id" in data

    result = memory_recall("mcp-test", limit=5)
    data = json.loads(result)
    assert data["project"] == "mcp-test"
    assert len(data["memories"]) >= 1
    assert any("MCP captured this" in m["content"] for m in data["memories"])


def test_mcp_memory_search() -> None:
    memory_capture("search-test", "unique mcp keyword foobar", category="fact")
    result = memory_search("search-test", "foobar")
    data = json.loads(result)
    assert any("foobar" in m["content"] for m in data["results"])


def test_mcp_memory_stats() -> None:
    result = memory_stats()
    data = json.loads(result)
    assert "total_memories" in data
    assert "projects" in data


def test_mcp_memory_stats_with_project() -> None:
    memory_capture("stat-test", "stat memory", category="fact")
    result = memory_stats("stat-test")
    data = json.loads(result)
    assert data.get("project") == "stat-test"
    assert data.get("project_memories", 0) >= 1
