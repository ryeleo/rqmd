"""Rollup configuration parsing and equation validation.

This module provides:
- Parsing of rollup map and rollup equation configurations
- Validation of status tokens against the active status catalog
- Equation compilation into rollup column definitions
- Error reporting for invalid rollup specifications
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import click

from .constants import STATUS_ORDER


def _build_status_name_map() -> dict[str, str]:
    """Build a mapping from status names/aliases to canonical labels.

    Returns:
        Dictionary mapping status names, slugs, and aliases to canonical labels.
    """
    mapping: dict[str, str] = {}
    for label, slug in STATUS_ORDER:
        lowered = label.lower()
        mapping[lowered] = label
        if slug:
            mapping[slug.lower()] = label
        parts = label.split(" ", 1)
        if len(parts) == 2 and parts[1].strip():
            mapping[parts[1].strip().lower()] = label

    # Backward compatible shortcodes for default catalog.
    if "💡 Proposed" in mapping.values():
        mapping.setdefault("p", "💡 Proposed")
    if "🔧 Implemented" in mapping.values():
        mapping.setdefault("i", "🔧 Implemented")
    if "✅ Verified" in mapping.values():
        mapping.setdefault("v", "✅ Verified")
    if "⛔ Blocked" in mapping.values():
        mapping.setdefault("b", "⛔ Blocked")
    if "🗑️ Deprecated" in mapping.values():
        mapping.setdefault("d", "🗑️ Deprecated")

    return mapping


def _canonical_status_label(token: str, source: str, key: str) -> str:
    """Validate and return the canonical label for a status token.

    Args:
        token: User-provided status token.
        source: Source context for error messages.
        key: Configuration key context for error messages.

    Returns:
        The canonical status label.

    Raises:
        click.ClickException: If token is not recognized.
    """
    normalized = token.strip().lower()
    if not normalized:
        raise click.ClickException(f"Invalid rollup mapping in {source}: empty status token for '{key}'.")

    status_name_map = _build_status_name_map()
    if normalized in status_name_map:
        return status_name_map[normalized]

    raise click.ClickException(
        f"Invalid rollup mapping in {source}: unknown status token '{token}' for '{key}'. "
        "Supported values are the active status labels/names from your status catalog."
    )


def _parse_equation_line(equation: str, source: str) -> tuple[str, list[str]]:
    """Parse a rollup equation line into column name and status list.

    Format: COLUMN_NAME = STATUS + STATUS + ...

    Args:
        equation: The equation string to parse.
        source: Source context for error messages.

    Returns:
        A tuple of (column_name, [status_labels]).

    Raises:
        click.ClickException: If equation is malformed or contains invalid statuses.
    """
    if "=" not in equation:
        raise click.ClickException(f"Invalid rollup equation in {source}: '{equation}' (expected NAME = A + B).")

    column, rhs = equation.split("=", 1)
    column = column.strip()
    if not column:
        raise click.ClickException(f"Invalid rollup equation in {source}: missing column name in '{equation}'.")

    raw_tokens = [part.strip() for part in re.split(r"\+|,", rhs) if part.strip()]
    if not raw_tokens:
        raise click.ClickException(f"Invalid rollup equation in {source}: no statuses in '{equation}'.")

    seen: set[str] = set()
    statuses: list[str] = []
    for token in raw_tokens:
        label = _canonical_status_label(token, source, column)
        if label not in seen:
            seen.add(label)
            statuses.append(label)

    return column, statuses


def _parse_rollup_map(raw_map: object, source: str) -> list[tuple[str, list[str]]]:
    """Parse a rollup_map configuration into column/status pairs.

    Args:
        raw_map: The raw configuration object (should be a dict).
        source: Source context for error messages.

    Returns:
        List of (column_name, [status_labels]) tuples.

    Raises:
        click.ClickException: If configuration is malformed.
    """
    if not isinstance(raw_map, dict):
        raise click.ClickException(f"Invalid rollup_map in {source}: expected an object mapping column names to statuses.")

    columns: list[tuple[str, list[str]]] = []
    for column, value in raw_map.items():
        column_name = str(column).strip()
        if not column_name:
            raise click.ClickException(f"Invalid rollup_map in {source}: column names cannot be empty.")

        tokens: list[str]
        if isinstance(value, list):
            tokens = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str):
            tokens = [part.strip() for part in re.split(r"\+|,", value) if part.strip()]
        else:
            raise click.ClickException(
                f"Invalid rollup_map in {source}: '{column_name}' must be a list or string expression."
            )

        if not tokens:
            raise click.ClickException(f"Invalid rollup_map in {source}: '{column_name}' has no statuses.")

        seen: set[str] = set()
        statuses: list[str] = []
        for token in tokens:
            label = _canonical_status_label(token, source, column_name)
            if label not in seen:
                seen.add(label)
                statuses.append(label)
        columns.append((column_name, statuses))

    if not columns:
        raise click.ClickException(f"Invalid rollup_map in {source}: mapping is empty.")
    return columns


def _parse_rollup_equations(raw_equations: object, source: str) -> list[tuple[str, list[str]]]:
    if not isinstance(raw_equations, list):
        raise click.ClickException(f"Invalid rollup_equations in {source}: expected a list of equation strings.")

    columns: list[tuple[str, list[str]]] = []
    for item in raw_equations:
        equation = str(item).strip()
        if not equation:
            continue
        columns.append(_parse_equation_line(equation, source))

    if not columns:
        raise click.ClickException(f"Invalid rollup_equations in {source}: no equations found.")
    return columns


def _load_yaml(path: Path) -> object:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise click.ClickException(
            f"YAML rollup config requires PyYAML. Install with: uv add pyyaml (while loading {path})"
        ) from exc

    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise click.ClickException(f"Unable to read rollup config '{path}': {exc}") from exc
    except Exception as exc:
        raise click.ClickException(f"Invalid YAML rollup config '{path}': {exc}") from exc


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise click.ClickException(f"Unable to read rollup config '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON rollup config '{path}': {exc.msg}") from exc


def load_rollup_columns_from_file(path: Path) -> list[tuple[str, list[str]]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        data = _load_json(path)
    elif suffix in {".yml", ".yaml"}:
        data = _load_yaml(path)
    else:
        raise click.ClickException(
            f"Unsupported rollup config extension for '{path}'. Use .json, .yml, or .yaml."
        )

    if not isinstance(data, dict):
        raise click.ClickException(f"Invalid rollup config '{path}': expected top-level object.")

    has_map = "rollup_map" in data
    has_eq = "rollup_equations" in data
    if has_map and has_eq:
        raise click.ClickException(
            f"Invalid rollup config '{path}': provide either rollup_map or rollup_equations, not both."
        )
    if not has_map and not has_eq:
        raise click.ClickException(
            f"Invalid rollup config '{path}': expected rollup_map or rollup_equations at top level."
        )

    if has_map:
        return _parse_rollup_map(data["rollup_map"], str(path))
    return _parse_rollup_equations(data["rollup_equations"], str(path))


def parse_rollup_cli_entries(entries: tuple[str, ...]) -> list[tuple[str, list[str]]]:
    if not entries:
        return []

    columns: list[tuple[str, list[str]]] = []
    for entry in entries:
        columns.append(_parse_equation_line(entry, "--rollup-map"))
    return columns


def resolve_rollup_columns(
    repo_root: Path,
    cli_rollup_map: tuple[str, ...],
    rollup_config_path: str | None,
) -> tuple[list[tuple[str, list[str]]], str | None]:
    cli_columns = parse_rollup_cli_entries(cli_rollup_map)
    if cli_columns:
        return cli_columns, "cli"

    if rollup_config_path:
        path = Path(rollup_config_path)
        if not path.is_absolute():
            path = (repo_root / path).resolve()
        if not path.exists():
            raise click.ClickException(f"Rollup config file not found: {path}")
        return load_rollup_columns_from_file(path), str(path)

    project_candidates = [
        repo_root / ".rqmd.yml",
        repo_root / ".rqmd.yaml",
    ]
    for candidate in project_candidates:
        if candidate.exists() and candidate.is_file():
            try:
                return load_rollup_columns_from_file(candidate), str(candidate)
            except click.ClickException as exc:
                # In unified config mode, .rqmd.* may define only non-rollup keys.
                if "expected rollup_map or rollup_equations at top level" in str(exc):
                    continue
                raise

    user_candidates = [
        Path.home() / ".config" / "rqmd" / "rollup.json",
        Path.home() / ".config" / "rqmd" / "rollup.yaml",
        Path.home() / ".config" / "rqmd" / "rollup.yml",
    ]
    for candidate in user_candidates:
        if candidate.exists() and candidate.is_file():
            return load_rollup_columns_from_file(candidate), str(candidate)

    return [], None


def compute_rollup_column_values(
    totals: dict[str, int],
    columns: list[tuple[str, list[str]]],
) -> list[tuple[str, int, list[str]]]:
    values: list[tuple[str, int, list[str]]] = []
    for label, statuses in columns:
        value = sum(totals.get(status, 0) for status in statuses)
        values.append((label, value, statuses))
    return values
