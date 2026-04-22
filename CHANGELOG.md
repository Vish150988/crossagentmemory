# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.7] - 2026-04-21

### Added
- SQLite FTS5 full-text search (`memories_fts` virtual table):
  - Ranked search using `bm25` relevance scoring.
  - Fallback to `LIKE` search when FTS5 is unavailable.
  - Manual sync in `store()`, `update_memory()`, `delete_memory()` (no triggers).
- PyPI auto-publish workflow (`.github/workflows/publish.yml`):
  - Builds and publishes to PyPI on every `v*` tag push via trusted publishing (OIDC).
- `tests/test_fts5.py` covering FTS5 search, ranking, and LIKE fallback.

### Changed
- Hardened GitHub Actions CI:
  - Uses `python -m ruff` / `python -m pytest` for PATH reliability.
  - Added `pg_isready` retry loop in `test-postgres` job.
- PyPI URLs in `pyproject.toml` updated to `Vish150988`.

### Fixed
- Legacy FTS5 triggers from earlier dev builds are auto-dropped on init.
- Flaky `test_team_import_adds_new_memories` handles duplicate exports across timestamps.

## [0.3.6] - 2026-04-21

### Added
- Configuration file support (`crossagentmemory/config.py`):
  - Auto-creates `~/.crossagentmemory/config.yaml` on first access.
  - Supports `backend`, `db_path`, `database_url`, and `llm` settings.
  - Env vars override config values (`CROSSAGENTMEMORY_BACKEND`, `CROSSAGENTMEMORY_DB_PATH`).
- `MemoryEngine()` reads backend and db_path from config + env vars automatically.
- Dashboard inline memory editing:
  - `PATCH /api/memories/{id}` endpoint.
  - ✎ edit button per row with prompt-based editing of content, category, confidence, and tags.
- `tests/test_config.py` for config loading, value resolution, and env override.
- `pyyaml>=6.0` added to `[dev]` and `[all]` optional dependencies.

### Fixed
- Reverted aggressive SQLite connection caching that caused Windows file-lock errors.
- SQLite backend returns to per-query open/close with WAL mode retained.

## [0.3.5] - 2026-04-21

### Added
- Backup and restore system (`crossagentmemory/backends/backup.py`):
  - `create_backup()` exports memories, projects, and embeddings to `.zip` or `.json`
  - `restore_backup()` imports from `.zip` or `.json` with ID remapping
  - Embeddings are restored by mapping old memory IDs to new ones
- CLI commands:
  - `crossagentmemory backup [--project] [--output]` — creates a dated `.zip` by default
  - `crossagentmemory restore <path> [--dry-run]` — restore with preview option
- `MemoryBackend.list_embedding_models(project)` — returns distinct embedding model names
- Tests: `tests/test_backup.py` covering zip/json backup, restore, and dry-run

## [0.3.4] - 2026-04-21

### Added
- Schema versioning system (`crossagentmemory/backends/migrations.py`):
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
- `crossagentmemory/__init__.py` now exports `MemoryEngine`, `MemoryEntry`, `MemoryBackend`, `SQLiteBackend`, and `PostgresBackend` (when available).
- SQLite backend enables WAL mode (`PRAGMA journal_mode=WAL`) for better concurrent read/write performance.

### Fixed
- Removed direct `_connection()` access from CLI `migrate` command; now uses public backend API.

## [0.3.2] - 2026-04-21

### Added
- Pluggable storage backend system:
  - `crossagentmemory/backends/base.py` — `MemoryBackend` abstract interface.
  - `crossagentmemory/backends/sqlite.py` — Full SQLite implementation (extracted from `core.py`).
  - `crossagentmemory/backends/postgres.py` — Full PostgreSQL implementation via `psycopg`.
  - `crossagentmemory/backends/__init__.py` — Factory and optional exports.
- `MemoryEngine` now accepts `backend="sqlite" | "postgres" | "auto"` and delegates to `self.backend`.
- Optional dependency: `pip install crossagentmemory[postgres]` for PostgreSQL support.
- `tests/test_storage_backends.py` for backend interface contract tests.
- Auto-detection: uses PostgreSQL when `DATABASE_URL` is set, otherwise SQLite.

### Changed
- `core.py` refactored from monolithic SQLite engine to thin wrapper over pluggable backends.
- `decay.py` and `llm_features.py` refactored to use public `engine.recall()` instead of direct SQL connections.

## [0.3.1] - 2026-04-18

### Added
- LLM client abstraction (`crossagentmemory/llm.py`) supporting OpenAI, Anthropic, and Ollama.
- LLM-powered project and session summarization.
- Smart auto-tagging via LLM (`crossagentmemory capture "..." --auto-tag`).
- Memory conflict detection — finds contradictory memories automatically.
- Weekly digest generation (`crossagentmemory digest`).
- REST API server (`crossagentmemory server`) on port 8746 with `/api/memories`, `/api/search`, `/api/summarize`, `/api/digest`.
- CLI `check-conflicts` command.

### Changed
- Version bump and stability improvements across dashboard and MCP server.

## [0.3.0] - 2026-04-15

### Added
- Shell integration for bash, zsh, fish, and PowerShell — auto-injects context into agents.
- Background daemon (`crossagentmemory daemon start`) for silent auto-capture.
- Memory graph visualization — relationship graph with category clusters and timeline.
- Mem0 importer (`crossagentmemory import <path> --format mem0`).
- Markdown and JSON importers.
- Social sharing — auto-post milestones to Twitter and LinkedIn.
- VS Code extension scaffold.
- `crossagentmemory graph` CLI command.
- `crossagentmemory post` CLI command.

## [0.2.0] - 2026-04-10

### Added
- Team sync via git — export/import shared memories via `.crossagentmemory/` folder.
- Auto-capture from git log, shell history, and Claude sessions.
- MCP server (stdio) for Cursor/Copilot/Claude integration.
- Web dashboard (FastAPI) on port 8745.
- `crossagentmemory team export`, `crossagentmemory team import`, `crossagentmemory team status` commands.
- `crossagentmemory capture-auto` command.
- `crossagentmemory mcp` command.
- `crossagentmemory dashboard` command.

## [0.1.0] - 2026-04-05

### Added
- Core SQLite memory engine with CRUD operations.
- CLI (`crossagentmemory` / `cam`) with `init`, `capture`, `recall`, `search`, `load`, `export`, `sync`, `stats`, `delete`.
- Semantic search via TF-IDF + cosine similarity (pure numpy, no heavy dependencies).
- Auto-summarization of projects and sessions.
- Confidence decay and reinforcement algorithms.
- `CLAUDE.md` auto-generation and sync.
- Git hooks for automatic `CLAUDE.md` updates on every commit.
- Memory categories: `decision`, `preference`, `fact`, `action`, `error`.
