"""Tests for RQMD-UI-010: rendering diff engine and TTY/non-TTY coverage."""

from __future__ import annotations

import io
import os
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
    assert menus_mod._SCREEN_WRITE_CLEAR_SEQUENCE in output


def test_RQMD_ui_010_non_tty_path_uses_fallback_without_escape() -> None:
    output = _capture_menu_output(screen_write_enabled=True, is_tty=False)
    assert menus_mod._SCREEN_WRITE_CLEAR_SEQUENCE not in output
    assert "UI-010" in output
    assert "One" in output


def test_RQMD_ui_010_fit_prefix_text_for_viewport_truncates_when_needed() -> None:
    prefix = "\n".join([f"line {i} " + ("x" * 60) for i in range(12)])

    rendered = menus_mod._fit_prefix_text_for_viewport(prefix, width=40, max_rows=6)

    assert rendered is not None
    assert "content truncated to fit terminal" in rendered


def test_RQMD_ui_010_screen_write_truncates_prefix_before_render() -> None:
    menus_mod.set_screen_write_enabled(True)
    captured: list[str] = []

    def _capture_echo(message: str = "", *args, **kwargs) -> None:
        if isinstance(message, str):
            captured.append(message)

    long_prefix = "\n".join([f"prefix {i} " + ("x" * 80) for i in range(30)])
    fake_terminal_size = io.StringIO()

    with patch("rqmd.menus.click.echo", side_effect=_capture_echo):
        with patch("sys.stdout", fake_terminal_size):
            with patch("sys.stdout.isatty", return_value=True):
                with patch("rqmd.menus.shutil.get_terminal_size", return_value=os.terminal_size((40, 12))):
                    with patch("click.getchar", return_value="q"):
                        menus_mod.select_from_menu(
                            "UI-010",
                            ["One", "Two", "Three"],
                            allow_paging_nav=False,
                            prefix_text=long_prefix,
                        )

    menus_mod.set_screen_write_enabled(False)

    rendered_prefixes = [msg for msg in captured if "prefix 0" in msg or "content truncated to fit terminal" in msg]
    assert rendered_prefixes
    assert any("content truncated to fit terminal" in msg for msg in rendered_prefixes)
