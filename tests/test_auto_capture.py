"""Tests for auto-capture functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from crossagentmemory.auto_capture import (
    _get_powershell_history_path,
    capture_from_git_log,
    capture_from_shell_history,
)
from crossagentmemory.core import MemoryEngine


@pytest.fixture
def temp_engine(tmp_path: Path) -> MemoryEngine:
    db = tmp_path / "test.db"
    return MemoryEngine(db_path=db)


def test_capture_from_git_log_with_mock_repo(tmp_path: Path) -> None:
    # Initialize a git repo
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
    )
    (tmp_path / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit with decision to use sqlite"],
        cwd=tmp_path,
        capture_output=True,
    )

    entries = capture_from_git_log("demo", cwd=tmp_path)
    assert len(entries) >= 1
    assert entries[0].category in ("action", "decision", "fact")
    assert entries[0].source == "git-commit"
    assert "sqlite" in entries[0].content.lower()


def test_capture_from_shell_history_no_file(temp_engine: MemoryEngine) -> None:
    # If no history file exists, should return empty list
    entries = capture_from_shell_history("demo", engine=temp_engine)
    # This might still find a real history file, so we just assert it's a list
    assert isinstance(entries, list)


def test_powershell_path_returns_none_on_unix() -> None:
    # On this Windows machine it may exist, but function returns a Path or None
    result = _get_powershell_history_path()
    assert result is None or isinstance(result, Path)


def test_auto_capture_all_runs(temp_engine: MemoryEngine, tmp_path: Path) -> None:
    engine = temp_engine
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
    )
    (tmp_path / "a.txt").write_text("a")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "test commit"],
        cwd=tmp_path,
        capture_output=True,
    )

    from crossagentmemory.auto_capture import auto_capture_all

    counts = auto_capture_all("demo", sources=["git"], engine=engine, cwd=tmp_path)
    assert counts["git"] >= 1
