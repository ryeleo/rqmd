"""Tests for RQMD-INTERACTIVE-012: config-driven zebra background color overrides.

Covers:
- resolve_zebra_bg() respects config_zebra_bg override
- resolve_zebra_bg() returns ZEBRA_BG_LIGHT for light theme
- resolve_zebra_bg() returns ZEBRA_BG_DARK for dark/None theme
- select_from_menu() uses custom zebra_bg when provided
- select_from_menu() falls back to ZEBRA_BG when zebra_bg=None
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from rqmd.theme import ZEBRA_BG_DARK, ZEBRA_BG_LIGHT, resolve_zebra_bg


class TestResolveZebraBg:
    def test_config_override_takes_precedence_over_light_theme(self):
        custom = "\x1b[48;5;200m"
        assert resolve_zebra_bg("light", config_zebra_bg=custom) == custom

    def test_config_override_takes_precedence_over_dark_theme(self):
        custom = "\x1b[48;5;200m"
        assert resolve_zebra_bg("dark", config_zebra_bg=custom) == custom

    def test_config_override_takes_precedence_over_none_theme(self):
        custom = "\x1b[48;5;100m"
        assert resolve_zebra_bg(None, config_zebra_bg=custom) == custom

    def test_light_theme_returns_zebra_bg_light(self):
        assert resolve_zebra_bg("light") == ZEBRA_BG_LIGHT

    def test_dark_theme_returns_zebra_bg_dark(self):
        assert resolve_zebra_bg("dark") == ZEBRA_BG_DARK

    def test_none_theme_returns_zebra_bg_dark(self):
        assert resolve_zebra_bg(None) == ZEBRA_BG_DARK

    def test_empty_config_override_falls_through_to_theme(self):
        # Falsy string should not be used as override
        assert resolve_zebra_bg("light", config_zebra_bg="") == ZEBRA_BG_LIGHT
        assert resolve_zebra_bg("dark", config_zebra_bg="") == ZEBRA_BG_DARK

    def test_none_config_override_falls_through_to_theme(self):
        assert resolve_zebra_bg("light", config_zebra_bg=None) == ZEBRA_BG_LIGHT


class TestSelectFromMenuZebraBgParam:
    """select_from_menu() should use the provided zebra_bg for odd-row backgrounds."""

    def _make_options(self, n: int = 4) -> list[str]:
        return [f"Option {i}" for i in range(n)]

    def test_custom_zebra_bg_is_applied_to_odd_rows(self):
        """When zebra=True and zebra_bg is set, that sequence should appear in output."""
        from rqmd import menus
        from rqmd.constants import ZEBRA_BG

        custom_bg = "\x1b[48;5;200m"
        applied: list[tuple] = []

        original_fn = menus.apply_background_preserving_styles

        def recording_fn(line, bg):
            applied.append((line, bg))
            return original_fn(line, bg)

        with patch.object(menus, "apply_background_preserving_styles", side_effect=recording_fn):
            with patch.object(menus, "click") as mock_click:
                mock_click.getchar.return_value = "q"
                menus.select_from_menu(
                    self._make_options(),
                    zebra=True,
                    zebra_bg=custom_bg,
                )

        assert any(bg == custom_bg for _, bg in applied), (
            f"Expected custom_bg {custom_bg!r} to be used; saw: {[bg for _, bg in applied]}"
        )
        assert not any(bg == ZEBRA_BG for _, bg in applied), (
            "Default ZEBRA_BG should not appear when zebra_bg override is set"
        )

    def test_none_zebra_bg_falls_back_to_default_zebra_bg(self):
        """When zebra=True and zebra_bg=None, ZEBRA_BG constant should be used."""
        from rqmd import menus
        from rqmd.constants import ZEBRA_BG

        applied: list[tuple] = []

        original_fn = menus.apply_background_preserving_styles

        def recording_fn(line, bg):
            applied.append((line, bg))
            return original_fn(line, bg)

        with patch.object(menus, "apply_background_preserving_styles", side_effect=recording_fn):
            with patch.object(menus, "click") as mock_click:
                mock_click.getchar.return_value = "q"
                menus.select_from_menu(
                    self._make_options(),
                    zebra=True,
                    zebra_bg=None,
                )

        assert any(bg == ZEBRA_BG for _, bg in applied), (
            f"Expected default ZEBRA_BG {ZEBRA_BG!r}; saw: {[bg for _, bg in applied]}"
        )
