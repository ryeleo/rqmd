from __future__ import annotations

import click

from .constants import (ANSI_ESCAPE_PATTERN, ANSI_RESET, NON_ALNUM_PATTERN,
                        NON_ALNUM_PREFIX_PATTERN, PRIORITY_ALIASES,
                        PRIORITY_ORDER, PRIORITY_PARSE_ALIASES)


def style_priority_label(priority_label: str) -> str:
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
    parts = priority_label.split(" ", 1)
    return parts[0] if parts else priority_label


def priority_lookup() -> dict[str, str]:
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


def priority_key(value: str) -> str:
    key = ANSI_ESCAPE_PATTERN.sub("", value).strip().lower()
    key = NON_ALNUM_PATTERN.sub("-", key)
    return key.strip("-")


def coerce_priority_label(value: str) -> str:
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

    # If coercion fails, return None to indicate unset priority
    return "unset"


def normalize_priority_input(value: str) -> str:
    normalized = coerce_priority_label(value)
    if normalized == "unset":
        raise click.ClickException(f"Unrecognized priority input: {value}")
    return normalized

def normalize_priority_input(value: str) -> str:
    normalized = coerce_priority_label(value)
    if normalized == "unset":
        raise click.ClickException(f"Unrecognized priority input: {value}")
    return normalized
