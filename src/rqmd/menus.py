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
import sys
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


def select_from_menu(
    title: str,
    options: list[str],
    repeat_choice_right: bool = False,
    zebra: bool = False,
    show_page_indicator: bool = True,
    allow_paging_nav: bool = True,
    extra_key: str | None = None,
    extra_key_help: str = "",
    extra_key_return: str = "extra",
    option_right_labels: list[str] | None = None,
    extra_keys: dict[str, str] | None = None,
    extra_keys_help: dict[str, str] | None = None,
    selected_option_index: int | None = None,
    selected_option_bg: str | None = None,
    footer_legend: str | None = None,
) -> int | str | None:
    """Interactive menu selection with single-key navigation and paging.

    Args:
        title: Menu title/prompt.
        options: List of menu options to display.
        repeat_choice_right: If True, allow repeated selection without exiting.
        zebra: If True, alternate row backgrounds (striping).
        show_page_indicator: If True, show (X/Y) page indicator.
        allow_paging_nav: If True, enable n/p for next/prev page navigation.
        extra_key: Single extra key to bind (e.g., 'r' for notes).
        extra_key_help: Help text for the extra key.
        extra_key_return: Value to return when extra key is pressed.
        option_right_labels: Optional right-aligned labels for each option.
        extra_keys: Optional dict of extra keys to function descriptions.
        extra_keys_help: Optional dict of extra key help text.
        selected_option_index: Initial selected option index.
        selected_option_bg: Background ANSI code for selected option.
        footer_legend: Optional legend text displayed at menu footer.

    Returns:
        Index of selected option and the option text, or extra_key_return if key pressed.
    """
    if not options:
        click.echo("No options available.")
        return None

    page_size = MENU_PAGE_SIZE
    page = 0

    while True:
        total_pages = (len(options) + page_size - 1) // page_size
        start = page * page_size
        page_items = options[start:start + page_size]
        term_width = shutil.get_terminal_size(fallback=(120, 24)).columns

        click.echo("")
        click.echo(title)
        if show_page_indicator and total_pages > 1:
            click.echo(f"Page {page + 1}/{total_pages}")
        for idx, option in enumerate(page_items):
            left = f"  {idx + 1}) {option}"
            global_idx = start + idx
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

            if selected_option_index is not None and global_idx == selected_option_index and selected_option_bg:
                line = apply_background_preserving_styles(line, selected_option_bg)
            elif zebra and (idx % 2 == 1):
                line = apply_background_preserving_styles(line, ZEBRA_BG)

            click.echo(line)

        if footer_legend is not None:
            keys_line = footer_legend
        else:
            if allow_paging_nav:
                keys_line = (
                    f"keys: 1-9 select | {MENU_PREV}=prev | {MENU_NEXT}=next | {MENU_UP}=up | {MENU_QUIT}=quit"
                )
            else:
                keys_line = f"keys: 1-9 select | {MENU_UP}=up | {MENU_QUIT}=quit"
            if extra_key:
                extra_help = extra_key_help if extra_key_help else "action"
                keys_line = f"{keys_line} | {extra_key}={extra_help}"
            if extra_keys:
                for key, ret in extra_keys.items():
                    help_text = (extra_keys_help or {}).get(key, ret)
                    keys_line = f"{keys_line} | {key}={help_text}"
        click.echo(keys_line)
        click.echo("choice: ", nl=False)
        raw_choice = click.getchar()
        choice = raw_choice.strip()
        click.echo(choice)

        if not choice:
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
            return extra_keys[choice]
        if extra_keys and choice.lower() in extra_keys:
            return extra_keys[choice.lower()]

        if allow_paging_nav and choice.lower() == MENU_NEXT:
            # Shift+N acts as reverse paging (previous page).
            if choice.isupper():
                if page > 0:
                    page -= 1
            elif page < total_pages - 1:
                page += 1
            continue
        if allow_paging_nav and choice.lower() == MENU_PREV:
            # Shift+P acts as reverse paging (next page).
            if choice.isupper():
                if page < total_pages - 1:
                    page += 1
            elif page > 0:
                page -= 1
            continue

        if choice.isdigit():
            local_index = int(choice) - 1
            if 0 <= local_index < len(page_items):
                return start + local_index

        click.echo("Invalid input. Use number or navigation keys.")
