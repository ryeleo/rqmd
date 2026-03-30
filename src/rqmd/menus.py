"""Interactive menu rendering and selection utilities.

This module provides:
- ASCII width calculation accounting for ANSI codes and wide characters
- Text truncation with ellipsis and ANSI-aware alignment
- Terminal-based menu selection with single-key input
- Zebra striping and sorting options for menu items
- Paging and navigation support
"""

from __future__ import annotations

import shutil
import signal
import sys
import textwrap
import time
import unicodedata

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from .constants import (ANSI_ESCAPE_PATTERN, ANSI_RESET, MENU_NEXT,
                        MENU_PAGE_SIZE, MENU_PREV, MENU_QUIT, MENU_UP,
                        ZEBRA_BG)
from .render_heuristics import RenderModeController

_SCREEN_WRITE_ENABLED = False
_SCREEN_WRITE_FORCED = False
_COLORIZED_REDRAW_ENABLED = True
_RESIZE_SIGNAL_PENDING = False
_RENDER_MODE_CONTROLLER = RenderModeController()
_ARROW_UP_KEYS = ("\x1b[A", "\x1bOA")
_ARROW_DOWN_KEYS = ("\x1b[B", "\x1bOB")
_CTRL_U = "\x15"
_CTRL_D = "\x04"
_HELP_TOGGLE_KEY = ":"


def set_screen_write_enabled(enabled: bool) -> None:
    """Enable or disable full-screen redraw behavior for interactive menus."""
    global _SCREEN_WRITE_ENABLED
    _SCREEN_WRITE_ENABLED = bool(enabled)


def set_screen_write_forced(forced: bool) -> None:
    """Force screen-write behavior to bypass adaptive append fallback."""
    global _SCREEN_WRITE_FORCED
    _SCREEN_WRITE_FORCED = bool(forced)


def get_screen_write_forced() -> bool:
    """Return whether screen-write is currently forced."""
    return _SCREEN_WRITE_FORCED


def get_screen_write_enabled() -> bool:
    """Return whether full-screen redraw behavior is enabled."""
    return _SCREEN_WRITE_ENABLED


def set_colorized_redraw_enabled(enabled: bool) -> None:
    """Enable or disable colorized row backgrounds in interactive menus."""
    global _COLORIZED_REDRAW_ENABLED
    _COLORIZED_REDRAW_ENABLED = bool(enabled)


def get_colorized_redraw_enabled() -> bool:
    """Return whether colorized row backgrounds are enabled."""
    return _COLORIZED_REDRAW_ENABLED


def reset_render_mode_controller() -> None:
    """Reset adaptive render mode controller state."""
    _RENDER_MODE_CONTROLLER.reset(mode="screen-write")


def configure_render_mode_controller(
    target_ms: float,
    upper_ms: float,
    hysteresis_ms: float,
    cooldown_seconds: float,
    window_size: int,
) -> None:
    """Configure adaptive render mode controller thresholds."""
    global _RENDER_MODE_CONTROLLER
    _RENDER_MODE_CONTROLLER = RenderModeController(
        target_ms=target_ms,
        upper_ms=upper_ms,
        hysteresis_ms=hysteresis_ms,
        cooldown_seconds=cooldown_seconds,
        window_size=window_size,
    )


def _mark_resize_pending(_signum: int, _frame: object) -> None:
    """Signal handler that marks terminal resize as pending."""
    global _RESIZE_SIGNAL_PENDING
    _RESIZE_SIGNAL_PENDING = True


def consume_resize_pending() -> bool:
    """Return and clear pending terminal-resize marker."""
    global _RESIZE_SIGNAL_PENDING
    pending = _RESIZE_SIGNAL_PENDING
    _RESIZE_SIGNAL_PENDING = False
    return pending


def _format_key_label(key: str) -> str:
    if key in _ARROW_UP_KEYS:
        return "↑"
    if key in _ARROW_DOWN_KEYS:
        return "↓"
    if key == _CTRL_U:
        return "^U"
    if key == _CTRL_D:
        return "^D"
    return key


def _resolve_arrow_navigation(
    choice: str,
    allow_paging_nav: bool,
    extra_keys: dict[str, str] | None,
) -> str | None:
    if choice in _ARROW_DOWN_KEYS:
        if extra_keys and "nav-next" in extra_keys.values():
            return "nav-next"
        if allow_paging_nav:
            return MENU_NEXT
    if choice in _ARROW_UP_KEYS:
        if extra_keys and "nav-prev" in extra_keys.values():
            return "nav-prev"
        if allow_paging_nav:
            return MENU_PREV
    return None


def _normalize_search_text(text: str) -> str:
    return ANSI_ESCAPE_PATTERN.sub("", text).casefold()


def _find_search_match(
    options: list[str],
    query: str,
    anchor_index: int,
    *,
    forward: bool,
) -> int | None:
    if not options:
        return None

    needle = query.casefold()
    total = len(options)
    start_index = anchor_index % total
    step = 1 if forward else -1
    current_index = start_index

    for _ in range(total):
        current_index = (current_index + step) % total
        if needle in _normalize_search_text(options[current_index]):
            return current_index

    return None


def _build_default_help_legend(
    *,
    allow_paging_nav: bool,
    extra_key: str | None,
    extra_key_help: str,
    extra_keys: dict[str, str] | None,
    extra_keys_help: dict[str, str] | None,
) -> str:
    if allow_paging_nav:
        keys_line = (
            f"keys: 1-9 select | ↓/{MENU_NEXT}=next | ↑/{MENU_PREV}=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | {MENU_UP}=up | {MENU_QUIT}=quit"
        )
    else:
        keys_line = f"keys: 1-9 select | {MENU_UP}=up | {MENU_QUIT}=quit"
    if extra_key:
        extra_help = extra_key_help if extra_key_help else "action"
        keys_line = f"{keys_line} | {_format_key_label(extra_key)}={extra_help}"
    if extra_keys:
        for key, ret in extra_keys.items():
            help_text = (extra_keys_help or {}).get(key, ret)
            keys_line = f"{keys_line} | {_format_key_label(key)}={help_text}"
    return keys_line


def _build_default_compact_footer(*, allow_paging_nav: bool) -> str:
    keys = ["keys: 1-9 select"]
    if allow_paging_nav:
        keys.append(f"↓/{MENU_NEXT}=next")
        keys.append(f"↑/{MENU_PREV}=prev")
    keys.append(f"{_HELP_TOGGLE_KEY}=help")
    keys.append(f"{MENU_UP}=up")
    keys.append(f"{MENU_QUIT}=quit")
    return " | ".join(keys)


def _wrap_help_legend(legend: str, width: int) -> list[str]:
    if not legend:
        return []

    tokens = [token.strip() for token in legend.split("|")]
    lines: list[str] = []
    current_tokens: list[str] = []
    max_width = max(24, width - 2)

    for token in tokens:
        candidate_tokens = current_tokens + [token]
        candidate = " | ".join(candidate_tokens)
        if current_tokens and visible_length(candidate) > max_width:
            lines.append(" | ".join(current_tokens))
            current_tokens = [token]
            continue
        if visible_length(token) > max_width:
            if current_tokens:
                lines.append(" | ".join(current_tokens))
                current_tokens = []
            lines.extend(textwrap.wrap(token, width=max_width, break_long_words=False, break_on_hyphens=False))
            continue
        current_tokens = candidate_tokens

    if current_tokens:
        lines.append(" | ".join(current_tokens))
    return lines


def visible_length(text: str) -> int:
    """Calculate the visible display width of a string, accounting for ANSI codes and wide characters.

    Args:
        text: Text string (may contain ANSI escape codes and wide characters).

    Returns:
        The visible width in character positions.
    """
    plain = ANSI_ESCAPE_PATTERN.sub("", text)
    width = 0
    for ch in plain:
        code = ord(ch)
        if ch in ("\u200d", "\ufe0e", "\ufe0f"):
            continue
        if unicodedata.combining(ch):
            continue
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
            continue
        if 0x1F300 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
            width += 2
            continue
        width += 1
    return width


def truncate_text(text: str, max_len: int) -> str:
    """Truncate text to a maximum visible width, adding ellipsis if needed.

    Args:
        text: Text to truncate (may contain ANSI codes).
        max_len: Maximum visible character width.

    Returns:
        Truncated text with ellipsis, preserving ANSI codes.
    """
    if max_len <= 0:
        return ""
    if visible_length(text) <= max_len:
        return text
    if max_len <= 3:
        return text[:max_len]

    suffix = "..."
    suffix_width = visible_length(suffix)
    budget = max_len - suffix_width
    if budget <= 0:
        return suffix[:max_len]

    out_chars: list[str] = []
    used = 0
    for ch in text:
        ch_width = visible_length(ch)
        if used + ch_width > budget:
            break
        out_chars.append(ch)
        used += ch_width

    return "".join(out_chars).rstrip() + suffix


def apply_background_preserving_styles(text: str, bg_ansi: str) -> str:
    """Apply background styling while preserving ANSI resets.

    Args:
        text: Text with possible ANSI codes.
        bg_ansi: Background ANSI code to apply.

    Returns:
        Text with background applied and resets patched.
    """
    patched = text.replace(ANSI_RESET, ANSI_RESET + bg_ansi)
    return f"{bg_ansi}{patched}{ANSI_RESET}"


def right_align_menu_suffix(label: str, suffix: str, index_width: int = 1) -> str:
    """Right-align a suffix next to a label in terminal width.

    Args:
        label: Left-aligned menu label.
        suffix: Right-aligned text (e.g., '(5/10)').
        index_width: Width of the index column.

    Returns:
        Label with suffix right-aligned to fit terminal width.
    """
    term_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    prefix_width = 5 if index_width == 1 else (4 + index_width)
    label_len = visible_length(label)
    suffix_len = visible_length(suffix)
    spaces = term_width - prefix_width - label_len - suffix_len
    if spaces < 2:
        spaces = 2
    return f"{label}{' ' * spaces}{suffix}"


def file_sort_key_by_priority(counts: dict[str, int], label: str) -> tuple[int, int, int, str]:
    """Generate a sort key prioritizing implemented, then proposed, then verified counts.

    Args:
        counts: Dictionary of status counts.
        label: File label (secondary sort key).

    Returns:
        A sort tuple (negative implemented, negative proposed, negative verified, label).
    """
    black = counts["🔧 Implemented"]
    blue = counts["💡 Proposed"]
    green = counts["✅ Verified"]
    return (-black, -blue, -green, label)


def compute_row_diff(previous_rows: list[str], current_rows: list[str]) -> list[tuple[int, str]]:
    """Return changed row positions between two rendered menu snapshots.

    The return value is a list of ``(row_index, row_text)`` tuples for rows that
    changed or were newly appended in ``current_rows``. Missing trailing rows are
    represented as empty strings for clear/overwrite behavior in renderer callers.
    """
    updates: list[tuple[int, str]] = []
    max_rows = max(len(previous_rows), len(current_rows))
    for row_index in range(max_rows):
        prev = previous_rows[row_index] if row_index < len(previous_rows) else None
        curr = current_rows[row_index] if row_index < len(current_rows) else ""
        if prev != curr:
            updates.append((row_index, curr))
    return updates


def select_from_menu(
    title: str,
    options: list[str],
    repeat_choice_right: bool = False,
    zebra: bool = False,
    zebra_bg: str | None = None,
    show_page_indicator: bool = True,
    allow_paging_nav: bool = True,
    extra_key: str | None = None,
    extra_key_help: str = "",
    extra_key_return: str = "extra",
    option_right_labels: list[str] | None = None,
    extra_keys: dict[str, str] | None = None,
    extra_keys_help: dict[str, str] | None = None,
    selected_option_index: int | None = None,
    initial_window_start: int | None = None,
    selected_option_bg: str | None = None,
    footer_legend: str | None = None,
    compact_footer: str | None = None,
    help_legend: str | None = None,
    prefix_text: str | None = None,
) -> int | str | None:
    """Interactive menu selection with single-key navigation and paging.

    Args:
        title: Menu title/prompt.
        options: List of menu options to display.
        repeat_choice_right: If True, allow repeated selection without exiting.
        zebra: If True, alternate row backgrounds (striping).
        show_page_indicator: If True, show (X/Y) page indicator.
        allow_paging_nav: If True, enable down/up-arrow and j/k navigation for next/prev page navigation.
        extra_key: Single extra key to bind (e.g., 'r' for notes).
        extra_key_help: Help text for the extra key.
        extra_key_return: Value to return when extra key is pressed.
        option_right_labels: Optional right-aligned labels for each option.
        extra_keys: Optional dict of extra keys to function descriptions.
        extra_keys_help: Optional dict of extra key help text.
        selected_option_index: Initial selected option index.
        initial_window_start: Optional initial top-of-window global index.
        selected_option_bg: Background ANSI code for selected option.
        footer_legend: Optional legend text displayed at menu footer, or full help legend when compact_footer is provided.
        compact_footer: Optional compact footer shown during normal menu rendering.
        help_legend: Optional full help legend shown when help is toggled open.
        prefix_text: Optional text block rendered above the menu title on each redraw.

    Returns:
        Index of selected option and the option text, or extra_key_return if key pressed.
    """
    if not options:
        click.echo("No options available.")
        return None

    page_size = MENU_PAGE_SIZE
    max_window_start = max(0, len(options) - 1)
    last_page_start = max(0, ((len(options) - 1) // page_size) * page_size)
    window_start = 0
    current_selected_index = selected_option_index if selected_option_index is not None and 0 <= selected_option_index < len(options) else None
    last_search_query: str | None = None
    last_search_forward = True
    help_visible = False
    is_tty = sys.stdout.isatty()
    previous_resize_handler: object | None = None

    default_help_legend = _build_default_help_legend(
        allow_paging_nav=allow_paging_nav,
        extra_key=extra_key,
        extra_key_help=extra_key_help,
        extra_keys=extra_keys,
        extra_keys_help=extra_keys_help,
    )
    resolved_help_legend = help_legend if help_legend is not None else footer_legend if compact_footer is not None else default_help_legend
    resolved_compact_footer = compact_footer
    if resolved_compact_footer is None:
        if footer_legend is not None:
            resolved_compact_footer = footer_legend
        else:
            resolved_compact_footer = _build_default_compact_footer(allow_paging_nav=allow_paging_nav)

    if is_tty and hasattr(signal, "SIGWINCH"):
        previous_resize_handler = signal.signal(signal.SIGWINCH, _mark_resize_pending)

    if initial_window_start is not None and initial_window_start >= 0:
        window_start = min(initial_window_start, max_window_start)
    elif selected_option_index is not None and selected_option_index >= 0:
        window_start = min((selected_option_index // page_size) * page_size, max_window_start)

    try:
        while True:
            total_pages = (len(options) + page_size - 1) // page_size
            start = window_start
            page_items = options[start:start + page_size]
            term_width = shutil.get_terminal_size(fallback=(120, 24)).columns
            current_page = min((window_start // page_size) + 1, total_pages)
            half_page = max(1, page_size // 2)

            _ = consume_resize_pending()

            effective_screen_write = _SCREEN_WRITE_ENABLED and is_tty
            if effective_screen_write and (not _SCREEN_WRITE_FORCED) and _RENDER_MODE_CONTROLLER.mode == "append":
                effective_screen_write = False

            if effective_screen_write:
                # Full-screen redraw mode: clear screen and return cursor to home.
                click.echo("\x1b[2J\x1b[H", nl=False)

            render_started = time.perf_counter()

            if prefix_text:
                click.echo(prefix_text)
            click.echo("")
            click.echo(title)
            if show_page_indicator and total_pages > 1:
                click.echo(f"Page {current_page}/{total_pages}")
            for idx, option in enumerate(page_items):
                global_idx = start + idx
                selection_marker = "→" if current_selected_index is not None and global_idx == current_selected_index else " "
                left = f"{selection_marker} {idx + 1}) {option}"
                if option_right_labels and global_idx < len(option_right_labels):
                    right = click.style(option_right_labels[global_idx], dim=True)
                    pad = term_width - visible_length(left) - visible_length(right)
                    if pad >= 2:
                        line = f"{left}{' ' * pad}{right}"
                    else:
                        line = left
                elif repeat_choice_right:
                    right = click.style(f"[{idx + 1}]", dim=True)
                    pad = term_width - visible_length(left) - visible_length(right)
                    if pad >= 2:
                        line = f"{left}{' ' * pad}{right}"
                    else:
                        line = left
                else:
                    line = left

                if _COLORIZED_REDRAW_ENABLED and current_selected_index is not None and global_idx == current_selected_index and selected_option_bg:
                    line = apply_background_preserving_styles(line, selected_option_bg)
                elif _COLORIZED_REDRAW_ENABLED and zebra and (idx % 2 == 1):
                    line = apply_background_preserving_styles(
                        line, zebra_bg if zebra_bg is not None else ZEBRA_BG
                    )

                click.echo(line)

            if help_visible:
                click.echo(click.style("Help", bold=True))
                for help_line in _wrap_help_legend(resolved_help_legend, term_width):
                    click.echo(help_line)
                click.echo(click.style("Press : or any invalid key to close help.", dim=True))
            click.echo(resolved_compact_footer)
            click.echo("choice: ", nl=False)
            raw_choice = click.getchar()
            choice = raw_choice.strip()
            click.echo(_format_key_label(choice))

            if choice == _HELP_TOGGLE_KEY:
                help_visible = not help_visible
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue

            if allow_paging_nav and choice == "g":
                click.echo("choice: ", nl=False)
                raw_second_choice = click.getchar()
                second_choice = raw_second_choice.strip()
                click.echo(_format_key_label(second_choice))
                if second_choice == "\x03":
                    raise click.Abort()
                if second_choice.lower() == "g":
                    if extra_keys and "g" in extra_keys:
                        mapped = extra_keys["g"]
                        if mapped == "refresh":
                            return f"refresh:{window_start}"
                        return mapped
                    window_start = 0
                    render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                    if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                        _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                    continue
                help_visible = not help_visible
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue

            arrow_navigation = _resolve_arrow_navigation(choice, allow_paging_nav, extra_keys)
            if arrow_navigation in {"nav-next", "nav-prev"}:
                return arrow_navigation
            if arrow_navigation is not None:
                choice = arrow_navigation

            if not choice:
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue
            if choice == "\x03":
                raise click.Abort()
            if choice.lower() == MENU_QUIT:
                return None
            if choice.lower() == MENU_UP:
                return "up"
            if extra_key and choice == extra_key:
                return extra_key_return
            if extra_key and choice.lower() == extra_key.lower():
                return extra_key_return
            if extra_keys and choice in extra_keys:
                mapped = extra_keys[choice]
                if mapped == "refresh":
                    return f"refresh:{window_start}"
                return mapped
            if extra_keys and choice.lower() in extra_keys:
                mapped = extra_keys[choice.lower()]
                if mapped == "refresh":
                    return f"refresh:{window_start}"
                return mapped

            if allow_paging_nav and choice in {"/", "?"}:
                search_query = click.prompt(
                    f"search {choice}",
                    default="",
                    show_default=False,
                ).strip()
                if not search_query:
                    render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                    if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                        _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                    continue

                anchor_index = current_selected_index if current_selected_index is not None else min(window_start, len(options) - 1)
                search_forward = choice == "/"
                match_index = _find_search_match(
                    options,
                    search_query,
                    anchor_index,
                    forward=search_forward,
                )
                last_search_query = search_query
                last_search_forward = search_forward
                if match_index is None:
                    click.echo(f"No matches for {search_query!r}.")
                    render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                    if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                        _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                    continue

                current_selected_index = match_index
                window_start = min((match_index // page_size) * page_size, max_window_start)
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue

            if allow_paging_nav and choice in {"n", "N"}:
                if not last_search_query:
                    click.echo("No active search.")
                    render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                    if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                        _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                    continue

                anchor_index = current_selected_index if current_selected_index is not None else min(window_start, len(options) - 1)
                repeat_forward = last_search_forward if choice == "n" else not last_search_forward
                match_index = _find_search_match(
                    options,
                    last_search_query,
                    anchor_index,
                    forward=repeat_forward,
                )
                if match_index is None:
                    click.echo(f"No matches for {last_search_query!r}.")
                    render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                    if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                        _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                    continue

                current_selected_index = match_index
                window_start = min((match_index // page_size) * page_size, max_window_start)
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue

            if allow_paging_nav and choice == "G":
                window_start = last_page_start
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue
            if allow_paging_nav and choice == _CTRL_D:
                window_start = min(window_start + half_page, max_window_start)
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue
            if allow_paging_nav and choice == _CTRL_U:
                window_start = max(window_start - half_page, 0)
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue

            if allow_paging_nav and choice.lower() == MENU_NEXT:
                window_start = min(window_start + page_size, last_page_start)
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue
            if allow_paging_nav and choice.lower() == MENU_PREV:
                window_start = max(window_start - page_size, 0)
                render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
                if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                    _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
                continue

            if choice.isdigit():
                local_index = int(choice) - 1
                if 0 <= local_index < len(page_items):
                    return start + local_index

            help_visible = not help_visible
            render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
            if _SCREEN_WRITE_ENABLED and (not _SCREEN_WRITE_FORCED):
                _RENDER_MODE_CONTROLLER.observe(render_elapsed_ms)
    finally:
        consume_resize_pending()
        if is_tty and hasattr(signal, "SIGWINCH") and previous_resize_handler is not None:
            signal.signal(signal.SIGWINCH, previous_resize_handler)
