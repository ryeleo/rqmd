from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

try:
    from tabulate import tabulate
except ImportError:
    print("Error: 'tabulate' package is required.", file=sys.stderr)
    print("Install with: pip3 install tabulate", file=sys.stderr)
    sys.exit(1)

from .constants import (STATUS_ORDER, STATUS_PATTERN,
                        STATUS_TERSE_HEADERS_ASCII, SUMMARY_END, SUMMARY_START)
from .status_model import coerce_status_label, style_status_count


def build_summary_line(counts: dict[str, int], verbose: bool = False, filename: str = "") -> str:
    if verbose:
        # Build a table row for this file
        row = [filename] + [counts[label] for label, _ in STATUS_ORDER]
        return row

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
    # Build simple inline summary for HTML comments in markdown.
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


def collect_summary_rows(
    domain_files: list[Path],
    check_only: bool,
    display_name_fn: Callable[[Path], str],
) -> tuple[list[Path], list[list[object]]]:
    changed_paths: list[Path] = []
    table_rows: list[list[object]] = []

    for path in domain_files:
        changed, counts = process_file(path, check_only=check_only)
        if changed:
            changed_paths.append(path)

        marker = "🆙" if changed else "✓"
        row = [f"{marker} {display_name_fn(path)}"] + [counts[label] for label, _ in STATUS_ORDER]
        table_rows.append(row)

    return changed_paths, table_rows


def print_summary_table(table_rows: list[list[object]], emoji_columns: bool) -> None:
    if emoji_columns:
        headers = ["File"] + [label.split()[0] for label, _ in STATUS_ORDER]
    else:
        headers = ["File"] + STATUS_TERSE_HEADERS_ASCII

    styled_rows: list[list[object]] = []
    for row in table_rows:
        # row format: ["marker filename", <status counts in STATUS_ORDER sequence>]
        styled_counts = [
            style_status_count(label, row[index + 1])
            for index, (label, _) in enumerate(STATUS_ORDER)
        ]
        styled_rows.append([row[0], *styled_counts])

    click.echo(tabulate(styled_rows, headers=headers, tablefmt="simple"))


def build_global_rollup_row(totals: dict[str, int]) -> list[object]:
    return ["All files"] + [totals[label] for label, _ in STATUS_ORDER]


def print_global_rollup_table(totals: dict[str, int], emoji_columns: bool) -> None:
    print_summary_table([build_global_rollup_row(totals)], emoji_columns=emoji_columns)


def print_custom_rollup_table(columns: list[tuple[str, int]]) -> None:
    headers = ["File"] + [label for label, _ in columns]
    row: list[object] = ["All files"] + [value for _label, value in columns]
    click.echo(tabulate([row], headers=headers, tablefmt="simple"))