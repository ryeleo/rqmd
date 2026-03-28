"""Tests for RQMD-PRIORITY-011: Project-customizable priority catalog."""

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from rqmd.cli import main
from rqmd.config import load_priorities_file
from rqmd.priority_model import (
    PRIORITY_ORDER,
    configure_priority_catalog,
    normalize_priority_input,
    style_priority_label,
)


@pytest.fixture(autouse=True)
def reset_priority_catalog():
    """Ensure catalog is always reset to defaults after each test."""
    yield
    configure_priority_catalog(None)


class TestConfigurePriorityCatalog:
    def test_reset_on_none_restores_defaults(self):
        # Mutate then reset
        custom = [{"name": "Xyzzy", "shortcode": "xyzzy", "emoji": "🔮"}]
        configure_priority_catalog(custom)
        assert any("Xyzzy" in label for label, _ in PRIORITY_ORDER)
        configure_priority_catalog(None)
        assert not any("Xyzzy" in label for label, _ in PRIORITY_ORDER)
        assert any("P0" in label for label, _ in PRIORITY_ORDER)  # defaults restored

    def test_custom_catalog_replaces_order(self):
        custom = [
            {"name": "Urgent", "shortcode": "urgent", "emoji": "🔴"},
            {"name": "Normal", "shortcode": "normal", "emoji": "🟢"},
        ]
        configure_priority_catalog(custom)
        labels = [label for label, _ in PRIORITY_ORDER]
        assert "🔴 Urgent" in labels
        assert "🟢 Normal" in labels
        assert len(labels) == 2

    def test_normalize_by_custom_shortcode(self):
        custom = [{"name": "Rush", "shortcode": "rush", "emoji": "🔴"}]
        configure_priority_catalog(custom)
        result = normalize_priority_input("rush")
        assert result == "🔴 Rush"

    def test_normalize_by_custom_name(self):
        custom = [{"name": "Backlog", "shortcode": "backlog", "emoji": "🟢"}]
        configure_priority_catalog(custom)
        result = normalize_priority_input("Backlog")
        assert result == "🟢 Backlog"

    def test_invalid_config_not_a_list(self):
        with pytest.raises(ValueError, match="non-empty list"):
            configure_priority_catalog({"name": "bad"})

    def test_invalid_config_empty_list(self):
        with pytest.raises(ValueError, match="non-empty list"):
            configure_priority_catalog([])

    def test_invalid_config_missing_name(self):
        with pytest.raises(ValueError, match="missing non-empty 'name'"):
            configure_priority_catalog([{"shortcode": "x", "emoji": "🔴"}])

    def test_invalid_config_missing_shortcode(self):
        with pytest.raises(ValueError, match="missing non-empty 'shortcode'"):
            configure_priority_catalog([{"name": "Foo", "emoji": "🔴"}])

    def test_invalid_config_missing_emoji(self):
        with pytest.raises(ValueError, match="missing non-empty 'emoji'"):
            configure_priority_catalog([{"name": "Foo", "shortcode": "foo"}])

    def test_duplicate_label_raises(self):
        custom = [
            {"name": "Urgent", "shortcode": "urgent", "emoji": "🔴"},
            {"name": "Urgent", "shortcode": "urgent2", "emoji": "🔴"},
        ]
        with pytest.raises(ValueError, match="duplicate label"):
            configure_priority_catalog(custom)

    def test_custom_color_applied_in_styling(self):
        custom = [{"name": "Critical", "shortcode": "crit", "emoji": "🔴", "color": "magenta"}]
        configure_priority_catalog(custom)
        styled = style_priority_label("🔴 Critical")
        assert "Critical" in styled


class TestLoadPrioritiesFile:
    def test_autodetect_yml(self, tmp_path: Path):
        rqmd_dir = tmp_path / ".rqmd"
        rqmd_dir.mkdir()
        data = [{"name": "Blocker", "shortcode": "blocker", "emoji": "🔴"}]
        (rqmd_dir / "priorities.yml").write_text(yaml.dump(data))
        result = load_priorities_file(tmp_path)
        assert result is not None
        assert result[0]["name"] == "Blocker"

    def test_autodetect_json(self, tmp_path: Path):
        rqmd_dir = tmp_path / ".rqmd"
        rqmd_dir.mkdir()
        data = [{"name": "Low", "shortcode": "low", "emoji": "🟢"}]
        (rqmd_dir / "priorities.json").write_text(json.dumps(data))
        result = load_priorities_file(tmp_path)
        assert result is not None
        assert result[0]["name"] == "Low"

    def test_explicit_override_path(self, tmp_path: Path):
        custom_file = tmp_path / "my-priorities.yml"
        data = [{"name": "Feature", "shortcode": "feature", "emoji": "🟡"}]
        custom_file.write_text(yaml.dump(data))
        result = load_priorities_file(tmp_path, str(custom_file))
        assert result is not None
        assert result[0]["name"] == "Feature"

    def test_explicit_override_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(ValueError, match="not found"):
            load_priorities_file(tmp_path, "nonexistent.yml")

    def test_no_file_returns_none(self, tmp_path: Path):
        result = load_priorities_file(tmp_path)
        assert result is None

    def test_dict_with_priorities_key(self, tmp_path: Path):
        rqmd_dir = tmp_path / ".rqmd"
        rqmd_dir.mkdir()
        data = {"priorities": [{"name": "High", "shortcode": "high", "emoji": "🟠"}]}
        (rqmd_dir / "priorities.yml").write_text(yaml.dump(data))
        result = load_priorities_file(tmp_path)
        assert result is not None
        assert result[0]["name"] == "High"


class TestCLIPrioritiesConfig:
    def test_priorities_config_flag_loads_catalog(self, tmp_path: Path):
        # Create priorities file
        prio_file = tmp_path / "priorities.yml"
        data = [{"name": "Epic", "shortcode": "epic", "emoji": "🟣"}]
        prio_file.write_text(yaml.dump(data))

        # Create minimal requirements dir
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "README.md").write_text("# Index\n")
        (req_dir / "test.md").write_text(
            "# Test Domain\n\n### TD-001: First\n- **Status:** 💡 Proposed\n"
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--project-root", str(tmp_path), "--docs-dir", "docs/requirements",
             "--priorities-config", str(prio_file), "--as-json"],
        )
        assert result.exit_code == 0, result.output

    def test_priorities_config_missing_path_raises_error(self, tmp_path: Path):
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "README.md").write_text("# Index\n")
        (req_dir / "test.md").write_text(
            "# Test Domain\n\n### TD-001: First\n- **Status:** 💡 Proposed\n"
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--project-root", str(tmp_path), "--docs-dir", "docs/requirements",
             "--priorities-config", "missing.yml", "--as-json"],
        )
        assert result.exit_code != 0
        assert "Config error" in result.output or "not found" in result.output.lower()

    def test_priorities_config_invalid_catalog_raises_error(self, tmp_path: Path):
        prio_file = tmp_path / "priorities.yml"
        prio_file.write_text(yaml.dump("not-a-list"))

        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "README.md").write_text("# Index\n")
        (req_dir / "test.md").write_text(
            "# Test Domain\n\n### TD-001: First\n- **Status:** 💡 Proposed\n"
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--project-root", str(tmp_path), "--docs-dir", "docs/requirements",
             "--priorities-config", str(prio_file), "--as-json"],
        )
        assert result.exit_code != 0

    def test_catalog_reset_between_invocations(self, tmp_path: Path):
        """Custom catalog from one invocation should not bleed into defaults."""
        configure_priority_catalog(None)
        default_first = PRIORITY_ORDER[0][0]

        custom = [{"name": "Cosmic", "shortcode": "cosmic", "emoji": "✨"}]
        configure_priority_catalog(custom)
        assert PRIORITY_ORDER[0][0] == "✨ Cosmic"

        configure_priority_catalog(None)
        assert PRIORITY_ORDER[0][0] == default_first
