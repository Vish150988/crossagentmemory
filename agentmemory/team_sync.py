"""Team sync — share memories via git-tracked `.agent-memory/` folder."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import MemoryEngine, MemoryEntry

TEAM_FOLDER = ".agent-memory"
TEAM_GITIGNORE = """# AgentMemory team sync folder
# Commit memory exports to share context with your team.
# Ignore large or auto-generated files:
*.log
backup/
"""


def _content_hash(content: str) -> str:
    """Generate a stable hash for deduplication."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _get_team_folder(cwd: Path | None = None) -> Path:
    """Resolve the team sync folder in the current project."""
    cwd = cwd or Path.cwd()
    return cwd / TEAM_FOLDER


def team_export(
    project: str,
    cwd: Path | None = None,
    engine: MemoryEngine | None = None,
) -> Path:
    """Export project memories to `.agent-memory/` as JSON for team sharing.

    Returns the path to the exported file.
    """
    engine = engine or MemoryEngine()
    folder = _get_team_folder(cwd)
    folder.mkdir(exist_ok=True)

    # Write gitignore if missing
    gitignore = folder / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(TEAM_GITIGNORE, encoding="utf-8")

    memories = engine.recall(project=project, limit=10000)

    data: dict[str, Any] = {
        "project": project,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "memories": [],
    }

    for m in memories:
        data["memories"].append(
            {
                "content": m.content,
                "category": m.category,
                "confidence": m.confidence,
                "source": m.source,
                "tags": m.tags,
                "timestamp": m.timestamp,
                "session_id": m.session_id,
                "metadata": m.metadata,
                "_hash": _content_hash(m.content),
            }
        )

    filename = f"memory-{project}-{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.json"
    export_path = folder / filename
    export_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # Also write a latest.json symlink-ish file (just overwrite)
    latest = folder / f"memory-{project}-latest.json"
    latest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return export_path


def team_import(
    project: str,
    cwd: Path | None = None,
    engine: MemoryEngine | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """Import team-shared memories from `.agent-memory/` into local DB.

    Returns counts: {'imported': int, 'skipped': int, 'files': int}
    """
    engine = engine or MemoryEngine()
    folder = _get_team_folder(cwd)

    if not folder.exists():
        return {"imported": 0, "skipped": 0, "files": 0}

    # Build set of existing content hashes for deduplication
    existing = engine.recall(project=project, limit=10000)
    existing_hashes = {_content_hash(m.content) for m in existing}

    imported = 0
    skipped = 0
    files_read = 0

    for file_path in sorted(folder.glob("memory-*.json")):
        if file_path.name.endswith("-latest.json"):
            continue  # Skip symlink duplicate
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if data.get("project") != project:
            continue

        files_read += 1
        for mem in data.get("memories", []):
            h = mem.get("_hash") or _content_hash(mem["content"])
            if h in existing_hashes:
                skipped += 1
                continue

            if not dry_run:
                entry = MemoryEntry(
                    project=project,
                    session_id=mem.get("session_id", "team-sync"),
                    category=mem.get("category", "fact"),
                    content=mem["content"],
                    confidence=mem.get("confidence", 1.0),
                    source=mem.get("source", "team"),
                    tags=mem.get("tags", ""),
                    timestamp=mem.get("timestamp"),
                    metadata=mem.get("metadata", "{}"),
                )
                engine.store(entry)
                existing_hashes.add(h)
            imported += 1

    return {"imported": imported, "skipped": skipped, "files": files_read}


def team_status(
    project: str, cwd: Path | None = None, engine: MemoryEngine | None = None
) -> dict[str, Any]:
    """Show team sync status for a project."""
    folder = _get_team_folder(cwd)
    engine = engine or MemoryEngine()

    local_count = len(engine.recall(project=project, limit=10000))
    export_files = list(folder.glob("memory-*.json")) if folder.exists() else []
    latest = folder / f"memory-{project}-latest.json" if folder.exists() else None

    return {
        "project": project,
        "local_memories": local_count,
        "team_folder": str(folder),
        "team_folder_exists": folder.exists(),
        "export_files": len([f for f in export_files if not f.name.endswith("-latest.json")]),
        "latest_export": str(latest) if latest and latest.exists() else None,
    }
