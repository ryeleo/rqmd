"""File I/O and markdown utilities for requirements discovery and initialization.

This module provides:
- Project and requirement directory discovery and validation
- Markdown file enumeration and readability checking
- Domain body extraction and H1 title parsing
- Requirements index (README) linking and sync validation
- Starter scaffold generation with template support
- Cross-platform path formatting for user display
"""

from __future__ import annotations

import importlib.resources
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
    """Format a path for user display, relative to repo root if possible.

    Args:
        path: Absolute path to format.
        repo_root: Root path of the project.

    Returns:
        A relative POSIX path if possible, otherwise absolute POSIX path.
    """
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def iter_requirements_search_roots(repo_root: Path, search_start: Path | None = None) -> list[Path]:
    """Iterate from a starting point up to repo root, returning all ancestors.

    Args:
        repo_root: The repository root path.
        search_start: Starting point for the search (defaults to CWD).

    Returns:
        List of paths from search_start up to and including repo_root.
    """
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


def _iter_ancestors_inclusive(start: Path) -> list[Path]:
    """Iterate all ancestor directories of a path, including itself.

    Args:
        start: Starting path.

    Returns:
        List of paths from start upward to the filesystem root.
    """
    current = start.resolve()
    ancestors = [current]
    while current != current.parent:
        current = current.parent
        ancestors.append(current)
    return ancestors


def discover_project_root(search_start: Path | None = None) -> tuple[Path, str]:
    """Discover project root by searching upward from CWD-like start.

    Marker precedence within each directory is:
    1) .rqmd.yml/.rqmd.yaml/.rqmd.json
    2) docs/requirements/
    3) requirements/

    Nearest ancestor with any marker wins.
    """
    start = (search_start or Path.cwd()).resolve()

    for candidate_root in _iter_ancestors_inclusive(start):
        config_markers = [
            ".rqmd.yml",
            ".rqmd.yaml",
            ".rqmd.json",
        ]
        for marker_name in config_markers:
            if (candidate_root / marker_name).is_file():
                return candidate_root, f"marker:{marker_name}"

        docs_requirements = candidate_root / "docs" / "requirements"
        if docs_requirements.is_dir():
            return candidate_root, "marker:docs/requirements"

        requirements = candidate_root / "requirements"
        if requirements.is_dir():
            return candidate_root, "marker:requirements"

    return start, "fallback:cwd"


def auto_detect_requirements_dir(repo_root: Path, search_start: Path | None = None) -> tuple[Path | None, str | None]:
    """Auto-detect the requirements directory via search heuristics.

    Searches for docs/requirements/README.md or requirements/README.md, starting
    from search_start (or CWD) and walking up to repo_root.

    Args:
        repo_root: Root path of the project.
        search_start: Starting point for search (defaults to CWD).

    Returns:
        A tuple of (detected_path, display_hint) or (None, None) if not found.
    """
    search_roots = iter_requirements_search_roots(repo_root, search_start)
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


def resolve_requirements_dir(repo_root: Path, requirements_dir_input: str | None) -> tuple[Path, str | None]:
    """Resolve the requirements directory with auto-detection fallback.

    If requirements_dir_input is provided, use it (after resolving relative paths).
    Otherwise, auto-detect it. Raises an error if neither is available.

    Args:
        repo_root: Root path of the project.
        requirements_dir_input: Explicitly provided requirements directory (optional).

    Returns:
        A tuple of (resolved_path, info_message) where info_message describes
        how the path was determined (auto-detected or explicit).

    Raises:
        click.ClickException: If no requirements directory found.
    """
    if requirements_dir_input:
        criteria_dir = Path(requirements_dir_input)
        if not criteria_dir.is_absolute():
            criteria_dir = (repo_root / criteria_dir).resolve()
        return criteria_dir, None

    detected, detected_display = auto_detect_requirements_dir(repo_root)
    if detected is None:
        raise click.ClickException(
            "No requirement docs found. Tried auto-detecting docs/requirements/README.md and requirements/README.md from the current working path. "
            "Pass --docs-dir to select a different location."
        )
    return detected, f"Auto-selected requirement docs: {detected_display}"


def iter_domain_files(repo_root: Path, requirements_dir_input: str) -> list[Path]:
    """Enumerate all domain markdown files (excluding the requirements index).

    Args:
        repo_root: Root path of the project.
        requirements_dir_input: Path to the requirements directory (absolute or repo-relative).

    Returns:
        Sorted list of Path objects for all domain files.

    Raises:
        click.ClickException: If directory not found or not readable.
    """
    criteria_dir = Path(requirements_dir_input)
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()

    if not criteria_dir.exists():
        raise click.ClickException(
            f"Requirement docs directory not found: {format_path_display(criteria_dir, repo_root)}\n"
            f"  Hint: run 'rqmd --bootstrap' to create a starter scaffold, or pass --docs-dir to select a different location."
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
    """Check that all domain files are writable (required for interactive mode).

    Args:
        domain_files: List of file paths to check.
        repo_root: Root path of the project (for display formatting).

    Raises:
        SystemExit: If any files are not writable.
    """
    not_writable = [f for f in domain_files if not os.access(f, os.W_OK)]
    if not_writable:
        click.echo("Error: interactive mode requires write access to requirement files.", err=True)
        click.echo("The following files are not writable:", err=True)
        for f in not_writable:
            click.echo(f"  {format_path_display(f, repo_root)}", err=True)
        click.echo("  Hint: check file permissions (chmod u+w <file>) or run in non-interactive mode (--no-walk).", err=True)
        raise SystemExit(1)


# ---------------------------------------------------------------------------
# Index sync helpers (RQMD-CORE-013)
# ---------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+\.md)\)")


def parse_index_links(index_path: Path) -> list[str]:
    """Extract all relative markdown links from a requirements index.

    Args:
        index_path: Path to the index (README.md) file.

    Returns:
        List of referenced markdown filenames (without subdirectory components).
    """
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

    Args:
        criteria_dir: Path to the requirements directory.
        index_path: Path to the index (README.md) file.

    Returns:
        A tuple of (stale_links, orphan_files) where stale_links are referenced
        in the index but missing on disk, and orphan_files exist on disk but
        are not referenced in the index.
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
    """Extract and format a display name from the H1 header of a markdown file.

    Removes 'Requirement' or 'Requirements' prefixes if present.

    Args:
        path: Path to the markdown file.

    Returns:
        The H1 title, or the file stem if no H1 header found.
    """
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


def scope_and_body_from_file(
    path: Path,
    id_prefixes: tuple[str, ...] = ("AC", "R", "RQMD"),
) -> tuple[str | None, str | None]:
    """Extract scope value and pre-requirement domain body from a markdown file.

    The scope is the value of the first ``Scope: ...`` line.
    The domain body is the freeform content between the H1/Scope lines
    and the first requirement header (``### ID: Title``), excluding the
    summary block.

    Args:
        path: Path to the markdown domain file.
        id_prefixes: Requirement ID prefixes to detect the first requirement header.

    Returns:
        A tuple of (scope, body) — either may be None if absent.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, None

    header_pattern = re.compile(
        r"^###\s+(?:" + "|".join(re.escape(p) for p in id_prefixes) + r")-[A-Z0-9-]+:\s*",
        re.MULTILINE,
    )

    lines = text.splitlines()
    scope: str | None = None
    first_req_index: int | None = None
    first_subsection_index: int | None = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if scope is None and stripped.startswith("Scope:"):
            scope = stripped[len("Scope:"):].strip().rstrip(".")
        if first_subsection_index is None and line.startswith("## "):
            first_subsection_index = i
        if header_pattern.match(line):
            first_req_index = i
            break

    boundary_index = first_req_index
    if first_subsection_index is not None:
        boundary_index = (
            first_subsection_index
            if boundary_index is None
            else min(boundary_index, first_subsection_index)
        )

    if boundary_index is None or boundary_index == 0:
        return scope, None

    prelude = lines[:boundary_index]
    in_summary = False
    kept: list[str] = []
    for line in prelude:
        stripped = line.strip()
        if stripped == "<!-- acceptance-status-summary:start -->":
            in_summary = True
            continue
        if stripped == "<!-- acceptance-status-summary:end -->":
            in_summary = False
            continue
        if in_summary:
            continue
        if stripped.startswith("# ") or stripped.startswith("Scope:"):
            continue
        kept.append(line)

    body = "\n".join(kept).strip()
    return scope, body if body else None


def _load_init_template(template_name: str) -> str:
    """Load an initialization template from the repository or package.

    Prefers the repo-local template for easy editing during development,
    then falls back to the packaged version.

    Args:
        template_name: Filename of the template (e.g., 'README.md').

    Returns:
        The template content as a string.
    """
    repo_template = Path(__file__).resolve().parents[2] / "init-docs" / template_name
    if repo_template.exists() and repo_template.is_file():
        return repo_template.read_text(encoding="utf-8")

    # Packaged fallback for installed distributions.
    packaged = importlib.resources.files("rqmd").joinpath("init_docs", template_name)
    return packaged.read_text(encoding="utf-8")


def _render_init_template(template_name: str, values: dict[str, str]) -> str:
    """Render an initialization template by variable substitution.

    Replaces {{VAR}} placeholders with corresponding dictionary values.

    Args:
        template_name: Filename of the template to load.
        values: Dictionary mapping variable names to values.

    Returns:
        The rendered template.
    """
    rendered = _load_init_template(template_name)
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def initialize_requirements_scaffold(repo_root: Path, requirements_dir_input: str, starter_prefix: str) -> list[Path]:
    """Initialize a starter requirements scaffold in a project.

    Creates the requirement directory structure and generates starter files
    (README.md index + example domain file) from templates.

    Args:
        repo_root: Root path of the project.
        requirements_dir_input: Path to the requirements directory (absolute or repo-relative).
        starter_prefix: ID prefix to use in the starter domain example (e.g., 'AC').

    Returns:
        List of newly created file paths.
    """
    criteria_dir = Path(requirements_dir_input)
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()

    criteria_dir.mkdir(parents=True, exist_ok=True)

    index_path = criteria_dir / REQUIREMENTS_INDEX_NAME
    starter_domain_path = criteria_dir / "starter.md"
    criteria_dir_display = criteria_dir.relative_to(repo_root).as_posix()
    index_display = index_path.relative_to(repo_root).as_posix()
    starter_display = starter_domain_path.relative_to(repo_root).as_posix()

    created_paths: list[Path] = []

    template_values = {
        "INDEX_DISPLAY": index_display,
        "STARTER_DISPLAY": starter_display,
        "CRITERIA_DIR_DISPLAY": criteria_dir_display,
        "STARTER_PREFIX": starter_prefix,
    }

    if not index_path.exists():
        index_path.write_text(_render_init_template("README.md", template_values), encoding="utf-8")
        created_paths.append(index_path)

    if not starter_domain_path.exists():
        starter_domain_path.write_text(_render_init_template("domain-example.md", template_values), encoding="utf-8")
        process_file(starter_domain_path, check_only=False)
        created_paths.append(starter_domain_path)

    return created_paths
