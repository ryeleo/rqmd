from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from .constants import REQUIREMENTS_INDEX_NAME
from .summary import process_file


def format_path_display(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def iter_criteria_search_roots(repo_root: Path, search_start: Path | None = None) -> list[Path]:
    current = (search_start or Path.cwd()).resolve()
    try:
        current.relative_to(repo_root)
    except ValueError:
        return [repo_root]

    roots: list[Path] = []
    while True:
        roots.append(current)
        if current == repo_root:
            break
        current = current.parent
    return roots


def auto_detect_criteria_dir(repo_root: Path, search_start: Path | None = None) -> tuple[Path | None, str | None]:
    search_roots = iter_criteria_search_roots(repo_root, search_start)
    candidate_specs = (
        ("docs/requirements/README.md", "docs/requirements"),
        ("requirements/README.md", "requirements"),
    )

    for root in search_roots:
        for relative_path, derived_dir in candidate_specs:
            candidate = (root / relative_path).resolve()
            derived = (root / derived_dir).resolve()
            if candidate.is_file() and derived.is_dir() and any(path.name != REQUIREMENTS_INDEX_NAME for path in derived.glob("*.md")):
                return derived, format_path_display(candidate, repo_root)

    return None, None


def resolve_criteria_dir(repo_root: Path, criteria_dir_input: str | None) -> tuple[Path, str | None]:
    if criteria_dir_input:
        criteria_dir = Path(criteria_dir_input)
        if not criteria_dir.is_absolute():
            criteria_dir = (repo_root / criteria_dir).resolve()
        return criteria_dir, None

    detected, detected_display = auto_detect_criteria_dir(repo_root)
    if detected is None:
        raise click.ClickException(
            "No requirement docs found. Tried auto-detecting docs/requirements/README.md and requirements/README.md from the current working path. "
            "Pass --requirements-dir to select a different location."
        )
    return detected, f"Auto-selected requirement docs: {detected_display}"


def iter_domain_files(repo_root: Path, criteria_dir_input: str) -> list[Path]:
    criteria_dir = Path(criteria_dir_input)
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()

    if not criteria_dir.exists():
        raise click.ClickException(
            f"Requirement docs directory not found: {format_path_display(criteria_dir, repo_root)}\n"
            f"  Hint: run 'rqmd --init' to create a starter scaffold, or pass --requirements-dir to select a different location."
        )

    try:
        return sorted(path for path in criteria_dir.glob("*.md") if path.name != REQUIREMENTS_INDEX_NAME)
    except PermissionError:
        raise click.ClickException(
            f"Permission denied reading requirement docs directory: {format_path_display(criteria_dir, repo_root)}\n"
            f"  Hint: check permissions with: ls -la \"{criteria_dir.parent}\""
        )


def validate_files_readable(domain_files: list[Path], repo_root: Path) -> None:
    """Raise ClickException listing any domain files that cannot be read, distinguishing not-found from permission-denied."""
    not_found: list[Path] = []
    denied: list[Path] = []
    for f in domain_files:
        if not f.exists():
            not_found.append(f)
        elif not os.access(f, os.R_OK):
            denied.append(f)
    if not_found or denied:
        lines = ["Startup validation failed — requirement files are inaccessible:"]
        for f in not_found:
            lines.append(f"  not found:         {format_path_display(f, repo_root)}")
        for f in denied:
            lines.append(f"  permission denied: {format_path_display(f, repo_root)}")
        lines.append("  Hint: verify the files exist and are readable.")
        raise click.ClickException("\n".join(lines))


def check_files_writable(domain_files: list[Path], repo_root: Path) -> None:
    """Exit with a per-file report if any domain file is not writable. Called before interactive mode."""
    not_writable = [f for f in domain_files if not os.access(f, os.W_OK)]
    if not_writable:
        click.echo("Error: interactive mode requires write access to requirement files.", err=True)
        click.echo("The following files are not writable:", err=True)
        for f in not_writable:
            click.echo(f"  {format_path_display(f, repo_root)}", err=True)
        click.echo("  Hint: check file permissions (chmod u+w <file>) or run in non-interactive mode (--no-interactive).", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Index sync helpers (RQMD-CORE-013)
# ---------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)\)")


def parse_index_links(index_path: Path) -> list[str]:
    """Return linked .md filenames extracted from relative links in the index (README)."""
    try:
        text = index_path.read_text(encoding="utf-8")
    except OSError:
        return []
    links: list[str] = []
    for _display, href in _MD_LINK_RE.findall(text):
        # Only simple relative filenames — no subdirectory components or ../
        if "/" not in href and not href.startswith(".."):
            links.append(href)
    return links


def check_index_sync(criteria_dir: Path, index_path: Path) -> tuple[list[str], list[Path]]:
    """Compare the requirements index against actual domain files.

    Returns:
        stale_links:  filenames referenced in the index that no longer exist on disk.
        orphan_files: domain files present on disk but not referenced in the index.
    """
    linked_names = parse_index_links(index_path)

    stale_links = [name for name in linked_names if not (criteria_dir / name).exists()]

    try:
        domain_names = {
            p.name
            for p in criteria_dir.glob("*.md")
            if p.name != REQUIREMENTS_INDEX_NAME
        }
    except PermissionError:
        domain_names = set()

    referenced = set(linked_names)
    orphan_files = sorted(criteria_dir / name for name in domain_names - referenced)

    return stale_links, orphan_files


def display_name_from_h1(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return path.stem

    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            shortened = title.replace("Requirement", "").strip()
            shortened = shortened.replace("Requirements", "").strip()
            if shortened:
                return shortened
            if title:
                return title
            break

    return path.stem


def initialize_requirements_scaffold(repo_root: Path, criteria_dir_input: str, starter_prefix: str) -> list[Path]:
    criteria_dir = Path(criteria_dir_input)
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()

    criteria_dir.mkdir(parents=True, exist_ok=True)

    index_path = criteria_dir / REQUIREMENTS_INDEX_NAME
    starter_domain_path = criteria_dir / "starter.md"
    criteria_dir_display = criteria_dir.relative_to(repo_root).as_posix()
    index_display = index_path.relative_to(repo_root).as_posix()
    starter_display = starter_domain_path.relative_to(repo_root).as_posix()

    created_paths: list[Path] = []

    if not index_path.exists():
        index_path.write_text(
            f"""# Requirements

This document is the source-of-truth index for rqmd requirements.

## How To Use

- Keep requirement IDs stable and unique.
- Keep one status line directly below each requirement heading.
- Use Given/When/Then when a requirement needs explicit acceptance detail.
- Simple one-line requirements with only a title and status are also valid.
- Keep this index at {index_display}.
- Keep domain docs under {criteria_dir_display}/.

Status workflow:
- 💡 Proposed -> 🔧 Implemented -> ✅ Verified
- Use ⛔ Blocked or 🗑️ Deprecated when needed.

## Domain Documents

### Starter
- [Starter]({starter_display}) - bootstrap requirement for first-run setup
""",
            encoding="utf-8",
        )
        created_paths.append(index_path)

    if not starter_domain_path.exists():
        starter_domain_path.write_text(
            f"""# Starter Requirements

Scope: starter bootstrap content.

### {starter_prefix}-HELLO-001: Replace this starter requirement
- **Status:** 💡 Proposed
- Given a newly initialized requirements catalog
- When teams adopt this tool in their project
- Then this requirement serves as an easy-to-delete handoff placeholder.
""",
            encoding="utf-8",
        )
        process_file(starter_domain_path, check_only=False)
        created_paths.append(starter_domain_path)

    return created_paths
