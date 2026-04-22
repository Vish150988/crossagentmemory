"""Configuration management for CrossAgentMemory.

Reads from ~/.crossagentmemory/config.yaml (created on first access if missing).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .core import DEFAULT_MEMORY_DIR

logger = logging.getLogger(__name__)

CONFIG_PATH = DEFAULT_MEMORY_DIR / "config.yaml"

DEFAULT_CONFIG = """# CrossAgentMemory configuration
# Restart your agent or re-create MemoryEngine for changes to take effect.

# Storage backend: sqlite | postgres | auto
backend: auto

# SQLite database path (ignored when using postgres)
db_path: null

# PostgreSQL connection URL (used when backend=postgres or auto with env var)
database_url: null

# LLM settings (optional)
llm:
  provider: openai  # openai | anthropic | ollama
  model: gpt-4o-mini
  api_key: null
  base_url: null
"""


def _ensure_config() -> None:
    """Create default config file if it doesn't exist."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(DEFAULT_CONFIG, encoding="utf-8")
        logger.info("Created default config at %s", CONFIG_PATH)


def load_config() -> dict[str, Any]:
    """Load configuration from YAML file. Falls back to defaults."""
    _ensure_config()
    try:
        import yaml

        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except ImportError:
        logger.debug("PyYAML not installed, using env vars only")
        return {}
    except Exception as e:
        logger.warning("Failed to load config: %s", e)
        return {}


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a single config value by dot-notation key (e.g., 'llm.provider')."""
    cfg = load_config()
    parts = key.split(".")
    for part in parts:
        if isinstance(cfg, dict):
            cfg = cfg.get(part)
        else:
            return default
    return cfg if cfg is not None else default


def resolve_backend_from_config() -> dict[str, Any]:
    """Return kwargs for MemoryEngine based on config + env vars.

    Precedence: env vars > config file > defaults
    """
    kwargs: dict[str, Any] = {}

    backend = os.environ.get("CROSSAGENTMEMORY_BACKEND") or get_config_value("backend", "auto")
    kwargs["backend"] = backend

    db_path = os.environ.get("CROSSAGENTMEMORY_DB_PATH") or get_config_value("db_path")
    if db_path:
        kwargs["db_path"] = Path(db_path)

    database_url = os.environ.get("DATABASE_URL") or get_config_value("database_url")
    if database_url:
        os.environ["DATABASE_URL"] = database_url

    return kwargs
