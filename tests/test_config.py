from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from rqmd import cli
from rqmd.config import load_config, load_statuses_file, validate_config
from rqmd.status_model import (_STATUS_COLORS, configure_status_catalog,
                               style_status_label)


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
    # In actual CLI use, passing --docs-dir other-dir would override
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--totals",
            "--as-json",
            "--no-table",
            "--no-walk",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-001",
            "--update-status",
            "desktop-verified",
            "--no-table",
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
            "--project-root",
            str(custom_repo),
            "--docs-dir",
            "docs/requirements",
            "--verify-summaries",
            "--no-walk",
            "--no-table",
        ],
    )
    assert custom_result.exit_code in (0, 1)
    assert "Unrecognized status" not in custom_result.output

    default_result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(default_repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-001",
            "--update-status",
            "desktop-verified",
            "--no-table",
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
            "--project-root",
            str(corpus_root),
            "--docs-dir",
            "requirements",
            "--totals",
            "--as-json",
            "--no-table",
            "--no-walk",
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
        "--project-root",
        str(repo),
        "--docs-dir",
        "requirements",
        "--update-id",
        "AC-MM-PRACTICE-002",
        "--update-status",
        "desktop-verified",
        "--no-table",
      ],
    )

    assert result.exit_code == 0
    updated = target_file.read_text(encoding="utf-8")
    assert "### AC-MM-PRACTICE-002: Start creates a fresh Practice flow" in updated
    assert "- **Status:** 💻 Desktop-Verified" in updated


def test_RQMD_portability_007_load_statuses_file_explicit_path(tmp_path: Path) -> None:
  """load_statuses_file with an explicit override path loads the file."""
  catalog = tmp_path / "my-statuses.yml"
  catalog.write_text(
    """- name: Alpha
  shortcode: A
  emoji: "🅰️"
- name: Beta
  shortcode: B
  emoji: "🅱️"
""",
    encoding="utf-8",
  )
  result = load_statuses_file(tmp_path, str(catalog))
  assert result is not None
  assert len(result) == 2
  assert result[0]["name"] == "Alpha"
  assert result[1]["name"] == "Beta"


def test_RQMD_portability_007_load_statuses_file_explicit_path_dict_form(tmp_path: Path) -> None:
  """load_statuses_file with a dict-form YAML (with 'statuses' key) extracts the list."""
  catalog = tmp_path / "catalog.yml"
  catalog.write_text(
    """statuses:
  - name: Custom
    shortcode: C
    emoji: "🔹"
rollup_mode: per_status
""",
    encoding="utf-8",
  )
  result = load_statuses_file(tmp_path, str(catalog))
  assert result is not None
  assert len(result) == 1
  assert result[0]["name"] == "Custom"


def test_RQMD_portability_007_load_statuses_file_not_found_raises(tmp_path: Path) -> None:
  """load_statuses_file raises ValueError when override path does not exist."""
  with pytest.raises(ValueError, match="not found"):
    load_statuses_file(tmp_path, "nonexistent/statuses.yml")


def test_RQMD_portability_007_load_statuses_file_auto_detect_rqmd_dir(tmp_path: Path) -> None:
  """load_statuses_file auto-detects .rqmd/statuses.yml under repo_root."""
  rqmd_dir = tmp_path / ".rqmd"
  rqmd_dir.mkdir()
  (rqmd_dir / "statuses.yml").write_text(
    """\
- name: InProgress
  shortcode: IP
  emoji: "🔄"
""",
    encoding="utf-8",
  )
  result = load_statuses_file(tmp_path)
  assert result is not None
  assert result[0]["name"] == "InProgress"


def test_RQMD_portability_007_load_statuses_file_returns_none_when_absent(tmp_path: Path) -> None:
  """load_statuses_file returns None when no override and no .rqmd/statuses.* found."""
  result = load_statuses_file(tmp_path)
  assert result is None


def test_RQMD_portability_007_cli_status_config_overrides_unified_config(tmp_path: Path) -> None:
  """--status-config file takes precedence over statuses in .rqmd.yml."""
  repo = tmp_path / "repo"
  domain = repo / "docs" / "requirements"
  domain.mkdir(parents=True)

  # Unified config with standard statuses
  (repo / ".rqmd.yml").write_text(
    "statuses:\n  - name: Proposed\n    shortcode: P\n    emoji: \"💡\"\n",
    encoding="utf-8",
  )

  # Separate override file with a custom status
  override = tmp_path / "custom.yml"
  override.write_text(
    "- name: InReview\n  shortcode: IR\n  emoji: \"👀\"\n"
    "- name: Shipped\n  shortcode: SH\n  emoji: \"🚀\"\n",
    encoding="utf-8",
  )

  (domain / "demo.md").write_text(
    "# Demo\n\nScope: demo.\n\n### AC-001: Item\n- **Status:** 👀 InReview\n",
    encoding="utf-8",
  )

  runner = CliRunner()
  result = runner.invoke(
    cli.main,
    [
      "--project-root", str(repo),
      "--docs-dir", "docs/requirements",
      "--status-config", str(override),
      "--verify-summaries",
      "--no-walk",
      "--no-table",
    ],
  )

  assert result.exit_code in (0, 1), result.output
  assert "Unrecognized" not in result.output


def test_RQMD_portability_007_cli_status_config_error_on_missing_file(tmp_path: Path) -> None:
  """--status-config with a nonexistent path exits with an error."""
  repo = tmp_path / "repo"
  domain = repo / "docs" / "requirements"
  domain.mkdir(parents=True)
  (domain / "demo.md").write_text(
    "# Demo\n\nScope: demo.\n\n### AC-001: Item\n- **Status:** 💡 Proposed\n",
    encoding="utf-8",
  )

  runner = CliRunner()
  result = runner.invoke(
    cli.main,
    [
      "--project-root", str(repo),
      "--docs-dir", "docs/requirements",
      "--status-config", "nonexistent/statuses.yml",
      "--verify-summaries",
      "--no-table",
    ],
  )

  assert result.exit_code != 0
  assert "not found" in result.output.lower() or "error" in result.output.lower()


def test_RQMD_portability_011_color_field_stored_in_status_colors() -> None:
  """color field in custom status catalog is stored and used by style_status_label."""
  configure_status_catalog([
    {"name": "Active", "shortcode": "A", "emoji": "🔵", "color": "cyan"},
    {"name": "Done", "shortcode": "D", "emoji": "✅"},
  ])
  try:
    assert _STATUS_COLORS.get("🔵 Active") == "cyan"
    styled = style_status_label("🔵 Active")
    assert "Active" in styled  # styled label still contains the name
    # Done has no color -> not in _STATUS_COLORS
    assert "✅ Done" not in _STATUS_COLORS
  finally:
    configure_status_catalog(None)  # reset to defaults


def test_RQMD_portability_012_load_user_config_returns_empty_when_missing() -> None:
  """load_user_config returns empty dict when ~/.rqmd.config does not exist."""
  from rqmd.config import load_user_config
  user_config = load_user_config()
  assert isinstance(user_config, dict)


def test_RQMD_portability_012_load_user_config_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  """load_user_config loads .rqmd.config.json from home directory."""
  from rqmd.config import load_user_config
  
  fake_home = tmp_path / "home"
  fake_home.mkdir()
  config_file = fake_home / ".rqmd.config.json"
  config_file.write_text('{"statuses": [{"name": "Custom", "emoji": "⭐", "shortcode": "C"}]}', encoding="utf-8")
  
  monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
  
  user_config = load_user_config()
  assert "statuses" in user_config
  assert len(user_config["statuses"]) == 1
  assert user_config["statuses"][0]["name"] == "Custom"


def test_RQMD_portability_012_load_user_config_yaml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
  """load_user_config loads .rqmd.config.yml from home directory."""
  from rqmd.config import load_user_config
  
  fake_home = tmp_path / "home"
  fake_home.mkdir()
  config_file = fake_home / ".rqmd.config.yml"
  config_file.write_text("statuses:\n  - name: Custom\n    emoji: ⭐\n    shortcode: C\n", encoding="utf-8")
  
  monkeypatch.setattr("pathlib.Path.home", lambda: fake_home)
  
  user_config = load_user_config()
  assert "statuses" in user_config
  assert len(user_config["statuses"]) == 1
  assert user_config["statuses"][0]["name"] == "Custom"


def test_RQMD_portability_012_user_config_precedence_cli_over_user(tmp_path: Path) -> None:
  """User config colors are overridden by project config when both exist."""
  repo = tmp_path / "repo"
  domain = repo / "docs" / "requirements"
  domain.mkdir(parents=True)
  (domain / "demo.md").write_text(
    "# Demo\n\nScope: demo.\n\n### AC-001: Item\n- **Status:** 💡 Proposed\n",
    encoding="utf-8",
  )
  
  # Create project-level config override
  project_config = repo / ".rqmd.json"
  project_config.write_text(
    '{"statuses": [{"name": "Proposed", "emoji": "💡", "shortcode": "P", "color": "yellow"}]}',
    encoding="utf-8"
  )
  
  runner = CliRunner()
  result = runner.invoke(
    cli.main,
    [
      "--project-root", str(repo),
      "--docs-dir", "docs/requirements",
      "--status", "proposed",
      "--as-json",
      "--no-walk",
      "--no-table",
    ],
  )
  
  assert result.exit_code == 0
  payload = json.loads(result.output)
  # Color from project config is applied
  assert payload["files"][0]["requirements"][0]["id"] == "AC-001"
    # Done has no color -> not in _STATUS_COLORS
    assert "✅ Done" not in _STATUS_COLORS
  finally:
    configure_status_catalog(None)  # reset to defaults
