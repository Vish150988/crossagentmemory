"""PostgreSQL storage backend for CrossAgentMemory.

Requires: pip install psycopg  (or psycopg2)
Configure via DATABASE_URL env var, e.g.:
  DATABASE_URL=postgresql://user:pass@localhost/crossagentmemory
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from ..core import MemoryEntry
from .base import MemoryBackend

try:
    import psycopg

    _HAS_PSYCOG = True
except ImportError:
    try:
        import psycopg2 as psycopg

        _HAS_PSYCOG = True
    except ImportError:
        _HAS_PSYCOG = False


class PostgresBackend(MemoryBackend):
    """PostgreSQL-backed memory storage with pgvector support."""

    def __init__(self, dsn: str | None = None):
        if not _HAS_PSYCOG:
            raise ImportError(
                "PostgreSQL backend requires psycopg. "
                "Install with: pip install crossagentmemory[postgres]"
            )
        self.dsn = dsn or os.environ.get(
            "DATABASE_URL",
            "postgresql://localhost/crossagentmemory",
        )
        self._conn = None

    def _connection(self):
        if self._conn is not None:
            try:
                # Quick health check: if closed, discard
                if not self._conn.closed:
                    return self._conn
            except Exception:
                pass
            self._conn = None
        self._conn = psycopg.connect(self.dsn)
        return self._conn

    def close(self) -> None:
        """Close the underlying cached connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def init(self) -> None:
        conn = psycopg.connect(self.dsn)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id SERIAL PRIMARY KEY,
                        project TEXT NOT NULL DEFAULT 'default',
                        session_id TEXT NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL,
                        category TEXT NOT NULL DEFAULT 'fact',
                        content TEXT NOT NULL,
                        confidence REAL NOT NULL DEFAULT 1.0,
                        source TEXT NOT NULL DEFAULT '',
                        tags TEXT NOT NULL DEFAULT '',
                        metadata JSONB NOT NULL DEFAULT '{}'
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id)"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)"
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS projects (
                        name TEXT PRIMARY KEY,
                        description TEXT,
                        created_at TIMESTAMPTZ NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL,
                        context JSONB NOT NULL DEFAULT '{}'
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS embeddings (
                        memory_id INTEGER PRIMARY KEY REFERENCES memories(id) ON DELETE CASCADE,
                        model_name TEXT NOT NULL,
                        embedding_json JSONB NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL
                    )
                    """
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name)"
                )
                # Try to enable pgvector if available
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                except Exception:
                    pass
            conn.commit()
        finally:
            conn.close()

        from .migrations import run_migrations

        run_migrations(self)

    def store(self, entry: MemoryEntry) -> int:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO memories (
                        project, session_id, timestamp, category,
                        content, confidence, source, tags, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        entry.project,
                        entry.session_id,
                        entry.timestamp,
                        entry.category,
                        entry.content,
                        entry.confidence,
                        entry.source,
                        entry.tags,
                        entry.metadata,
                    ),
                )
                result = cur.fetchone()
                conn.commit()
                return result[0] if result else 0
        except Exception:
            conn.close()
            self._conn = None
            raise

    def recall(
        self,
        project: str | None = None,
        category: str | None = None,
        limit: int = 50,
        session_id: str | None = None,
    ) -> list[MemoryEntry]:
        query = "SELECT * FROM memories WHERE 1=1"
        params: list[Any] = []

        if project:
            query += " AND project = %s"
            params.append(project)
        if category:
            query += " AND category = %s"
            params.append(category)
        if session_id:
            query += " AND session_id = %s"
            params.append(session_id)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [MemoryEntry(**dict(zip(cols, row))) for row in rows]
        except Exception:
            conn.close()
            self._conn = None
            raise

    def search(
        self,
        keyword: str,
        project: str | None = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        query = "SELECT * FROM memories WHERE content ILIKE %s"
        params: list[Any] = [f"%{keyword}%"]

        if project:
            query += " AND project = %s"
            params.append(project)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                cols = [desc[0] for desc in cur.description]
                return [MemoryEntry(**dict(zip(cols, row))) for row in rows]
        except Exception:
            conn.close()
            self._conn = None
            raise

    def get_project_context(self, project: str) -> dict[str, Any]:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT context FROM projects WHERE name = %s", (project,)
                )
                row = cur.fetchone()
                if row:
                    return row[0] if isinstance(row[0], dict) else json.loads(row[0])
                return {}
        except Exception:
            conn.close()
            self._conn = None
            raise

    def get_project_description(self, project: str) -> str:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT description FROM projects WHERE name = %s", (project,)
                )
                row = cur.fetchone()
                return row[0] if row and row[0] else ""
        except Exception:
            conn.close()
            self._conn = None
            raise

    def set_project_context(
        self,
        project: str,
        context: dict[str, Any],
        description: str = "",
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO projects (name, description, created_at, updated_at, context)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT(name) DO UPDATE SET
                        description=EXCLUDED.description,
                        updated_at=EXCLUDED.updated_at,
                        context=EXCLUDED.context
                    """,
                    (project, description, now, now, json.dumps(context)),
                )
            conn.commit()
        except Exception:
            conn.close()
            self._conn = None
            raise

    def stats(self) -> dict[str, Any]:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM memories")
                total = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT project) FROM memories")
                projects = cur.fetchone()[0]

                cur.execute("SELECT COUNT(DISTINCT session_id) FROM memories")
                sessions = cur.fetchone()[0]

                cur.execute(
                    "SELECT category, COUNT(*) FROM memories GROUP BY category"
                )
                categories = {row[0]: row[1] for row in cur.fetchall()}

                return {
                    "total_memories": total,
                    "projects": projects,
                    "sessions": sessions,
                    "by_category": categories,
                }
        except Exception:
            conn.close()
            self._conn = None
            raise

    def delete_project(self, project: str) -> int:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM memories WHERE project = %s", (project,))
                deleted = cur.rowcount
                cur.execute("DELETE FROM projects WHERE name = %s", (project,))
            conn.commit()
            return deleted
        except Exception:
            conn.close()
            self._conn = None
            raise

    def store_embedding(
        self, memory_id: int, model_name: str, embedding: list[float]
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO embeddings (memory_id, model_name, embedding_json, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(memory_id) DO UPDATE SET
                        model_name=EXCLUDED.model_name,
                        embedding_json=EXCLUDED.embedding_json,
                        created_at=EXCLUDED.created_at
                    """,
                    (memory_id, model_name, json.dumps(embedding), now),
                )
            conn.commit()
        except Exception:
            conn.close()
            self._conn = None
            raise

    def get_embeddings(
        self, project: str, model_name: str
    ) -> list[tuple[int, list[float]]]:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT e.memory_id, e.embedding_json
                    FROM embeddings e
                    JOIN memories m ON e.memory_id = m.id
                    WHERE m.project = %s AND e.model_name = %s
                    """,
                    (project, model_name),
                )
                return [(row[0], json.loads(row[1])) for row in cur.fetchall()]
        except Exception:
            conn.close()
            self._conn = None
            raise

    def list_embedding_models(self, project: str) -> list[str]:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT DISTINCT e.model_name
                    FROM embeddings e
                    JOIN memories m ON e.memory_id = m.id
                    WHERE m.project = %s
                    """,
                    (project,),
                )
                return [row[0] for row in cur.fetchall()]
        except Exception:
            conn.close()
            self._conn = None
            raise

    def list_projects(self) -> list[str]:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT project FROM memories ORDER BY project"
                )
                return [row[0] for row in cur.fetchall()]
        except Exception:
            conn.close()
            self._conn = None
            raise

    def get_memory_by_id(self, memory_id: int) -> MemoryEntry | None:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM memories WHERE id = %s", (memory_id,))
                row = cur.fetchone()
                if row:
                    cols = [desc[0] for desc in cur.description]
                    return MemoryEntry(**dict(zip(cols, row)))
                return None
        except Exception:
            conn.close()
            self._conn = None
            raise

    def update_memory(self, memory_id: int, updates: dict[str, Any]) -> bool:
        allowed = {"content", "category", "confidence", "tags"}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return False

        conn = self._connection()
        try:
            with conn.cursor() as cur:
                set_clause = ", ".join(f"{k} = %s" for k in filtered)
                cur.execute(
                    f"UPDATE memories SET {set_clause} WHERE id = %s",
                    (*filtered.values(), memory_id),
                )
                updated = cur.rowcount > 0
            conn.commit()
            return updated
        except Exception:
            conn.close()
            self._conn = None
            raise

    def delete_memory(self, memory_id: int) -> bool:
        conn = self._connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        except Exception:
            conn.close()
            self._conn = None
            raise
