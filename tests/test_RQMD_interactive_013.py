"""Tests for RQMD-INTERACTIVE-013: automatic light/dark terminal theme detection.

Covers:
- detect_theme() priority: CLI > config > system > default
- _probe_macos() returns 'dark' when defaults command indicates dark mode
- _probe_macos() returns 'light' when defaults command returns non-zero (light)
- _probe_macos() returns None on exceptions (command not found etc.)
- _probe_gnome() returns 'dark'/'light' from gsettings output
- _probe_gnome() returns None on exceptions
- --theme CLI option accepted by main()
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from rqmd import cli
from rqmd.theme import _probe_gnome, _probe_macos, detect_theme


class TestDetectThemePriority:
    def test_cli_override_dark_takes_highest_priority(self):
        theme, source = detect_theme(cli_override="dark", config_override="light")
        assert theme == "dark"
        assert source == "cli"

    def test_cli_override_light_takes_highest_priority(self):
        theme, source = detect_theme(cli_override="light", config_override="dark")
        assert theme == "light"
        assert source == "cli"

    def test_config_override_used_when_no_cli(self):
        theme, source = detect_theme(cli_override=None, config_override="dark")
        assert theme == "dark"
        assert source == "config"

    def test_config_override_light(self):
        theme, source = detect_theme(config_override="light")
        assert theme == "light"
        assert source == "config"

    def test_cli_override_case_insensitive(self):
        theme, source = detect_theme(cli_override="DARK")
        assert theme == "dark"
        assert source == "cli"

    def test_config_override_case_insensitive(self):
        theme, source = detect_theme(config_override="LIGHT")
        assert theme == "light"
        assert source == "config"

    def test_invalid_cli_override_falls_through_to_config(self):
        theme, source = detect_theme(cli_override="bogus", config_override="dark")
        assert theme == "dark"
        assert source == "config"

    def test_no_overrides_returns_default_when_probes_return_none(self):
        with patch("rqmd.theme.platform.system", return_value="Windows"):
            theme, source = detect_theme()
        assert theme is None
        assert source == "default"

    def test_system_detection_used_when_no_overrides(self):
        """With no overrides, macOS probe result is used when on Darwin."""
        with patch("rqmd.theme.platform.system", return_value="Darwin"):
            with patch("rqmd.theme._probe_macos", return_value="dark"):
                theme, source = detect_theme()
        assert theme == "dark"
        assert source == "system"

    def test_gnome_used_on_linux(self):
        with patch("rqmd.theme.platform.system", return_value="Linux"):
            with patch("rqmd.theme._probe_gnome", return_value="light"):
                theme, source = detect_theme()
        assert theme == "light"
        assert source == "system"

    def test_macos_probe_inconclusive_falls_back_to_default(self):
        with patch("rqmd.theme.platform.system", return_value="Darwin"):
            with patch("rqmd.theme._probe_macos", return_value=None):
                theme, source = detect_theme()
        assert theme is None
        assert source == "default"


class TestProbeMacos:
    def _mock_run(self, returncode: int, stdout: str) -> MagicMock:
        m = MagicMock()
        m.returncode = returncode
        m.stdout = stdout
        return m

    def test_returns_dark_when_command_exits_0_with_dark_output(self):
        with patch("rqmd.theme.subprocess.run", return_value=self._mock_run(0, "Dark\n")):
            assert _probe_macos() == "dark"

    def test_returns_light_when_command_exits_nonzero(self):
        with patch("rqmd.theme.subprocess.run", return_value=self._mock_run(1, "")):
            assert _probe_macos() == "light"

    def test_returns_none_on_file_not_found(self):
        with patch("rqmd.theme.subprocess.run", side_effect=FileNotFoundError):
            assert _probe_macos() is None

    def test_returns_none_on_timeout(self):
        import subprocess
        with patch("rqmd.theme.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="defaults", timeout=1)):
            assert _probe_macos() is None

    def test_dark_case_insensitive_match(self):
        with patch("rqmd.theme.subprocess.run", return_value=self._mock_run(0, "dark\n")):
            assert _probe_macos() == "dark"


class TestProbeGnome:
    def _mock_run(self, returncode: int, stdout: str) -> MagicMock:
        m = MagicMock()
        m.returncode = returncode
        m.stdout = stdout
        return m

    def test_returns_dark_when_gsettings_has_dark(self):
        with patch("rqmd.theme.subprocess.run", return_value=self._mock_run(0, "'prefer-dark'\n")):
            assert _probe_gnome() == "dark"

    def test_returns_light_when_gsettings_has_no_dark(self):
        with patch("rqmd.theme.subprocess.run", return_value=self._mock_run(0, "'prefer-light'\n")):
            assert _probe_gnome() == "light"

    def test_returns_none_on_file_not_found(self):
        with patch("rqmd.theme.subprocess.run", side_effect=FileNotFoundError):
            assert _probe_gnome() is None

    def test_returns_none_when_returncode_nonzero(self):
        with patch("rqmd.theme.subprocess.run", return_value=self._mock_run(1, "")):
            assert _probe_gnome() is None


class TestThemeCliOption:
    """Smoke-test that --theme is wired into the main() Click command."""

    def _make_repo(self, tmp_path: Path) -> Path:
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            "# Demo\n\n### AC-001: Demo\n- **Status:** 💡 Proposed\n",
            encoding="utf-8",
        )
        return repo

    def test_theme_light_accepted(self, tmp_path: Path):
        repo = self._make_repo(tmp_path)

        runner = CliRunner()
        with patch("rqmd.cli.interactive_update_loop", return_value=0):
            result = runner.invoke(
                cli.main,
                [
                    "--project-root", str(repo),
                    "--docs-dir", "docs/requirements",
                    "--no-table",
                    "--theme", "light",
                ],
                catch_exceptions=False,
            )
        # Exit 0 (interactive loop not actually entered —
        # we accept any non-error exit to confirm option is parsed)
        assert result.exit_code in (0, 1)  # 1 is acceptable if terminal not a TTY
        assert "Error: Invalid value for '--theme'" not in (result.output or "")

    def test_theme_dark_accepted(self, tmp_path: Path):
        repo = self._make_repo(tmp_path)

        runner = CliRunner()
        with patch("rqmd.cli.interactive_update_loop", return_value=0):
            result = runner.invoke(
                cli.main,
                [
                    "--project-root", str(repo),
                    "--docs-dir", "docs/requirements",
                    "--no-table",
                    "--theme", "dark",
                ],
                catch_exceptions=False,
            )
        assert result.exit_code in (0, 1)
        assert "Error: Invalid value for '--theme'" not in (result.output or "")

    def test_theme_invalid_rejected(self, tmp_path: Path):
        repo = self._make_repo(tmp_path)

        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--project-root", str(repo),
                "--docs-dir", "docs/requirements",
                "--no-table",
                "--theme", "purple",
            ],
        )
        assert result.exit_code != 0
        assert "Invalid value for '--theme'" in (result.output or "")


class TestScreenWritePrecedence:
    def _make_repo(self, tmp_path: Path, config_text: str | None = None) -> Path:
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            "# Demo\n\n### AC-001: Demo\n- **Status:** 💡 Proposed\n",
            encoding="utf-8",
        )
        if config_text is not None:
            (repo / ".rqmd.json").write_text(config_text, encoding="utf-8")
        return repo

    def test_cli_no_screen_write_overrides_project_config(self, tmp_path: Path):
        repo = self._make_repo(tmp_path, '{"screen_write": true}')
        runner = CliRunner()
        with patch("rqmd.cli.menus_mod.set_screen_write_enabled") as set_sw:
            with patch("rqmd.cli.menus_mod.set_screen_write_forced") as set_sw_forced:
                with patch("rqmd.cli.menus_mod.reset_render_mode_controller") as reset_render:
                    with patch("rqmd.cli.interactive_update_loop", return_value=0):
                        result = runner.invoke(
                            cli.main,
                            [
                                "--project-root", str(repo),
                                "--docs-dir", "docs/requirements",
                                "--no-table",
                                "--no-screen-write",
                            ],
                            catch_exceptions=False,
                        )
        assert result.exit_code in (0, 1)
        reset_render.assert_called_once_with()
        set_sw.assert_called_with(False)
                        set_sw_forced.assert_any_call(True)

    def test_project_config_screen_write_used_when_cli_omitted(self, tmp_path: Path):
        repo = self._make_repo(tmp_path, '{"screen_write": false}')
        runner = CliRunner()
        with patch("rqmd.cli.menus_mod.set_screen_write_enabled") as set_sw:
            with patch("rqmd.cli.menus_mod.set_screen_write_forced") as set_sw_forced:
                with patch("rqmd.cli.menus_mod.reset_render_mode_controller") as reset_render:
                    with patch("rqmd.cli.interactive_update_loop", return_value=0):
                        result = runner.invoke(
                            cli.main,
                            [
                                "--project-root", str(repo),
                                "--docs-dir", "docs/requirements",
                                "--no-table",
                            ],
                            catch_exceptions=False,
                        )
        assert result.exit_code in (0, 1)
        reset_render.assert_called_once_with()
        set_sw.assert_called_with(False)
                        set_sw_forced.assert_any_call(False)

    def test_non_tty_default_used_when_no_cli_or_config(self, tmp_path: Path):
        repo = self._make_repo(tmp_path)
        runner = CliRunner()
        with patch("rqmd.cli.menus_mod.set_screen_write_enabled") as set_sw:
            with patch("rqmd.cli.menus_mod.set_screen_write_forced") as set_sw_forced:
                with patch("rqmd.cli.menus_mod.reset_render_mode_controller") as reset_render:
                    with patch("rqmd.cli.interactive_update_loop", return_value=0):
                        result = runner.invoke(
                            cli.main,
                            [
                                "--project-root", str(repo),
                                "--docs-dir", "docs/requirements",
                                "--no-table",
                            ],
                            catch_exceptions=False,
                        )
        assert result.exit_code in (0, 1)
        # CliRunner uses a non-TTY stream, so default falls back to disabled.
        reset_render.assert_called_once_with()
        set_sw.assert_called_with(False)
        set_sw_forced.assert_any_call(False)

    def test_cli_screen_write_forces_screen_write_mode(self, tmp_path: Path):
        repo = self._make_repo(tmp_path)
        runner = CliRunner()
        with patch("rqmd.cli.menus_mod.set_screen_write_enabled") as set_sw:
            with patch("rqmd.cli.menus_mod.set_screen_write_forced") as set_sw_forced:
                with patch("rqmd.cli.menus_mod.reset_render_mode_controller") as reset_render:
                    with patch("rqmd.cli.interactive_update_loop", return_value=0):
                        result = runner.invoke(
                            cli.main,
                            [
                                "--project-root", str(repo),
                                "--docs-dir", "docs/requirements",
                                "--no-table",
                                "--screen-write",
                            ],
                            catch_exceptions=False,
                        )
        assert result.exit_code in (0, 1)
        reset_render.assert_called_once_with()
        set_sw.assert_called_with(True)
        set_sw_forced.assert_any_call(True)
