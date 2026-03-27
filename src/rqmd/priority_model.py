"""Priority model and normalization logic for requirements.

This module provides:
- Priority label canonicalization and aliasing
- Priority-based styling (ANSI colors, emoji handling)
- Priority lookup tables and normalization
- Display utilities for priority values
"""

from __future__ import annotations

import click

from .constants import (ANSI_ESCAPE_PATTERN, ANSI_RESET, NON_ALNUM_PATTERN,
                        NON_ALNUM_PREFIX_PATTERN, PRIORITY_ALIASES,
                        PRIORITY_ORDER, PRIORITY_PARSE_ALIASES)


def style_priority_label(priority_label: str) -> str:
    """Apply ANSI styling to a full priority label.

    Red for P0, yellow for P1, bright yellow for P2, green for P3.

    Args:
        priority_label: The full priority label (e.g., '🔴 P0 - Critical').

    Returns:
        Styled label text with ANSI codes.
    """
    if priority_label.startswith("🔴"):
        return click.style(priority_label, fg="red")
    if priority_label.startswith("🟠"):
        return click.style(priority_label, fg="yellow")
    if priority_label.startswith("🟡"):
        return click.style(priority_label, fg="bright_yellow")
    if priority_label.startswith("🟢"):
        return click.style(priority_label, fg="green")
    return priority_label


def priority_emoji(priority_label: str) -> str:
    """Extract the emoji from a priority label.

    Args:
        priority_label: The full priority label (e.g., '🔴 P0 - Critical').

    Returns:
        Just the emoji character(s).
    """
    parts = priority_label.split(" ", 1)
    return parts[0] if parts else priority_label


def priority_lookup() -> dict[str, str]:
    """Build a lookup table for priority label resolution.

    Maps various representations (lowercase label, slug, aliases) to their
    canonical priority label.

    Returns:
        Dictionary mapping priority names/aliases to canonical labels.
    """
    lookup: dict[str, str] = {}
    for label, slug in PRIORITY_ORDER:
        lower_label = label.lower()
        plain_label = label.split(" ", 1)[1].lower() if " " in label else label.lower()
        lookup[lower_label] = label
        lookup[plain_label] = label
        lookup[slug.lower()] = label
    for alias_from, alias_to in PRIORITY_ALIASES.items():
        lookup[alias_from.lower()] = alias_to
        if " " in alias_from:
            lookup[alias_from.split(" ", 1)[1].lower()] = alias_to
    for alias_from, alias_to in PRIORITY_PARSE_ALIASES.items():
        lookup[alias_from.lower()] = alias_to
    return lookup


PRIORITY_LOOKUP = priority_lookup()


def _priority_prefix_matches(value: str) -> list[str]:
    """Return canonical priority labels matching a prefix-like input."""
    token = priority_key(value)
    if not token:
        return []
    matches = sorted({label for key, label in PRIORITY_LOOKUP.items() if key.startswith(token)})
    return matches


def priority_key(value: str) -> str:
    """Generate a canonical key for a priority value for lookup purposes.

    Removes ANSI codes, converts to lowercase, replaces non-alphanumeric with dashes.

    Args:
        value: The priority value to key.

    Returns:
        A canonical key suitable for lookup.
    """
    key = ANSI_ESCAPE_PATTERN.sub("", value).strip().lower()
    key = NON_ALNUM_PATTERN.sub("-", key)
    return key.strip("-")


def coerce_priority_label(value: str) -> str:
    """Coerce a user-provided priority value to a canonical label.

    Handles partial labels, missing emoji, and aliases through flexible matching
    against the PRIORITY_LOOKUP table.

    Args:
        value: User-provided priority value (e.g., 'p0', 'critical', '🔴 P0 - Critical').

    Returns:
        The canonical priority label.

    Raises:
        ValueError: If the value cannot be matched to any priority.
    """
    raw = value.strip()
    candidates: list[str] = [raw]

    # Handle malformed/broken emoji prefixes by trying the label tail.
    tail = NON_ALNUM_PREFIX_PATTERN.sub("", raw)
    if tail and tail != raw:
        candidates.append(tail)
    if " " in raw:
        candidates.append(raw.split(" ", 1)[1].strip())
    if " " in tail:
        candidates.append(tail.split(" ", 1)[1].strip())

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate:
            continue
        lowered = candidate.lower().strip()
        if lowered and lowered not in seen:
            seen.add(lowered)
            if lowered in PRIORITY_LOOKUP:
                return PRIORITY_LOOKUP[lowered]

        canonical_key = priority_key(candidate)
        if canonical_key and canonical_key not in seen:
            seen.add(canonical_key)
            if canonical_key in PRIORITY_LOOKUP:
                return PRIORITY_LOOKUP[canonical_key]

        # Accept the smallest differentiable token/prefix when unique.
        prefix_matches = _priority_prefix_matches(candidate)
        if len(prefix_matches) == 1:
            return prefix_matches[0]

    # If coercion fails, return None to indicate unset priority
    return "unset"


def normalize_priority_input(value: str) -> str:
    normalized = coerce_priority_label(value)
    if normalized == "unset":
        matches = _priority_prefix_matches(value)
        if len(matches) > 1:
            raise click.ClickException(
                f"Ambiguous priority input '{value}'. Matches: {', '.join(matches)}. "
                f"Use one of: {', '.join(matches)}"
            )
        raise click.ClickException(f"Unrecognized priority input: {value}")
    return normalized
