"""Tests for RQMD-UI-008 terminal resize handling."""

from __future__ import annotations

import io
import signal
from unittest.mock import patch

from rqmd import menus as menus_mod


def test_RQMD_ui_008_menu_installs_and_restores_sigwinch_handler() -> None:
    menus_mod.set_screen_write_enabled(True)
    registered: list[object] = []

    original_signal = signal.signal

    def _record_signal(sig: int, handler: object) -> object:
        registered.append((sig, handler))
        return signal.SIG_DFL

    output_buffer = io.StringIO()
    with patch("signal.signal", side_effect=_record_signal):
        with patch("sys.stdout", output_buffer):
            with patch("sys.stdout.isatty", return_value=True):
                with patch("click.getchar", return_value="q"):
                    menus_mod.select_from_menu("Resize", ["A", "B"], allow_paging_nav=False)

    menus_mod.set_screen_write_enabled(False)

    sigwinch_calls = [item for item in registered if item[0] == signal.SIGWINCH]
    assert len(sigwinch_calls) >= 2
    assert sigwinch_calls[0][1] == menus_mod._mark_resize_pending


def test_RQMD_ui_008_resize_signal_marks_and_consumes_pending() -> None:
    menus_mod.consume_resize_pending()
    menus_mod._mark_resize_pending(signal.SIGWINCH, None)
    assert menus_mod.consume_resize_pending() is True
    assert menus_mod.consume_resize_pending() is False


def test_RQMD_ui_008_resize_during_menu_keeps_render_stable() -> None:
    menus_mod.set_screen_write_enabled(True)
    captured_handler: dict[str, object] = {}

    def _record_signal(sig: int, handler: object) -> object:
        if sig == signal.SIGWINCH:
            captured_handler["handler"] = handler
        return signal.SIG_DFL

    def _getchar_side_effect() -> str:
        handler = captured_handler.get("handler")
        if callable(handler):
            handler(signal.SIGWINCH, None)
        return "q"

    output_buffer = io.StringIO()
    with patch("signal.signal", side_effect=_record_signal):
        with patch("sys.stdout", output_buffer):
            with patch("sys.stdout.isatty", return_value=True):
                with patch("click.getchar", side_effect=_getchar_side_effect):
                    menus_mod.select_from_menu("Resize Stable", ["One", "Two"], allow_paging_nav=False)

    menus_mod.set_screen_write_enabled(False)
    output = output_buffer.getvalue()
    assert "Resize Stable" in output
    assert "One" in output
