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
                        MARKDOWN_LINK_PATTERN, PRIORITY_PATTERN,
                        REQUIREMENTS_INDEX_NAME, STATUS_PATTERN)
from .priority_model import coerce_priority_label
from .status_model import coerce_status_label


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
    ordered: list[str] = []
    counts: dict[str, dict[str, object]] = {}

    for requirement in parse_requirements(path, id_prefixes=id_prefixes):
        sub_domain = display_sub_domain_name(requirement.get("sub_domain"))
        if sub_domain is None:
            continue
        key = normalize_sub_domain_name(sub_domain)
        if key not in counts:
            ordered.append(key)
            counts[key] = {"name": sub_domain, "count": 0}
        counts[key]["count"] = int(counts[key]["count"]) + 1

    return [counts[key] for key in ordered]


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
        matching = [c for c in requirements if c.get("flagged") is flagged]
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
