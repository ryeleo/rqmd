from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .constants import (BLOCKED_REASON_PATTERN, DEFAULT_ID_PREFIXES,
                        DEPRECATED_REASON_PATTERN,
                        GENERIC_CRITERION_HEADER_PATTERN, ID_PREFIX_PATTERN,
                        MARKDOWN_LINK_PATTERN, REQUIREMENTS_INDEX_NAME,
                        STATUS_PATTERN)
from .status_model import coerce_status_label


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


def detect_id_prefixes_from_requirements_index(repo_root: Path, criteria_dir_input: str) -> tuple[str, ...]:
    criteria_dir = Path(criteria_dir_input)
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
            match = GENERIC_CRITERION_HEADER_PATTERN.match(line)
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
    criteria_dir_input: str,
    raw_prefixes: tuple[str, ...] | list[str] | None,
) -> tuple[str, ...]:
    if raw_prefixes:
        return normalize_id_prefixes(raw_prefixes)

    detected = detect_id_prefixes_from_requirements_index(repo_root, criteria_dir_input)
    if detected:
        return detected

    return DEFAULT_ID_PREFIXES


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

    return "\n".join(lines[start_index:end_index]).strip()


def collect_criteria_by_status(
    repo_root: Path,
    domain_files: list[Path],
    target_status: str,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[Path, list[dict[str, object]]]:
    del repo_root
    result: dict[Path, list[dict[str, object]]] = {}
    for path in domain_files:
        criteria = parse_criteria(path, id_prefixes=id_prefixes)
        matching = [c for c in criteria if c["status"] == target_status]
        if matching:
            result[path] = matching
    return result
