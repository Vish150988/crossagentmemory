"""Pluggable storage backends for CrossAgentMemory."""

from __future__ import annotations

from .base import MemoryBackend
from .sqlite import SQLiteBackend

try:
    from .postgres import PostgresBackend
except ImportError:
    PostgresBackend = None  # type: ignore[assignment,misc]

__all__ = ["MemoryBackend", "SQLiteBackend", "PostgresBackend"]
