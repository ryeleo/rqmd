"""Tests for RQMD-UI-010: rendering diff engine and TTY/non-TTY coverage."""

from __future__ import annotations

import io
from unittest.mock import patch

from rqmd import menus as menus_mod


def _capture_menu_output(*, screen_write_enabled: bool, is_tty: bool) -> str:
    menus_mod.set_screen_write_enabled(screen_write_enabled)
    output_buffer = io.StringIO()
    with patch("sys.stdout", output_buffer):
        with patch("sys.stdout.isatty", return_value=is_tty):
            with patch("click.getchar", return_value="q"):
                menus_mod.select_from_menu("UI-010", ["One", "Two"], allow_paging_nav=False)
    menus_mod.set_screen_write_enabled(False)
    return output_buffer.getvalue()


def test_RQMD_ui_010_row_diff_engine_reports_changed_rows_only() -> None:
    previous_rows = ["Title", "  1) Alpha", "  2) Beta", "keys: ..."]
    current_rows = ["Title", "  1) Alpha", "  2) Gamma", "keys: ..."]

    updates = menus_mod.compute_row_diff(previous_rows, current_rows)

    assert updates == [(2, "  2) Gamma")]


def test_RQMD_ui_010_row_diff_engine_handles_row_removal() -> None:
    previous_rows = ["Title", "  1) Alpha", "  2) Beta", "keys: ..."]
    current_rows = ["Title", "  1) Alpha", "keys: ..."]

    updates = menus_mod.compute_row_diff(previous_rows, current_rows)

    assert (2, "keys: ...") in updates
    assert (3, "") in updates


def test_RQMD_ui_010_tty_path_emits_screen_write_escape() -> None:
    output = _capture_menu_output(screen_write_enabled=True, is_tty=True)
    assert "\x1b[2J\x1b[H" in output


def test_RQMD_ui_010_non_tty_path_uses_fallback_without_escape() -> None:
    output = _capture_menu_output(screen_write_enabled=True, is_tty=False)
    assert "\x1b[2J\x1b[H" not in output
    assert "UI-010" in output
    assert "One" in output
