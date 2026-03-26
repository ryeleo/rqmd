from __future__ import annotations

import click

from .constants import (ANSI_ESCAPE_PATTERN, ANSI_RESET, NON_ALNUM_PATTERN,
                        NON_ALNUM_PREFIX_PATTERN, PROPOSED_FG, STATUS_ALIASES,
                        STATUS_ORDER, STATUS_PARSE_ALIASES)


def style_status_count(status_label: str, value: object) -> str:
    text = str(value)
    if status_label == "✅ Verified":
        return click.style(text, fg="green")
    if status_label == "💡 Proposed":
        return f"{PROPOSED_FG}{text}{ANSI_RESET}"
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return click.style(text, dim=True)
    return text


def style_status_label(status_label: str) -> str:
    if status_label == "✅ Verified":
        return click.style(status_label, fg="green")
    if status_label == "💡 Proposed":
        return f"{PROPOSED_FG}{status_label}{ANSI_RESET}"
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return click.style(status_label, dim=True)
    return status_label


def style_status_line(status_label: str, text: str) -> str:
    if status_label == "✅ Verified":
        return click.style(text, fg="green")
    if status_label == "💡 Proposed":
        return f"{PROPOSED_FG}{text}{ANSI_RESET}"
    if status_label in ("⛔ Blocked", "🗑️ Deprecated"):
        return click.style(text, dim=True)
    return text


def status_emoji(status_label: str) -> str:
    parts = status_label.split(" ", 1)
    return parts[0] if parts else status_label


def status_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for label, slug in STATUS_ORDER:
        lower_label = label.lower()
        plain_label = label.split(" ", 1)[1].lower()
        lookup[lower_label] = label
        lookup[plain_label] = label
        lookup[slug.lower()] = label
    for alias_from, alias_to in STATUS_ALIASES.items():
        lookup[alias_from.lower()] = alias_to
        if " " in alias_from:
            lookup[alias_from.split(" ", 1)[1].lower()] = alias_to
    for alias_from, alias_to in STATUS_PARSE_ALIASES.items():
        lookup[alias_from.lower()] = alias_to
    return lookup


STATUS_LOOKUP = status_lookup()


def status_key(value: str) -> str:
    key = ANSI_ESCAPE_PATTERN.sub("", value).strip().lower()
    key = NON_ALNUM_PATTERN.sub("-", key)
    return key.strip("-")


def coerce_status_label(value: str) -> str:
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
            if lowered in STATUS_LOOKUP:
                return STATUS_LOOKUP[lowered]

        canonical_key = status_key(candidate)
        if canonical_key and canonical_key not in seen:
            seen.add(canonical_key)
            if canonical_key in STATUS_LOOKUP:
                return STATUS_LOOKUP[canonical_key]

    raise ValueError(f"Unrecognized status value: {value}")


def normalize_status_input(value: str) -> str:
    try:
        return coerce_status_label(value)
    except ValueError as exc:
        raise click.ClickException(
            "Unrecognized status input "
            f"'{value}'. Use one of: "
            + ", ".join(label for label, _ in STATUS_ORDER)
        ) from exc


def build_color_rollup_text(counts: dict[str, int]) -> str:
    blue = counts["💡 Proposed"]
    normal = counts["🔧 Implemented"]
    green = counts["✅ Verified"]
    dimmed = counts["⛔ Blocked"] + counts["🗑️ Deprecated"]

    blue_text = click.style(f"{blue:>3}", fg="bright_blue")
    normal_text = f"{normal:>3}"
    green_text = click.style(f"{green:>3}", fg="green")
    dimmed_text = click.style(f"{dimmed:>3}", dim=True)

    return f"{blue_text} | {normal_text} | {green_text} | {dimmed_text}"
