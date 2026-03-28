"""Tests for RQMD-UI-007 accessibility and contrast-preserving redraw behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from rqmd import menus as menus_mod
from rqmd.cli import main as rqmd_main
from rqmd.theme import ZEBRA_BG_DARK, ZEBRA_BG_LIGHT, is_accessible_zebra_bg


def test_RQMD_ui_007_vetted_backgrounds_are_accessible() -> None:
    assert is_accessible_zebra_bg(ZEBRA_BG_DARK, "dark") is True
    assert is_accessible_zebra_bg(ZEBRA_BG_LIGHT, "light") is True


def test_RQMD_ui_007_unknown_background_disables_colorized_redraw() -> None:
    assert is_accessible_zebra_bg("\x1b[48;5;200m", "light") is False


def test_RQMD_ui_007_cli_disables_colorized_redraw_for_unsafe_override(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    req_dir = repo / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    (req_dir / "demo.md").write_text(
        """# Demo Requirements

### AC-001: Demo
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    with patch("rqmd.cli.menus_mod.set_colorized_redraw_enabled") as set_colorized:
        with patch("rqmd.cli.menus_mod.set_screen_write_enabled"):
            with patch("rqmd.theme.resolve_zebra_bg", return_value="\x1b[48;5;200m"):
                with patch("rqmd.theme.detect_theme", return_value=("light", "cli")):
                    result = runner.invoke(
                        rqmd_main,
                        [
                            "--project-root",
                            str(repo),
                            "--docs-dir",
                            "docs/requirements",
                            "--as-json",
                            "--status",
                            "proposed",
                            "--no-walk",
                            "--no-table",
                        ],
                    )

    assert result.exit_code == 0, result.output
    set_colorized.assert_called_once_with(False)


def test_RQMD_ui_007_menu_omits_background_styles_when_colorized_disabled() -> None:
    menus_mod.set_colorized_redraw_enabled(False)
    applied_calls: list[tuple[str, str]] = []

    original = menus_mod.apply_background_preserving_styles

    def recorder(line: str, bg: str) -> str:
        applied_calls.append((line, bg))
        return original(line, bg)

    with patch.object(menus_mod, "apply_background_preserving_styles", side_effect=recorder):
        with patch("click.getchar", return_value="q"):
            menus_mod.select_from_menu("UI-007", ["One", "Two", "Three"], zebra=True, allow_paging_nav=False)

    menus_mod.set_colorized_redraw_enabled(True)
    assert applied_calls == []
