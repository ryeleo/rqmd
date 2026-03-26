from __future__ import annotations

import shutil
import sys
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from .constants import DEFAULT_ID_PREFIXES, STATUS_ORDER
from .criteria_parser import find_criterion_by_id, parse_criteria
from .markdown_io import (display_name_from_h1, format_path_display,
                          iter_domain_files)
from .menus import (file_sort_key_by_priority, right_align_menu_suffix,
                    select_from_menu, truncate_text, visible_length)
from .status_model import (build_color_rollup_text, status_emoji,
                           style_status_label, style_status_line)
from .status_update import (print_criterion_panel, prompt_for_blocked_reason,
                            prompt_for_deprecated_reason,
                            update_criterion_status)
from .summary import (collect_summary_rows, count_statuses,
                      print_summary_table, process_file)


def print_criteria_tree(repo_root: Path, criteria_by_file: dict[Path, list[dict[str, object]]], target_status: str) -> None:
    if not criteria_by_file:
        click.echo(f"No criteria found with status: {target_status}")
        return

    click.echo(click.style(f"\n{target_status}", bold=True))
    click.echo()

    files = sorted(criteria_by_file.keys())
    for file_idx, path in enumerate(files):
        is_last_file = file_idx == len(files) - 1
        file_prefix = "└── " if is_last_file else "├── "
        relative_path = path.relative_to(repo_root)
        click.echo(f"{file_prefix}{click.style(relative_path.as_posix(), dim=True)}")

        criteria = criteria_by_file[path]
        for crit_idx, criterion in enumerate(criteria):
            is_last_crit = crit_idx == len(criteria) - 1
            crit_prefix = "    " if is_last_file else "│   "
            branch = "└── " if is_last_crit else "├── "
            crit_id = criterion["id"]
            crit_title = criterion["title"]
            click.echo(f"{crit_prefix}{branch}{crit_id}: {crit_title}")

    click.echo()


def build_filtered_criteria_payload(
    repo_root: Path,
    criteria_dir: Path,
    criteria_by_file: dict[Path, list[dict[str, object]]],
    target_status: str,
) -> dict[str, object]:
    files_payload: list[dict[str, object]] = []
    total = 0

    for path in sorted(criteria_by_file.keys()):
        relative_path = format_path_display(path, repo_root)
        criteria_payload: list[dict[str, str]] = []
        for criterion in criteria_by_file[path]:
            criteria_payload.append(
                {
                    "id": str(criterion["id"]),
                    "title": str(criterion["title"]),
                }
            )
        files_payload.append({"path": relative_path, "criteria": criteria_payload})
        total += len(criteria_payload)

    return {
        "mode": "filter-status",
        "status": target_status,
        "criteria_dir": format_path_display(criteria_dir, repo_root),
        "total": total,
        "files": files_payload,
    }


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

        files_payload.append(
            {
                "path": format_path_display(path, repo_root),
                "display_name": display_name_from_h1(path),
                "changed": path.resolve() in changed_set,
                "counts": {label: counts[label] for label, _slug in STATUS_ORDER},
            }
        )

    return {
        "mode": "summary",
        "criteria_dir": format_path_display(criteria_dir, repo_root),
        "changed_files": [format_path_display(path, repo_root) for path in changed_paths],
        "totals": totals,
        "files": files_payload,
    }


def interactive_update_loop(
    repo_root: Path,
    criteria_dir: str,
    domain_files: list[Path],
    emoji_columns: bool,
    sort_files: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    select_from_menu_fn=select_from_menu,
) -> int:
    current_sort_files = sort_files
    ordered_paths = [path.resolve() for path in domain_files]
    force_rescan = True

    while True:
        if force_rescan:
            scanned_paths = [path.resolve() for path in iter_domain_files(repo_root, criteria_dir)]
            file_rows_for_sort: list[tuple[Path, dict[str, int], str]] = []
            for path in scanned_paths:
                counts = count_statuses(path.read_text(encoding="utf-8"))
                label = display_name_from_h1(path)
                file_rows_for_sort.append((path, counts, label))

            if current_sort_files:
                file_rows_for_sort.sort(key=lambda row: file_sort_key_by_priority(row[1], row[2]))

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
            right_align_menu_suffix(label, build_color_rollup_text(counts), index_width=1)
            for _, counts, label in file_rows
        ]

        file_choice = select_from_menu_fn(
            "Select file",
            file_options,
            repeat_choice_right=True,
            zebra=True,
            extra_key="s",
            extra_key_help="toggle-sort+rescan",
            extra_key_return="toggle-sort",
        )
        if file_choice is None:
            return 0
        if file_choice == "up":
            continue
        if file_choice == "toggle-sort":
            current_sort_files = not current_sort_files
            force_rescan = True
            mode = "sorted" if current_sort_files else "unsorted"
            click.echo(f"Select file mode: {mode} (rescanned)")
            continue

        selected_path = file_rows[int(file_choice)][0]

        current_sort_criteria = current_sort_files

        def sort_criteria(clist: list[dict[str, object]]) -> list[dict[str, object]]:
            if not current_sort_criteria:
                return clist
            status_priority = {label: i for i, (label, _) in enumerate(STATUS_ORDER)}
            return sorted(clist, key=lambda c: status_priority.get(str(c["status"]), 99))

        history: list[int] = []
        history_pos = -1
        criterion_index: int | None = None

        while True:
            raw_criteria = parse_criteria(selected_path, id_prefixes=id_prefixes)
            criteria = sort_criteria(raw_criteria)

            if criterion_index is None:
                term_width = shutil.get_terminal_size(fallback=(80, 24)).columns
                criterion_right_labels = [str(c["id"]) for c in criteria]
                criterion_options = [
                    style_status_line(str(c["status"]), truncate_text(
                        f"{status_emoji(str(c['status']))} {c['title']}",
                        max(8, term_width - 5 - visible_length(str(c["id"])) - 2),
                    ))
                    for c in criteria
                ]
                criterion_choice = select_from_menu_fn(
                    f"Select requirement in {selected_path.relative_to(repo_root).as_posix()}",
                    criterion_options,
                    zebra=True,
                    option_right_labels=criterion_right_labels,
                    extra_key="s",
                    extra_key_help="toggle-sort",
                    extra_key_return="toggle-sort",
                )
                if criterion_choice is None:
                    return 0
                if criterion_choice == "up":
                    break
                if criterion_choice == "toggle-sort":
                    current_sort_criteria = not current_sort_criteria
                    click.echo(f"Criterion sort: {'on' if current_sort_criteria else 'off'}")
                    continue

                criterion_index = int(criterion_choice)
                del history[history_pos + 1:]
                history.append(criterion_index)
                history_pos = len(history) - 1

            selected_criterion = criteria[criterion_index] if criterion_index < len(criteria) else criteria[-1]
            refreshed = next((c for c in criteria if str(c["id"]) == str(selected_criterion["id"])), None)
            if refreshed:
                selected_criterion = refreshed
                criterion_index = criteria.index(refreshed)

            print_criterion_panel(selected_path, selected_criterion, repo_root, id_prefixes=id_prefixes)

            status_labels = [label for label, _ in STATUS_ORDER]
            status_options = [style_status_label(label) for label, _ in STATUS_ORDER]
            current_status = str(selected_criterion.get("status") or "")
            try:
                current_status_idx = status_labels.index(current_status)
            except ValueError:
                current_status_idx = None
            highlight_bg = "\x1b[48;5;220m"
            if current_status == "✅ Verified":
                highlight_bg = "\x1b[48;5;28m"
            elif current_status == "💡 Proposed":
                highlight_bg = "\x1b[48;5;27m"
            elif current_status in ("⛔ Blocked", "🗑️ Deprecated"):
                highlight_bg = "\x1b[48;5;238m"

            status_choice = select_from_menu_fn(
                f"Set status for {selected_criterion['id']}",
                status_options,
                show_page_indicator=False,
                allow_paging_nav=False,
                extra_keys={"n": "nav-next", "p": "nav-prev"},
                extra_keys_help={"n": "next", "p": "prev"},
                selected_option_index=current_status_idx,
                selected_option_bg=highlight_bg,
            )
            if status_choice is None:
                return 0
            if status_choice == "up":
                criterion_index = None
                continue
            if status_choice == "nav-prev":
                if history_pos > 0:
                    history_pos -= 1
                    criterion_index = history[history_pos]
                else:
                    click.echo("Already at first requirement.")
                continue
            if status_choice == "nav-next":
                if history_pos < len(history) - 1:
                    history_pos += 1
                    criterion_index = history[history_pos]
                elif criterion_index < len(criteria) - 1:
                    criterion_index += 1
                    del history[history_pos + 1:]
                    history.append(criterion_index)
                    history_pos = len(history) - 1
                else:
                    click.echo("Already at last requirement in file.")
                continue

            new_status = status_labels[int(status_choice)]
            blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
            deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

            changed = update_criterion_status(
                selected_path,
                selected_criterion,
                new_status,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
            )
            process_file(selected_path, check_only=False)

            if changed:
                click.echo(f"Updated {selected_criterion['id']} -> {new_status}")
            else:
                click.echo(f"No change for {selected_criterion['id']} ({new_status})")

            _, table_rows = collect_summary_rows(domain_files, check_only=True, display_name_fn=display_name_from_h1)
            print_summary_table(table_rows, emoji_columns=emoji_columns)

            raw_criteria_after = parse_criteria(selected_path, id_prefixes=id_prefixes)
            criteria_after = sort_criteria(raw_criteria_after)
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
) -> int:
    def build_flat_list() -> list[tuple[Path, dict[str, object]]]:
        result: list[tuple[Path, dict[str, object]]] = []
        for path in domain_files:
            for crit in parse_criteria(path, id_prefixes=id_prefixes):
                if crit["status"] == target_status:
                    result.append((path, crit))
        return result

    flat_list = build_flat_list()
    if not flat_list:
        click.echo(f"No criteria found with status: {target_status}")
        return 0

    click.echo(click.style(
        f"\nFiltered walk: {target_status} ({len(flat_list)} criteria across all files)",
        bold=True,
    ))

    index = 0
    while True:
        flat_list = build_flat_list()
        if not flat_list:
            click.echo("No more criteria with this status.")
            return 0
        index = min(index, len(flat_list) - 1)

        path, criterion = flat_list[index]
        refreshed = find_criterion_by_id(path, str(criterion["id"]), id_prefixes=id_prefixes)
        if refreshed:
            criterion = refreshed

        click.echo(click.style(f"\n[{index + 1}/{len(flat_list)}]", dim=True))
        print_criterion_panel(path, criterion, repo_root, id_prefixes=id_prefixes)

        status_labels = [label for label, _ in STATUS_ORDER]
        status_options = [style_status_label(label) for label, _ in STATUS_ORDER]
        current_status = str(criterion.get("status") or "")
        try:
            current_status_idx = status_labels.index(current_status)
        except ValueError:
            current_status_idx = None

        highlight_bg = "\x1b[48;5;220m"
        if current_status == "\u2705 Verified":
            highlight_bg = "\x1b[48;5;28m"
        elif current_status == "\U0001f4a1 Proposed":
            highlight_bg = "\x1b[48;5;27m"
        elif current_status in ("\u26d4 Blocked", "\U0001f5d1\ufe0f Deprecated"):
            highlight_bg = "\x1b[48;5;238m"

        status_choice = select_from_menu_fn(
            f"Set status for {criterion['id']} [{index + 1}/{len(flat_list)}]",
            status_options,
            show_page_indicator=False,
            allow_paging_nav=False,
            extra_keys={"n": "nav-next", "p": "nav-prev"},
            extra_keys_help={"n": "next", "p": "prev"},
            selected_option_index=current_status_idx,
            selected_option_bg=highlight_bg,
        )

        if status_choice is None:
            return 0
        if status_choice == "up":
            return 0
        if status_choice == "nav-prev":
            if index > 0:
                index -= 1
            else:
                click.echo("Already at first filtered AC.")
            continue
        if status_choice == "nav-next":
            if index < len(flat_list) - 1:
                index += 1
            else:
                click.echo("End of filtered list. All criteria reviewed.")
                return 0
            continue

        new_status = status_labels[int(status_choice)]
        blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
        deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

        changed = update_criterion_status(
            path,
            criterion,
            new_status,
            blocked_reason=blocked_reason,
            deprecated_reason=deprecated_reason,
        )
        process_file(path, check_only=False)

        if changed:
            click.echo(f"Updated {criterion['id']} -> {new_status}")
        else:
            click.echo(f"No change for {criterion['id']} ({new_status})")

        _, table_rows = collect_summary_rows(domain_files, check_only=True, display_name_fn=display_name_from_h1)
        print_summary_table(table_rows, emoji_columns=emoji_columns)

        flat_after = build_flat_list()
        if changed and new_status != target_status:
            if not flat_after:
                click.echo("All filtered criteria reviewed.")
                return 0
            index = min(index, len(flat_after) - 1)
        else:
            if flat_after and index < len(flat_after) - 1:
                index += 1
            elif flat_after:
                click.echo("End of filtered list, wrapping to first.")
                index = 0
            else:
                click.echo("All filtered criteria reviewed.")
                return 0


def lookup_criterion_interactive(
    repo_root: Path,
    domain_files: list[Path],
    criterion_id: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    select_from_menu_fn=select_from_menu,
) -> int:
    criterion_id = criterion_id.strip().upper()
    matches: list[tuple[Path, dict[str, object]]] = []
    for path in domain_files:
        crit = find_criterion_by_id(path, criterion_id, id_prefixes=id_prefixes)
        if crit:
            matches.append((path, crit))

    if not matches:
        raise click.ClickException(f"Requirement '{criterion_id}' not found in the configured docs.")

    if len(matches) > 1:
        locs = ", ".join(p.relative_to(repo_root).as_posix() for p, _ in matches)
        raise click.ClickException(
            f"Criterion '{criterion_id}' found in multiple files: {locs}. Use --file to disambiguate."
        )

    path, criterion = matches[0]

    while True:
        refreshed = find_criterion_by_id(path, criterion_id, id_prefixes=id_prefixes)
        if refreshed:
            criterion = refreshed

        print_criterion_panel(path, criterion, repo_root, id_prefixes=id_prefixes)

        status_labels = [label for label, _ in STATUS_ORDER]
        status_options = [style_status_label(label) for label, _ in STATUS_ORDER]
        current_status = str(criterion.get("status") or "")
        try:
            current_status_idx = status_labels.index(current_status)
        except ValueError:
            current_status_idx = None

        highlight_bg = "\x1b[48;5;220m"
        if current_status == "\u2705 Verified":
            highlight_bg = "\x1b[48;5;28m"
        elif current_status == "\U0001f4a1 Proposed":
            highlight_bg = "\x1b[48;5;27m"
        elif current_status in ("\u26d4 Blocked", "\U0001f5d1\ufe0f Deprecated"):
            highlight_bg = "\x1b[48;5;238m"

        status_choice = select_from_menu_fn(
            f"Set status for {criterion['id']}",
            status_options,
            show_page_indicator=False,
            allow_paging_nav=False,
            selected_option_index=current_status_idx,
            selected_option_bg=highlight_bg,
        )

        if status_choice is None or status_choice == "up":
            return 0

        new_status = status_labels[int(status_choice)]
        blocked_reason = prompt_for_blocked_reason() if "Blocked" in new_status else None
        deprecated_reason = prompt_for_deprecated_reason() if "Deprecated" in new_status else None

        changed = update_criterion_status(
            path,
            criterion,
            new_status,
            blocked_reason=blocked_reason,
            deprecated_reason=deprecated_reason,
        )
        process_file(path, check_only=False)

        if changed:
            click.echo(f"Updated {criterion['id']} -> {new_status}")
        else:
            click.echo(f"No change for {criterion['id']} ({new_status})")

        _, table_rows = collect_summary_rows(domain_files, check_only=True, display_name_fn=display_name_from_h1)
        print_summary_table(table_rows, emoji_columns=emoji_columns)
        return 0
