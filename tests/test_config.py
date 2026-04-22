"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

from crossagentmemory.config import (
    CONFIG_PATH,
    get_config_value,
    load_config,
    resolve_backend_from_config,
)


class TestConfig:
    def test_load_config_creates_default(self, tmp_path: Path) -> None:
        # Temporarily redirect config path
        original = CONFIG_PATH
        try:
            from crossagentmemory import config as cfg_mod

            cfg_mod.CONFIG_PATH = tmp_path / "config.yaml"
            cfg = load_config()
            assert isinstance(cfg, dict)
            assert cfg_mod.CONFIG_PATH.exists()
        finally:
            cfg_mod.CONFIG_PATH = original

    def test_get_config_value_missing(self, tmp_path: Path) -> None:
        original = CONFIG_PATH
        try:
            from crossagentmemory import config as cfg_mod

            cfg_mod.CONFIG_PATH = tmp_path / "empty.yaml"
            cfg_mod.CONFIG_PATH.write_text("", encoding="utf-8")
            assert get_config_value("backend", "auto") == "auto"
            assert get_config_value("llm.model", "gpt-4") == "gpt-4"
        finally:
            cfg_mod.CONFIG_PATH = original

    def test_resolve_backend_from_config_env_override(self, monkeypatch) -> None:
        monkeypatch.setenv("CROSSAGENTMEMORY_BACKEND", "sqlite")
        kwargs = resolve_backend_from_config()
        assert kwargs["backend"] == "sqlite"
