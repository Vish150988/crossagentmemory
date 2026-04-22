"""Tests for backup and restore."""

from __future__ import annotations

from pathlib import Path

from crossagentmemory import MemoryEngine, MemoryEntry
from crossagentmemory.backup import create_backup, restore_backup


class TestBackup:
    def test_backup_and_restore_zip(self, tmp_path: Path) -> None:
        db = tmp_path / "source.db"
        engine = MemoryEngine(db_path=db, backend="sqlite")
        engine.store(MemoryEntry(project="backup-proj", content="hello", category="fact"))
        engine.set_project_context("backup-proj", {"key": "value"}, description="test desc")
        engine.store_embedding(1, "tfidf", [0.1, 0.2])

        backup_path = tmp_path / "backup.zip"
        meta = create_backup(engine, backup_path)
        assert meta["memories"] == 1
        assert meta["projects"] == 1
        assert meta["embeddings"] == 1
        assert backup_path.exists()

        # Restore into a fresh engine
        restore_db = tmp_path / "restored.db"
        target = MemoryEngine(db_path=restore_db, backend="sqlite")
        stats = restore_backup(target, backup_path)
        assert stats["memories"] == 1
        assert stats["projects"] == 1
        assert stats["embeddings"] == 1

        memories = target.recall(project="backup-proj")
        assert len(memories) == 1
        assert memories[0].content == "hello"
        assert target.get_project_context("backup-proj") == {"key": "value"}
        assert target.get_project_description("backup-proj") == "test desc"

    def test_backup_json_format(self, tmp_path: Path) -> None:
        db = tmp_path / "source.db"
        engine = MemoryEngine(db_path=db, backend="sqlite")
        engine.store(MemoryEntry(project="json-proj", content="json test", category="decision"))

        backup_path = tmp_path / "backup.json"
        meta = create_backup(engine, backup_path)
        assert meta["memories"] == 1
        assert backup_path.exists()

    def test_restore_dry_run(self, tmp_path: Path) -> None:
        db = tmp_path / "source.db"
        engine = MemoryEngine(db_path=db, backend="sqlite")
        engine.store(MemoryEntry(project="dry", content="dry run", category="fact"))

        backup_path = tmp_path / "backup.zip"
        create_backup(engine, backup_path)

        restore_db = tmp_path / "restore.db"
        target = MemoryEngine(db_path=restore_db, backend="sqlite")
        stats = restore_backup(target, backup_path, dry_run=True)
        assert stats["dry_run"] is True
        assert target.recall(project="dry") == []
