"""Status update and display utilities for requirements.

This module provides:
- Functions to update requirement status/priority/flagged fields in markdown
- Display/printing of criterion details in formatted panels
- Prompts for collecting blocked/deprecated reasons
- File I/O and change application logic
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from .constants import DEFAULT_ID_PREFIXES, LINK_ITEM_PATTERN, LINKS_HEADER_PATTERN
from .markdown_io import scope_and_body_from_file
from .priority_model import coerce_priority_label
from .req_parser import extract_requirement_block, find_requirement_by_id
from .req_parser import extract_requirement_block, find_requirement_by_id
from .status_model import normalize_status_input
from .summary import process_file


def _rule_style_kwargs(status_label: str) -> dict:
    """Determine Click styling kwargs for a requirement status rule.

    Args:
        status_label: The status label (e.g., '✅ Verified').

    Returns:
        Dictionary of kwargs suitable for click.style().
    """
    if status_label == "✅ Verified":
        return {"fg": "green"}
    if status_label == "💡 Proposed":
        return {"fg": "bright_blue"}
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return {"dim": True}
    return {"fg": "yellow"}


def print_criterion_panel(
    path: Path,
    requirement: dict[str, object],
    repo_root: Path,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> None:
    """Print a formatted panel displaying a single requirement.

    Includes ID, title, source file, full criterion block, and status-colored rule.

    Args:
        path: Path to the domain file.
        requirement: The requirement dictionary.
        repo_root: Root path of the project (for display formatting).
        id_prefixes: Allowed ID prefixes (used for criterion extraction).
    """
    requirement_id = str(requirement["id"])
    title = str(requirement["title"])
    status = str(requirement.get("status") or "")
    criterion_text = extract_requirement_block(path, requirement_id, id_prefixes=id_prefixes)
    term_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    rule = "=" * max(24, min(term_width, 100))
    rule_kwargs = _rule_style_kwargs(status)

    click.echo("")
    click.echo(click.style(rule, **rule_kwargs))
    click.echo(click.style(f"{requirement_id}: {title}", bold=True))
    click.echo(click.style(f"Source: {path.relative_to(repo_root).as_posix()}", dim=True))

    _, domain_body = scope_and_body_from_file(path, id_prefixes=id_prefixes)
    if domain_body:
        domain_lines = [ln for ln in domain_body.splitlines() if ln.strip()]
        max_notes_lines = 3
        truncated = len(domain_lines) > max_notes_lines
        display_lines = domain_lines[:max_notes_lines]
        notes_text = " | ".join(display_lines)
        if truncated:
            notes_text += " …"
        click.echo(click.style(f"Domain notes: {notes_text}", dim=True))

    click.echo(click.style(rule, **rule_kwargs))
    if criterion_text:
        click.echo(criterion_text)
    click.echo(click.style(rule, **rule_kwargs))


def update_criterion_status(
    path: Path,
    requirement: dict[str, object],
    new_status: str,
    blocked_reason: str | None = None,
    deprecated_reason: str | None = None,
    new_priority: str | None = None,
    new_flagged: bool | None = None,
    apply_changes: bool = True,
) -> bool:
    """Update all fields of a requirement in a markdown file.

    Args:
        path: Path to the domain file.
        requirement: The requirement dictionary (must have status_line set).
        new_status: New canonical status value.
        blocked_reason: Optional blocked reason text.
        deprecated_reason: Optional deprecated reason text.
        new_priority: Optional new priority value.
        new_flagged: Optional new flagged boolean state.
        apply_changes: If True, write changes to disk; if False, return success only.

    Returns:
        True if changes were made and applied/validated successfully.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    status_line = requirement["status_line"]
    blocked_reason_line = requirement.get("blocked_reason_line")
    deprecated_reason_line = requirement.get("deprecated_reason_line")
    priority_line = requirement.get("priority_line")
    flagged_line = requirement.get("flagged_line")
    if not isinstance(status_line, int):
        raise ValueError("Invalid requirement status line.")

    new_status_line_text = f"- **Status:** {new_status}"
    status_changed = lines[status_line] != new_status_line_text

    if status_changed:
        lines[status_line] = new_status_line_text

    is_blocked = "Blocked" in new_status
    is_deprecated = "Deprecated" in new_status

    shift = 0

    if isinstance(blocked_reason_line, int):
        adj_blocked = blocked_reason_line + shift
        if is_blocked and blocked_reason:
            new_line = f"**Blocked:** {blocked_reason}"
            if lines[adj_blocked] != new_line:
                lines[adj_blocked] = new_line
                status_changed = True
        elif is_blocked:
            pass
        else:
            lines.pop(adj_blocked)
            shift -= 1
            status_changed = True
    elif is_blocked and blocked_reason:
        insert_at = status_line + 1 + shift
        lines.insert(insert_at, f"**Blocked:** {blocked_reason}")
        shift += 1
        status_changed = True

    if isinstance(deprecated_reason_line, int):
        adj_deprecated = deprecated_reason_line + shift
        if is_deprecated and deprecated_reason:
            new_line = f"**Deprecated:** {deprecated_reason}"
            if lines[adj_deprecated] != new_line:
                lines[adj_deprecated] = new_line
                status_changed = True
        elif is_deprecated:
            pass
        else:
            lines.pop(adj_deprecated)
            status_changed = True
    elif is_deprecated and deprecated_reason:
        insert_at = status_line + 1 + shift
        lines.insert(insert_at, f"**Deprecated:** {deprecated_reason}")
        status_changed = True

    # Handle priority updates
    if new_priority:
        if isinstance(priority_line, int):
            adj_priority = priority_line + shift
            new_priority_line_text = f"- **Priority:** {new_priority}"
            if lines[adj_priority] != new_priority_line_text:
                lines[adj_priority] = new_priority_line_text
                status_changed = True
        else:
            # Insert new priority line after status
            insert_at = status_line + 1 + shift
            new_priority_line_text = f"- **Priority:** {new_priority}"
            lines.insert(insert_at, new_priority_line_text)
            shift += 1
            status_changed = True

    if new_flagged is not None:
        flagged_text = "true" if new_flagged else "false"
        new_flagged_line_text = f"- **Flagged:** {flagged_text}"
        if isinstance(flagged_line, int):
            adj_flagged = flagged_line + shift
            if lines[adj_flagged] != new_flagged_line_text:
                lines[adj_flagged] = new_flagged_line_text
                status_changed = True
        else:
            insert_at = status_line + 1 + shift
            if isinstance(priority_line, int):
                insert_at = max(insert_at, priority_line + 1 + shift)
            lines.insert(insert_at, new_flagged_line_text)
            status_changed = True

    if status_changed and apply_changes:
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    return status_changed


def prompt_for_blocked_reason() -> str:
    click.echo()
    click.echo("Provide a reason for blocking (or press Enter to skip):")
    reason = click.prompt("Reason", default="", show_default=False).strip()
    return reason


def prompt_for_deprecated_reason() -> str:
    click.echo()
    click.echo("Provide a reason for deprecating (or press Enter to skip):")
    reason = click.prompt("Reason", default="", show_default=False).strip()
    return reason


def prompt_for_priority() -> str:
    """Interactive priority selection menu."""
    from .constants import PRIORITY_ORDER
    
    click.echo()
    click.echo("Select a priority:")
    for i, (label, _) in enumerate(PRIORITY_ORDER, 1):
        click.echo(f"  {i}. {label}")
    
    choice = click.prompt("Priority choice (1-4, or press Enter to skip)", default="", show_default=False).strip()
    if not choice:
        return ""
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(PRIORITY_ORDER):
            return PRIORITY_ORDER[idx][0]
    except (ValueError, IndexError):
        pass
    
    click.echo("Invalid choice. Skipping priority update.")
    return ""


def _add_link_to_file(path: Path, requirement: dict, link_text: str) -> None:
    """Append a link item to a requirement's **Links:** section.

    Creates the **Links:** header if it doesn't yet exist.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    links_line = requirement.get("links_line")
    if isinstance(links_line, int):
        # Find the end of the existing link items block
        insert_at = links_line + 1
        while insert_at < len(lines) and LINK_ITEM_PATTERN.match(lines[insert_at]):
            insert_at += 1
        lines.insert(insert_at, f"  - {link_text}")
    else:
        # No **Links:** header yet - insert after the last known metadata line
        candidates = [
            requirement.get("flagged_line"),
            requirement.get("deprecated_reason_line"),
            requirement.get("blocked_reason_line"),
            requirement.get("priority_line"),
            requirement.get("status_line"),
        ]
        insert_after = max((ln for ln in candidates if isinstance(ln, int)), default=None)
        if insert_after is None:
            return
        insert_at = insert_after + 1
        lines.insert(insert_at, f"  - {link_text}")
        lines.insert(insert_at, "- **Links:**")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _remove_link_from_file(path: Path, requirement: dict, link_index: int) -> None:
    """Remove the link item at *link_index* from a requirement's **Links:** section.

    Removes the **Links:** header too when the section becomes empty.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    links_line = requirement.get("links_line")
    if not isinstance(links_line, int):
        return
    item_line_numbers: list[int] = []
    for idx in range(links_line + 1, len(lines)):
        if LINK_ITEM_PATTERN.match(lines[idx]):
            item_line_numbers.append(idx)
        else:
            break
    if link_index >= len(item_line_numbers):
        return
    lines.pop(item_line_numbers[link_index])
    if len(item_line_numbers) == 1:
        # Section is now empty - remove header too
        lines.pop(links_line)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def prompt_for_links_flow(
    path: Path,
    requirement: dict,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> bool:
    """Interactive loop for managing links on a requirement.

    Displays existing links numbered, then lets the user add (by entering a URL
    or ``[label](url)``) or remove (by entering the item number) links.  The
    loop continues until the user presses Enter on an empty line.

    Returns True if any changes were written to disk.
    """
    changed = False
    req = requirement
    while True:
        existing_links: list[dict] = req.get("links") or []  # type: ignore[assignment]
        click.echo()
        if existing_links:
            click.echo("Links:")
            for i, link in enumerate(existing_links, 1):
                label = link.get("label")
                url = str(link.get("url") or "")
                click.echo(f"  {i}. {f'[{label}]({url})' if label else url}")
        else:
            click.echo("No links yet.")
        click.echo("Enter a number to remove, a URL or [label](url) to add,")
        raw = click.prompt("or press Enter to go back", default="", show_default=False).strip()
        if not raw:
            return changed
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(existing_links):
                _remove_link_from_file(path, req, idx)
                changed = True
                refreshed = find_requirement_by_id(path, str(req["id"]), id_prefixes)
                if refreshed:
                    req = refreshed
            else:
                click.echo(f"Invalid number. Enter 1-{len(existing_links)}.")
            continue
        # Add operation
        link_text = raw
        if raw.startswith(("http://", "https://", "ftp://", "/")) and not re.match(
            r"^\[[^\]]+\]\(", raw
        ):
            label = click.prompt(
                "Add a label? (press Enter to skip)", default="", show_default=False
            ).strip()
            if label:
                link_text = f"[{label}]({raw})"
        _add_link_to_file(path, req, link_text)
        changed = True
        refreshed = find_requirement_by_id(path, str(req["id"]), id_prefixes)
        if refreshed:
            req = refreshed

def apply_status_change_by_id(
    repo_root: Path,
    domain_files: list[Path],
    requirement_id: str,
    new_status_input: str | None,
    file_filter: str | None,
    blocked_reason: str | None = None,
    deprecated_reason: str | None = None,
    new_priority_input: str | None = None,
    new_flagged_value: bool | None = None,
    include_status_emojis: bool = True,
    include_priority_summary: bool = False,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    emit_output: bool = True,
    dry_run: bool = False,
) -> bool:
    target_paths: list[Path]
    if file_filter:
        candidate = (repo_root / file_filter).resolve()
        if not candidate.exists() or not candidate.is_file():
            raise click.ClickException(f"--scope-file path not found: {file_filter}")
        target_paths = [candidate]
    else:
        target_paths = domain_files

    matches: list[tuple[Path, dict[str, object]]] = []
    for path in target_paths:
        requirement = find_requirement_by_id(path, requirement_id, id_prefixes=id_prefixes)
        if requirement:
            matches.append((path, requirement))

    if not matches:
        if file_filter:
            raise click.ClickException(
                f"Requirement '{requirement_id}' not found in {file_filter}."
            )
        raise click.ClickException(f"Requirement '{requirement_id}' not found in the configured docs.")

    if len(matches) > 1 and not file_filter:
        locations = ", ".join(path.relative_to(repo_root).as_posix() for path, _ in matches)
        raise click.ClickException(
            f"Requirement '{requirement_id}' matched multiple files: {locations}. Use --scope-file to disambiguate."
        )

    path, requirement = matches[0]

    if new_status_input is None and new_priority_input is None and new_flagged_value is None:
        raise click.ClickException("No update requested. Provide status, priority, and/or flagged.")

    current_status = str(requirement.get("status") or "")
    new_status = current_status
    if new_status_input is not None:
        new_status = normalize_status_input(new_status_input)

    new_priority: str | None = None
    if new_priority_input is not None:
        normalized_priority = coerce_priority_label(new_priority_input)
        if normalized_priority == "unset":
            raise click.ClickException(f"Unrecognized priority input: {new_priority_input}")
        new_priority = normalized_priority

    changed = update_criterion_status(
        path,
        requirement,
        new_status,
        blocked_reason=blocked_reason,
        deprecated_reason=deprecated_reason,
        new_priority=new_priority,
        new_flagged=new_flagged_value,
        apply_changes=not dry_run,
    )
    if not dry_run:
        process_file(
            path,
            check_only=False,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )

    if emit_output:
        updates: list[str] = []
        if new_status_input is not None:
            updates.append(new_status)
        if new_priority is not None:
            updates.append(new_priority)
        if new_flagged_value is not None:
            updates.append(f"flagged={str(new_flagged_value).lower()}")
        update_summary = " | ".join(updates) if updates else "no-op"
        if changed:
            action = "Would update" if dry_run else "Updated"
            click.echo(f"{action} {requirement['id']} in {path.relative_to(repo_root).as_posix()} -> {update_summary}")
        else:
            prefix = "No dry-run change" if dry_run else "No change"
            click.echo(f"{prefix} for {requirement['id']} in {path.relative_to(repo_root).as_posix()} ({update_summary})")
    return changed
