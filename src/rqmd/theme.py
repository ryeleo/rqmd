"""Theme (light/dark) detection and zebra color resolution.

Detection priority order (highest to lowest):
1. Explicit ``--theme light|dark`` CLI flag (cli_override)
2. User or project config ``theme`` key (config_override)
3. macOS system appearance via ``defaults read -g AppleInterfaceStyle``
4. GNOME color-scheme via ``gsettings``
5. Inconclusive — fall back to safe defaults
"""

from __future__ import annotations

import platform
import subprocess
from typing import Literal

# ThemeMode is "light", "dark", or None (inconclusive / unknown)
ThemeMode = Literal["light", "dark"] | None

# Zebra stripe for dark-background terminals — light gray, subtle contrast
ZEBRA_BG_DARK = "\x1b[48;5;254m"
# Zebra stripe for light-background terminals — medium gray, readable contrast
ZEBRA_BG_LIGHT = "\x1b[48;5;250m"

# Vetted zebra backgrounds that have been manually verified for readability.
_VETTED_ZEBRA_BACKGROUNDS = {
    ZEBRA_BG_DARK,
    ZEBRA_BG_LIGHT,
}


def _probe_macos() -> ThemeMode:
    """Return 'dark' or 'light' on macOS, or None if inconclusive."""
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        # Command exits 0 and prints "Dark" when dark mode is active.
        # Non-zero exit means key absent → light mode.
        if result.returncode == 0 and "dark" in result.stdout.lower():
            return "dark"
        return "light"
    except Exception:
        return None


def _probe_gnome() -> ThemeMode:
    """Return 'dark' or 'light' from GNOME settings, or None if unavailable."""
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            return "dark" if "dark" in result.stdout.lower() else "light"
    except Exception:
        pass
    return None


def detect_theme(
    cli_override: str | None = None,
    config_override: str | None = None,
) -> tuple[ThemeMode, str]:
    """Detect the terminal light/dark theme.

    Args:
        cli_override: Value from ``--theme`` CLI flag (takes highest priority).
        config_override: Value from project/user config ``theme`` key.

    Returns:
        ``(theme, source)`` where *theme* is ``"light"``, ``"dark"``, or
        ``None`` (inconclusive) and *source* describes how the theme was
        determined (``"cli"``, ``"config"``, ``"system"``, or ``"default"``).
    """
    for override, source in ((cli_override, "cli"), (config_override, "config")):
        if override:
            v = override.strip().lower()
            if v in ("light", "dark"):
                return v, source  # type: ignore[return-value]

    system = platform.system()
    if system == "Darwin":
        theme = _probe_macos()
        if theme is not None:
            return theme, "system"
    elif system == "Linux":
        theme = _probe_gnome()
        if theme is not None:
            return theme, "system"

    return None, "default"


def resolve_zebra_bg(
    theme: ThemeMode,
    config_zebra_bg: str | None = None,
) -> str:
    """Return the ANSI escape sequence for zebra striping.

    Args:
        theme: Detected theme (``"light"``, ``"dark"``, or ``None``).
        config_zebra_bg: Raw ANSI escape override from project/user config.
            When provided this takes precedence over the theme-based default.

    Returns:
        ANSI escape sequence string suitable for use as a row background.
    """
    if config_zebra_bg:
        return config_zebra_bg
    if theme == "light":
        return ZEBRA_BG_LIGHT
    # "dark" or None → use the existing default (light gray, works on dark bg)
    return ZEBRA_BG_DARK


def is_accessible_zebra_bg(bg_ansi: str | None, theme: ThemeMode) -> bool:
    """Return whether zebra background styling is contrast-safe.

    The check is intentionally conservative: only vetted ANSI backgrounds are
    allowed for colorized redraw. Unknown overrides fall back to plain redraw so
    interaction remains readable across terminal/theme combinations.
    """
    if not bg_ansi:
        return False
    _ = theme  # Reserved for future theme-specific contrast policies.
    return bg_ansi in _VETTED_ZEBRA_BACKGROUNDS
