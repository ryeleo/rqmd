"""Summary generation and status counting utilities.

This module provides:
- Status counting and aggregation by file
- Summary block generation and insertion into markdown files
- Status line normalization
- Table generation for verbose output
- Priority counting and aggregation
"""

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

from .constants import (
    PRIORITY_ORDER,
    STATUS_ORDER,
    STATUS_PATTERN,
    STATUS_TERSE_HEADERS_ASCII,
    SUMMARY_END,
    SUMMARY_START,
)
from .status_model import coerce_status_label, style_status_count, suggest_status_labels


class UnknownStatusValueError(ValueError):
    """Raised when a requirement status value is unknown to the configured catalog."""

    def __init__(
        self,
        status_value: str,
        source_path: Path | None,
        line_number: int,
        suggestions: list[str],
    ) -> None:
        self.status_value = status_value
        self.source_path = source_path
        self.line_number = line_number
        self.suggestions = suggestions
        source_display = str(source_path) if source_path is not None else "<unknown file>"
        message = (
            f"Unknown status value '{status_value}' in {source_display}:{line_number}. "
            f"Nearest configured statuses: {', '.join(suggestions)}"
        )
        super().__init__(message)


def _plain_status_label(canonical_status: str) -> str:
    """Extract the plain label portion from a canonical status (removing emoji).

    Args:
        canonical_status: Full status label (e.g., '✅ Verified').

    Returns:
        Plain label text (e.g., 'Verified').
    """
    parts = canonical_status.split(" ", 1)
    return parts[1] if len(parts) > 1 else canonical_status


def build_summary_line(
    counts: dict[str, int],
    verbose: bool = False,
    filename: str = "",
    include_status_emojis: bool = True,
) -> str:
    """Build a summary line or table row from status counts.

    Args:
        counts: Dictionary mapping status labels to counts.
        verbose: If True, return a table row list; if False, return inline summary string.
        filename: Filename (only used when verbose=True).
        include_status_emojis: If True, include emoji in output.

    Returns:
        Either a formatted string (terse mode) or a list (verbose mode).
    """
    if verbose:
        # Build a table row for this file
        row = [filename] + [counts[label] for label, _ in STATUS_ORDER]
        return row

    # Terse mode: show just emojis and counts inline
    parts = [
        f"{counts[label]}{label.split()[0] if include_status_emojis else _plain_status_label(label)}"
        for label, _ in STATUS_ORDER
    ]
    return " ".join(parts)


def build_summary_table(rows: list[list], verbose: bool = False) -> str:
    """Build a tabular summary with headers using tabulate.

    Args:
        rows: List of rows (each a list of values).
        verbose: If True, include headers; if False, return empty string.

    Returns:
        A formatted table string, or empty string if not verbose or no rows.
    """
    if not verbose or not rows:
        return ""

    headers = ["File"] + [label for label, _ in STATUS_ORDER]
    return tabulate(rows, headers=headers, tablefmt="simple")


def build_summary_block(
    counts: dict[str, int],
    include_status_emojis: bool = True,
    priority_counts: dict[str, int] | None = None,
) -> str:
    """Build a markdown HTML comment block with status summary.

    Args:
        counts: Dictionary mapping status labels to counts.
        include_status_emojis: If True, include emoji in output.
        priority_counts: Optional dictionary of priority counts (appends priority summary).

    Returns:
        A multi-line summary block wrapped in <!-- acceptance-status-summary:start/end -->.
    """
    parts = [
        f"{counts[label]}{label.split()[0] if include_status_emojis else _plain_status_label(label)}"
        for label, _ in STATUS_ORDER
    ]
    summary_text = " ".join(parts)
    
    result = [
        SUMMARY_START,
        f"Summary: {summary_text}",
    ]
    
    # Optionally include priority summary
    if priority_counts:
        priority_parts = [
            f"{priority_counts[label]}{label.split()[0]}"
            for label, _ in PRIORITY_ORDER
        ]
        priority_summary = " ".join(priority_parts)
        result.append(f"Priorities: {priority_summary}")
    
    result.append(SUMMARY_END)
    return "\n".join(result)


def normalize_status_lines(text: str, include_status_emojis: bool = True) -> tuple[str, bool]:
    """Normalize all status lines in markdown text to canonical labels.

    Args:
        text: Markdown content to normalize.
        include_status_emojis: If True, preserve emoji; if False, use plain labels.

    Returns:
        A tuple of (updated_text, changed) indicating whether modifications were made.

    """
    changed = False
    def replace_status_line(match: re.Match[str]) -> str:
        nonlocal changed
        raw_status = match.group("status")
        try:
            canonical = coerce_status_label(raw_status)
        except ValueError:
            return match.group(0)

        normalized_status = canonical if include_status_emojis else _plain_status_label(canonical)
        updated_line = f"- **Status:** {normalized_status}"
        if updated_line != match.group(0):
            changed = True
        return updated_line

    updated_text = STATUS_PATTERN.sub(replace_status_line, text)
    return updated_text, changed


def count_statuses(text: str, source_path: Path | None = None) -> dict[str, int]:
    """Count requirements by status in markdown text.

    Args:
        text: Markdown content to analyze.

    Returns:
        Dictionary mapping status labels to counts.
    """
    counts = {label: 0 for label, _ in STATUS_ORDER}
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = STATUS_PATTERN.match(line)
        if not match:
            continue

        raw_status = match.group("status")
        try:
            status = coerce_status_label(raw_status)
        except ValueError as exc:
            suggestions = suggest_status_labels(raw_status)
            raise UnknownStatusValueError(
                status_value=raw_status,
                source_path=source_path,
                line_number=line_number,
                suggestions=suggestions,
            ) from exc
        counts[status] += 1
    return counts


def count_priorities(text: str) -> dict[str, int]:
    """Count requirements by priority level in markdown text.

    Args:
        text: Markdown content to analyze.

    Returns:
        Dictionary mapping priority labels to counts.
    """
    from .constants import PRIORITY_PATTERN
    from .priority_model import coerce_priority_label
    
    counts = {label: 0 for label, _ in PRIORITY_ORDER}
    for match in PRIORITY_PATTERN.finditer(text):
        raw_priority = match.group("priority")
        try:
            priority = coerce_priority_label(raw_priority)
            if priority != "unset" and priority in counts:
                counts[priority] += 1
        except (ValueError, KeyError):
            pass
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


def process_file(
    path: Path,
    check_only: bool,
    verbose: bool = False,
    include_status_emojis: bool = True,
    include_priority_summary: bool = False,
) -> tuple[bool, dict[str, int]]:
    original = path.read_text(encoding="utf-8")
    normalized, _ = normalize_status_lines(original, include_status_emojis=include_status_emojis)
    counts = count_statuses(normalized, source_path=path)
    priority_counts = count_priorities(normalized) if include_priority_summary else None
    updated = insert_or_replace_summary(
        normalized,
        build_summary_block(
            counts,
            include_status_emojis=include_status_emojis,
            priority_counts=priority_counts,
        ),
    )

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
    include_status_emojis: bool = True,
    include_priority_summary: bool = False,
) -> tuple[list[Path], list[list[object]]]:
    changed_paths: list[Path] = []
    table_rows: list[list[object]] = []

    for path in domain_files:
        changed, counts = process_file(
            path,
            check_only=check_only,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )
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
        if len(STATUS_TERSE_HEADERS_ASCII) == len(STATUS_ORDER):
            headers = ["File"] + STATUS_TERSE_HEADERS_ASCII
        else:
            headers = ["File"] + [label.split(" ", 1)[-1] for label, _ in STATUS_ORDER]

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