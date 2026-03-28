"""Requirements parsing and manipulation utilities.

This module provides:
- Parsing markdown requirements from domain files
- Extraction of requirement properties (status, priority, blocked reason, etc.)
- Lookup and filtering of requirements by ID, status, priority, sub-domain, etc.
- H2 subsection tracking and aggregation
- Criterion block extraction with line number tracking
- ID prefix detection and normalization
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .constants import (BLOCKED_REASON_PATTERN, DEFAULT_ID_PREFIXES,
                        DEPRECATED_REASON_PATTERN, FLAGGED_PATTERN,
                        GENERIC_REQUIREMENT_HEADER_PATTERN,
                        H2_SUBSECTION_PATTERN, ID_PREFIX_PATTERN,
                        LINK_ITEM_PATTERN, LINKS_HEADER_PATTERN,
                        MARKDOWN_LINK_PATTERN, PRIORITY_PATTERN,
                        REQUIREMENTS_INDEX_NAME, STATUS_PATTERN)
from .priority_model import coerce_priority_label
from .status_model import coerce_status_label


@lru_cache(maxsize=None)
@lru_cache(maxsize=None)
def build_requirement_header_pattern(id_prefixes: tuple[str, ...]) -> re.Pattern[str]:
    """Build a compiled regex pattern for matching requirement headers.

    Args:
        id_prefixes: Tuple of allowed ID prefixes (e.g., ('AC', 'R', 'RQMD')).

    Returns:
        A compiled regex pattern that matches lines like '### AC-001: Title'.
    """
    alternation = "|".join(re.escape(prefix) for prefix in id_prefixes)
    return re.compile(
        rf"^###\s+(?P<id>(?:{alternation})-[A-Z0-9-]+):\s*(?P<title>.+?)\s*$"
    )


def normalize_id_prefixes(raw_prefixes: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    """Normalize and validate requirement ID prefixes.

    Ensures all prefixes are uppercase, alphanumeric, and unique.

    Args:
        raw_prefixes: Raw prefix input (comma-separated string or list).

    Returns:
        Normalized tuple of validated prefixes.

    Raises:
        ValueError: If no valid prefixes provided or invalid format detected.
    """
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


def _parse_link_item(link_text: str) -> dict[str, str | None] | None:
    """Parse a single link item from a markdown list.

    Handles both:
    - Plain URLs: 'https://github.com/issue/123'
    - Markdown hyperlinks: '[GitHub Issue](https://github.com/issue/123)'

    Args:
        link_text: The text of a link list item (after "- ").

    Returns:
        A dict with keys 'url' (required) and 'label' (optional, None for plain URLs).
        Returns None if parsing fails.
    """
    link_text = link_text.strip()
    if not link_text:
        return None

    # Try markdown link format: [label](url)
    md_match = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", link_text)
    if md_match:
        label = md_match.group(1).strip()
        url = md_match.group(2).strip()
        if url:
            return {"url": url, "label": label if label else None}

    # Otherwise treat as plain URL
    if link_text.startswith(("http://", "https://", "ftp://", "/")):
        return {"url": link_text, "label": None}

    # Unknown format; skip
    return None


def detect_id_prefixes_from_requirements_index(repo_root: Path, requirements_dir_input: str) -> tuple[str, ...]:
    """Auto-detect requirement ID prefixes by scanning the index and linked documents.

    Reads the requirements index (README.md) and scans referenced markdown files
    for actual requirement headers to infer real-world ID prefixes.

    Args:
        repo_root: Root path of the project.
        requirements_dir_input: Path to the requirements directory.

    Returns:
        Tuple of detected ID prefixes, or empty tuple if none found.
    """
    criteria_dir = Path(requirements_dir_input)
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()

    index_path = criteria_dir / REQUIREMENTS_INDEX_NAME
    if not index_path.exists() or not index_path.is_file():
        return ()

    discovered: list[str] = []
    seen: set[str] = set()

    def add_prefix(prefix: str) -> None:
        normalized = prefix.strip().upper().rstrip("-")
        if not normalized:
            return
        if not ID_PREFIX_PATTERN.fullmatch(normalized):
            return
        if normalized in seen:
            return
        seen.add(normalized)
        discovered.append(normalized)

    def scan_markdown_for_prefixes(text: str) -> None:
        for line in text.splitlines():
            match = GENERIC_REQUIREMENT_HEADER_PATTERN.match(line)
            if match:
                add_prefix(match.group("prefix"))

    try:
        index_text = index_path.read_text(encoding="utf-8")
    except OSError:
        return ()

    scan_markdown_for_prefixes(index_text)

    # Read linked markdown docs from the index to infer real-world prefixes.
    for match in MARKDOWN_LINK_PATTERN.finditer(index_text):
        target = match.group("target").strip()
        if not target:
            continue

        raw_path = Path(target)
        candidates = []
        if raw_path.is_absolute():
            candidates.append(raw_path)
        else:
            candidates.append((index_path.parent / raw_path).resolve())
            candidates.append((repo_root / raw_path).resolve())

        selected: Path | None = next((candidate for candidate in candidates if candidate.exists() and candidate.is_file()), None)
        if not selected:
            continue

        try:
            scan_markdown_for_prefixes(selected.read_text(encoding="utf-8"))
        except OSError:
            continue

    return tuple(discovered)


def resolve_id_prefixes(
    repo_root: Path,
    requirements_dir_input: str,
    raw_prefixes: tuple[str, ...] | list[str] | None,
) -> tuple[str, ...]:
    """Resolve requirement ID prefixes with fallback strategy.

    Priority:
    1. Use explicitly provided prefixes (if valid)
    2. Auto-detect from index and linked documents
    3. Fall back to defaults (AC, R, RQMD)

    Args:
        repo_root: Root path of the project.
        requirements_dir_input: Path to the requirements directory.
        raw_prefixes: Explicitly provided prefixes (optional).

    Returns:
        Resolved tuple of ID prefixes.
    """
    if raw_prefixes:
        return normalize_id_prefixes(raw_prefixes)

    detected = detect_id_prefixes_from_requirements_index(repo_root, requirements_dir_input)
    if detected:
        return detected

    return DEFAULT_ID_PREFIXES


def normalize_sub_domain_name(value: object | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split()).casefold()


def display_sub_domain_name(value: object | None) -> str | None:
    normalized = " ".join(str(value).split()) if value is not None else ""
    return normalized or None


def collect_sub_sections(
    path: Path,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> list[dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header_pattern = build_requirement_header_pattern(id_prefixes)

    ordered: list[str] = []
    sections: dict[str, dict[str, object]] = {}

    # First pass: discover subsection boundaries in file order.
    subsection_starts: list[tuple[int, str, str]] = []
    for index, line in enumerate(lines):
        match = H2_SUBSECTION_PATTERN.match(line)
        if not match:
            continue
        name = display_sub_domain_name(match.group("section_title"))
        if name is None:
            continue
        key = normalize_sub_domain_name(name)
        subsection_starts.append((index, key, name))
        if key not in sections:
            ordered.append(key)
            sections[key] = {"name": name, "count": 0}

    # Second pass: count requirements by active subsection.
    current_key: str | None = None
    for line in lines:
        subsection_match = H2_SUBSECTION_PATTERN.match(line)
        if subsection_match:
            name = display_sub_domain_name(subsection_match.group("section_title"))
            current_key = normalize_sub_domain_name(name) if name else None
            continue
        if current_key and header_pattern.match(line):
            sections[current_key]["count"] = int(sections[current_key]["count"]) + 1

    # Third pass: capture optional subsection body (text between H2 and first H3 in that section).
    for idx, (_start, key, _name) in enumerate(subsection_starts):
        start_line = subsection_starts[idx][0]
        next_start = subsection_starts[idx + 1][0] if idx + 1 < len(subsection_starts) else len(lines)

        body_lines: list[str] = []
        for line in lines[start_line + 1:next_start]:
            if header_pattern.match(line):
                break
            body_lines.append(line)

        body = "\n".join(body_lines).strip()
        if body:
            sections[key]["body"] = body

    return [sections[key] for key in ordered]


def parse_requirements(
    path: Path,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> list[dict[str, object]]:
    """Parse all requirements from a markdown domain file.

    Extracts requirement headers (### ID: Title), status lines, and associated metadata
    (priority, blocked reason, deprecated reason, flagged status, sub-domain).

    Args:
        path: Path to the markdown file.
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        List of requirement dictionaries with keys: id, title, status, status_line,
        priority, priority_line, blocked_reason, blocked_reason_line,
        deprecated_reason, deprecated_reason_line, flagged, flagged_line, sub_domain.
        Only requirements with a status_line are included.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    requirements: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_subsection: str | None = None  # Track active H2 subsection
    header_pattern = build_requirement_header_pattern(id_prefixes)

    for index, line in enumerate(lines):
        # Track H2 subsection headers (optional organizational structure)
        subsection_match = H2_SUBSECTION_PATTERN.match(line)
        if subsection_match:
            current_subsection = display_sub_domain_name(subsection_match.group("section_title"))
            continue

        header_match = header_pattern.match(line)
        if header_match:
            current = {
                "id": header_match.group("id"),
                "title": header_match.group("title"),
                "status": None,
                "header_line": index,
                "status_line": None,
                "priority": None,
                "priority_line": None,
                "blocked_reason": None,
                "blocked_reason_line": None,
                "deprecated_reason": None,
                "deprecated_reason_line": None,
                "flagged": None,
                "flagged_line": None,
                "links": None,
                "links_line": None,
                "sub_domain": current_subsection,  # Assign current subsection if present
            }
            requirements.append(current)
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

        priority_match = PRIORITY_PATTERN.match(line)
        if priority_match and current and current["priority"] is None:
            raw_priority = priority_match.group("priority")
            try:
                priority = coerce_priority_label(raw_priority)
            except ValueError:
                priority = raw_priority
            current["priority"] = priority
            current["priority_line"] = index
            continue

        blocked_match = BLOCKED_REASON_PATTERN.match(line)
        if blocked_match and current and current["status_line"] is not None:
            current["blocked_reason"] = blocked_match.group(1).strip()
            current["blocked_reason_line"] = index

        deprecated_match = DEPRECATED_REASON_PATTERN.match(line)
        if deprecated_match and current and current["status_line"] is not None:
            current["deprecated_reason"] = deprecated_match.group(1).strip()
            current["deprecated_reason_line"] = index

        flagged_match = FLAGGED_PATTERN.match(line)
        if flagged_match and current and current["status_line"] is not None:
            current["flagged"] = flagged_match.group("flagged") == "true"
            current["flagged_line"] = index

        links_match = LINKS_HEADER_PATTERN.match(line)
        if links_match and current and current["status_line"] is not None:
            if current["links"] is None:
                current["links_line"] = index
                links_list: list[dict[str, str | None]] = []
                # Collect all following link items (indented with 2 spaces)
                for next_index in range(index + 1, len(lines)):
                    item_match = LINK_ITEM_PATTERN.match(lines[next_index])
                    if not item_match:
                        # Stop at first non-link line
                        break
                    link_text = item_match.group("link_text").strip()
                    parsed = _parse_link_item(link_text)
                    if parsed:
                        links_list.append(parsed)
                if links_list:
                    current["links"] = links_list

    return [requirement for requirement in requirements if requirement["status_line"] is not None]


def find_requirement_by_id(
    path: Path,
    requirement_id: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[str, object] | None:
    """Find a single requirement by ID in a markdown file.

    Args:
        path: Path to the markdown file.
        requirement_id: The requirement ID to search for (case-insensitive).
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        The requirement dictionary if found, None otherwise.
    """
    target = requirement_id.strip().upper()
    for requirement in parse_requirements(path, id_prefixes=id_prefixes):
        if str(requirement["id"]).upper() == target:
            return requirement
    return None


def extract_requirement_block(
    path: Path,
    requirement_id: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> str:
    """Extract the full text block of a single requirement.

    Extracts from the requirement header until the next requirement header
    (or end of file).

    Args:
        path: Path to the markdown file.
        requirement_id: The requirement ID to extract.
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        The requirement text block as a string, or empty string if not found.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    start_index: int | None = None
    target = requirement_id.strip().upper()
    header_pattern = build_requirement_header_pattern(id_prefixes)

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

    return "\n".join(lines[start_index:end_index]).strip()


def extract_requirement_block_with_lines(
    path: Path,
    requirement_id: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> tuple[str, int | None, int | None]:
    """Extract a requirement block and its line range.

    Args:
        path: Path to the markdown file.
        requirement_id: The requirement ID to extract.
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        A tuple of (block_text, start_line_index, end_line_index), or
        ('', None, None) if the requirement is not found.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    start_index: int | None = None
    target = requirement_id.strip().upper()
    header_pattern = build_requirement_header_pattern(id_prefixes)

    for index, line in enumerate(lines):
        match = header_pattern.match(line)
        if match and match.group("id").upper() == target:
            start_index = index
            break

    if start_index is None:
        return "", None, None

    end_index = len(lines)
    for index in range(start_index + 1, len(lines)):
        if header_pattern.match(lines[index]):
            end_index = index
            break

    return "\n".join(lines[start_index:end_index]).strip(), start_index, end_index - 1


def collect_requirements_by_status(
    repo_root: Path,
    domain_files: list[Path],
    target_status: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    """Collect all requirements matching a target status across files.

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain files to scan.
        target_status: Status to match (e.g., '✅ Verified').
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        Dictionary mapping file paths to lists of matching requirements.
    """
    result: dict[Path, list[dict[str, object]]] = {}
    for path in domain_files:
        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        matching = [c for c in requirements if c["status"] == target_status]
        if matching:
            result[path] = matching
    return result


def collect_requirements_by_priority(
    repo_root: Path,
    domain_files: list[Path],
    target_priority: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    """Collect all requirements matching a target priority across files.

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain files to scan.
        target_priority: Priority to match (e.g., '🔴 P0 - Critical').
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        Dictionary mapping file paths to lists of matching requirements.
    """
    result: dict[Path, list[dict[str, object]]] = {}
    for path in domain_files:
        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        matching = [c for c in requirements if c.get("priority") == target_priority]
        if matching:
            result[path] = matching
    return result


def collect_requirements_by_flagged(
    repo_root: Path,
    domain_files: list[Path],
    flagged: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    """Collect all requirements with a matching flagged state across files.

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain files to scan.
        flagged: Boolean value to filter by (True or False).
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        Dictionary mapping file paths to lists of matching requirements.
    """
    result: dict[Path, list[dict[str, object]]] = {}
    for path in domain_files:
        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        if flagged:
            matching = [c for c in requirements if c.get("flagged") is True]
        else:
            # Treat missing flagged metadata as unflagged for inverse filtering.
            matching = [c for c in requirements if c.get("flagged") is not True]
        if matching:
            result[path] = matching
    return result


def collect_requirements_by_sub_domain(
    repo_root: Path,
    domain_files: list[Path],
    target_sub_domain: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    """Collect all requirements in a sub-domain (H2 section) across files.

    Matching is prefix-based: requirements with sub_domain starting with target match.

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain files to scan.
        target_sub_domain: Sub-domain name to match (e.g., 'Accessibility').
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        Dictionary mapping file paths to lists of matching requirements.
    """
    normalized_target = normalize_sub_domain_name(target_sub_domain)
    if not normalized_target:
        return {}

    result: dict[Path, list[dict[str, object]]] = {}
    for path in domain_files:
        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        matching = [
            c
            for c in requirements
            if (sub_domain := normalize_sub_domain_name(c.get("sub_domain")))
            and sub_domain.startswith(normalized_target)
        ]
        if matching:
            result[path] = matching
    return result


def collect_requirements_by_links(
    repo_root: Path,
    domain_files: list[Path],
    has_link: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    """Collect requirements by link presence across files.

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain files to scan.
        has_link: True to include requirements with links; False for no links.
        id_prefixes: Allowed ID prefixes for matching headers.

    Returns:
        Dictionary mapping file paths to lists of matching requirements.
    """
    del repo_root
    result: dict[Path, list[dict[str, object]]] = {}
    for path in domain_files:
        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        if has_link:
            matching = [
                c
                for c in requirements
                if isinstance(c.get("links"), list) and len(c.get("links") or []) > 0
            ]
        else:
            matching = [
                c
                for c in requirements
                if not (isinstance(c.get("links"), list) and len(c.get("links") or []) > 0)
            ]
        if matching:
            result[path] = matching
    return result


# Pattern for bare requirement IDs (PREFIX-SUFFIX) in free text.
_BARE_REQ_ID_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]*-[A-Z0-9][A-Z0-9-]*)\b")
# Pattern for the label of a markdown link: [LABEL](target)
_MD_LINK_LABEL_PATTERN = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def extract_blocking_id(
    blocked_reason: str | None,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> str | None:
    """Extract a linked requirement ID from a blocked reason string.

    Looks first for markdown hyperlinks whose label is a requirement ID,
    then for bare requirement IDs in the text.  The first match is returned.

    Args:
        blocked_reason: The raw blocked reason text, or None.
        id_prefixes: Allowed ID prefixes to match against.

    Returns:
        A requirement ID string (e.g. ``"RQMD-CORE-001"``) or ``None``.
    """
    if not blocked_reason:
        return None

    upper_prefixes = tuple(p.upper() for p in id_prefixes)

    # Try markdown link labels first: [RQMD-CORE-001](some-target)
    for m in _MD_LINK_LABEL_PATTERN.finditer(blocked_reason):
        label = m.group(1).strip()
        bare = _BARE_REQ_ID_PATTERN.match(label)
        if bare:
            candidate = bare.group(1).upper()
            if any(candidate.startswith(f"{pfx}-") for pfx in upper_prefixes):
                return candidate

    # Fall back to bare ID anywhere in the text
    for m in _BARE_REQ_ID_PATTERN.finditer(blocked_reason):
        candidate = m.group(1).upper()
        if any(candidate.startswith(f"{pfx}-") for pfx in upper_prefixes):
            return candidate

    return None


def collect_requirements_by_filters(
    repo_root: Path,
    domain_files: list[Path],
    status_filters: tuple[str, ...] = (),
    priority_filters: tuple[str, ...] = (),
    flagged_filters: tuple[bool, ...] = (),
    link_filters: tuple[bool, ...] = (),
    sub_domain_filters: tuple[str, ...] = (),
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    """Collect requirements using combined filter semantics.

    Semantics:
    - OR across different filter families (status/priority/flagged/sub-domain)
    - AND within each family (all configured values in a family must match)
    """
    normalized_sub_domains = tuple(
        normalize_sub_domain_name(value) for value in sub_domain_filters if normalize_sub_domain_name(value)
    )

    has_status = bool(status_filters)
    has_priority = bool(priority_filters)
    has_flagged = bool(flagged_filters)
    has_links = bool(link_filters)
    has_sub_domain = bool(normalized_sub_domains)

    if not (has_status or has_priority or has_flagged or has_links or has_sub_domain):
        return {}

    result: dict[Path, list[dict[str, object]]] = {}

    for path in domain_files:
        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        matching: list[dict[str, object]] = []

        for requirement in requirements:
            matches_status = False
            if has_status:
                req_status = str(requirement.get("status") or "")
                matches_status = all(req_status == value for value in status_filters)

            matches_priority = False
            if has_priority:
                req_priority = str(requirement.get("priority") or "")
                matches_priority = all(req_priority == value for value in priority_filters)

            matches_flagged = False
            if has_flagged:
                req_flagged = requirement.get("flagged")
                def _flagged_match(value: bool) -> bool:
                    if value:
                        return req_flagged is True
                    # `False` filter includes explicit false and missing flag.
                    return req_flagged is not True

                matches_flagged = all(_flagged_match(value) for value in flagged_filters)

            matches_links = False
            if has_links:
                req_has_links = isinstance(requirement.get("links"), list) and len(requirement.get("links") or []) > 0

                def _link_match(value: bool) -> bool:
                    return req_has_links is value

                matches_links = all(_link_match(value) for value in link_filters)

            matches_sub_domain = False
            if has_sub_domain:
                req_sub_domain = normalize_sub_domain_name(requirement.get("sub_domain"))
                matches_sub_domain = bool(req_sub_domain) and all(
                    req_sub_domain.startswith(value) for value in normalized_sub_domains
                )

            if matches_status or matches_priority or matches_flagged or matches_links or matches_sub_domain:
                matching.append(requirement)

        if matching:
            result[path] = matching

    return result


def parse_domain_priority_metadata(
    path: Path,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[str, object]:
    """Parse domain-level and per-H2 sub-section priority metadata.

    Looks for an optional ``- **Priority:** <label>`` line in the domain
    preamble (before the first requirement header) and in each H2 sub-section
    header block (lines between the ``## Title`` line and the next header).

    Args:
        path: Path to the markdown domain file.
        id_prefixes: Requirement ID prefixes to detect requirement headers.

    Returns:
        A dict with keys:
        - ``"domain_priority"``: ``str | None``
        - ``"sub_section_priorities"``: ``dict[str, str | None]`` mapping
          H2 section title to priority label.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {"domain_priority": None, "sub_section_priorities": {}}

    req_header = re.compile(
        r"^###\s+(?:" + "|".join(re.escape(p) for p in id_prefixes) + r")-[A-Z0-9-]+:\s*",
        re.MULTILINE,
    )
    h2_header = re.compile(r"^## (?P<title>.+?)\s*$", re.MULTILINE)

    lines = text.splitlines()
    domain_priority: str | None = None
    sub_section_priorities: dict[str, str | None] = {}

    current_h2_title: str | None = None
    current_h2_lines: list[str] = []

    def _extract_priority_from_lines(block: list[str]) -> str | None:
        for bl in block:
            m = PRIORITY_PATTERN.match(bl)
            if m:
                return m.group("priority").strip()
        return None

    in_preamble = True
    preamble_lines: list[str] = []

    for line in lines:
        if req_header.match(line):
            # Entered requirements section — flush preamble
            if in_preamble:
                in_preamble = False
                domain_priority = _extract_priority_from_lines(preamble_lines)
            # Flush any open H2 block
            if current_h2_title is not None:
                sub_section_priorities[current_h2_title] = _extract_priority_from_lines(current_h2_lines)
                current_h2_title = None
                current_h2_lines = []
            continue

        h2m = h2_header.match(line)
        if h2m:
            # Flush preamble if not yet done
            if in_preamble:
                in_preamble = False
                domain_priority = _extract_priority_from_lines(preamble_lines)
            # Flush previous H2 block
            if current_h2_title is not None:
                sub_section_priorities[current_h2_title] = _extract_priority_from_lines(current_h2_lines)
            current_h2_title = h2m.group("title").strip()
            current_h2_lines = []
            continue

        if in_preamble:
            preamble_lines.append(line)
        elif current_h2_title is not None:
            current_h2_lines.append(line)

    # Flush any remaining H2 block
    if current_h2_title is not None:
        sub_section_priorities[current_h2_title] = _extract_priority_from_lines(current_h2_lines)

    # If we never left the preamble (no req headers or H2 headers)
    if in_preamble:
        domain_priority = _extract_priority_from_lines(preamble_lines)

    return {
        "domain_priority": domain_priority,
        "sub_section_priorities": sub_section_priorities,
    }
