from __future__ import annotations

import json
from pathlib import Path

import click

from .criteria_parser import (collect_sub_sections, find_criterion_by_id,
                              normalize_sub_domain_name, parse_criteria)
from .markdown_io import display_name_from_h1, format_path_display


def parse_target_token_file(repo_root: Path, file_path_input: str) -> list[str]:
    path = Path(file_path_input)
    if not path.is_absolute():
        path = (repo_root / file_path_input).resolve()

    if not path.exists() or not path.is_file():
        raise click.ClickException(f"--filter-ids-file path not found: {file_path_input}")

    if path.suffix.lower() not in {".txt", ".conf", ".md"}:
        raise click.ClickException("--filter-ids-file must end with .txt, .conf, or .md")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise click.ClickException(f"Unable to read --filter-ids-file {path}: {exc}") from exc

    tokens = tokenize_target_text(text)
    if not tokens:
        raise click.ClickException(f"--filter-ids-file contains no target tokens: {path}")
    return tokens


def tokenize_target_text(text: str) -> list[str]:
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


def collect_target_completion_tokens(
    repo_root: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        normalized = _normalized_token(value)
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        ordered.append(value)

    for path in domain_files:
        relative = format_path_display(path, repo_root)
        add(relative)
        add(path.name)
        add(path.stem)
        add(display_name_from_h1(path))
        for requirement in parse_criteria(path, id_prefixes=id_prefixes):
            add(str(requirement["id"]))
        for subsection in collect_sub_sections(path, id_prefixes=id_prefixes):
            name = str(subsection.get("name") or "").strip()
            if name:
                add(name)

    return ordered


def complete_target_tokens(
    repo_root: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    incomplete: str,
) -> list[str]:
    prefix = _normalized_token(incomplete)
    candidates = collect_target_completion_tokens(repo_root, domain_files, id_prefixes)
    if not prefix:
        return sorted(candidates, key=lambda item: (_normalized_token(item), item))
    matches = [item for item in candidates if _normalized_token(item).startswith(prefix)]
    return sorted(matches, key=lambda item: (_normalized_token(item), item))


def resolve_target_tokens(
    repo_root: Path,
    domain_files: list[Path],
    raw_tokens: list[str] | tuple[str, ...],
    id_prefixes: tuple[str, ...],
) -> list[tuple[Path, dict[str, object]]]:
    ordered_matches: list[tuple[Path, dict[str, object]]] = []
    seen_requirements: set[tuple[str, str]] = set()

    domain_token_map: dict[str, list[Path]] = {}
    subsection_requirements: list[tuple[str, Path, dict[str, object]]] = []

    def add_domain_token(token: str, path: Path) -> None:
        normalized = _normalized_token(token)
        if not normalized:
            return
        domain_token_map.setdefault(normalized, [])
        if path not in domain_token_map[normalized]:
            domain_token_map[normalized].append(path)

    for path in domain_files:
        relative = format_path_display(path, repo_root)
        add_domain_token(relative, path)
        add_domain_token(path.name, path)
        add_domain_token(path.stem, path)
        add_domain_token(display_name_from_h1(path), path)

        for requirement in parse_criteria(path, id_prefixes=id_prefixes):
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

    for raw_token in raw_tokens:
        token = raw_token.strip()
        normalized_token = _normalized_token(token)
        if not normalized_token:
            continue

        id_matches: list[tuple[Path, dict[str, object]]] = []
        for path in domain_files:
            requirement = find_criterion_by_id(path, token, id_prefixes=id_prefixes)
            if requirement:
                id_matches.append((path, requirement))

        if len(id_matches) == 1:
            append_requirement(*id_matches[0])
            continue
        if len(id_matches) > 1:
            ambiguous_tokens.append(f"{token} (matches multiple requirement IDs)")
            continue

        domain_matches = domain_token_map.get(normalized_token, [])
        if len(domain_matches) == 1:
            for requirement in parse_criteria(domain_matches[0], id_prefixes=id_prefixes):
                append_requirement(domain_matches[0], requirement)
            continue
        if len(domain_matches) > 1:
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