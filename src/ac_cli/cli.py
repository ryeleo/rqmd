#!/usr/bin/env python

"""Requirements/criteria summary updater and fast interactive status editor.

This tool keeps per-file status summaries synchronized and provides an
optimized, keyboard-driven workflow for updating requirement statuses across a
markdown catalog.

Core behavior:
- Scans all markdown files under a requirements directory.
- Computes status counts from "- **Status:** ..." lines.
- Inserts or updates the summary block between:
    <!-- acceptance-status-summary:start -->
    <!-- acceptance-status-summary:end -->
- Supports both batch/check mode and interactive status editing.

Interactive workflow highlights:
- Select file, then requirement, then status.
- Fast single-key input via click.getchar() for menu navigation.
- Paging keys:
    n = next page, p = previous page, r = back, q = quit.
- Requirement-level next/prev shortcuts at status menu:
    n = next requirement, p = previous requirement (history-aware).
- Optional sort toggles (s) at file and requirement selection levels.
- Optional blocked/deprecated reason prompts when setting those statuses.

Status model:
- 💡 Proposed
- 🔧 Implemented
- 💻 Desktop-Verified
- 🎮 VR-Verified
- ✅ Done
- ⛔ Blocked
- 🗑️ Deprecated

Non-interactive usage:
- Update a single requirement by id/status (optionally scoped by file).
- Update multiple requirements in one command via repeated --set ID=STATUS.
- Useful for automation and agent-driven workflows.

Examples:
- Check only (no writes):
    ac-cli --check
- Interactive mode with emoji headers:
    ac-cli --emoji-columns
- Non-interactive single update:
    ac-cli \
            --set-criterion-id R-TELEMETRY-LOG-001 \
            --set-status implemented
- Non-interactive bulk update:
    ac-cli \
            --set R-STEELTARGET-AUDIO-004=implemented \
            --set R-STEELTARGET-AUDIO-005=desktop-verified
- Non-interactive batch update from file:
    ac-cli \
            --set-file tmp/ac-updates.jsonl

Notes:
- This script expects markdown requirement sections to use "### <PREFIX>-..."
    headers and "- **Status:** ..." lines.
- Header prefixes are configurable with --id-prefix and default to AC and R.
- If click/tabulate are missing, install them with pip3.
"""

from __future__ import annotations

import csv
import json
import re
import readline  # noqa: F401 — activates arrow-key line editing in input()/click.prompt()
import shutil
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

try:
    from tabulate import tabulate
except ImportError:
    print("Error: 'tabulate' package is required.", file=sys.stderr)
    print("Install with: pip3 install tabulate", file=sys.stderr)
    sys.exit(1)

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)


SUMMARY_START = "<!-- acceptance-status-summary:start -->"
SUMMARY_END = "<!-- acceptance-status-summary:end -->"
DEFAULT_ID_PREFIXES = ("AC", "R")
STATUS_ORDER = [
    ("💡 Proposed", "proposed"),
    ("🔧 Implemented", "implemented"),
    ("💻 Desktop-Verified", "desktop-verified"),
    ("🎮 VR-Verified", "vr-verified"),
    ("✅ Done", "done"),
    ("⛔ Blocked", "blocked"),
    ("🗑️ Deprecated", "deprecated"),
]
STATUS_TERSE_HEADERS_ASCII = ["P", "I", "DT", "VR", "Done", "Blk", "Dep", "WaitVR"]
STATUS_ALIASES = {
    "✅ Verified": "✅ Done",
}
STATUS_PARSE_ALIASES = {
    "proposal": "💡 Proposed",
    "propose": "💡 Proposed",
    "desktop verified": "💻 Desktop-Verified",
    "vr verified": "🎮 VR-Verified",
}
MENU_BACK = "r"
MENU_QUIT = "q"
MENU_NEXT = "n"
MENU_PREV = "p"
MENU_TOGGLE_SORT = "s"
MENU_PAGE_SIZE = 9
STATUS_PATTERN = re.compile(r"^- \*\*Status:\*\* (?P<status>.+?)\s*$", re.MULTILINE)
BLOCKED_REASON_PATTERN = re.compile(r"^\*\*Blocked:\*\*\s*(.+?)\s*$", re.MULTILINE)
DEPRECATED_REASON_PATTERN = re.compile(r"^\*\*Deprecated:\*\*\s*(.+?)\s*$", re.MULTILINE)
ID_PREFIX_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*$")
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
NON_ALNUM_PREFIX_PATTERN = re.compile(r"^[^a-zA-Z0-9]+")
NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")
ANSI_RESET = "\x1b[0m"
ZEBRA_BG = "\x1b[48;5;236m"
# Fixed 256-color purple for Proposed status — avoids theme-dependent 16-color
# rendering where bright_blue (\x1b[94m) shifts noticeably on dark zebra backgrounds.
PROPOSED_FG = "\x1b[38;5;135m"


@lru_cache(maxsize=None)
def build_criterion_header_pattern(id_prefixes: tuple[str, ...]) -> re.Pattern[str]:
    alternation = "|".join(re.escape(prefix) for prefix in id_prefixes)
    return re.compile(
        rf"^###\s+(?P<id>(?:{alternation})-[A-Z0-9-]+):\s*(?P<title>.+?)\s*$"
    )


def normalize_id_prefixes(raw_prefixes: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if not raw_prefixes:
        return DEFAULT_ID_PREFIXES

    prefixes: list[str] = []
    seen: set[str] = set()
    for raw in raw_prefixes:
        for part in raw.split(","):
            prefix = part.strip().upper()
            if not prefix:
                continue
            if not ID_PREFIX_PATTERN.fullmatch(prefix):
                raise ValueError(
                    f"Invalid id prefix '{part.strip()}'. Use uppercase letters/numbers, for example AC, R, or REQ."
                )
            if prefix not in seen:
                seen.add(prefix)
                prefixes.append(prefix)

    if not prefixes:
        raise ValueError("At least one non-empty id prefix is required.")

    return tuple(prefixes)


def style_status_count(status_label: str, value: object) -> str:
    text = str(value)
    if status_label in ("✅ Done", "🎮 VR-Verified"):
        return click.style(text, fg="green")
    if status_label == "💡 Proposed":
        return f"{PROPOSED_FG}{text}{ANSI_RESET}"
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return click.style(text, dim=True)
    # Implemented/Desktop-Verified stay normal for baseline readability.
    return text


def style_status_label(status_label: str) -> str:
    if status_label in ("✅ Done", "🎮 VR-Verified"):
        return click.style(status_label, fg="green")
    if status_label == "💡 Proposed":
        return f"{PROPOSED_FG}{status_label}{ANSI_RESET}"
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return click.style(status_label, dim=True)
    # Implemented/Desktop-Verified stay normal for baseline readability.
    return status_label


def style_status_line(status_label: str, text: str) -> str:
    if status_label in ("✅ Done", "🎮 VR-Verified"):
        return click.style(text, fg="green")
    if status_label == "💡 Proposed":
        return f"{PROPOSED_FG}{text}{ANSI_RESET}"
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return click.style(text, dim=True)
    # Implemented/Desktop-Verified stay normal for baseline readability.
    return text


def status_emoji(status_label: str) -> str:
    parts = status_label.split(" ", 1)
    return parts[0] if parts else status_label


def waiting_vr_count(counts: dict[str, int]) -> int:
    return counts["🔧 Implemented"] + counts["💻 Desktop-Verified"]


def status_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for label, slug in STATUS_ORDER:
        lower_label = label.lower()
        plain_label = label.split(" ", 1)[1].lower()
        lookup[lower_label] = label
        lookup[plain_label] = label
        lookup[slug.lower()] = label
    for alias_from, alias_to in STATUS_ALIASES.items():
        lookup[alias_from.lower()] = alias_to
        if " " in alias_from:
            lookup[alias_from.split(" ", 1)[1].lower()] = alias_to
    for alias_from, alias_to in STATUS_PARSE_ALIASES.items():
        lookup[alias_from.lower()] = alias_to
    return lookup


STATUS_LOOKUP = status_lookup()


def status_key(value: str) -> str:
    key = ANSI_ESCAPE_PATTERN.sub("", value).strip().lower()
    key = NON_ALNUM_PATTERN.sub("-", key)
    return key.strip("-")


def coerce_status_label(value: str) -> str:
    raw = value.strip()
    candidates: list[str] = [raw]

    # Handle malformed/broken emoji prefixes by trying the label tail.
    tail = NON_ALNUM_PREFIX_PATTERN.sub("", raw)
    if tail and tail != raw:
        candidates.append(tail)
    if " " in raw:
        candidates.append(raw.split(" ", 1)[1].strip())
    if " " in tail:
        candidates.append(tail.split(" ", 1)[1].strip())

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        lowered = candidate.lower().strip()
        if lowered and lowered not in seen:
            seen.add(lowered)
            if lowered in STATUS_LOOKUP:
                return STATUS_LOOKUP[lowered]

        canonical_key = status_key(candidate)
        if canonical_key and canonical_key not in seen:
            seen.add(canonical_key)
            if canonical_key in STATUS_LOOKUP:
                return STATUS_LOOKUP[canonical_key]

    raise ValueError(f"Unrecognized status value: {value}")


def normalize_status_input(value: str) -> str:
    try:
        return coerce_status_label(value)
    except ValueError as exc:
        raise click.ClickException(
            "Unrecognized status input "
            f"'{value}'. Use one of: "
            + ", ".join(label for label, _ in STATUS_ORDER)
        ) from exc


def build_color_rollup_text(counts: dict[str, int]) -> str:
    blue = counts["💡 Proposed"]
    normal = counts["🔧 Implemented"] + counts["💻 Desktop-Verified"]
    green = counts["🎮 VR-Verified"] + counts["✅ Done"]
    dimmed = counts["⛔ Blocked"] + counts["🗑️ Deprecated"]

    blue_text = click.style(f"{blue:>3}", fg="bright_blue")
    normal_text = f"{normal:>3}"
    green_text = click.style(f"{green:>3}", fg="green")
    dimmed_text = click.style(f"{dimmed:>3}", dim=True)

    return f"{blue_text} | {normal_text} | {green_text} | {dimmed_text}"


def visible_length(text: str) -> int:
    plain = ANSI_ESCAPE_PATTERN.sub("", text)
    width = 0
    for ch in plain:
        code = ord(ch)
        if ch in ("\u200d", "\ufe0e", "\ufe0f"):
            # Zero-width joiner and variation selectors should not consume columns.
            continue
        if unicodedata.combining(ch):
            continue
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
            continue
        # Common emoji blocks often render double-width in terminals.
        if 0x1F300 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
            width += 2
            continue
        width += 1
    return width


def truncate_text(text: str, max_len: int) -> str:
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
    # Re-apply background after any nested reset so inline foreground colors keep
    # working without dropping zebra striping mid-line.
    patched = text.replace(ANSI_RESET, ANSI_RESET + bg_ansi)
    return f"{bg_ansi}{patched}{ANSI_RESET}"


def right_align_menu_suffix(label: str, suffix: str, index_width: int = 1) -> str:
    term_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    # Printed prefix is: "  {n}) " where n is one digit for our 1-9 menu.
    prefix_width = 5 if index_width == 1 else (4 + index_width)
    label_len = visible_length(label)
    suffix_len = visible_length(suffix)
    spaces = term_width - prefix_width - label_len - suffix_len
    if spaces < 2:
        spaces = 2
    return f"{label}{' ' * spaces}{suffix}"


def file_sort_key_by_priority(counts: dict[str, int], label: str) -> tuple[int, int, int, str]:
    # Priority buckets: Black (Implemented + Desktop-Verified), then Blue, then Green.
    black = counts["🔧 Implemented"] + counts["💻 Desktop-Verified"]
    blue = counts["💡 Proposed"]
    green = counts["🎮 VR-Verified"] + counts["✅ Done"]
    return (-black, -blue, -green, label)


def build_summary_line(counts: dict[str, int], verbose: bool = False, filename: str = "") -> str:
    if verbose:
        # Build a table row for this file
        row = [filename] + [counts[label] for label, _ in STATUS_ORDER]
        return row
    else:
        # Terse mode: show just emojis and counts inline
        parts = [f"{counts[label]}{label.split()[0]}" for label, _ in STATUS_ORDER]
        return " ".join(parts)


def build_summary_table(rows: list[list], verbose: bool = False) -> str:
    """Build a tabular summary, optionally with headers."""
    if not verbose or not rows:
        return ""
    
    headers = ["File"] + [label for label, _ in STATUS_ORDER]
    return tabulate(rows, headers=headers, tablefmt="simple")


def build_summary_block(counts: dict[str, int]) -> str:
    # Build simple inline summary for HTML comments in markdown
    parts = [f"{counts[label]}{label.split()[0]}" for label, _ in STATUS_ORDER]
    summary_text = " ".join(parts)
    return "\n".join([
        SUMMARY_START,
        f"Summary: {summary_text}",
        SUMMARY_END,
    ])


def normalize_status_lines(text: str) -> tuple[str, bool]:
    changed = False

    def replace_status_line(match: re.Match[str]) -> str:
        nonlocal changed
        raw_status = match.group("status")
        try:
            canonical = coerce_status_label(raw_status)
        except ValueError:
            return match.group(0)

        updated_line = f"- **Status:** {canonical}"
        if updated_line != match.group(0):
            changed = True
        return updated_line

    updated_text = STATUS_PATTERN.sub(replace_status_line, text)
    return updated_text, changed


def count_statuses(text: str) -> dict[str, int]:
    counts = {label: 0 for label, _ in STATUS_ORDER}
    for match in STATUS_PATTERN.finditer(text):
        raw_status = match.group("status")
        status = coerce_status_label(raw_status)
        counts[status] += 1
    return counts


def insert_or_replace_summary(text: str, summary_block: str) -> str:
    existing_pattern = re.compile(
        rf"{re.escape(SUMMARY_START)}\n.*?\n{re.escape(SUMMARY_END)}\n?",
        re.DOTALL,
    )

    if existing_pattern.search(text):
        return existing_pattern.sub(summary_block + "\n", text, count=1)

    lines = text.splitlines()
    if not lines:
        return summary_block + "\n"

    insert_at = 1 if lines[0].startswith("# ") else 0

    for index, line in enumerate(lines):
        if line.startswith("Scope:"):
            insert_at = index + 1
            break

    new_lines = lines[:insert_at]
    if new_lines and new_lines[-1] != "":
        new_lines.append("")
    new_lines.extend(summary_block.splitlines())
    new_lines.append("")
    if insert_at < len(lines) and lines[insert_at] != "":
        new_lines.append("")
    new_lines.extend(lines[insert_at:])
    return "\n".join(new_lines).rstrip() + "\n"


def iter_domain_files(repo_root: Path, criteria_dir_input: str) -> list[Path]:
    criteria_dir = Path(criteria_dir_input)
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()
    return sorted(criteria_dir.glob("*.md"))


def display_name_from_h1(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return path.stem

    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            shortened = title.replace("Acceptance Criteria", "").strip()
            shortened = shortened.replace("Requirements", "").strip()
            if shortened:
                return shortened
            if title:
                return title
            break

    return path.stem


def process_file(path: Path, check_only: bool, verbose: bool = False) -> tuple[bool, dict[str, int]]:
    original = path.read_text(encoding="utf-8")
    normalized, _ = normalize_status_lines(original)
    counts = count_statuses(normalized)
    updated = insert_or_replace_summary(normalized, build_summary_block(counts))

    # Normalize trailing newline so repeated processing stays idempotent.
    original_canonical = original.rstrip("\n") + "\n"
    updated = updated.rstrip("\n") + "\n"
    changed = updated != original_canonical

    if changed and not check_only:
        path.write_text(updated, encoding="utf-8")

    return changed, counts


def parse_criteria(
    path: Path,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    criteria: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    header_pattern = build_criterion_header_pattern(id_prefixes)

    for index, line in enumerate(lines):
        header_match = header_pattern.match(line)
        if header_match:
            current = {
                "id": header_match.group("id"),
                "title": header_match.group("title"),
                "status": None,
                "status_line": None,
                "blocked_reason": None,
                "blocked_reason_line": None,
                "deprecated_reason": None,
                "deprecated_reason_line": None,
            }
            criteria.append(current)
            continue

        status_match = STATUS_PATTERN.match(line)
        if status_match and current and current["status"] is None:
            raw_status = status_match.group("status")
            try:
                status = coerce_status_label(raw_status)
            except ValueError:
                status = raw_status
            current["status"] = status
            current["status_line"] = index
            continue

        blocked_match = BLOCKED_REASON_PATTERN.match(line)
        if blocked_match and current and current["status_line"] is not None:
            current["blocked_reason"] = blocked_match.group(1).strip()
            current["blocked_reason_line"] = index

        deprecated_match = DEPRECATED_REASON_PATTERN.match(line)
        if deprecated_match and current and current["status_line"] is not None:
            current["deprecated_reason"] = deprecated_match.group(1).strip()
            current["deprecated_reason_line"] = index

    return [criterion for criterion in criteria if criterion["status_line"] is not None]


def find_criterion_by_id(
    path: Path,
    criterion_id: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[str, object] | None:
    target = criterion_id.strip().upper()
    for criterion in parse_criteria(path, id_prefixes=id_prefixes):
        if str(criterion["id"]).upper() == target:
            return criterion
    return None


def extract_criterion_block(
    path: Path,
    criterion_id: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    start_index: int | None = None
    target = criterion_id.strip().upper()
    header_pattern = build_criterion_header_pattern(id_prefixes)

    for index, line in enumerate(lines):
        match = header_pattern.match(line)
        if match and match.group("id").upper() == target:
            start_index = index
            break

    if start_index is None:
        return ""

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        if header_pattern.match(lines[index]):
            end_index = index
            break

    block = "\n".join(lines[start_index:end_index]).strip()
    return block


def _rule_style_kwargs(status_label: str) -> dict:
    if status_label in ("✅ Done", "🎮 VR-Verified"):
        return {"fg": "green"}
    if status_label == "💡 Proposed":
        return {"fg": "bright_blue"}
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return {"dim": True}
    return {"fg": "yellow"}


def print_criterion_panel(
    path: Path,
    criterion: dict[str, object],
    repo_root: Path,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> None:
    criterion_id = str(criterion["id"])
    title = str(criterion["title"])
    status = str(criterion.get("status") or "")
    criterion_text = extract_criterion_block(path, criterion_id, id_prefixes=id_prefixes)
    term_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    rule = "=" * max(24, min(term_width, 100))
    rule_kwargs = _rule_style_kwargs(status)

    click.echo("")
    click.echo(click.style(rule, **rule_kwargs))
    click.echo(click.style(f"{criterion_id}: {title}", bold=True))
    click.echo(click.style(f"Source: {path.relative_to(repo_root).as_posix()}", dim=True))
    click.echo(click.style(rule, **rule_kwargs))
    if criterion_text:
        click.echo(criterion_text)
    click.echo(click.style(rule, **rule_kwargs))


def update_criterion_status(
    path: Path,
    criterion: dict[str, object],
    new_status: str,
    blocked_reason: str | None = None,
    deprecated_reason: str | None = None,
) -> bool:
    lines = path.read_text(encoding="utf-8").splitlines()
    status_line = criterion["status_line"]
    blocked_reason_line = criterion.get("blocked_reason_line")
    deprecated_reason_line = criterion.get("deprecated_reason_line")
    if not isinstance(status_line, int):
        raise ValueError("Invalid criterion status line.")

    new_status_line_text = f"- **Status:** {new_status}"
    status_changed = lines[status_line] != new_status_line_text

    if status_changed:
        lines[status_line] = new_status_line_text

    is_blocked = "Blocked" in new_status
    is_deprecated = "Deprecated" in new_status

    # We may insert or remove lines after status_line; track a cumulative shift so
    # that removal/insertion of the *other* annotation line stays correct.
    shift = 0

    # --- Handle blocked reason annotation ---
    if isinstance(blocked_reason_line, int):
        adj_blocked = blocked_reason_line + shift
        if is_blocked and blocked_reason:
            new_line = f"**Blocked:** {blocked_reason}"
            if lines[adj_blocked] != new_line:
                lines[adj_blocked] = new_line
                status_changed = True
        elif is_blocked:
            pass  # keep existing reason as-is
        else:
            lines.pop(adj_blocked)
            shift -= 1
            status_changed = True
    elif is_blocked and blocked_reason:
        insert_at = status_line + 1 + shift
        lines.insert(insert_at, f"**Blocked:** {blocked_reason}")
        shift += 1
        status_changed = True

    # --- Handle deprecated reason annotation ---
    if isinstance(deprecated_reason_line, int):
        adj_deprecated = deprecated_reason_line + shift
        if is_deprecated and deprecated_reason:
            new_line = f"**Deprecated:** {deprecated_reason}"
            if lines[adj_deprecated] != new_line:
                lines[adj_deprecated] = new_line
                status_changed = True
        elif is_deprecated:
            pass  # keep existing reason as-is
        else:
            lines.pop(adj_deprecated)
            status_changed = True
    elif is_deprecated and deprecated_reason:
        insert_at = status_line + 1 + shift
        lines.insert(insert_at, f"**Deprecated:** {deprecated_reason}")
        status_changed = True

    if status_changed:
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    return status_changed


def prompt_for_blocked_reason() -> str:
    """Prompt user for a reason why criterion is blocked."""
    click.echo()
    click.echo("Provide a reason for blocking (or press Enter to skip):")
    reason = click.prompt("Reason", default="", show_default=False).strip()
    return reason


def prompt_for_deprecated_reason() -> str:
    """Prompt user for a reason why criterion is deprecated."""
    click.echo()
    click.echo("Provide a reason for deprecating (or press Enter to skip):")
    reason = click.prompt("Reason", default="", show_default=False).strip()
    return reason


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
) -> int | str | None:
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

        if allow_paging_nav:
            keys_line = (
                f"keys: 1-9 select | {MENU_PREV}=prev | {MENU_NEXT}=next | {MENU_BACK}=back | {MENU_QUIT}=quit"
            )
        else:
            keys_line = f"keys: 1-9 select | {MENU_BACK}=back | {MENU_QUIT}=quit"
        if extra_key:
            extra_help = extra_key_help if extra_key_help else "action"
            keys_line = f"{keys_line} | {extra_key}={extra_help}"
        if extra_keys:
            for k, _ret in extra_keys.items():
                help_text = (extra_keys_help or {}).get(k, _ret)
                keys_line = f"{keys_line} | {k}={help_text}"
        click.echo(keys_line)
        click.echo("choice: ", nl=False)
        choice = click.getchar().strip().lower()
        click.echo(choice)

        if not choice:
            continue
        if choice == "\x03":
            raise click.Abort()
        if choice == MENU_QUIT:
            return None
        if choice == MENU_BACK:
            return "back"
        if extra_key and choice == extra_key:
            return extra_key_return
        if extra_keys and choice in extra_keys:
            return extra_keys[choice]
        if allow_paging_nav and choice == MENU_NEXT:
            if page < total_pages - 1:
                page += 1
            continue
        if allow_paging_nav and choice == MENU_PREV:
            if page > 0:
                page -= 1
            continue

        if choice.isdigit():
            local_index = int(choice) - 1
            if 0 <= local_index < len(page_items):
                return start + local_index

        click.echo("Invalid input. Use number or navigation keys.")


def interactive_update_loop(
    repo_root: Path,
    criteria_dir: str,
    domain_files: list[Path],
    emoji_columns: bool,
    sort_files: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> int:
    current_sort_files = sort_files
    ordered_paths = [path.resolve() for path in domain_files]
    force_rescan = True

    while True:
        if force_rescan:
            scanned_paths = [path.resolve() for path in iter_domain_files(repo_root, criteria_dir)]
            file_rows_for_sort: list[tuple[Path, dict[str, int], str]] = []
            for path in scanned_paths:
                counts = count_statuses(path.read_text(encoding="utf-8"))
                label = display_name_from_h1(path)
                file_rows_for_sort.append((path, counts, label))

            if current_sort_files:
                file_rows_for_sort.sort(key=lambda row: file_sort_key_by_priority(row[1], row[2]))

            ordered_paths = [row[0] for row in file_rows_for_sort]
            force_rescan = False

        existing_paths = [path for path in ordered_paths if path.exists() and path.is_file()]
        if not existing_paths:
            click.echo("No requirement markdown files found.")
            return 1

        file_rows: list[tuple[Path, dict[str, int], str]] = []
        for path in existing_paths:
            counts = count_statuses(path.read_text(encoding="utf-8"))
            label = display_name_from_h1(path)
            file_rows.append((path, counts, label))

        file_options = [
            right_align_menu_suffix(label, build_color_rollup_text(counts), index_width=1)
            for _, counts, label in file_rows
        ]

        file_choice = select_from_menu(
            "Select file",
            file_options,
            repeat_choice_right=True,
            zebra=True,
            extra_key=MENU_TOGGLE_SORT,
            extra_key_help="toggle-sort+rescan",
            extra_key_return="toggle-sort",
        )
        if file_choice is None:
            return 0
        if file_choice == "back":
            continue
        if file_choice == "toggle-sort":
            current_sort_files = not current_sort_files
            force_rescan = True
            mode = "sorted" if current_sort_files else "unsorted"
            click.echo(f"Select file mode: {mode} (rescanned)")
            continue

        selected_path = file_rows[int(file_choice)][0]

        # Criterion-level sort mirrors file-level sort.
        current_sort_criteria = current_sort_files

        def sort_criteria(clist: list[dict[str, object]]) -> list[dict[str, object]]:
            if not current_sort_criteria:
                return clist
            status_priority = {label: i for i, (label, _) in enumerate(STATUS_ORDER)}
            return sorted(clist, key=lambda c: status_priority.get(str(c["status"]), 99))

        # Navigation uses a flat index into the sorted criteria list.
        # history is a stack of (criteria_snapshot_id_list, index) for p/n.
        history: list[int] = []   # sorted-index stack
        history_pos = -1
        criterion_index: int | None = None  # index into sorted criteria list

        while True:
            raw_criteria = parse_criteria(selected_path, id_prefixes=id_prefixes)
            criteria = sort_criteria(raw_criteria)

            if criterion_index is None:
                term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
                criterion_right_labels = [str(c["id"]) for c in criteria]
                criterion_options = [
                    style_status_line(str(c["status"]), truncate_text(
                        f"{status_emoji(str(c['status']))} {c['title']}",
                        max(8, term_width - 5 - visible_length(str(c["id"])) - 2),
                    ))
                    for c in criteria
                ]
                criterion_choice = select_from_menu(
                    f"Select requirement in {selected_path.relative_to(repo_root).as_posix()}",
                    criterion_options,
                    zebra=True,
                    option_right_labels=criterion_right_labels,
                    extra_key=MENU_TOGGLE_SORT,
                    extra_key_help="toggle-sort",
                    extra_key_return="toggle-sort",
                )
                if criterion_choice is None:
                    return 0
                if criterion_choice == "back":
                    break
                if criterion_choice == "toggle-sort":
                    current_sort_criteria = not current_sort_criteria
                    click.echo(f"Criterion sort: {'on' if current_sort_criteria else 'off'}")
                    continue

                criterion_index = int(criterion_choice)
                del history[history_pos + 1:]
                history.append(criterion_index)
                history_pos = len(history) - 1

            # Refresh from latest parse (line numbers may have shifted after edits).
            selected_criterion = criteria[criterion_index] if criterion_index < len(criteria) else criteria[-1]
            # Re-sync by ID in case sort order changed.
            refreshed = next((c for c in criteria if str(c["id"]) == str(selected_criterion["id"])), None)
            if refreshed:
                selected_criterion = refreshed
                criterion_index = criteria.index(refreshed)

            print_criterion_panel(selected_path, selected_criterion, repo_root, id_prefixes=id_prefixes)

            # Build status menu with current status highlighted.
            status_labels = [label for label, _ in STATUS_ORDER]
            status_options = [style_status_label(label) for label, _ in STATUS_ORDER]
            current_status = str(selected_criterion.get("status") or "")
            try:
                current_status_idx = status_labels.index(current_status)
            except ValueError:
                current_status_idx = None
            # Background for highlighted status row mirrors the status color family.
            STATUS_HIGHLIGHT_BG = "\x1b[48;5;220m"   # amber — visible on both light/dark
            if current_status in ("✅ Done", "🎮 VR-Verified"):
                STATUS_HIGHLIGHT_BG = "\x1b[48;5;28m"   # dark green
            elif current_status == "💡 Proposed":
                STATUS_HIGHLIGHT_BG = "\x1b[48;5;27m"   # bright blue
            elif current_status in ("⛔ Blocked", "🗑️ Deprecated"):
                STATUS_HIGHLIGHT_BG = "\x1b[48;5;238m"  # dark gray

            status_choice = select_from_menu(
                f"Set status for {selected_criterion['id']}",
                status_options,
                show_page_indicator=False,
                allow_paging_nav=False,
                extra_keys={"n": "nav-next", "p": "nav-prev"},
                extra_keys_help={"n": "next-req", "p": "prev-req"},
                selected_option_index=current_status_idx,
                selected_option_bg=STATUS_HIGHLIGHT_BG,
            )
            if status_choice is None:
                return 0
            if status_choice == "back":
                criterion_index = None
                continue
            if status_choice == "nav-prev":
                if history_pos > 0:
                    history_pos -= 1
                    criterion_index = history[history_pos]
                else:
                    click.echo("Already at first requirement.")
                continue
            if status_choice == "nav-next":
                if history_pos < len(history) - 1:
                    history_pos += 1
                    criterion_index = history[history_pos]
                elif criterion_index < len(criteria) - 1:
                    criterion_index += 1
                    del history[history_pos + 1:]
                    history.append(criterion_index)
                    history_pos = len(history) - 1
                else:
                    click.echo("Already at last requirement in file.")
                continue

            new_status = status_labels[int(status_choice)]

            # Prompt for blocked/deprecated reason
            blocked_reason = None
            if "Blocked" in new_status:
                blocked_reason = prompt_for_blocked_reason()
            deprecated_reason = None
            if "Deprecated" in new_status:
                deprecated_reason = prompt_for_deprecated_reason()

            changed = update_criterion_status(selected_path, selected_criterion, new_status, blocked_reason=blocked_reason, deprecated_reason=deprecated_reason)
            process_file(selected_path, check_only=False)

            if changed:
                click.echo(f"Updated {selected_criterion['id']} -> {new_status}")
            else:
                click.echo(f"No change for {selected_criterion['id']} ({new_status})")

            # Refresh and show current table after each update.
            _, table_rows = collect_summary_rows(repo_root, domain_files, check_only=True)
            print_summary_table(table_rows, emoji_columns=emoji_columns)

            # Auto-advance: move to next requirement in the sorted list (wraps at end).
            raw_criteria_after = parse_criteria(selected_path, id_prefixes=id_prefixes)
            criteria_after = sort_criteria(raw_criteria_after)
            cur_id = str(selected_criterion["id"])
            new_idx = next((i for i, c in enumerate(criteria_after) if str(c["id"]) == cur_id), criterion_index)
            if new_idx < len(criteria_after) - 1:
                criterion_index = new_idx + 1
                del history[history_pos + 1:]
                history.append(criterion_index)
                history_pos = len(history) - 1
            else:
                if criteria_after:
                    # Wrap to first requirement instead of jumping up to the selection menu.
                    criterion_index = 0
                    del history[history_pos + 1:]
                    history.append(criterion_index)
                    history_pos = len(history) - 1
                else:
                    criterion_index = None
                continue


def collect_criteria_by_status(
    repo_root: Path,
    domain_files: list[Path],
    target_status: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    """Collect all criteria matching target_status, grouped by file."""
    result: dict[Path, list[dict[str, object]]] = {}
    for path in domain_files:
        criteria = parse_criteria(path, id_prefixes=id_prefixes)
        matching = [c for c in criteria if c["status"] == target_status]
        if matching:
            result[path] = matching
    return result


def print_criteria_tree(repo_root: Path, criteria_by_file: dict[Path, list[dict[str, object]]], target_status: str) -> None:
    """Print criteria in tree format grouped by file."""
    if not criteria_by_file:
        click.echo(f"No criteria found with status: {target_status}")
        return

    click.echo(click.style(f"\n{target_status}", bold=True))
    click.echo()

    files = sorted(criteria_by_file.keys())
    for file_idx, path in enumerate(files):
        is_last_file = file_idx == len(files) - 1
        file_prefix = "└── " if is_last_file else "├── "
        relative_path = path.relative_to(repo_root)
        click.echo(f"{file_prefix}{click.style(relative_path.as_posix(), dim=True)}")

        criteria = criteria_by_file[path]
        for crit_idx, criterion in enumerate(criteria):
            is_last_crit = crit_idx == len(criteria) - 1
            crit_prefix = "    " if is_last_file else "│   "
            branch = "└── " if is_last_crit else "├── "
            crit_id = criterion["id"]
            crit_title = criterion["title"]
            click.echo(f"{crit_prefix}{branch}{crit_id}: {crit_title}")

    click.echo()


def filtered_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    target_status: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> int:
    """Walk through all ACs matching target_status one by one in interactive mode."""

    def build_flat_list() -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        for path in domain_files:
            for c in parse_criteria(path, id_prefixes=id_prefixes):
                if c["status"] == target_status:
                    result.append((path, c))
        return result

    flat_list = build_flat_list()
    if not flat_list:
        click.echo(f"No criteria found with status: {target_status}")
        return 0

    click.echo(click.style(
        f"\nFiltered walk: {target_status} ({len(flat_list)} criteria across all files)",
        bold=True,
    ))

    index = 0
    while True:
        # Rebuild after each update so dropped-out items and refreshed line numbers are correct.
        flat_list = build_flat_list()
        if not flat_list:
            click.echo("No more criteria with this status.")
            return 0
        index = min(index, len(flat_list) - 1)

        path, criterion = flat_list[index]
        # Re-fetch from file for up-to-date line numbers.
        refreshed = find_criterion_by_id(path, str(criterion["id"]), id_prefixes=id_prefixes)
        if refreshed:
            criterion = refreshed

        click.echo(click.style(f"\n[{index + 1}/{len(flat_list)}]", dim=True))
        print_criterion_panel(path, criterion, repo_root, id_prefixes=id_prefixes)

        status_labels = [label for label, _ in STATUS_ORDER]
        status_options = [style_status_label(label) for label, _ in STATUS_ORDER]
        current_status = str(criterion.get("status") or "")
        try:
            current_status_idx = status_labels.index(current_status)
        except ValueError:
            current_status_idx = None

        STATUS_HIGHLIGHT_BG = "\x1b[48;5;220m"   # amber
        if current_status in ("\u2705 Done", "\U0001f3ae VR-Verified"):
            STATUS_HIGHLIGHT_BG = "\x1b[48;5;28m"   # dark green
        elif current_status == "\U0001f4a1 Proposed":
            STATUS_HIGHLIGHT_BG = "\x1b[48;5;27m"   # bright blue
        elif current_status in ("\u26d4 Blocked", "\U0001f5d1\ufe0f Deprecated"):
            STATUS_HIGHLIGHT_BG = "\x1b[48;5;238m"  # dark gray

        status_choice = select_from_menu(
            f"Set status for {criterion['id']} [{index + 1}/{len(flat_list)}]",
            status_options,
            show_page_indicator=False,
            allow_paging_nav=False,
            extra_keys={"n": "nav-next", "p": "nav-prev"},
            extra_keys_help={"n": "next-req", "p": "prev-req"},
            selected_option_index=current_status_idx,
            selected_option_bg=STATUS_HIGHLIGHT_BG,
        )

        if status_choice is None:
            return 0
        if status_choice == "back":
            return 0
        if status_choice == "nav-prev":
            if index > 0:
                index -= 1
            else:
                click.echo("Already at first filtered AC.")
            continue
        if status_choice == "nav-next":
            if index < len(flat_list) - 1:
                index += 1
            else:
                click.echo("End of filtered list. All criteria reviewed.")
                return 0
            continue

        new_status = status_labels[int(status_choice)]

        blocked_reason = None
        if "Blocked" in new_status:
            blocked_reason = prompt_for_blocked_reason()
        deprecated_reason = None
        if "Deprecated" in new_status:
            deprecated_reason = prompt_for_deprecated_reason()

        changed = update_criterion_status(
            path, criterion, new_status,
            blocked_reason=blocked_reason, deprecated_reason=deprecated_reason,
        )
        process_file(path, check_only=False)

        if changed:
            click.echo(f"Updated {criterion['id']} -> {new_status}")
        else:
            click.echo(f"No change for {criterion['id']} ({new_status})")

        _, table_rows = collect_summary_rows(repo_root, domain_files, check_only=True)
        print_summary_table(table_rows, emoji_columns=emoji_columns)

        # If the status changed away from target_status this requirement drops out of the list;
        # the same index now points to what was the next item. Otherwise advance by 1.
        flat_after = build_flat_list()
        if changed and new_status != target_status:
            if not flat_after:
                click.echo("All filtered criteria reviewed.")
                return 0
            index = min(index, len(flat_after) - 1)
        else:
            if flat_after and index < len(flat_after) - 1:
                index += 1
            elif flat_after:
                click.echo("End of filtered list, wrapping to first.")
                index = 0
            else:
                click.echo("All filtered criteria reviewed.")
                return 0


def lookup_criterion_interactive(
    repo_root: Path,
    domain_files: list[Path],
    criterion_id: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> int:
    """Find a single requirement by id, show its panel, present the status menu once, and exit."""
    criterion_id = criterion_id.strip().upper()
    matches: list[tuple[Path, dict[str, object]]] = []
    for path in domain_files:
        c = find_criterion_by_id(path, criterion_id, id_prefixes=id_prefixes)
        if c:
            matches.append((path, c))

    if not matches:
        raise click.ClickException(f"Requirement '{criterion_id}' not found in the configured docs.")

    if len(matches) > 1:
        locs = ", ".join(p.relative_to(repo_root).as_posix() for p, _ in matches)
        raise click.ClickException(
            f"Criterion '{criterion_id}' found in multiple files: {locs}. Use --file to disambiguate."
        )

    path, criterion = matches[0]

    while True:
        # Re-fetch for up-to-date line numbers after each potential edit.
        refreshed = find_criterion_by_id(path, criterion_id, id_prefixes=id_prefixes)
        if refreshed:
            criterion = refreshed

        print_criterion_panel(path, criterion, repo_root, id_prefixes=id_prefixes)

        status_labels = [label for label, _ in STATUS_ORDER]
        status_options = [style_status_label(label) for label, _ in STATUS_ORDER]
        current_status = str(criterion.get("status") or "")
        try:
            current_status_idx = status_labels.index(current_status)
        except ValueError:
            current_status_idx = None

        STATUS_HIGHLIGHT_BG = "\x1b[48;5;220m"   # amber
        if current_status in ("\u2705 Done", "\U0001f3ae VR-Verified"):
            STATUS_HIGHLIGHT_BG = "\x1b[48;5;28m"   # dark green
        elif current_status == "\U0001f4a1 Proposed":
            STATUS_HIGHLIGHT_BG = "\x1b[48;5;27m"   # bright blue
        elif current_status in ("\u26d4 Blocked", "\U0001f5d1\ufe0f Deprecated"):
            STATUS_HIGHLIGHT_BG = "\x1b[48;5;238m"  # dark gray

        status_choice = select_from_menu(
            f"Set status for {criterion['id']}",
            status_options,
            show_page_indicator=False,
            allow_paging_nav=False,
            selected_option_index=current_status_idx,
            selected_option_bg=STATUS_HIGHLIGHT_BG,
        )

        if status_choice is None or status_choice == "back":
            return 0

        new_status = status_labels[int(status_choice)]

        blocked_reason = None
        if "Blocked" in new_status:
            blocked_reason = prompt_for_blocked_reason()
        deprecated_reason = None
        if "Deprecated" in new_status:
            deprecated_reason = prompt_for_deprecated_reason()

        changed = update_criterion_status(
            path, criterion, new_status,
            blocked_reason=blocked_reason, deprecated_reason=deprecated_reason,
        )
        process_file(path, check_only=False)

        if changed:
            click.echo(f"Updated {criterion['id']} -> {new_status}")
        else:
            click.echo(f"No change for {criterion['id']} ({new_status})")

        _, table_rows = collect_summary_rows(repo_root, domain_files, check_only=True)
        print_summary_table(table_rows, emoji_columns=emoji_columns)
        return 0


def apply_status_change_by_id(
    repo_root: Path,
    domain_files: list[Path],
    criterion_id: str,
    new_status_input: str,
    file_filter: str | None,
    blocked_reason: str | None = None,
    deprecated_reason: str | None = None,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> bool:
    target_paths: list[Path]
    if file_filter:
        candidate = (repo_root / file_filter).resolve()
        if not candidate.exists() or not candidate.is_file():
            raise click.ClickException(f"--file path not found: {file_filter}")
        target_paths = [candidate]
    else:
        target_paths = domain_files

    matches: list[tuple[Path, dict[str, object]]] = []
    for path in target_paths:
        criterion = find_criterion_by_id(path, criterion_id, id_prefixes=id_prefixes)
        if criterion:
            matches.append((path, criterion))

    if not matches:
        if file_filter:
            raise click.ClickException(
                f"Requirement '{criterion_id}' not found in {file_filter}."
            )
        raise click.ClickException(f"Requirement '{criterion_id}' not found in the configured docs.")

    if len(matches) > 1 and not file_filter:
        locations = ", ".join(path.relative_to(repo_root).as_posix() for path, _ in matches)
        raise click.ClickException(
            f"Criterion '{criterion_id}' matched multiple files: {locations}. Use --file to disambiguate."
        )

    path, criterion = matches[0]
    new_status = normalize_status_input(new_status_input)
    changed = update_criterion_status(
        path,
        criterion,
        new_status,
        blocked_reason=blocked_reason,
        deprecated_reason=deprecated_reason,
    )
    process_file(path, check_only=False)

    if changed:
        click.echo(f"Updated {criterion['id']} in {path.relative_to(repo_root).as_posix()} -> {new_status}")
    else:
        click.echo(f"No change for {criterion['id']} in {path.relative_to(repo_root).as_posix()} ({new_status})")
    return changed


def parse_set_entry(entry: str) -> tuple[str, str]:
    raw = entry.strip()
    if "=" not in raw:
        raise click.ClickException(
            f"Invalid --set value '{entry}'. Expected format ID=STATUS."
        )

    criterion_id, status = raw.split("=", 1)
    criterion_id = criterion_id.strip()
    status = status.strip()
    if not criterion_id or not status:
        raise click.ClickException(
            f"Invalid --set value '{entry}'. Expected format ID=STATUS."
        )

    return criterion_id, status


def parse_batch_update_file(repo_root: Path, file_path_input: str) -> list[dict[str, str | None]]:
    path = Path(file_path_input)
    if not path.is_absolute():
        path = (repo_root / file_path_input).resolve()

    if not path.exists() or not path.is_file():
        raise click.ClickException(f"--set-file path not found: {file_path_input}")

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return parse_batch_update_jsonl(path)
    if suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        return parse_batch_update_csv(path, delimiter=delimiter)

    raise click.ClickException("--set-file must end with .jsonl, .csv, or .tsv")


def parse_batch_update_jsonl(path: Path) -> list[dict[str, str | None]]:
    updates: list[dict[str, str | None]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue

            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                raise click.ClickException(
                    f"Invalid JSONL at {path}:{line_number}: {exc.msg}"
                ) from exc

            if not isinstance(record, dict):
                raise click.ClickException(
                    f"Invalid JSONL object at {path}:{line_number}: expected object"
                )

            criterion_id = str(
                record.get("criterion_id")
                or record.get("requirement_id")
                or record.get("id")
                or record.get("ac_id")
                or record.get("r_id")
                or ""
            ).strip()
            status = str(record.get("status") or "").strip()
            if not criterion_id or not status:
                raise click.ClickException(
                    f"Invalid JSONL row at {path}:{line_number}: requires criterion_id/requirement_id/id/ac_id/r_id and status"
                )

            file_filter = str(record.get("file") or "").strip() or None
            blocked_reason = str(record.get("blocked_reason") or "").strip() or None
            deprecated_reason = str(record.get("deprecated_reason") or "").strip() or None

            updates.append(
                {
                    "criterion_id": criterion_id,
                    "status": status,
                    "file": file_filter,
                    "blocked_reason": blocked_reason,
                    "deprecated_reason": deprecated_reason,
                }
            )

    if not updates:
        raise click.ClickException(f"--set-file contains no update rows: {path}")

    return updates


def parse_batch_update_csv(path: Path, delimiter: str = ",") -> list[dict[str, str | None]]:
    updates: list[dict[str, str | None]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise click.ClickException(f"Invalid CSV/TSV at {path}: missing header row")

        for line_number, row in enumerate(reader, start=2):
            criterion_id = str(
                row.get("criterion_id")
                or row.get("requirement_id")
                or row.get("id")
                or row.get("ac_id")
                or row.get("r_id")
                or ""
            ).strip()
            status = str(row.get("status") or "").strip()
            if not criterion_id or not status:
                raise click.ClickException(
                    f"Invalid CSV/TSV row at {path}:{line_number}: requires criterion_id/requirement_id/id/ac_id/r_id and status columns"
                )

            file_filter = str(row.get("file") or "").strip() or None
            blocked_reason = str(row.get("blocked_reason") or "").strip() or None
            deprecated_reason = str(row.get("deprecated_reason") or "").strip() or None

            updates.append(
                {
                    "criterion_id": criterion_id,
                    "status": status,
                    "file": file_filter,
                    "blocked_reason": blocked_reason,
                    "deprecated_reason": deprecated_reason,
                }
            )

    if not updates:
        raise click.ClickException(f"--set-file contains no update rows: {path}")

    return updates


def collect_summary_rows(
    repo_root: Path,
    domain_files: list[Path],
    check_only: bool,
) -> tuple[list[Path], list[list[object]]]:
    changed_paths: list[Path] = []
    table_rows: list[list[object]] = []

    for path in domain_files:
        changed, counts = process_file(path, check_only=check_only)
        if changed:
            changed_paths.append(path)

        marker = "🆙" if changed else "✓"
        row = [f"{marker} {display_name_from_h1(path)}"] + [counts[label] for label, _ in STATUS_ORDER]
        table_rows.append(row)

    return changed_paths, table_rows


def print_summary_table(table_rows: list[list[object]], emoji_columns: bool) -> None:
    if emoji_columns:
        headers = ["File"] + [label.split()[0] for label, _ in STATUS_ORDER] + ["⏳ VR"]
    else:
        headers = ["File"] + STATUS_TERSE_HEADERS_ASCII

    styled_rows: list[list[object]] = []
    for row in table_rows:
        # row format: ["marker filename", <status counts in STATUS_ORDER sequence>]
        styled_counts = [
            style_status_count(label, row[index + 1])
            for index, (label, _) in enumerate(STATUS_ORDER)
        ]
        wait_vr = str((row[2] if isinstance(row[2], int) else int(row[2])) + (row[3] if isinstance(row[3], int) else int(row[3])))
        styled_wait_vr = click.style(wait_vr, fg="cyan")
        styled_rows.append([row[0], *styled_counts, styled_wait_vr])

    click.echo(tabulate(styled_rows, headers=headers, tablefmt="simple"))


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help=__doc__,
)
@click.argument(
    "criterion_id",
    required=False,
    default=None,
    metavar="[ID]",
)
@click.option("--check", is_flag=True, help="Check whether summaries are up to date without writing changes.")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose output with full words.")
@click.option(
    "--emoji-columns",
    is_flag=True,
    help="Use emoji column headers in terse table output (may misalign in some terminals).",
)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Open interactive file/criterion/status flow after summary table.",
)
@click.option(
    "-u",
    "--unsorted",
    is_flag=True,
    help="Keep Select file menu in filesystem order (disable default priority sorting).",
)
@click.option(
    "--set-criterion-id",
    type=str,
    help="Non-interactive mode: requirement id to update, for example R-TELEMETRY-LOG-001.",
)
@click.option(
    "--set-status",
    "set_status",
    type=str,
    help="Non-interactive mode: target status (label, plain text, or slug, e.g. 'Implemented' or 'desktop-verified').",
)
@click.option(
    "--set",
    "set_updates",
    multiple=True,
    type=str,
    help="Non-interactive bulk mode: repeat ID=STATUS (for example --set R-FOO-001=implemented).",
)
@click.option(
    "--set-file",
    "set_file_input",
    type=str,
    help="Non-interactive batch mode: path to .jsonl/.csv/.tsv with rows containing criterion_id/requirement_id/id/ac_id/r_id and status.",
)
@click.option(
    "--file",
    "set_file",
    type=str,
    help="Optional file scope for non-interactive updates, repo-relative path such as docs/requirements/telemetry.md.",
)
@click.option(
    "--set-blocked-reason",
    type=str,
    help="Optional reason text when setting status to Blocked in non-interactive mode.",
)
@click.option(
    "--set-deprecated-reason",
    type=str,
    help="Optional reason text when setting status to Deprecated in non-interactive mode.",
)
@click.option(
    "--filter-status",
    type=str,
    help="Filter by status: walks matching requirements interactively (default) or shows tree with --tree.",
)
@click.option(
    "--tree",
    is_flag=True,
    help="With --filter-status: print a tree view only and exit instead of opening the interactive walk.",
)
@click.option(
    "--summary-table/--no-summary-table",
    default=True,
    help="Print the summary table output (disable in automation with --no-summary-table).",
)
@click.option(
    "--repo-root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Project root containing requirement documentation.",
)
@click.option(
    "--criteria-dir",
    type=str,
    default="docs/requirements",
    show_default=True,
    help="Directory (absolute or relative to --repo-root) containing requirement markdown files.",
)
@click.option(
    "--id-prefix",
    "id_prefixes",
    multiple=True,
    default=DEFAULT_ID_PREFIXES,
    show_default=True,
    help="Allowed header ID prefixes. Repeat or comma-separate values, for example --id-prefix R or --id-prefix AC,R.",
)
def main(
    check: bool,
    verbose: bool,
    emoji_columns: bool,
    interactive: bool,
    unsorted: bool,
    set_criterion_id: str | None,
    set_status: str | None,
    set_updates: tuple[str, ...],
    set_file_input: str | None,
    set_file: str | None,
    set_blocked_reason: str | None,
    set_deprecated_reason: str | None,
    filter_status: str | None,
    tree: bool,
    summary_table: bool,
    repo_root: Path,
    criteria_dir: str,
    id_prefixes: tuple[str, ...],
    criterion_id: str | None,
) -> None:

    try:
        id_prefixes = normalize_id_prefixes(id_prefixes)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    repo_root = repo_root.resolve()
    domain_files = iter_domain_files(repo_root, criteria_dir)
    if not domain_files:
        print(f"No requirement markdown files found under: {criteria_dir}", file=sys.stderr)
        raise SystemExit(1)

    # Positional ID lookup: find the requirement, show panel + status menu, done.
    if criterion_id:
        if check or filter_status or set_criterion_id or set_status or set_updates or set_file_input or set_file or tree:
            raise click.ClickException(
                "Positional ID cannot be combined with --check, --filter-status, --tree, or --set-* options."
            )
        raise SystemExit(
            lookup_criterion_interactive(
                repo_root,
                domain_files,
                criterion_id=criterion_id,
                emoji_columns=emoji_columns,
                id_prefixes=id_prefixes,
            )
        )

    changed_paths, table_rows = collect_summary_rows(repo_root, domain_files, check_only=check)

    if summary_table and verbose:
        for row, path in zip(table_rows, domain_files):
            marker = "UPDATE" if path in changed_paths else "OK"
            parts = [
                f"{style_status_count(label, row[index + 1])} {label}"
                for index, (label, _) in enumerate(STATUS_ORDER)
            ]
            wait_vr = (row[2] if isinstance(row[2], int) else int(row[2])) + (row[3] if isinstance(row[3], int) else int(row[3]))
            parts.append(f"{click.style(str(wait_vr), fg='cyan')} waiting-VR")
            summary = ", ".join(parts)
            click.echo(f"[{marker}] {path.relative_to(repo_root)} :: {summary}")
    elif summary_table:
        print_summary_table(table_rows, emoji_columns=emoji_columns)

    if check and changed_paths:
        if verbose:
            print(
                f"{len(changed_paths)} requirement file(s) need summary updates.",
                file=sys.stderr,
            )
        else:
            msg = f"{len(changed_paths)} file(s) need updates"
            print(msg, file=sys.stderr)
        raise SystemExit(1)

    # --tree without --filter-status is a no-op guard
    if tree and not filter_status:
        raise click.ClickException("--tree requires --filter-status.")

    # Handle --filter-status mode
    if filter_status:
        if check or set_criterion_id or set_status or set_updates or set_file_input or set_file:
            raise click.ClickException("--filter-status cannot be combined with --check / --set-criterion-id / --set-status / --file.")
        try:
            normalized_status = normalize_status_input(filter_status)
        except click.ClickException:
            raise
        criteria_by_file = collect_criteria_by_status(
            repo_root,
            domain_files,
            normalized_status,
            id_prefixes=id_prefixes,
        )
        if tree or not interactive:
            # Non-interactive: just print the tree and exit.
            print_criteria_tree(repo_root, criteria_by_file, normalized_status)
            raise SystemExit(0)
        # Interactive: walk through matching requirements one by one.
        raise SystemExit(
            filtered_interactive_loop(
                repo_root,
                domain_files,
                target_status=normalized_status,
                emoji_columns=emoji_columns,
                id_prefixes=id_prefixes,
            )
        )

    non_interactive_requested = bool(set_criterion_id or set_status or set_updates or set_file_input or set_file)
    if non_interactive_requested:
        if check:
            raise click.ClickException("--check cannot be combined with --set-criterion-id/--set-status.")
        mode_count = int(bool(set_updates)) + int(bool(set_file_input)) + int(bool(set_criterion_id or set_status))
        if mode_count > 1:
            raise click.ClickException(
                "Use exactly one non-interactive update mode: --set-file, --set ID=STATUS (repeatable), or --set-criterion-id with --set-status."
            )

        update_requests: list[dict[str, str | None]] = []
        if set_updates:
            update_requests = [
                {
                    "criterion_id": cid,
                    "status": status,
                    "file": set_file,
                    "blocked_reason": None,
                    "deprecated_reason": None,
                }
                for cid, status in (parse_set_entry(entry) for entry in set_updates)
            ]
        elif set_file_input:
            if set_file:
                raise click.ClickException("--file cannot be combined with --set-file because each row may include its own file scope.")
            if set_blocked_reason or set_deprecated_reason:
                raise click.ClickException("--set-blocked-reason/--set-deprecated-reason cannot be combined with --set-file; provide per-row values in the file.")
            update_requests = parse_batch_update_file(repo_root, set_file_input)
        else:
            if set_criterion_id is None or set_status is None:
                raise click.ClickException("Both --set-criterion-id and --set-status are required for non-interactive update mode.")
            update_requests = [
                {
                    "criterion_id": set_criterion_id,
                    "status": set_status,
                    "file": set_file,
                    "blocked_reason": set_blocked_reason,
                    "deprecated_reason": set_deprecated_reason,
                }
            ]

        if (set_blocked_reason or set_deprecated_reason) and len(update_requests) != 1:
            raise click.ClickException("--set-blocked-reason/--set-deprecated-reason currently support single-target updates only.")

        for request in update_requests:
            criterion_id_value = str(request["criterion_id"])
            status_value = str(request["status"])
            row_file_filter = str(request["file"]) if request["file"] is not None else None
            normalized = normalize_status_input(status_value)

            blocked_reason = str(request["blocked_reason"]) if request["blocked_reason"] is not None else None
            deprecated_reason = str(request["deprecated_reason"]) if request["deprecated_reason"] is not None else None
            if "Blocked" not in normalized:
                blocked_reason = None
            if "Deprecated" not in normalized:
                deprecated_reason = None

            apply_status_change_by_id(
                repo_root,
                domain_files,
                criterion_id=criterion_id_value,
                new_status_input=status_value,
                file_filter=row_file_filter,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
                id_prefixes=id_prefixes,
            )

        if summary_table:
            _, table_rows = collect_summary_rows(repo_root, domain_files, check_only=True)
            print_summary_table(table_rows, emoji_columns=emoji_columns)
        raise SystemExit(0)

    if interactive and not check:
        raise SystemExit(
            interactive_update_loop(
                repo_root,
                criteria_dir,
                domain_files,
                emoji_columns=emoji_columns,
                sort_files=not unsorted,
                id_prefixes=id_prefixes,
            )
        )


if __name__ == "__main__":
    main()