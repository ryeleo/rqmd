from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from .constants import (DEFAULT_ID_PREFIXES, MENU_PAGE_SIZE, MENU_REFRESH,
                        MENU_TOGGLE_DIRECTION, MENU_TOGGLE_SORT,
                        PRIORITY_ORDER, STATUS_ORDER, STATUS_PATTERN)
from .markdown_io import (display_name_from_h1, format_path_display,
                          iter_domain_files, scope_and_body_from_file)
from .menus import (right_align_menu_suffix, select_from_menu, truncate_text,
                    visible_length)
from .priority_model import style_priority_label
from .req_parser import (collect_sub_sections,
                         extract_requirement_block_with_lines,
                         find_requirement_by_id, normalize_sub_domain_name,
                         parse_requirements)
from .status_model import (build_color_rollup_text, status_emoji,
                           style_status_label, style_status_line)
from .status_update import (print_criterion_panel, prompt_for_blocked_reason,
                            prompt_for_deprecated_reason,
                            prompt_for_links_flow, update_criterion_status)
from .summary import (collect_summary_rows, count_priorities, count_statuses,
                      print_summary_table, process_file)

SORT_STRATEGY_SPECS: dict[str, dict[str, object]] = {
    "standard": {
        "file_columns": [
            ("name", "name"),
            ("priority", "Pri"),
            ("proposed", "P"),
            ("implemented", "I"),
            ("verified", "Ver"),
            ("blocked_deprecated", "Blk/Dep"),
        ],
        "file_default_key": "name",
        "file_default_ascending": False,
        "criterion_columns": [
            ("status", "status"),
            ("priority", "priority"),
            ("title", "title"),
            ("id", "id"),
        ],
        "criterion_default_key": "status",
        "criterion_default_ascending": False,
        "criterion_cycle_wrap": True,
    },
    "status-focus": {
        "file_columns": [
            ("priority", "Pri"),
            ("implemented", "I"),
            ("verified", "Ver"),
            ("proposed", "P"),
            ("blocked_deprecated", "Blk/Dep"),
            ("name", "name"),
        ],
        "file_default_key": "implemented",
        "file_default_ascending": False,
        "criterion_columns": [
            ("status", "status"),
            ("priority", "priority"),
            ("title", "title"),
            ("id", "id"),
        ],
        "criterion_default_key": "status",
        "criterion_default_ascending": False,
        "criterion_cycle_wrap": True,
    },
    "alpha-asc": {
        "file_columns": [
            ("name", "name"),
            ("priority", "Pri"),
            ("proposed", "P"),
            ("implemented", "I"),
            ("verified", "Ver"),
            ("blocked_deprecated", "Blk/Dep"),
        ],
        "file_default_key": "name",
        "file_default_ascending": True,
        "criterion_columns": [
            ("status", "status"),
            ("priority", "priority"),
            ("title", "title"),
            ("id", "id"),
        ],
        "criterion_default_key": "status",
        "criterion_default_ascending": False,
        "criterion_cycle_wrap": True,
    },
}

SORT_STRATEGY_NAMES = tuple(sorted(SORT_STRATEGY_SPECS.keys()))


FILE_SORT_COLUMNS: list[tuple[str, str]] = [
    ("name", "name"),
    ("priority", "priority"),
    ("proposed", "P"),
    ("implemented", "I"),
    ("verified", "Ver"),
    ("blocked_deprecated", "Blk/Dep"),
]

CRITERION_SORT_COLUMNS: list[tuple[str, str]] = [
    ("status", "status"),
    ("priority", "priority"),
    ("title", "title"),
    ("id", "id"),
]


def _cycle_sort_key(
    current_key: str | None,
    columns: list[tuple[str, str]],
    wrap_to_first: bool = False,
    reverse: bool = False,
) -> str | None:
    """Cycle to the next/previous sort key from a list of columns.

    Args:
        current_key: Current sort key (or None for first).
        columns: List of (key, label) tuples.
        wrap_to_first: If True, wrap to first item when at end (or last when reverse).
        reverse: If True, cycle backwards; if False, cycle forwards.

    Returns:
        The next sort key, or None if no rotation possible.
    """
    keys = [key for key, _label in columns]
    if current_key is None:
        return keys[0] if keys else None
    try:
        index = keys.index(current_key)
    except ValueError:
        return keys[0] if keys else None
    if reverse:
        if index == 0:
            return keys[-1] if wrap_to_first and keys else None
        return keys[index - 1]
    if index == len(keys) - 1:
        return keys[0] if wrap_to_first and keys else None
    return keys[index + 1]


def _sort_indicator(ascending: bool) -> str:
    """Generate a sort direction indicator character.

    Args:
        ascending: If True, return up arrow; if False, return down arrow.

    Returns:
        A directional indicator character.
    """
    return "↑" if ascending else "↓"


def _format_sort_token(label: str, active: bool, ascending: bool) -> str:
    """Format a sort token with styling.

    Args:
        label: Column label.
        active: If True, apply bold styling.
        ascending: Current sort direction.

    Returns:
        Formatted token with sort indicator.
    """
    indicator = _sort_indicator(ascending) if active else " "
    text = f"{label} {indicator}"
    return click.style(text, bold=True) if active else text


def _right_align_sort_token(text: str, width: int) -> str:
    padding = max(0, width - visible_length(text))
    return f"{' ' * padding}{text}"


def _build_sort_title(base_title: str, default_label: str, columns: list[tuple[str, str]], active_key: str | None, ascending: bool) -> str:
    tokens = [_format_sort_token(default_label, active_key is None, ascending)]
    for key, label in columns:
        tokens.append(_format_sort_token(label, active_key == key, ascending))
    return f"{base_title}\nsort: {' | '.join(tokens)}"


def _right_align_text(left: str, right: str) -> str:
    term_width = shutil.get_terminal_size(fallback=(120, 24)).columns
    pad = term_width - visible_length(left) - visible_length(right)
    if pad < 1:
        pad = 1
    return f"{left}{' ' * pad}{right}"


def _build_file_stats_header(active_key: str, ascending: bool, emoji_columns: bool = False) -> str:
    labels = {
        "priority": "priority",
        "proposed": "💡" if emoji_columns else "P",
        "implemented": "🔧" if emoji_columns else "I",
        "verified": "✅" if emoji_columns else "Ver",
        "blocked_deprecated": "⛔/🗑️" if emoji_columns else "Blk/Dep",
    }

    def cell(key: str, width: int) -> str:
        label = labels[key]
        indicator = _sort_indicator(ascending) if active_key == key else " "
        styled = click.style(f"{label} {indicator}", bold=(active_key == key))
        return _right_align_sort_token(styled, width)

    return " | ".join(
        [
            cell("priority", 12),
            cell("proposed", 5),
            cell("implemented", 5),
            cell("verified", 5),
            cell("blocked_deprecated", 9 if not emoji_columns else 8),
        ]
    )


def _build_file_sort_title(
    base_title: str,
    active_key: str,
    ascending: bool,
    columns: list[tuple[str, str]],
    emoji_columns: bool = False,
) -> str:
    name_indicator = _sort_indicator(ascending) if active_key == "name" else " "
    name_label = click.style(
        f"name {name_indicator}",
        bold=(active_key == "name"),
    )
    left = f"sort: {name_label}"
    right = _build_file_stats_header(active_key, ascending, emoji_columns=emoji_columns)
    return f"{base_title}\n{_right_align_text(left, right)}"


def _build_criterion_sort_title(base_title: str, active_key: str | None, ascending: bool) -> str:
    status_indicator = _sort_indicator(ascending) if active_key == "status" else " "
    status_label = click.style(
        f"status {status_indicator}",
        bold=(active_key == "status"),
    )
    priority_indicator = _sort_indicator(ascending) if active_key == "priority" else " "
    priority_label = click.style(
        f"priority {priority_indicator}",
        bold=(active_key == "priority"),
    )
    title_indicator = _sort_indicator(ascending) if active_key == "title" else " "
    title_label = click.style(
        f"title {title_indicator}",
        bold=(active_key == "title"),
    )
    id_indicator = _sort_indicator(ascending) if active_key == "id" else " "
    id_label = click.style(
        f"id {id_indicator}",
        bold=(active_key == "id"),
    )

    left = f"sort: {status_label} | {priority_label} | {title_label}"
    return f"{base_title}\n{_right_align_text(left, id_label)}"


def _build_file_rollup_text(path: Path, status_counts: dict[str, int]) -> str:
    priority_counts = count_priorities(path.read_text(encoding="utf-8"))
    priority_cell = " ".join(
        f"{priority_counts[label]}{label.split(' ', 1)[0]}"
        for label, _slug in PRIORITY_ORDER
    )
    return (
        f"{click.style(priority_cell, dim=True)} | "
        f"{build_color_rollup_text(status_counts)}"
    )


def _refresh_index_from_choice(choice: str) -> int | None:
    if not isinstance(choice, str):
        return None
    if not choice.startswith("refresh:"):
        return None
    raw = choice.split(":", 1)[1].strip()
    if not raw.isdigit():
        return None
    return int(raw) * MENU_PAGE_SIZE


def get_sort_strategy_spec(name: str) -> dict[str, object]:
    """Look up a sort strategy specification by name.

    Args:
        name: Strategy name (e.g., 'standard', 'status-focus', 'alpha-asc').

    Returns:
        Dictionary with keys: file_columns, file_default_key, criterion_columns, etc.

    Raises:
        click.ClickException: If strategy name not recognized.
    """
    key = (name or "standard").strip().lower()
    if key not in SORT_STRATEGY_SPECS:
        supported = ", ".join(SORT_STRATEGY_NAMES)
        raise click.ClickException(f"Unknown sort strategy '{name}'. Supported values: {supported}")
    return SORT_STRATEGY_SPECS[key]


def _build_sort_footer(ascending: bool) -> str:
    direction = "asc" if ascending else "dsc"
    return (
        f"keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | "
        f"{MENU_TOGGLE_SORT}=sort | S=sort-back | {MENU_TOGGLE_DIRECTION}=[{direction}] | {MENU_REFRESH}=rfrsh | q=quit"
    )


def _build_requirement_action_footer(allow_nav: bool) -> str:
    base = "keys: 1-9 select | u=up | t=toggle | q=quit"
    if not allow_nav:
        return base
    return "keys: 1-9 select | ↓/n=next | ↑/p=prev | g=begin | G=end | u=up | t=toggle | q=quit"


def _file_sort_value(counts: dict[str, int], sort_key: str) -> int | str:
    if sort_key == "name":
        raise ValueError("name sort should be handled separately")
    if sort_key == "proposed":
        return counts["💡 Proposed"]
    if sort_key == "implemented":
        return counts["🔧 Implemented"]
    if sort_key == "verified":
        return counts["✅ Verified"]
    if sort_key == "blocked_deprecated":
        return counts["⛔ Blocked"] + counts["🗑️ Deprecated"]
    raise ValueError(f"Unknown file sort key: {sort_key}")


def _file_priority_tuple(path: Path) -> tuple[int, int, int, int]:
    priority_counts = count_priorities(path.read_text(encoding="utf-8"))
    return tuple(priority_counts[label] for label, _slug in PRIORITY_ORDER)


def _sort_file_rows(
    rows: list[tuple[Path, dict[str, int], str]],
    sort_key: str | None,
    ascending: bool,
) -> list[tuple[Path, dict[str, int], str]]:
    """Sort file rows by the specified key and direction.

    Args:
        rows: List of (path, counts, display_name) tuples.
        sort_key: Sort column key (or None for unsorted).
        ascending: If True, sort ascending; if False, sort descending.

    Returns:
        Sorted list of rows.
    """
    if sort_key is None:
        return list(rows)
    if sort_key == "name":
        return sorted(rows, key=lambda row: (row[2].lower(), row[0].name.lower()), reverse=not ascending)
    if sort_key == "priority":
        return sorted(
            rows,
            key=lambda row: (_file_priority_tuple(row[0]), row[2].lower(), row[0].name.lower()),
            reverse=not ascending,
        )
    return sorted(
        rows,
        key=lambda row: (_file_sort_value(row[1], sort_key), row[2].lower(), row[0].name.lower()),
        reverse=not ascending,
    )


def sort_file_rows_for_strategy(
    rows: list[tuple[Path, dict[str, int], str]],
    sort_strategy: str,
) -> list[tuple[Path, dict[str, int], str]]:
    strategy = get_sort_strategy_spec(sort_strategy)
    sort_key = str(strategy["file_default_key"])
    ascending = bool(strategy["file_default_ascending"])
    return _sort_file_rows(rows, sort_key, ascending)


def resolve_resume_state_dir(repo_root: Path, state_dir: str) -> Path:
    mode = (state_dir or "system-temp").strip().lower()
    if mode == "system-temp":
        return Path(tempfile.gettempdir()) / "rqmd"
    if mode == "project-local":
        return repo_root / "tmp" / "rqmd"

    resolved = Path(state_dir).expanduser()
    if resolved.is_absolute():
        return resolved
    return (repo_root / resolved).resolve()


def infer_include_status_emojis(domain_files: list[Path]) -> bool:
    emoji_prefixes = tuple(label.split(" ", 1)[0] for label, _ in STATUS_ORDER)
    for path in domain_files:
        text = path.read_text(encoding="utf-8")
        for match in STATUS_PATTERN.finditer(text):
            raw = match.group("status").strip()
            if raw.startswith(emoji_prefixes):
                return True
    return False


def _criterion_status_rank(status: str) -> int:
    status_priority = {label: i for i, (label, _slug) in enumerate(STATUS_ORDER)}
    return status_priority.get(status, 99)


def _criterion_priority_rank(priority: str | None) -> int:
    priority_order = {label: i for i, (label, _slug) in enumerate(PRIORITY_ORDER)}
    if not priority or priority == "unset":
        return len(PRIORITY_ORDER)
    return priority_order.get(priority, len(PRIORITY_ORDER) + 1)


def _priority_highlight_bg(priority: str) -> str:
    if priority.startswith("🔴"):
        return "\x1b[48;5;52m"
    if priority.startswith("🟠"):
        return "\x1b[48;5;130m"
    if priority.startswith("🟡"):
        return "\x1b[48;5;178m"
    if priority.startswith("🟢"):
        return "\x1b[48;5;22m"
    return "\x1b[48;5;238m"


ENTRY_FIELDS = ("status", "priority", "flagged", "links")


def _next_entry_field(current: str) -> str:
    try:
        current_index = ENTRY_FIELDS.index(current)
    except ValueError:
        return ENTRY_FIELDS[0]
    return ENTRY_FIELDS[(current_index + 1) % len(ENTRY_FIELDS)]


def _build_requirement_field_menu(
    requirement: dict[str, object],
    active_field: str,
    title_suffix: str = "",
) -> tuple[str, list[str], list[str], int | None, str]:
    if active_field == "flagged":
        labels = ["true", "false"]
        options = ["Flagged: true", "Flagged: false"]
        current_flagged = requirement.get("flagged")
        current_index = 0 if current_flagged is True else 1 if current_flagged is False else None
        highlight_bg = "\x1b[48;5;88m" if current_flagged is True else "\x1b[48;5;238m"
        title = f"Set flagged for {requirement['id']}{title_suffix}\nsetting: flagged"
        return title, labels, options, current_index, highlight_bg

    if active_field == "priority":
        labels = [label for label, _ in PRIORITY_ORDER]
        options = [style_priority_label(label) for label in labels]
        current_value = str(requirement.get("priority") or "")
        try:
            current_index = labels.index(current_value)
        except ValueError:
            current_index = None
        highlight_bg = _priority_highlight_bg(current_value)
        title = f"Set priority for {requirement['id']}{title_suffix}\nsetting: priority"
        return title, labels, options, current_index, highlight_bg

    if active_field == "links":
        existing_links = requirement.get("links") or []
        link_count = len(existing_links)  # type: ignore[arg-type]
        count_str = f"{link_count} link{'s' if link_count != 1 else ''}" if link_count else "no links"
        labels = ["manage"]
        options = [f"🔗 Manage links ({count_str})\u2026"]
        title = f"Edit links for {requirement['id']}{title_suffix}\nsetting: links"
        return title, labels, options, None, "\x1b[48;5;25m"

    labels = [label for label, _ in STATUS_ORDER]
    options = [style_status_label(label) for label in labels]
    current_value = str(requirement.get("status") or "")
    try:
        current_index = labels.index(current_value)
    except ValueError:
        current_index = None

    highlight_bg = "\x1b[48;5;220m"
    if current_value == "✅ Verified":
        highlight_bg = "\x1b[48;5;28m"
    elif current_value == "💡 Proposed":
        highlight_bg = "\x1b[48;5;27m"
    elif current_value in ("⛔ Blocked", "🗑️ Deprecated"):
        highlight_bg = "\x1b[48;5;238m"

    title = f"Set status for {requirement['id']}{title_suffix}\nsetting: status"
    return title, labels, options, current_index, highlight_bg


def _prompt_for_requirement_action(
    requirement: dict[str, object],
    active_field: str,
    select_from_menu_fn,
    title_suffix: str = "",
    allow_nav: bool = True,
) -> tuple[str, str | None]:
    title, labels, options, selected_index, selected_bg = _build_requirement_field_menu(
        requirement,
        active_field,
        title_suffix=title_suffix,
    )
    extra_keys = {"t": "toggle-field"}
    extra_keys_help = {"t": "toggle"}
    if allow_nav:
        extra_keys.update({"n": "nav-next", "p": "nav-prev", "N": "nav-prev", "g": "nav-first", "G": "nav-last"})
        extra_keys_help.update({"n": "next", "p": "prev", "N": "prev", "g": "begin", "G": "end"})

    choice = select_from_menu_fn(
        title,
        options,
        show_page_indicator=False,
        allow_paging_nav=False,
        extra_keys=extra_keys,
        extra_keys_help=extra_keys_help,
        selected_option_index=selected_index,
        selected_option_bg=selected_bg,
        footer_legend=_build_requirement_action_footer(allow_nav),
    )
    if choice is None:
        return "quit", None
    if isinstance(choice, str) and choice in {"up", "nav-prev", "nav-next", "nav-first", "nav-last", "toggle-field"}:
        return choice, None
    return "apply", labels[int(choice)]


def _sort_criteria(
    requirements: list[dict[str, object]],
    sort_key: str | None,
    ascending: bool,
) -> list[dict[str, object]]:
    if sort_key is None:
        return list(requirements)
    if sort_key == "title":
        return sorted(requirements, key=lambda item: (str(item["title"]).lower(), str(item["id"]).lower()), reverse=not ascending)
    if sort_key == "id":
        return sorted(requirements, key=lambda item: str(item["id"]).lower(), reverse=not ascending)
    if sort_key == "priority":
        return sorted(
            requirements,
            key=lambda item: (_criterion_priority_rank(item.get("priority") if isinstance(item.get("priority"), str) else None), str(item["title"]).lower(), str(item["id"]).lower()),
            reverse=ascending,
        )
    if sort_key == "status":
        return sorted(
            requirements,
            key=lambda item: (_criterion_status_rank(str(item["status"])), str(item["title"]).lower(), str(item["id"]).lower()),
            reverse=not ascending,
        )
    raise ValueError(f"Unknown requirement sort key: {sort_key}")


def print_criteria_tree(
    repo_root: Path,
    criteria_by_file: dict[Path, list[dict[str, object]]],
    target_value: str,
    filter_label: str = "status",
) -> None:
    if not criteria_by_file:
        click.echo(f"No requirements found with {filter_label}: {target_value}")
        return

    click.echo(click.style(f"\n{target_value}", bold=True))
    click.echo()

    files = sorted(criteria_by_file.keys())
    for file_idx, path in enumerate(files):
        is_last_file = file_idx == len(files) - 1
        file_prefix = "└── " if is_last_file else "├── "
        relative_path = path.relative_to(repo_root)
        click.echo(f"{file_prefix}{click.style(relative_path.as_posix(), dim=True)}")

        requirements = criteria_by_file[path]
        for crit_idx, requirement in enumerate(requirements):
            is_last_crit = crit_idx == len(requirements) - 1
            crit_prefix = "    " if is_last_file else "│   "
            branch = "└── " if is_last_crit else "├── "
            crit_id = requirement["id"]
            crit_title = requirement["title"]
            click.echo(f"{crit_prefix}{branch}{crit_id}: {crit_title}")

    click.echo()


def print_criteria_list(
    repo_root: Path,
    criteria_by_file: dict[Path, list[dict[str, object]]],
    target_value: str,
    filter_label: str = "status",
) -> None:
    if not criteria_by_file:
        click.echo(f"No requirements found with {filter_label}: {target_value}")
        return

    click.echo(click.style(f"\n{target_value}", bold=True))
    click.echo()

    for path in sorted(criteria_by_file.keys()):
        relative_path = path.relative_to(repo_root).as_posix()
        requirements = sorted(criteria_by_file[path], key=lambda req: str(req.get("id") or "").lower())
        for requirement in requirements:
            crit_id = requirement["id"]
            crit_title = requirement["title"]
            click.echo(f"{relative_path}::{crit_id}: {crit_title}")

    click.echo()


def build_filtered_criteria_payload(
    repo_root: Path,
    criteria_dir: Path,
    criteria_by_file: dict[Path, list[dict[str, object]]],
    target_value: object,
    include_body: bool = True,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    filter_mode: str = "filter-status",
    filter_label: str = "status",
) -> dict[str, object]:
    files_payload: list[dict[str, object]] = []
    total = 0

    for path in sorted(criteria_by_file.keys()):
        relative_path = format_path_display(path, repo_root)
        criteria_payload: list[dict[str, object]] = []
        sub_sections = collect_sub_sections(path, id_prefixes=id_prefixes)
        sorted_requirements = sorted(
            criteria_by_file[path],
            key=lambda req: str(req.get("id") or "").lower(),
        )
        for requirement in sorted_requirements:
            entry: dict[str, object] = {
                "id": str(requirement["id"]),
                "title": str(requirement["title"]),
                "sub_domain": requirement.get("sub_domain"),
            }
            flagged_value = requirement.get("flagged")
            if isinstance(flagged_value, bool):
                entry["flagged"] = flagged_value

            links_value = requirement.get("links")
            if links_value is not None and isinstance(links_value, list):
                entry["links"] = links_value

            if include_body:
                body_markdown, block_start, block_end = extract_requirement_block_with_lines(
                    path,
                    str(requirement["id"]),
                    id_prefixes=id_prefixes,
                )
                lines_payload = {
                    "header": int(requirement.get("header_line") or 0) + 1,
                    "status": int(requirement.get("status_line") or 0) + 1,
                }
                blocked_line = requirement.get("blocked_reason_line")
                if isinstance(blocked_line, int):
                    lines_payload["blocked_reason"] = blocked_line + 1
                deprecated_line = requirement.get("deprecated_reason_line")
                if isinstance(deprecated_line, int):
                    lines_payload["deprecated_reason"] = deprecated_line + 1
                if block_start is not None and block_end is not None:
                    lines_payload["body_start"] = block_start + 1
                    lines_payload["body_end"] = block_end + 1

                entry["body"] = {
                    "markdown": body_markdown,
                    "lines": lines_payload,
                }

            criteria_payload.append(entry)
        domain_scope, domain_body = scope_and_body_from_file(path, id_prefixes=id_prefixes)
        domain_entry: dict[str, object] = {
            "path": relative_path,
            "scope": domain_scope,
            "domain_body": domain_body,
            "requirements": criteria_payload,
            "sub_sections": sub_sections,
        }
        files_payload.append(domain_entry)
        total += len(criteria_payload)

    payload: dict[str, object] = {
        "mode": filter_mode,
        filter_label: target_value,
        "requirements_dir": format_path_display(criteria_dir, repo_root),
        "total": total,
        "files": files_payload,
    }
    if filter_label == "sub_domain":
        payload["sub_domain_match_count"] = total
    return payload


def build_summary_payload(
    repo_root: Path,
    criteria_dir: Path,
    domain_files: list[Path],
    changed_paths: list[Path],
) -> dict[str, object]:
    files_payload: list[dict[str, object]] = []
    totals = {label: 0 for label, _ in STATUS_ORDER}
    changed_set = {path.resolve() for path in changed_paths}

    for path in domain_files:
        counts = count_statuses(path.read_text(encoding="utf-8"))
        for label, _slug in STATUS_ORDER:
            totals[label] += counts[label]

        sub_sections = collect_sub_sections(path)
        scope, domain_body = scope_and_body_from_file(path)
        files_payload.append(
            {
                "path": format_path_display(path, repo_root),
                "display_name": display_name_from_h1(path),
                "scope": scope,
                "domain_body": domain_body,
                "changed": path.resolve() in changed_set,
                "counts": {label: counts[label] for label, _slug in STATUS_ORDER},
                "sub_sections": sub_sections,
            }
        )

    return {
        "mode": "summary",
        "requirements_dir": format_path_display(criteria_dir, repo_root),
        "changed_files": [format_path_display(path, repo_root) for path in changed_paths],
        "totals": totals,
        "files": files_payload,
    }


def build_targeted_criteria_payload(
    repo_root: Path,
    criteria_dir: Path,
    selected_items: list[tuple[Path, dict[str, object]]],
    target_tokens: list[str],
    include_body: bool = True,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> dict[str, object]:
    file_order: list[Path] = []
    file_map: dict[Path, list[dict[str, object]]] = {}

    for path, requirement in selected_items:
        if path not in file_map:
            file_order.append(path)
            file_map[path] = []
        file_map[path].append(requirement)

    files_payload: list[dict[str, object]] = []
    for path in file_order:
        criteria_payload: list[dict[str, object]] = []
        for requirement in file_map[path]:
            entry: dict[str, object] = {
                "id": str(requirement["id"]),
                "title": str(requirement["title"]),
                "sub_domain": requirement.get("sub_domain"),
            }
            flagged_value = requirement.get("flagged")
            if isinstance(flagged_value, bool):
                entry["flagged"] = flagged_value

            links_value = requirement.get("links")
            if links_value is not None and isinstance(links_value, list):
                entry["links"] = links_value

            if include_body:
                body_markdown, block_start, block_end = extract_requirement_block_with_lines(
                    path,
                    str(requirement["id"]),
                    id_prefixes=id_prefixes,
                )
                lines_payload = {
                    "header": int(requirement.get("header_line") or 0) + 1,
                    "status": int(requirement.get("status_line") or 0) + 1,
                }
                if block_start is not None and block_end is not None:
                    lines_payload["body_start"] = block_start + 1
                    lines_payload["body_end"] = block_end + 1
                blocked_line = requirement.get("blocked_reason_line")
                if isinstance(blocked_line, int):
                    lines_payload["blocked_reason"] = blocked_line + 1
                deprecated_line = requirement.get("deprecated_reason_line")
                if isinstance(deprecated_line, int):
                    lines_payload["deprecated_reason"] = deprecated_line + 1
                entry["body"] = {
                    "markdown": body_markdown,
                    "lines": lines_payload,
                }

            criteria_payload.append(entry)

        domain_scope, domain_body = scope_and_body_from_file(path, id_prefixes=id_prefixes)
        files_payload.append(
            {
                "path": format_path_display(path, repo_root),
                "scope": domain_scope,
                "domain_body": domain_body,
                "requirements": criteria_payload,
                "sub_sections": collect_sub_sections(path, id_prefixes=id_prefixes),
            }
        )

    return {
        "mode": "filter-targets",
        "targets": target_tokens,
        "requirements_dir": format_path_display(criteria_dir, repo_root),
        "total": len(selected_items),
        "files": files_payload,
    }


def focused_target_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    selected_items: list[tuple[Path, dict[str, object]]],
    target_tokens: list[str],
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    select_from_menu_fn=select_from_menu,
    resume_filter: bool = True,
    state_dir: str = "system-temp",
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
) -> int:
    if include_status_emojis is None:
        include_status_emojis = infer_include_status_emojis(domain_files)
    repo_hash = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()[:12]
    token_hash = hashlib.sha256(json.dumps(target_tokens, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
    resume_root = resolve_resume_state_dir(repo_root, state_dir)
    resume_path = resume_root / f"filter-targets-resume-{repo_hash}-{token_hash}.json"
    membership = [(path, str(requirement["id"])) for path, requirement in selected_items]

    def load_resume_state() -> dict[str, str]:
        if not resume_path.exists() or not resume_path.is_file():
            return {}
        try:
            loaded = json.loads(resume_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(loaded, dict):
            return {}
        return {
            "id": str(loaded.get("id") or ""),
            "path": str(loaded.get("path") or ""),
        }

    def save_current(flat_items: list[tuple[Path, dict[str, object]]], current_index: int) -> None:
        if not resume_filter or not flat_items:
            return
        idx = min(max(current_index, 0), len(flat_items) - 1)
        cur_path, cur_req = flat_items[idx]
        payload = {
            "path": format_path_display(cur_path, repo_root),
            "id": str(cur_req["id"]),
        }
        try:
            resume_path.parent.mkdir(parents=True, exist_ok=True)
            resume_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            return

    def resolve_resume_index(flat_items: list[tuple[Path, dict[str, object]]]) -> int:
        if not resume_filter or not flat_items:
            return 0
        saved = load_resume_state()
        saved_id = saved.get("id")
        saved_path = saved.get("path")
        for index, (path, req) in enumerate(flat_items):
            if str(req["id"]) == saved_id and format_path_display(path, repo_root) == saved_path:
                click.echo(click.style(f"Resuming focused walk at {saved_id}.", dim=True))
                return index
        return 0

    def build_flat_list() -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        for path, req_id in membership:
            refreshed = find_requirement_by_id(path, req_id, id_prefixes=id_prefixes)
            if refreshed:
                result.append((path, refreshed))
        return result

    flat_list = build_flat_list()
    if not flat_list:
        click.echo("No requirements found for the selected target list.")
        return 0

    click.echo(click.style(
        f"\nFocused walk: {len(flat_list)} requirements from {len(target_tokens)} target token(s)",
        bold=True,
    ))

    index = resolve_resume_index(flat_list)
    current_entry_field = "priority" if priority_mode else "status"
    while True:
        flat_list = build_flat_list()
        if not flat_list:
            click.echo("No more requirements in the selected target list.")
            return 0
        index = min(index, len(flat_list) - 1)
        save_current(flat_list, index)

        path, requirement = flat_list[index]
        click.echo(click.style(f"\n[{index + 1}/{len(flat_list)}]", dim=True))
        print_criterion_panel(path, requirement, repo_root, id_prefixes=id_prefixes)

        action, selected_value = _prompt_for_requirement_action(
            requirement,
            current_entry_field,
            select_from_menu_fn,
            title_suffix=f" [{index + 1}/{len(flat_list)}]",
        )

        if action == "quit":
            save_current(flat_list, index)
            return 0
        if action == "up":
            save_current(flat_list, index)
            return 0
        if action == "toggle-field":
            current_entry_field = _next_entry_field(current_entry_field)
            save_current(flat_list, index)
            continue
        if action == "nav-prev":
            if index > 0:
                index -= 1
            else:
                click.echo("Already at first selected AC.")
            save_current(flat_list, index)
            continue
        if action == "nav-first":
            index = 0
            save_current(flat_list, index)
            continue
        if action == "nav-last":
            index = len(flat_list) - 1
            save_current(flat_list, index)
            continue
        if action == "nav-next":
            if index < len(flat_list) - 1:
                index += 1
            else:
                click.echo("End of selected list, wrapping to first.")
                index = 0
            save_current(flat_list, index)
            continue

        if current_entry_field == "priority":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_priority=selected_value,
            )
        elif current_entry_field == "flagged":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_flagged=(selected_value == "true"),
            )
        elif current_entry_field == "links":
            changed = prompt_for_links_flow(path, requirement, id_prefixes=id_prefixes)
        else:
            new_status = selected_value or str(requirement.get("status") or "")
            blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None
            changed = update_criterion_status(
                path,
                requirement,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )

        process_file(
            path,
            check_only=False,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )

        if changed:
            click.echo(f"Updated {requirement['id']} -> {selected_value}")
        else:
            click.echo(f"No change for {requirement['id']} ({selected_value})")

        _, table_rows = collect_summary_rows(
            domain_files,
            check_only=True,
            display_name_fn=display_name_from_h1,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )
        print_summary_table(table_rows, emoji_columns=emoji_columns)

        if index < len(flat_list) - 1:
            index += 1
        else:
            index = 0
        save_current(flat_list, index)


def interactive_update_loop(
    repo_root: Path,
    criteria_dir: str,
    domain_files: list[Path],
    emoji_columns: bool,
    sort_files: bool,
    sort_strategy: str = "standard",
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    select_from_menu_fn=select_from_menu,
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
    initial_file_path: Path | None = None,
    zebra_bg: str | None = None,
) -> int:
    """Run the interactive file/requirement/status selection and update loop.

    Provides a multi-level menu interface:
    1. Select a domain file
    2. Select a requirement from the file
    3. Select/confirm a new status and optional reason
    4. Repeat or exit

    Args:
        repo_root: Root path of the project.
        criteria_dir: Path to the requirements directory.
        domain_files: List of domain file paths.
        emoji_columns: If True, show emoji in file stat columns.
        sort_files: If True, enable sorting toggle in file menu.
        sort_strategy: Sort strategy name (e.g., 'standard', 'status-focus').
        id_prefixes: Allowed ID prefixes for matching headers.
        select_from_menu_fn: Menu selection function (injectable for testing).
        include_status_emojis: If True, include emoji in status labels (auto-inferred if None).
        priority_mode: If True, include priority tracking and summary.
        include_priority_summary: If True, include priority counts in summary blocks.
        initial_file_path: If provided, open this file on first iteration (skip file menu).

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    if include_status_emojis is None:
        include_status_emojis = infer_include_status_emojis(domain_files)
    strategy = get_sort_strategy_spec(sort_strategy)
    file_columns = list(FILE_SORT_COLUMNS)
    criterion_columns = list(CRITERION_SORT_COLUMNS)
    current_file_sort_key = str(strategy["file_default_key"])
    current_file_sort_ascending = bool(strategy["file_default_ascending"])
    ordered_paths = [path.resolve() for path in domain_files]
    force_rescan = True
    pending_initial_file = initial_file_path.resolve() if isinstance(initial_file_path, Path) else None
    file_menu_selected_index = 0

    while True:
        if force_rescan:
            scanned_paths = [path.resolve() for path in iter_domain_files(repo_root, criteria_dir)]
            file_rows_for_sort: list[tuple[Path, dict[str, int], str]] = []
            for path in scanned_paths:
                counts = count_statuses(path.read_text(encoding="utf-8"))
                label = display_name_from_h1(path)
                file_rows_for_sort.append((path, counts, label))

            file_rows_for_sort = _sort_file_rows(
                file_rows_for_sort,
                current_file_sort_key,
                current_file_sort_ascending,
            )

            ordered_paths = [row[0] for row in file_rows_for_sort]
            force_rescan = False

        existing_paths = [path for path in ordered_paths if path.exists() and path.is_file()]
        if not existing_paths:
            click.echo("No requirement markdown files found.")
            return 1

        file_rows: list[tuple[Path, dict[str, int], str]] = []
        for path in existing_paths:
            counts = count_statuses(path.read_text(encoding="utf-8"))
            label = display_name_from_h1(path)
            file_rows.append((path, counts, label))

        file_options = [
            right_align_menu_suffix(label, _build_file_rollup_text(path, counts), index_width=1)
            for path, counts, label in file_rows
        ]

        selected_path: Path | None = None
        if pending_initial_file is not None:
            initial_match = next((path for path, _counts, _label in file_rows if path.resolve() == pending_initial_file), None)
            if initial_match is not None:
                selected_path = initial_match
            pending_initial_file = None

        if selected_path is None:
            file_choice = select_from_menu_fn(
                _build_file_sort_title(
                    "Select file",
                    active_key=current_file_sort_key,
                    ascending=current_file_sort_ascending,
                    columns=file_columns,
                    emoji_columns=emoji_columns,
                ),
                file_options,
                repeat_choice_right=True,
                zebra=True,
                zebra_bg=zebra_bg,
                extra_keys={
                    MENU_TOGGLE_SORT: "cycle-sort",
                    "S": "cycle-sort-backward",
                    MENU_TOGGLE_DIRECTION: "toggle-direction",
                    MENU_REFRESH: "refresh",
                },
                footer_legend=_build_sort_footer(current_file_sort_ascending),
                selected_option_index=file_menu_selected_index,
            )
            if file_choice is None:
                return 0
            if file_choice == "up":
                continue
            if file_choice == "cycle-sort":
                current_file_sort_key = _cycle_sort_key(current_file_sort_key, file_columns, wrap_to_first=True) or "name"
                current_file_sort_ascending = False
                force_rescan = True
                mode = current_file_sort_key
                click.echo(f"Select file sort: {mode} ({'asc' if current_file_sort_ascending else 'dsc'})")
                continue
            if file_choice == "cycle-sort-backward":
                current_file_sort_key = _cycle_sort_key(
                    current_file_sort_key,
                    file_columns,
                    wrap_to_first=True,
                    reverse=True,
                ) or "name"
                current_file_sort_ascending = False
                force_rescan = True
                mode = current_file_sort_key
                click.echo(f"Select file sort: {mode} ({'asc' if current_file_sort_ascending else 'dsc'})")
                continue
            if file_choice == "toggle-direction":
                current_file_sort_ascending = not current_file_sort_ascending
                force_rescan = True
                click.echo(f"Select file direction: {'asc' if current_file_sort_ascending else 'dsc'}")
                continue
            if isinstance(file_choice, str) and file_choice.startswith("refresh"):
                refresh_index = _refresh_index_from_choice(file_choice)
                if refresh_index is not None and file_rows:
                    file_menu_selected_index = min(max(refresh_index, 0), len(file_rows) - 1)
                force_rescan = True
                click.echo("Select file refreshed.")
                continue

            file_menu_selected_index = int(file_choice)
            selected_path = file_rows[int(file_choice)][0]

        criterion_default_key = strategy["criterion_default_key"]
        current_criterion_sort_key: str | None = str(criterion_default_key) if criterion_default_key is not None else None
        current_criterion_sort_ascending = bool(strategy["criterion_default_ascending"])

        history: list[int] = []
        history_pos = -1
        criterion_index: int | None = None
        criterion_menu_selected_index = 0
        current_entry_field = "priority" if priority_mode else "status"

        while True:
            raw_criteria = parse_requirements(selected_path, id_prefixes=id_prefixes)
            requirements = _sort_criteria(
                raw_criteria,
                current_criterion_sort_key,
                current_criterion_sort_ascending,
            )

            if criterion_index is None:
                term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
                criterion_right_labels = [str(c["id"]) for c in requirements]
                criterion_options = [
                    style_status_line(str(c["status"]), truncate_text(
                        f"{str(c.get('priority') or '⚪').split(' ', 1)[0]} {status_emoji(str(c['status']))} {c['title']}",
                        max(8, term_width - 5 - visible_length(str(c["id"])) - 2),
                    ))
                    for c in requirements
                ]
                criterion_choice = select_from_menu_fn(
                    _build_criterion_sort_title(
                        f"Select requirement in {selected_path.relative_to(repo_root).as_posix()}",
                        active_key=current_criterion_sort_key,
                        ascending=current_criterion_sort_ascending,
                    ),
                    criterion_options,
                    zebra=True,
                    zebra_bg=zebra_bg,
                    option_right_labels=criterion_right_labels,
                    extra_keys={
                        MENU_TOGGLE_SORT: "cycle-sort",
                        "S": "cycle-sort-backward",
                        MENU_TOGGLE_DIRECTION: "toggle-direction",
                        MENU_REFRESH: "refresh",
                        "g": "jump-subsection",
                    },
                    extra_keys_help={
                        "g": "jump-sub",
                    },
                    footer_legend=_build_sort_footer(current_criterion_sort_ascending),
                    selected_option_index=criterion_menu_selected_index,
                )
                if criterion_choice is None:
                    return 0
                if criterion_choice == "up":
                    break
                if criterion_choice == "cycle-sort":
                    current_criterion_sort_key = _cycle_sort_key(
                        current_criterion_sort_key,
                        criterion_columns,
                        wrap_to_first=bool(strategy["criterion_cycle_wrap"]),
                    )
                    current_criterion_sort_ascending = False
                    click.echo(f"Requirement sort: {current_criterion_sort_key or 'document'} (dsc)")
                    continue
                if criterion_choice == "cycle-sort-backward":
                    current_criterion_sort_key = _cycle_sort_key(
                        current_criterion_sort_key,
                        criterion_columns,
                        wrap_to_first=bool(strategy["criterion_cycle_wrap"]),
                        reverse=True,
                    )
                    current_criterion_sort_ascending = False
                    click.echo(f"Requirement sort: {current_criterion_sort_key or 'document'} (dsc)")
                    continue
                if criterion_choice == "toggle-direction":
                    current_criterion_sort_ascending = not current_criterion_sort_ascending
                    click.echo(f"Requirement direction: {'asc' if current_criterion_sort_ascending else 'dsc'}")
                    continue
                if isinstance(criterion_choice, str) and criterion_choice.startswith("refresh"):
                    refresh_index = _refresh_index_from_choice(criterion_choice)
                    if refresh_index is not None and requirements:
                        criterion_menu_selected_index = min(max(refresh_index, 0), len(requirements) - 1)
                    click.echo("Requirement list refreshed.")
                    continue
                if criterion_choice == "jump-subsection":
                    query = click.prompt(
                        "Subsection prefix to jump to",
                        default="",
                        show_default=False,
                    ).strip()
                    normalized_query = normalize_sub_domain_name(query)
                    if not normalized_query:
                        click.echo("Jump cancelled (empty subsection prefix).")
                        continue
                    jump_index = next(
                        (
                            idx
                            for idx, requirement in enumerate(requirements)
                            if normalize_sub_domain_name(requirement.get("sub_domain")).startswith(normalized_query)
                        ),
                        None,
                    )
                    if jump_index is None:
                        click.echo(f"No subsection match for: {query}")
                        continue

                    criterion_index = jump_index
                    del history[history_pos + 1:]
                    history.append(criterion_index)
                    history_pos = len(history) - 1
                    continue

                criterion_index = int(criterion_choice)
                criterion_menu_selected_index = criterion_index
                del history[history_pos + 1:]
                history.append(criterion_index)
                history_pos = len(history) - 1

            selected_criterion = requirements[criterion_index] if criterion_index < len(requirements) else requirements[-1]
            refreshed = next((c for c in requirements if str(c["id"]) == str(selected_criterion["id"])), None)
            if refreshed:
                selected_criterion = refreshed
                criterion_index = requirements.index(refreshed)

            print_criterion_panel(selected_path, selected_criterion, repo_root, id_prefixes=id_prefixes)

            action, selected_value = _prompt_for_requirement_action(
                selected_criterion,
                current_entry_field,
                select_from_menu_fn,
            )
            if action == "quit":
                return 0
            if action == "up":
                criterion_index = None
                continue
            if action == "toggle-field":
                current_entry_field = _next_entry_field(current_entry_field)
                continue
            if action == "nav-prev":
                if history_pos > 0:
                    history_pos -= 1
                    criterion_index = history[history_pos]
                else:
                    click.echo("Already at first requirement.")
                continue
            if action == "nav-next":
                if history_pos < len(history) - 1:
                    history_pos += 1
                    criterion_index = history[history_pos]
                elif criterion_index < len(requirements) - 1:
                    criterion_index += 1
                    del history[history_pos + 1:]
                    history.append(criterion_index)
                    history_pos = len(history) - 1
                else:
                    click.echo("Already at last requirement in file.")
                continue

            changed = False
            if current_entry_field == "priority":
                changed = update_criterion_status(
                    selected_path,
                    selected_criterion,
                    str(selected_criterion.get("status") or ""),
                    new_priority=selected_value,
                )
                process_file(
                    selected_path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=include_priority_summary,
                )
            elif current_entry_field == "flagged":
                changed = update_criterion_status(
                    selected_path,
                    selected_criterion,
                    str(selected_criterion.get("status") or ""),
                    new_flagged=(selected_value == "true"),
                )
                process_file(
                    selected_path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=include_priority_summary,
                )
            elif current_entry_field == "links":
                changed = prompt_for_links_flow(
                    selected_path,
                    selected_criterion,
                    id_prefixes=id_prefixes,
                )
                process_file(
                    selected_path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=include_priority_summary,
                )
            else:
                new_status = selected_value or str(selected_criterion.get("status") or "")
                blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
                deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

                changed = update_criterion_status(
                    selected_path,
                    selected_criterion,
                    new_status,
                    blocked_reason=blocked_reason,
                    deprecated_reason=deprecated_reason,
                )
                process_file(
                    selected_path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=include_priority_summary,
                )

            if changed:
                click.echo(f"Updated {selected_criterion['id']} -> {selected_value}")
            else:
                click.echo(f"No change for {selected_criterion['id']} ({selected_value})")

            _, table_rows = collect_summary_rows(
                domain_files,
                check_only=True,
                display_name_fn=display_name_from_h1,
                include_status_emojis=include_status_emojis,
                include_priority_summary=include_priority_summary,
            )
            print_summary_table(table_rows, emoji_columns=emoji_columns)

            raw_criteria_after = parse_requirements(selected_path, id_prefixes=id_prefixes)
            criteria_after = _sort_criteria(
                raw_criteria_after,
                current_criterion_sort_key,
                current_criterion_sort_ascending,
            )
            cur_id = str(selected_criterion["id"])
            new_idx = next((i for i, c in enumerate(criteria_after) if str(c["id"]) == cur_id), criterion_index)
            if new_idx < len(criteria_after) - 1:
                criterion_index = new_idx + 1
                del history[history_pos + 1:]
                history.append(criterion_index)
                history_pos = len(history) - 1
            else:
                if criteria_after:
                    criterion_index = 0
                    del history[history_pos + 1:]
                    history.append(criterion_index)
                    history_pos = len(history) - 1
                else:
                    criterion_index = None
                continue


def filtered_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    target_status: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    select_from_menu_fn=select_from_menu,
    resume_filter: bool = True,
    state_dir: str = "system-temp",
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
) -> int:
    if include_status_emojis is None:
        include_status_emojis = infer_include_status_emojis(domain_files)
    repo_hash = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()[:12]
    resume_root = resolve_resume_state_dir(repo_root, state_dir)
    resume_path = resume_root / f"filter-resume-{repo_hash}.json"

    def load_resume_state() -> dict[str, dict[str, str]]:
        if not resume_path.exists() or not resume_path.is_file():
            return {}
        try:
            loaded = json.loads(resume_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(loaded, dict):
            return {}
        normalized: dict[str, dict[str, str]] = {}
        for key, value in loaded.items():
            if isinstance(key, str) and isinstance(value, dict):
                req_id = value.get("id")
                req_path = value.get("path")
                if isinstance(req_id, str) and isinstance(req_path, str):
                    normalized[key] = {"id": req_id, "path": req_path}
        return normalized

    def save_resume_state(state: dict[str, dict[str, str]]) -> None:
        try:
            resume_path.parent.mkdir(parents=True, exist_ok=True)
            resume_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            return

    def state_key() -> str:
        return target_status

    def save_current(flat_items: list[tuple[Path, dict[str, object]]], current_index: int) -> None:
        if not resume_filter or not flat_items:
            return
        idx = min(max(current_index, 0), len(flat_items) - 1)
        cur_path, cur_req = flat_items[idx]
        state = load_resume_state()
        state[state_key()] = {
            "path": format_path_display(cur_path, repo_root),
            "id": str(cur_req["id"]),
        }
        save_resume_state(state)

    def resolve_resume_index(flat_items: list[tuple[Path, dict[str, object]]]) -> int:
        if not resume_filter or not flat_items:
            return 0
        state = load_resume_state()
        saved = state.get(state_key())
        if not saved:
            return 0
        saved_id = saved.get("id")
        saved_path = saved.get("path")
        for i, (path, req) in enumerate(flat_items):
            if str(req["id"]) == saved_id and format_path_display(path, repo_root) == saved_path:
                click.echo(click.style(f"Resuming filtered walk at {saved_id}.", dim=True))
                return i
        return 0

    def build_flat_list() -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        for path in domain_files:
            for crit in parse_requirements(path, id_prefixes=id_prefixes):
                if crit["status"] == target_status:
                    result.append((path, crit))
        return result

    flat_list = build_flat_list()
    if not flat_list:
        click.echo(f"No requirements found with status: {target_status}")
        return 0

    click.echo(click.style(
        f"\nFiltered walk: {target_status} ({len(flat_list)} requirements across all files)",
        bold=True,
    ))

    index = resolve_resume_index(flat_list)
    current_entry_field = "priority" if priority_mode else "status"
    while True:
        flat_list = build_flat_list()
        if not flat_list:
            click.echo("No more requirements with this status.")
            return 0
        index = min(index, len(flat_list) - 1)
        save_current(flat_list, index)

        path, requirement = flat_list[index]
        refreshed = find_requirement_by_id(path, str(requirement["id"]), id_prefixes=id_prefixes)
        if refreshed:
            requirement = refreshed

        click.echo(click.style(f"\n[{index + 1}/{len(flat_list)}]", dim=True))
        print_criterion_panel(path, requirement, repo_root, id_prefixes=id_prefixes)

        action, selected_value = _prompt_for_requirement_action(
            requirement,
            current_entry_field,
            select_from_menu_fn,
            title_suffix=f" [{index + 1}/{len(flat_list)}]",
        )

        if action == "quit":
            save_current(flat_list, index)
            return 0
        if action == "up":
            save_current(flat_list, index)
            return 0
        if action == "toggle-field":
            current_entry_field = _next_entry_field(current_entry_field)
            save_current(flat_list, index)
            continue
        if action == "nav-prev":
            if index > 0:
                index -= 1
            else:
                click.echo("Already at first filtered AC.")
            save_current(flat_list, index)
            continue
        if action == "nav-first":
            index = 0
            save_current(flat_list, index)
            continue
        if action == "nav-last":
            index = len(flat_list) - 1
            save_current(flat_list, index)
            continue
        if action == "nav-next":
            if index < len(flat_list) - 1:
                index += 1
            else:
                click.echo(f"No more {target_status} requirements.")
                save_current(flat_list, index)
                continue
            save_current(flat_list, index)
            continue

        if current_entry_field == "priority":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_priority=selected_value,
            )
        elif current_entry_field == "flagged":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_flagged=(selected_value == "true"),
            )
        elif current_entry_field == "links":
            changed = prompt_for_links_flow(path, requirement, id_prefixes=id_prefixes)
        else:
            new_status = selected_value or str(requirement.get("status") or "")
            blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

            changed = update_criterion_status(
                path,
                requirement,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )
        process_file(
            path,
            check_only=False,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )

        if changed:
            click.echo(f"Updated {requirement['id']} -> {selected_value}")
        else:
            click.echo(f"No change for {requirement['id']} ({selected_value})")

        _, table_rows = collect_summary_rows(
            domain_files,
            check_only=True,
            display_name_fn=display_name_from_h1,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )
        print_summary_table(table_rows, emoji_columns=emoji_columns)

        flat_after = build_flat_list()
        if current_entry_field == "status" and changed and selected_value != target_status:
            if not flat_after:
                click.echo("All filtered requirements reviewed.")
                return 0


def filtered_priority_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    target_priority: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    select_from_menu_fn=select_from_menu,
    resume_filter: bool = True,
    state_dir: str = "system-temp",
    include_status_emojis: bool | None = None,
    priority_mode: bool = True,
    include_priority_summary: bool = False,
) -> int:
    if include_status_emojis is None:
        include_status_emojis = infer_include_status_emojis(domain_files)
    repo_hash = hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()[:12]
    resume_root = resolve_resume_state_dir(repo_root, state_dir)
    resume_path = resume_root / f"filter-priority-resume-{repo_hash}.json"

    def load_resume_state() -> dict[str, dict[str, str]]:
        if not resume_path.exists() or not resume_path.is_file():
            return {}
        try:
            loaded = json.loads(resume_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(loaded, dict):
            return {}
        normalized: dict[str, dict[str, str]] = {}
        for key, value in loaded.items():
            if isinstance(key, str) and isinstance(value, dict):
                req_id = value.get("id")
                req_path = value.get("path")
                if isinstance(req_id, str) and isinstance(req_path, str):
                    normalized[key] = {"id": req_id, "path": req_path}
        return normalized

    def save_resume_state(state: dict[str, dict[str, str]]) -> None:
        try:
            resume_path.parent.mkdir(parents=True, exist_ok=True)
            resume_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            return

    def state_key() -> str:
        return target_priority

    def save_current(flat_items: list[tuple[Path, dict[str, object]]], current_index: int) -> None:
        if not resume_filter or not flat_items:
            return
        idx = min(max(current_index, 0), len(flat_items) - 1)
        cur_path, cur_req = flat_items[idx]
        state = load_resume_state()
        state[state_key()] = {
            "path": format_path_display(cur_path, repo_root),
            "id": str(cur_req["id"]),
        }
        save_resume_state(state)

    def resolve_resume_index(flat_items: list[tuple[Path, dict[str, object]]]) -> int:
        if not resume_filter or not flat_items:
            return 0
        state = load_resume_state()
        saved = state.get(state_key())
        if not saved:
            return 0
        saved_id = saved.get("id")
        saved_path = saved.get("path")
        for index, (path, req) in enumerate(flat_items):
            if str(req["id"]) == saved_id and format_path_display(path, repo_root) == saved_path:
                click.echo(click.style(f"Resuming filtered walk at {saved_id}.", dim=True))
                return index
        return 0

    def build_flat_list() -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        for path in domain_files:
            for crit in parse_requirements(path, id_prefixes=id_prefixes):
                if crit.get("priority") == target_priority:
                    result.append((path, crit))
        return result

    flat_list = build_flat_list()
    if not flat_list:
        click.echo(f"No requirements found with priority: {target_priority}")
        return 0

    click.echo(click.style(
        f"\nFiltered walk: {target_priority} ({len(flat_list)} requirements across all files)",
        bold=True,
    ))

    index = resolve_resume_index(flat_list)
    current_entry_field = "priority" if priority_mode else "status"
    while True:
        flat_list = build_flat_list()
        if not flat_list:
            click.echo("No more requirements with this priority.")
            return 0
        index = min(index, len(flat_list) - 1)
        save_current(flat_list, index)

        path, requirement = flat_list[index]
        refreshed = find_requirement_by_id(path, str(requirement["id"]), id_prefixes=id_prefixes)
        if refreshed:
            requirement = refreshed

        click.echo(click.style(f"\n[{index + 1}/{len(flat_list)}]", dim=True))
        print_criterion_panel(path, requirement, repo_root, id_prefixes=id_prefixes)

        action, selected_value = _prompt_for_requirement_action(
            requirement,
            current_entry_field,
            select_from_menu_fn,
            title_suffix=f" [{index + 1}/{len(flat_list)}]",
        )

        if action == "quit":
            save_current(flat_list, index)
            return 0
        if action == "up":
            save_current(flat_list, index)
            return 0
        if action == "toggle-field":
            current_entry_field = _next_entry_field(current_entry_field)
            save_current(flat_list, index)
            continue
        if action == "nav-prev":
            if index > 0:
                index -= 1
            else:
                click.echo("Already at first filtered AC.")
            save_current(flat_list, index)
            continue
        if action == "nav-first":
            index = 0
            save_current(flat_list, index)
            continue
        if action == "nav-last":
            index = len(flat_list) - 1
            save_current(flat_list, index)
            continue
        if action == "nav-next":
            if index < len(flat_list) - 1:
                index += 1
            else:
                click.echo(f"No more {target_priority} requirements.")
                save_current(flat_list, index)
                continue
            save_current(flat_list, index)
            continue

        if current_entry_field == "priority":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_priority=selected_value,
            )
        elif current_entry_field == "flagged":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_flagged=(selected_value == "true"),
            )
        elif current_entry_field == "links":
            changed = prompt_for_links_flow(path, requirement, id_prefixes=id_prefixes)
        else:
            new_status = selected_value or str(requirement.get("status") or "")
            blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

            changed = update_criterion_status(
                path,
                requirement,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )
        process_file(
            path,
            check_only=False,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )

        if changed:
            click.echo(f"Updated {requirement['id']} -> {selected_value}")
        else:
            click.echo(f"No change for {requirement['id']} ({selected_value})")

        _, table_rows = collect_summary_rows(
            domain_files,
            check_only=True,
            display_name_fn=display_name_from_h1,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )
        print_summary_table(table_rows, emoji_columns=emoji_columns)

        flat_after = build_flat_list()
        if current_entry_field == "priority" and changed and selected_value != target_priority:
            if not flat_after:
                click.echo("All filtered requirements reviewed.")
                return 0
            index = min(index, len(flat_after) - 1)
            save_current(flat_after, index)
        else:
            if flat_after and index < len(flat_after) - 1:
                index += 1
                save_current(flat_after, index)
            elif flat_after:
                click.echo("End of filtered list, wrapping to first.")
                index = 0
                save_current(flat_after, index)
            else:
                click.echo("All filtered requirements reviewed.")
                return 0


def lookup_criterion_interactive(
    repo_root: Path,
    domain_files: list[Path],
    requirement_id: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    select_from_menu_fn=select_from_menu,
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
) -> int:
    if include_status_emojis is None:
        include_status_emojis = infer_include_status_emojis(domain_files)
    requirement_id = requirement_id.strip().upper()
    matches: list[tuple[Path, dict[str, object]]] = []
    for path in domain_files:
        crit = find_requirement_by_id(path, requirement_id, id_prefixes=id_prefixes)
        if crit:
            matches.append((path, crit))

    if not matches:
        raise click.ClickException(f"Requirement '{requirement_id}' not found in the configured docs.")

    if len(matches) > 1:
        locs = ", ".join(p.relative_to(repo_root).as_posix() for p, _ in matches)
        raise click.ClickException(
            f"Requirement '{requirement_id}' found in multiple files: {locs}. Use --scope-file to disambiguate."
        )

    path, requirement = matches[0]

    current_entry_field = "priority" if priority_mode else "status"

    while True:
        refreshed = find_requirement_by_id(path, requirement_id, id_prefixes=id_prefixes)
        if refreshed:
            requirement = refreshed

        print_criterion_panel(path, requirement, repo_root, id_prefixes=id_prefixes)

        action, selected_value = _prompt_for_requirement_action(
            requirement,
            current_entry_field,
            select_from_menu_fn,
            allow_nav=False,
        )

        if action in {"quit", "up"}:
            return 0

        if action == "toggle-field":
            current_entry_field = _next_entry_field(current_entry_field)
            continue

        if current_entry_field == "priority":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_priority=selected_value,
            )
        elif current_entry_field == "flagged":
            changed = update_criterion_status(
                path,
                requirement,
                str(requirement.get("status") or ""),
                new_flagged=(selected_value == "true"),
            )
        elif current_entry_field == "links":
            changed = prompt_for_links_flow(path, requirement, id_prefixes=id_prefixes)
        else:
            new_status = selected_value or str(requirement.get("status") or "")
            blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

            changed = update_criterion_status(
                path,
                requirement,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )
        process_file(
            path,
            check_only=False,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )

        if changed:
            click.echo(f"Updated {requirement['id']} -> {selected_value}")
        else:
            click.echo(f"No change for {requirement['id']} ({selected_value})")

        _, table_rows = collect_summary_rows(
            domain_files,
            check_only=True,
            display_name_fn=display_name_from_h1,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )
        print_summary_table(table_rows, emoji_columns=emoji_columns)
        return 0
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

            changed = update_criterion_status(
                path,
                requirement,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )
        process_file(
            path,
            check_only=False,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )

        if changed:
            click.echo(f"Updated {requirement['id']} -> {selected_value}")
        else:
            click.echo(f"No change for {requirement['id']} ({selected_value})")

        _, table_rows = collect_summary_rows(
            domain_files,
            check_only=True,
            display_name_fn=display_name_from_h1,
            include_status_emojis=include_status_emojis,
            include_priority_summary=include_priority_summary,
        )
        print_summary_table(table_rows, emoji_columns=emoji_columns)
        return 0
