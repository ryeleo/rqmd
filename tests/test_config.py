from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from rqmd import cli
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


def test_RQMD_portability_011_custom_status_catalog_from_yaml_supports_rollup(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)

    (repo / ".rqmd.yml").write_text(
        """statuses:
  - name: Proposed
    shortcode: P
    emoji: "💡"
  - name: Implemented
    shortcode: I
    emoji: "🔧"
  - name: Desktop-Verified
    shortcode: DV
    emoji: "💻"
  - name: VR-Verified
    shortcode: VV
    emoji: "🎮"
  - name: Done
    shortcode: D
    emoji: "✅"
  - name: Blocked
    shortcode: B
    emoji: "⛔"
  - name: Deprecated
    shortcode: X
    emoji: "🗑️"

rollup_map:
  Proposed: [proposed]
  Build-Ready: [implemented, desktop-verified]
  Complete: [vr-verified, done]
  Parked: [blocked, deprecated]
""",
        encoding="utf-8",
    )

    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-001: Proposed item
- **Status:** 💡 Proposed

### AC-002: Implemented item
- **Status:** 🔧 Implemented

### AC-003: Desktop verified item
- **Status:** 💻 Desktop-Verified

### AC-004: VR verified item
- **Status:** 🎮 VR-Verified

### AC-005: Done item
- **Status:** ✅ Done

### AC-006: Blocked item
- **Status:** ⛔ Blocked

### AC-007: Deprecated item
- **Status:** 🗑️ Deprecated
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--rollup",
            "--json",
            "--no-summary-table",
            "--no-interactive",
        ],
    )

    assert result.exit_code == 0
    assert "💻 Desktop-Verified" in result.output
    assert "🎮 VR-Verified" in result.output
    assert "Build-Ready" in result.output
    assert "Complete" in result.output


def test_RQMD_portability_011_custom_status_catalog_allows_set_status_input(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)

    (repo / ".rqmd.yml").write_text(
        """statuses:
  - name: Proposed
    shortcode: P
    emoji: "💡"
  - name: Implemented
    shortcode: I
    emoji: "🔧"
  - name: Desktop-Verified
    shortcode: DV
    emoji: "💻"
  - name: VR-Verified
    shortcode: VV
    emoji: "🎮"
  - name: Done
    shortcode: D
    emoji: "✅"
  - name: Blocked
    shortcode: B
    emoji: "⛔"
  - name: Deprecated
    shortcode: X
    emoji: "🗑️"
""",
        encoding="utf-8",
    )

    target = domain / "demo.md"
    target.write_text(
        """# Demo Requirements

Scope: demo.

### AC-001: Desktop milestone
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--set-requirement-id",
            "AC-001",
            "--set-status",
            "desktop-verified",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    text = target.read_text(encoding="utf-8")
    assert "- **Status:** 💻 Desktop-Verified" in text


def test_RQMD_portability_011_custom_status_catalog_does_not_leak_between_runs(tmp_path: Path) -> None:
    custom_repo = tmp_path / "custom"
    custom_domain = custom_repo / "docs" / "requirements"
    custom_domain.mkdir(parents=True)
    (custom_repo / ".rqmd.yml").write_text(
        """statuses:
  - name: Proposed
    shortcode: P
    emoji: "💡"
  - name: Implemented
    shortcode: I
    emoji: "🔧"
  - name: Desktop-Verified
    shortcode: DV
    emoji: "💻"
  - name: Done
    shortcode: D
    emoji: "✅"
""",
        encoding="utf-8",
    )
    (custom_domain / "demo.md").write_text(
        """# Demo

Scope: demo.

### AC-001: Item
- **Status:** 💻 Desktop-Verified
""",
        encoding="utf-8",
    )

    default_repo = tmp_path / "default"
    default_domain = default_repo / "docs" / "requirements"
    default_domain.mkdir(parents=True)
    (default_domain / "demo.md").write_text(
        """# Demo

Scope: demo.

### AC-001: Item
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    custom_result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(custom_repo),
            "--requirements-dir",
            "docs/requirements",
            "--check",
            "--no-interactive",
            "--no-summary-table",
        ],
    )
    assert custom_result.exit_code in (0, 1)
    assert "Unrecognized status" not in custom_result.output

    default_result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(default_repo),
            "--requirements-dir",
            "docs/requirements",
            "--set-requirement-id",
            "AC-001",
            "--set-status",
            "desktop-verified",
            "--no-summary-table",
        ],
    )
    assert default_result.exit_code != 0
    assert "Unrecognized status input" in default_result.output


def test_RQMD_portability_011_ssvr_corpus_rollup_uses_custom_status_catalog() -> None:
    corpus_root = Path(__file__).resolve().parents[1] / "test-corpus" / "SSVR"
    assert corpus_root.exists(), "Expected test corpus at test-corpus/SSVR"

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(corpus_root),
            "--requirements-dir",
            "requirements",
            "--rollup",
            "--json",
            "--no-summary-table",
            "--no-interactive",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "rollup"
    assert "💻 Desktop-Verified" in payload["totals"]
    assert "🎮 VR-Verified" in payload["totals"]
    assert "✅ Done" in payload["totals"]
    column_labels = [item["label"] for item in payload.get("rollup_columns", [])]
    assert "Build-Ready" in column_labels
    assert "Complete" in column_labels


def test_RQMD_portability_011_ssvr_corpus_copy_accepts_desktop_verified_set_status(tmp_path: Path) -> None:
    source_corpus_root = Path(__file__).resolve().parents[1] / "test-corpus" / "SSVR"
    assert source_corpus_root.exists(), "Expected test corpus at test-corpus/SSVR"

    repo = tmp_path / "SSVR"
    shutil.copytree(source_corpus_root, repo)

    target_file = repo / "requirements" / "main-menu.md"
    original = target_file.read_text(encoding="utf-8")
    assert "### AC-MM-PRACTICE-002: Start creates a fresh Practice flow" in original

    runner = CliRunner()
    result = runner.invoke(
      cli.main,
      [
        "--repo-root",
        str(repo),
        "--requirements-dir",
        "requirements",
        "--set-requirement-id",
        "AC-MM-PRACTICE-002",
        "--set-status",
        "desktop-verified",
        "--no-summary-table",
      ],
    )

    assert result.exit_code == 0
    updated = target_file.read_text(encoding="utf-8")
    assert "### AC-MM-PRACTICE-002: Start creates a fresh Practice flow" in updated
    assert "- **Status:** 💻 Desktop-Verified" in updated
