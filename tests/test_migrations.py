"""Tests for schema versioning and migrations."""

from __future__ import annotations

from pathlib import Path

from agentmemory.backends.migrations import (
    CURRENT_SCHEMA_VERSION,
    ensure_version_table,
    get_schema_version,
    run_migrations,
    set_schema_version,
)
from agentmemory.backends.sqlite import SQLiteBackend


class TestMigrations:
    def test_new_backend_gets_current_version(self, tmp_path: Path) -> None:
        db = tmp_path / "versioned.db"
        backend = SQLiteBackend(db_path=db)
        backend.init()
        version = get_schema_version(backend)
        assert version == CURRENT_SCHEMA_VERSION

    def test_version_table_idempotent(self, tmp_path: Path) -> None:
        db = tmp_path / "idempotent.db"
        backend = SQLiteBackend(db_path=db)
        backend.init()
        ensure_version_table(backend)
        ensure_version_table(backend)
        version = get_schema_version(backend)
        assert version == CURRENT_SCHEMA_VERSION

    def test_set_and_get_version(self, tmp_path: Path) -> None:
        db = tmp_path / "setget.db"
        backend = SQLiteBackend(db_path=db)
        backend.init()
        set_schema_version(backend, 42)
        assert get_schema_version(backend) == 42

    def test_run_migrations_idempotent(self, tmp_path: Path) -> None:
        db = tmp_path / "idempotent_migrations.db"
        backend = SQLiteBackend(db_path=db)
        backend.init()
        run_migrations(backend)
        run_migrations(backend)
        assert get_schema_version(backend) == CURRENT_SCHEMA_VERSION
