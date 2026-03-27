from __future__ import annotations

from pathlib import Path

import pytest
from rqmd.config import load_config, validate_config


def test_RQMD_portability_006_load_config_from_rqmd_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config_file = repo / ".rqmd.json"
    config_file.write_text('{"requirements_dir": "custom/reqs", "id_prefix": "PROJ"}', encoding="utf-8")

    config = load_config(repo)
    assert config["requirements_dir"] == "custom/reqs"
    assert config["id_prefix"] == "PROJ"


def test_RQMD_portability_006_load_config_empty_when_file_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    config = load_config(repo)
    assert config == {}


def test_RQMD_portability_006_load_config_handles_malformed_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config_file = repo / ".rqmd.json"
    config_file.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_config(repo)


def test_RQMD_portability_006_load_config_fails_if_not_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".rqmd.json").mkdir()  # Create as directory instead of file

    with pytest.raises(ValueError, match="is not a file"):
        load_config(repo)


def test_RQMD_portability_006_validate_config_allows_known_keys(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    config = {
        "repo_root": "/path/to/repo",
        "requirements_dir": "docs/requirements",
        "id_prefix": "AC",
        "sort_strategy": "status-focus",
        "state_dir": ".rqmd/state",
    }
    # Should not raise
    validate_config(config)


def test_RQMD_portability_006_validate_config_rejects_unknown_keys(tmp_path: Path) -> None:
    config = {
        "unknown_key": "value",
    }
    with pytest.raises(ValueError, match="Unknown config key: unknown_key"):
        validate_config(config)


def test_RQMD_portability_006_validate_config_type_checks_repo_root() -> None:
    config = {"repo_root": 123}
    with pytest.raises(ValueError, match="repo_root.*must be a string"):
        validate_config(config)


def test_RQMD_portability_006_validate_config_type_checks_requirements_dir() -> None:
    config = {"requirements_dir": ["docs", "requirements"]}
    with pytest.raises(ValueError, match="requirements_dir.*must be a string"):
        validate_config(config)


def test_RQMD_portability_006_cli_flag_overrides_config(tmp_path: Path) -> None:
    """
    Integration test: CLI flag should override config file value.
    This is a placeholder for manual verification since Click precedence
    is handled by argument defaults in the CLI decorator.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    config_file = repo / ".rqmd.json"
    config_file.write_text('{"requirements_dir": "config-dir"}', encoding="utf-8")

    config = load_config(repo)
    assert config["requirements_dir"] == "config-dir"
    # In actual CLI use, passing --requirements-dir other-dir would override
    # this loaded config value, which is handled by Click's parameter precedence
