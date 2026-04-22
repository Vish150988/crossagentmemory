# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.4] - 2026-04-21

### Added
- Schema versioning system (`agentmemory/backends/migrations.py`):
  - `schema_version` table tracked on both SQLite and PostgreSQL.
  - `CURRENT_SCHEMA_VERSION` constant for future migrations.
  - `run_migrations()` automatically applied when backends initialize.
- PostgreSQL connection pooling in `PostgresBackend`:
  - Reuses a single cached connection across queries.
  - Automatic reconnection on stale/closed connections.
  - `PostgresBackend.close()` for explicit cleanup.
- `tests/test_migrations.py` covering version table creation, idempotency, and get/set operations.

### Changed
- `SQLiteBackend.init()` and `PostgresBackend.init()` now call `run_migrations()` after table creation.
- `PostgresBackend` methods now invalidate the cached connection on exceptions to force reconnection.

## [0.3.3] - 2026-04-21

### Added
- `docker-compose.yml` with PostgreSQL 17 + pgvector for team deployments.
- `MemoryBackend.get_project_description()` abstract method with SQLite and PostgreSQL implementations.
- `MemoryEngine.get_project_description()` public API.
- `tests/test_migrate.py` covering SQLite→SQLite migration and embedding preservation.
- README "Storage Backends" section with Docker Compose, env var, and programmatic examples.

### Changed
- CLI `init --backend` now actually uses the selected backend (was previously ignored).
- CLI `migrate` enhanced with `--from-db-path`, `--to-dsn`, embedding migration, and project description preservation.
- `agentmemory/__init__.py` now exports `MemoryEngine`, `MemoryEntry`, `MemoryBackend`, `SQLiteBackend`, and `PostgresBackend` (when available).
- SQLite backend enables WAL mode (`PRAGMA journal_mode=WAL`) for better concurrent read/write performance.

### Fixed
- Removed direct `_connection()` access from CLI `migrate` command; now uses public backend API.

## [0.3.2] - 2026-04-21

### Added
- Pluggable storage backend system:
  - `agentmemory/backends/base.py` — `MemoryBackend` abstract interface.
  - `agentmemory/backends/sqlite.py` — Full SQLite implementation (extracted from `core.py`).
  - `agentmemory/backends/postgres.py` — Full PostgreSQL implementation via `psycopg`.
  - `agentmemory/backends/__init__.py` — Factory and optional exports.
- `MemoryEngine` now accepts `backend="sqlite" | "postgres" | "auto"` and delegates to `self.backend`.
- Optional dependency: `pip install agentmemory[postgres]` for PostgreSQL support.
- `tests/test_storage_backends.py` for backend interface contract tests.
- Auto-detection: uses PostgreSQL when `DATABASE_URL` is set, otherwise SQLite.

### Changed
- `core.py` refactored from monolithic SQLite engine to thin wrapper over pluggable backends.
- `decay.py` and `llm_features.py` refactored to use public `engine.recall()` instead of direct SQL connections.

## [0.3.1] - 2026-04-18

### Added
- LLM client abstraction (`agentmemory/llm.py`) supporting OpenAI, Anthropic, and Ollama.
- LLM-powered project and session summarization.
- Smart auto-tagging via LLM (`agentmemory capture "..." --auto-tag`).
- Memory conflict detection — finds contradictory memories automatically.
- Weekly digest generation (`agentmemory digest`).
- REST API server (`agentmemory server`) on port 8746 with `/api/memories`, `/api/search`, `/api/summarize`, `/api/digest`.
- CLI `check-conflicts` command.

### Changed
- Version bump and stability improvements across dashboard and MCP server.

## [0.3.0] - 2026-04-15

### Added
- Shell integration for bash, zsh, fish, and PowerShell — auto-injects context into agents.
- Background daemon (`agentmemory daemon start`) for silent auto-capture.
- Memory graph visualization — relationship graph with category clusters and timeline.
- Mem0 importer (`agentmemory import <path> --format mem0`).
- Markdown and JSON importers.
- Social sharing — auto-post milestones to Twitter and LinkedIn.
- VS Code extension scaffold.
- `agentmemory graph` CLI command.
- `agentmemory post` CLI command.

## [0.2.0] - 2026-04-10

### Added
- Team sync via git — export/import shared memories via `.agent-memory/` folder.
- Auto-capture from git log, shell history, and Claude sessions.
- MCP server (stdio) for Cursor/Copilot/Claude integration.
- Web dashboard (FastAPI) on port 8745.
- `agentmemory team export`, `agentmemory team import`, `agentmemory team status` commands.
- `agentmemory capture-auto` command.
- `agentmemory mcp` command.
- `agentmemory dashboard` command.

## [0.1.0] - 2026-04-05

### Added
- Core SQLite memory engine with CRUD operations.
- CLI (`agentmemory` / `am`) with `init`, `capture`, `recall`, `search`, `load`, `export`, `sync`, `stats`, `delete`.
- Semantic search via TF-IDF + cosine similarity (pure numpy, no heavy dependencies).
- Auto-summarization of projects and sessions.
- Confidence decay and reinforcement algorithms.
- `CLAUDE.md` auto-generation and sync.
- Git hooks for automatic `CLAUDE.md` updates on every commit.
- Memory categories: `decision`, `preference`, `fact`, `action`, `error`.
