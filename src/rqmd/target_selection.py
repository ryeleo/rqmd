"""Target token resolution and completion logic.

This module provides:
- Parsing of target token files (JSONL, CSV, MD, TXT formats)
- Tokenization of target input (IDs, file paths, sub-domains)
- Completion suggestions for partial target tokens
- Resolution of raw tokens to actual requirements/files
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from .markdown_io import display_name_from_h1, format_path_display
from .req_parser import (
    collect_sub_sections,
    find_requirement_by_id,
    normalize_sub_domain_name,
    parse_requirements,
)


def parse_target_token_file(repo_root: Path, file_path_input: str) -> list[str]:
    """Parse target tokens from a file (TXT, CONF, or MD format).

    Args:
        repo_root: Root path of the project.
        file_path_input: Path to the token file (absolute or repo-relative).

    Returns:
        List of extracted target tokens.

    Raises:
        click.ClickException: If file not found, wrong format, or no tokens extracted.
    """
    path = Path(file_path_input)
    if not path.is_absolute():
        path = (repo_root / file_path_input).resolve()

    if not path.exists() or not path.is_file():
        raise click.ClickException(f"--targets-file path not found: {file_path_input}")

    if path.suffix.lower() not in {".txt", ".conf", ".md"}:
        raise click.ClickException("--targets-file must end with .txt, .conf, or .md")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Unable to read --targets-file {path}: {exc}") from exc

    tokens = tokenize_target_text(text)
    if not tokens:
        raise click.ClickException(f"--targets-file contains no target tokens: {path}")
    return tokens


def tokenize_target_text(text: str) -> list[str]:
    """Tokenize a text string into target tokens (IDs, file names, sub-domains).

    Handles comments (lines after #), comma and whitespace separation.

    Args:
        text: Text content to tokenize.

    Returns:
        List of non-empty tokens.
    """
    tokens: list[str] = []
    for raw_line in text.splitlines():
        uncommented = raw_line.split("#", 1)[0].replace(",", " ")
        for token in uncommented.split():
            stripped = token.strip()
            if stripped:
                tokens.append(stripped)
    return tokens


def _normalized_token(value: str) -> str:
    return normalize_sub_domain_name(value)


def collect_target_completion_candidates(
    repo_root: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
) -> list[dict[str, str]]:
    """Collect completion candidates with a user-facing kind label."""
    ordered: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(value: str, kind: str) -> None:
        normalized = _normalized_token(value)
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        ordered.append({"value": value, "kind": kind})

    for path in domain_files:
        relative = format_path_display(path, repo_root)
        add(relative, "domain")
        add(path.name, "domain")
        add(path.stem, "domain")
        add(display_name_from_h1(path), "domain")
        for requirement in parse_requirements(path, id_prefixes=id_prefixes):
            add(str(requirement["id"]), "requirement-id")
        for subsection in collect_sub_sections(path, id_prefixes=id_prefixes):
            name = str(subsection.get("name") or "").strip()
            if name:
                add(name, "subsection")

    return ordered


def collect_target_completion_tokens(
    repo_root: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
) -> list[str]:
    """Collect all possible completion tokens (IDs, file names, sub-domains).

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain file paths.
        id_prefixes: Allowed ID prefixes.

    Returns:
        Deduplicated list of completion tokens.
    """
    return [item["value"] for item in collect_target_completion_candidates(repo_root, domain_files, id_prefixes)]


def complete_target_completion_candidates(
    repo_root: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    incomplete: str,
) -> list[dict[str, str]]:
    """Return matching completion candidates with kind metadata."""
    prefix = _normalized_token(incomplete)
    candidates = collect_target_completion_candidates(repo_root, domain_files, id_prefixes)
    if not prefix:
        return sorted(candidates, key=lambda item: (_normalized_token(item["value"]), item["value"]))
    matches = [item for item in candidates if _normalized_token(item["value"]).startswith(prefix)]
    return sorted(matches, key=lambda item: (_normalized_token(item["value"]), item["value"]))


def complete_target_tokens(
    repo_root: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    incomplete: str,
) -> list[str]:
    """Complete partial target tokens.

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain file paths.
        id_prefixes: Allowed ID prefixes.
        incomplete: Partial token to match.

    Returns:
        Sorted list of matching completion tokens.
    """
    return [
        item["value"]
        for item in complete_target_completion_candidates(
            repo_root,
            domain_files,
            id_prefixes,
            incomplete,
        )
    ]


def resolve_target_tokens(
    repo_root: Path,
    domain_files: list[Path],
    raw_tokens: list[str] | tuple[str, ...],
    id_prefixes: tuple[str, ...],
) -> list[tuple[Path, dict[str, object]]]:
    """Resolve raw target tokens to (file, requirement) tuples.

    Handles file-scoped tokens, ID-only tokens, and sub-domain tokens.

    Args:
        repo_root: Root path of the project.
        domain_files: List of domain file paths.
        raw_tokens: List of tokens to resolve (IDs, file names, sub-domains).
        id_prefixes: Allowed ID prefixes.

    Returns:
        List of (file_path, requirement_dict) tuples.
    """
    ordered_matches: list[tuple[Path, dict[str, object]]] = []
    seen_requirements: set[tuple[str, str]] = set()

    domain_token_map: dict[str, list[Path]] = {}
    requirement_token_map: dict[str, list[tuple[Path, dict[str, object]]]] = {}
    subsection_requirements: list[tuple[str, Path, dict[str, object]]] = []

    def add_domain_token(token: str, path: Path) -> None:
        normalized = _normalized_token(token)
        if not normalized:
            return
        domain_token_map.setdefault(normalized, [])
        if path not in domain_token_map[normalized]:
            domain_token_map[normalized].append(path)

    def add_requirement_token(token: str, path: Path, requirement: dict[str, object]) -> None:
        normalized = _normalized_token(token)
        if not normalized:
            return
        requirement_token_map.setdefault(normalized, [])
        candidate = (path, requirement)
        if candidate not in requirement_token_map[normalized]:
            requirement_token_map[normalized].append(candidate)

    for path in domain_files:
        relative = format_path_display(path, repo_root)
        add_domain_token(relative, path)
        add_domain_token(path.name, path)
        add_domain_token(path.stem, path)
        add_domain_token(display_name_from_h1(path), path)

        for requirement in parse_requirements(path, id_prefixes=id_prefixes):
            add_requirement_token(str(requirement["id"]), path, requirement)
            normalized_sub_domain = normalize_sub_domain_name(str(requirement.get("sub_domain") or ""))
            if normalized_sub_domain:
                subsection_requirements.append((normalized_sub_domain, path, requirement))

    invalid_tokens: list[str] = []
    ambiguous_tokens: list[str] = []

    def append_requirement(path: Path, requirement: dict[str, object]) -> None:
        key = (str(path.resolve()), str(requirement["id"]))
        if key in seen_requirements:
            return
        seen_requirements.add(key)
        ordered_matches.append((path, requirement))

    def unique_requirement_matches(prefix: str) -> list[tuple[Path, dict[str, object]]]:
        deduped: list[tuple[Path, dict[str, object]]] = []
        seen: set[tuple[str, str]] = set()
        for token_key, entries in requirement_token_map.items():
            if not token_key.startswith(prefix):
                continue
            for path, requirement in entries:
                key = (str(path.resolve()), str(requirement["id"]))
                if key in seen:
                    continue
                seen.add(key)
                deduped.append((path, requirement))
        return deduped

    def unique_domain_matches(prefix: str) -> list[Path]:
        matches: list[Path] = []
        seen: set[str] = set()
        for token_key, paths in domain_token_map.items():
            if not token_key.startswith(prefix):
                continue
            for path in paths:
                resolved = str(path.resolve())
                if resolved in seen:
                    continue
                seen.add(resolved)
                matches.append(path)
        return matches

    for raw_token in raw_tokens:
        token = raw_token.strip()
        normalized_token = _normalized_token(token)
        if not normalized_token:
            continue

        id_matches: list[tuple[Path, dict[str, object]]] = []
        for path in domain_files:
            requirement = find_requirement_by_id(path, token, id_prefixes=id_prefixes)
            if requirement:
                id_matches.append((path, requirement))

        if len(id_matches) == 1:
            append_requirement(*id_matches[0])
            continue
        if len(id_matches) > 1:
            ambiguous_tokens.append(f"{token} (matches multiple requirement IDs)")
            continue

        prefix_id_matches = unique_requirement_matches(normalized_token)
        if len(prefix_id_matches) == 1:
            append_requirement(*prefix_id_matches[0])
            continue
        if len(prefix_id_matches) > 1:
            ambiguous_tokens.append(f"{token} (matches multiple requirement IDs)")
            continue

        domain_matches = domain_token_map.get(normalized_token, [])
        if len(domain_matches) == 1:
            for requirement in parse_requirements(domain_matches[0], id_prefixes=id_prefixes):
                append_requirement(domain_matches[0], requirement)
            continue
        if len(domain_matches) > 1:
            ambiguous_tokens.append(f"{token} (matches multiple domain identifiers)")
            continue

        prefix_domain_matches = unique_domain_matches(normalized_token)
        if len(prefix_domain_matches) == 1:
            for requirement in parse_requirements(prefix_domain_matches[0], id_prefixes=id_prefixes):
                append_requirement(prefix_domain_matches[0], requirement)
            continue
        if len(prefix_domain_matches) > 1:
            ambiguous_tokens.append(f"{token} (matches multiple domain identifiers)")
            continue

        subsection_matches = [
            (path, requirement)
            for subsection_name, path, requirement in subsection_requirements
            if subsection_name.startswith(normalized_token)
        ]
        if subsection_matches:
            for path, requirement in subsection_matches:
                append_requirement(path, requirement)
            continue

        invalid_tokens.append(token)

    errors: list[str] = []
    if ambiguous_tokens:
        errors.append("Ambiguous target tokens: " + ", ".join(ambiguous_tokens))
    if invalid_tokens:
        errors.append("Unrecognized target tokens: " + ", ".join(invalid_tokens))
    if errors:
        raise click.ClickException("\n".join(errors))

    if not ordered_matches:
        raw_json = json.dumps(list(raw_tokens), ensure_ascii=False)
        raise click.ClickException(f"No requirements resolved from target tokens: {raw_json}")

    return ordered_matches