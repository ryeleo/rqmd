#!/usr/bin/env python

"""Requirements/criteria summary updater and fast interactive status editor.

This tool keeps per-file status summaries synchronized and provides an
optimized, keyboard-driven workflow for updating requirement statuses across a
markdown catalog.

Core behavior:
- Scans all markdown files under a requirements directory.
- Computes status counts from "- **Status:** ..." lines.
- Inserts or updates the summary block between:
    <!-- acceptance-status-summary:start -->
    <!-- acceptance-status-summary:end -->
- Supports both batch/check mode and interactive status editing.

Interactive workflow highlights:
- Select file, then requirement, then status.
- Fast single-key input via click.getchar() for menu navigation.
- Paging keys:
    n = next page, p = previous page, u = up, q = quit.
- Requirement-level next/prev shortcuts at status menu:
    n = next requirement, p = previous requirement (history-aware).
- Optional sort toggles (s) at file and requirement selection levels.
- Optional blocked/deprecated reason prompts when setting those statuses.

Status model:
- 💡 Proposed
- 🔧 Implemented
- ✅ Verified
- ⛔ Blocked
- 🗑️ Deprecated

Non-interactive usage:
- Update a single requirement by id/status (optionally scoped by file).
- Update multiple requirements in one command via repeated --set ID=STATUS.
- Useful for automation and agent-driven workflows.

Examples:
- Check only (no writes):
    rqmd --check
- Interactive mode with emoji headers:
    rqmd --emoji-columns
- Non-interactive single update:
    rqmd \
            --set-criterion-id R-TELEMETRY-LOG-001 \
            --set-status implemented
- Non-interactive bulk update:
    rqmd \
            --set R-STEELTARGET-AUDIO-004=implemented \
            --set R-STEELTARGET-AUDIO-005=verified
- Non-interactive batch update from file:
    rqmd \
            --set-file tmp/ac-updates.jsonl

Notes:
- This script expects markdown requirement sections to use "### <PREFIX>-..."
    headers and "- **Status:** ..." lines.
- Header prefixes are configurable with --id-prefix and default to AC and R.
- If click/tabulate are missing, install them with pip3.
"""

from __future__ import annotations

import json
import readline  # noqa: F401 — activates arrow-key line editing in input()/click.prompt()
import sys
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from . import workflows as workflows_mod
from .batch_inputs import (parse_batch_update_csv, parse_batch_update_file,
                           parse_batch_update_jsonl, parse_set_entry)
from .constants import (DEFAULT_CRITERIA_DIR, DEFAULT_ID_PREFIXES,
                        ID_PREFIX_PATTERN, MENU_REFRESH, MENU_TOGGLE_DIRECTION,
                        MENU_TOGGLE_SORT, STATUS_ORDER, SUMMARY_END,
                        SUMMARY_START)
from .criteria_parser import (collect_criteria_by_status, find_criterion_by_id,
                              normalize_id_prefixes, parse_criteria,
                              resolve_id_prefixes)
from .markdown_io import (auto_detect_criteria_dir, check_files_writable,
                          check_index_sync, display_name_from_h1,
                          format_path_display,
                          initialize_requirements_scaffold,
                          iter_criteria_search_roots, iter_domain_files,
                          parse_index_links, resolve_criteria_dir,
                          validate_files_readable)
from .menus import (apply_background_preserving_styles,
                    file_sort_key_by_priority, select_from_menu)
from .rollup_config import (compute_rollup_column_values,
                            resolve_rollup_columns)
from .status_model import (build_color_rollup_text, normalize_status_input,
                           style_status_count, style_status_label)
from .status_update import (apply_status_change_by_id, print_criterion_panel,
                            prompt_for_blocked_reason,
                            prompt_for_deprecated_reason,
                            update_criterion_status)
from .summary import (build_summary_block, build_summary_line,
                      build_summary_table, collect_summary_rows,
                      count_statuses, insert_or_replace_summary,
                      normalize_status_lines, print_custom_rollup_table,
                      print_global_rollup_table,
                      print_summary_table, process_file)
from .workflows import (build_filtered_criteria_payload, build_summary_payload,
                        print_criteria_tree)

__all__ = [
    "SUMMARY_START",
    "SUMMARY_END",
    "normalize_status_lines",
    "insert_or_replace_summary",
    "build_summary_block",
    "build_summary_line",
    "build_summary_table",
    "count_statuses",
    "collect_summary_rows",
    "print_summary_table",
    "process_file",
    "parse_set_entry",
    "parse_batch_update_file",
    "parse_batch_update_jsonl",
    "parse_batch_update_csv",
    "format_path_display",
    "iter_criteria_search_roots",
    "auto_detect_criteria_dir",
    "resolve_criteria_dir",
    "iter_domain_files",
    "validate_files_readable",
    "check_files_writable",
    "parse_index_links",
    "check_index_sync",
    "display_name_from_h1",
    "print_criterion_panel",
    "update_criterion_status",
    "prompt_for_blocked_reason",
    "prompt_for_deprecated_reason",
    "style_status_label",
    "build_color_rollup_text",
    "main",
]


def prompt_for_init_prefix(default_prefix: str = "REQ") -> str:
    click.echo("Initialize scaffold: choose a requirement ID key prefix (for example AC, R, RQMD).")
    click.echo("Tip: customize this for your project to avoid generic IDs.")

    raw = click.prompt(
        "Starter key prefix (without trailing '-')",
        default=default_prefix,
        show_default=True,
    )
    value = str(raw).strip().upper().rstrip("-")
    if not value or not ID_PREFIX_PATTERN.fullmatch(value):
        raise click.ClickException("Invalid key prefix. Use uppercase letters/numbers, for example REQ, AC, or TEAM1.")
    return value


def interactive_update_loop(
    repo_root: Path,
    criteria_dir: str,
    domain_files: list[Path],
    emoji_columns: bool,
    sort_files: bool,
    sort_strategy: str = "standard",
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> int:
    return workflows_mod.interactive_update_loop(
        repo_root=repo_root,
        criteria_dir=criteria_dir,
        domain_files=domain_files,
        emoji_columns=emoji_columns,
        sort_files=sort_files,
        sort_strategy=sort_strategy,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
    )


def filtered_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    target_status: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> int:
    return workflows_mod.filtered_interactive_loop(
        repo_root=repo_root,
        domain_files=domain_files,
        target_status=target_status,
        emoji_columns=emoji_columns,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
    )


def lookup_criterion_interactive(
    repo_root: Path,
    domain_files: list[Path],
    criterion_id: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
) -> int:
    return workflows_mod.lookup_criterion_interactive(
        repo_root=repo_root,
        domain_files=domain_files,
        criterion_id=criterion_id,
        emoji_columns=emoji_columns,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
    )


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help=__doc__,
)
@click.argument(
    "criterion_id",
    required=False,
    default=None,
    metavar="[ID]",
)
@click.option("--check", is_flag=True, help="Check whether summaries are up to date without writing changes.")
@click.option("-v", "--verbose", is_flag=True, help="Show verbose output with full words.")
@click.option(
    "--emoji-columns",
    is_flag=True,
    help="Use emoji column headers in terse table output (may misalign in some terminals).",
)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Open interactive file/criterion/status flow after summary table.",
)
@click.option(
    "-u",
    "--unsorted",
    is_flag=True,
    help="Deprecated compatibility alias; filesystem ordering is already the default for Select file.",
)
@click.option(
    "--set-criterion-id",
    type=str,
    help="Non-interactive mode: requirement id to update, for example R-TELEMETRY-LOG-001.",
)
@click.option(
    "--set-status",
    "set_status",
    type=str,
    help="Non-interactive mode: target status (label, plain text, or slug, e.g. 'Implemented' or 'verified').",
)
@click.option(
    "--set",
    "set_updates",
    multiple=True,
    type=str,
    help="Non-interactive bulk mode: repeat ID=STATUS (for example --set R-FOO-001=implemented).",
)
@click.option(
    "--set-file",
    "set_file_input",
    type=str,
    help="Non-interactive batch mode: path to .jsonl/.csv/.tsv with rows containing criterion_id/requirement_id/id/ac_id/r_id and status.",
)
@click.option(
    "--file",
    "set_file",
    type=str,
    help="Optional file scope for non-interactive updates, repo-relative path such as docs/requirements/telemetry.md.",
)
@click.option(
    "--set-blocked-reason",
    type=str,
    help="Optional reason text when setting status to Blocked in non-interactive mode.",
)
@click.option(
    "--set-deprecated-reason",
    type=str,
    help="Optional reason text when setting status to Deprecated in non-interactive mode.",
)
@click.option(
    "--filter-status",
    type=str,
    help="Filter by status: walks matching requirements interactively (default) or shows tree with --tree.",
)
@click.option(
    "--tree",
    is_flag=True,
    help="With --filter-status: print a tree view only and exit instead of opening the interactive walk.",
)
@click.option(
    "--summary-table/--no-summary-table",
    default=True,
    help="Print the summary table output (disable in automation with --no-summary-table).",
)
@click.option(
    "--sort-strategy",
    type=click.Choice(workflows_mod.SORT_STRATEGY_NAMES, case_sensitive=False),
    default="standard",
    show_default=True,
    help="Select a named interactive sort strategy catalog.",
)
@click.option(
    "--rollup",
    "rollup_mode",
    is_flag=True,
    help="Print aggregate status totals across all requirement files and exit.",
)
@click.option(
    "--rollup-map",
    "rollup_map_entries",
    multiple=True,
    type=str,
    help="Custom rollup column equation, repeatable (for example --rollup-map 'C1=I+V').",
)
@click.option(
    "--rollup-config",
    type=str,
    default=None,
    help="Optional path to rollup config (.json/.yml/.yaml) containing rollup_map or rollup_equations.",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Print machine-readable JSON output for non-interactive workflows.",
)
@click.option(
    "--repo-root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Project root containing requirement documentation.",
)
@click.option(
    "--criteria-dir",
    type=str,
    default=None,
    help="Directory (absolute or relative to --repo-root) containing requirement markdown files. When omitted, rqmd auto-detects from the current working path.",
)
@click.option(
    "--id-prefix",
    "id_prefixes",
    multiple=True,
    default=(),
    help="Allowed header ID prefixes. Repeat or comma-separate values, for example --id-prefix R or --id-prefix AC,R.",
)
@click.option(
    "--check-index",
    "check_index",
    is_flag=True,
    help="Check that the requirements index (README.md) links match actual domain files; report stale links and orphan files.",
)
@click.option(
    "--init",
    "init_scaffold",
    is_flag=True,
    help="Initialize docs scaffold (index + starter domain file) and exit.",
)
def main(
    check: bool,
    verbose: bool,
    emoji_columns: bool,
    interactive: bool,
    unsorted: bool,
    set_criterion_id: str | None,
    set_status: str | None,
    set_updates: tuple[str, ...],
    set_file_input: str | None,
    set_file: str | None,
    set_blocked_reason: str | None,
    set_deprecated_reason: str | None,
    filter_status: str | None,
    tree: bool,
    summary_table: bool,
    sort_strategy: str,
    rollup_mode: bool,
    rollup_map_entries: tuple[str, ...],
    rollup_config: str | None,
    json_output: bool,
    repo_root: Path,
    criteria_dir: str | None,
    id_prefixes: tuple[str, ...],
    check_index: bool,
    init_scaffold: bool,
    criterion_id: str | None,
) -> None:
    repo_root = repo_root.resolve()

    if unsorted and not json_output:
        click.echo(
            "Warning: --unsorted is deprecated and now acts as a compatibility alias because filesystem ordering is already the default.",
            err=True,
        )

    if init_scaffold:
        if check or filter_status or set_criterion_id or set_status or set_updates or set_file_input or set_file or tree or rollup_mode or criterion_id:
            raise click.ClickException(
                "--init cannot be combined with --check, --rollup, positional ID, --filter-status/--tree, or --set-* options."
            )

        try:
            if id_prefixes:
                starter_prefix = normalize_id_prefixes(id_prefixes)[0]
            else:
                starter_prefix = prompt_for_init_prefix(default_prefix="REQ")
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

        created = initialize_requirements_scaffold(
            repo_root,
            criteria_dir or DEFAULT_CRITERIA_DIR,
            starter_prefix=starter_prefix,
        )
        if created:
            click.echo("Initialized requirement scaffold:")
            for path in created:
                click.echo(f"  + {path.relative_to(repo_root)}")
        else:
            click.echo("Requirement scaffold already present; no files created.")
        raise SystemExit(0)

    resolved_criteria_dir, criteria_dir_message = resolve_criteria_dir(repo_root, criteria_dir)
    resolved_criteria_dir_input = str(resolved_criteria_dir)
    if criteria_dir_message and not json_output:
        click.echo(criteria_dir_message)

    try:
        id_prefixes = resolve_id_prefixes(repo_root, resolved_criteria_dir_input, id_prefixes)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    domain_files = iter_domain_files(repo_root, resolved_criteria_dir_input)
    if not domain_files:
        print(f"No requirement markdown files found under: {format_path_display(resolved_criteria_dir, repo_root)}", file=sys.stderr)
        raise SystemExit(1)

    # RQMD-PORTABILITY-009: validate files are readable before proceeding
    validate_files_readable(domain_files, repo_root)

    # RQMD-CORE-013: --check-index mode — compare index links with actual domain files
    if check_index:
        index_path = resolved_criteria_dir / "README.md"
        if not index_path.exists():
            click.echo(f"No requirements index found at: {format_path_display(index_path, repo_root)}", err=True)
            click.echo("  Hint: run 'rqmd --init' to create a starter scaffold.", err=True)
            raise SystemExit(1)
        stale_links, orphan_files = check_index_sync(resolved_criteria_dir, index_path)
        issues: list[str] = []
        for name in stale_links:
            issues.append(f"  stale link:   {name}  (referenced in index but file does not exist)")
        for path in orphan_files:
            issues.append(f"  orphan file:  {format_path_display(path, repo_root)}  (exists on disk but not in index)")
        if issues:
            click.echo(f"Index sync issues found in: {format_path_display(index_path, repo_root)}")
            for line in issues:
                click.echo(line)
            click.echo(f"  Hint: update {format_path_display(index_path, repo_root)} to add missing links or remove stale ones.")
            raise SystemExit(1)
        click.echo(f"Index is in sync: {format_path_display(index_path, repo_root)}")
        raise SystemExit(0)

    # Positional ID lookup: find the requirement, show panel + status menu, done.
    if criterion_id:
        if check or filter_status or set_criterion_id or set_status or set_updates or set_file_input or set_file or tree or rollup_mode:
            raise click.ClickException(
                "Positional ID cannot be combined with --check, --rollup, --filter-status, --tree, or --set-* options."
            )
        raise SystemExit(
            lookup_criterion_interactive(
                repo_root,
                domain_files,
                criterion_id=criterion_id,
                emoji_columns=emoji_columns,
                id_prefixes=id_prefixes,
            )
        )

    changed_paths, table_rows = collect_summary_rows(domain_files, check_only=check, display_name_fn=display_name_from_h1)
    summary_payload = build_summary_payload(repo_root, resolved_criteria_dir, domain_files, changed_paths)

    if summary_table and verbose and not json_output and not rollup_mode:
        for row, path in zip(table_rows, domain_files):
            marker = "UPDATE" if path in changed_paths else "OK"
            parts = [
                f"{style_status_count(label, row[index + 1])} {label}"
                for index, (label, _) in enumerate(STATUS_ORDER)
            ]
            summary = ", ".join(parts)
            click.echo(f"[{marker}] {path.relative_to(repo_root)} :: {summary}")
    elif summary_table and not json_output and not rollup_mode:
        print_summary_table(table_rows, emoji_columns=emoji_columns)

    if rollup_mode:
        if check or filter_status or set_criterion_id or set_status or set_updates or set_file_input or set_file or tree:
            raise click.ClickException("--rollup cannot be combined with --check, --filter-status, --tree, or --set-* options.")
        rollup_columns, rollup_source = resolve_rollup_columns(
            repo_root,
            cli_rollup_map=rollup_map_entries,
            rollup_config_path=rollup_config,
        )
        rollup_column_values = compute_rollup_column_values(summary_payload["totals"], rollup_columns)

        if json_output:
            payload = {
                "mode": "rollup",
                "criteria_dir": format_path_display(resolved_criteria_dir, repo_root),
                "file_count": len(domain_files),
                "totals": summary_payload["totals"],
            }
            if rollup_column_values:
                payload["rollup_source"] = rollup_source
                payload["rollup_columns"] = [
                    {
                        "label": label,
                        "statuses": statuses,
                        "count": value,
                    }
                    for label, value, statuses in rollup_column_values
                ]
            click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            raise SystemExit(0)

        if rollup_column_values:
            print_custom_rollup_table([(label, value) for label, value, _statuses in rollup_column_values])
            if rollup_source and rollup_source != "cli":
                click.echo(f"Using rollup config: {rollup_source}")
            raise SystemExit(0)

        print_global_rollup_table(summary_payload["totals"], emoji_columns=emoji_columns)
        raise SystemExit(0)

    if check and changed_paths:
        if json_output:
            payload = dict(summary_payload)
            payload["mode"] = "check"
            payload["ok"] = False
            click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            raise SystemExit(1)
        if verbose:
            print(
                f"{len(changed_paths)} requirement file(s) need summary updates.",
                file=sys.stderr,
            )
        else:
            msg = f"{len(changed_paths)} file(s) need updates"
            print(msg, file=sys.stderr)
        raise SystemExit(1)

    # --tree without --filter-status is a no-op guard
    if tree and not filter_status:
        raise click.ClickException("--tree requires --filter-status.")

    # Handle --filter-status mode
    if filter_status:
        if check or set_criterion_id or set_status or set_updates or set_file_input or set_file:
            raise click.ClickException("--filter-status cannot be combined with --check / --set-criterion-id / --set-status / --file.")
        try:
            normalized_status = normalize_status_input(filter_status)
        except click.ClickException:
            raise
        criteria_by_file = collect_criteria_by_status(
            repo_root,
            domain_files,
            normalized_status,
            id_prefixes=id_prefixes,
        )
        if json_output:
            payload = build_filtered_criteria_payload(
                repo_root,
                resolved_criteria_dir,
                criteria_by_file,
                normalized_status,
            )
            click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            raise SystemExit(0)
        if tree or not interactive:
            # Non-interactive: just print the tree and exit.
            print_criteria_tree(repo_root, criteria_by_file, normalized_status)
            raise SystemExit(0)
        # Interactive: walk through matching requirements one by one.
        raise SystemExit(
            filtered_interactive_loop(
                repo_root,
                domain_files,
                target_status=normalized_status,
                emoji_columns=emoji_columns,
                id_prefixes=id_prefixes,
            )
        )

    non_interactive_requested = bool(set_criterion_id or set_status or set_updates or set_file_input or set_file)
    if non_interactive_requested:
        if check:
            raise click.ClickException("--check cannot be combined with --set-criterion-id/--set-status.")
        mode_count = int(bool(set_updates)) + int(bool(set_file_input)) + int(bool(set_criterion_id or set_status))
        if mode_count > 1:
            raise click.ClickException(
                "Use exactly one non-interactive update mode: --set-file, --set ID=STATUS (repeatable), or --set-criterion-id with --set-status."
            )

        update_requests: list[dict[str, str | None]] = []
        if set_updates:
            update_requests = [
                {
                    "criterion_id": cid,
                    "status": status,
                    "file": set_file,
                    "blocked_reason": None,
                    "deprecated_reason": None,
                }
                for cid, status in (parse_set_entry(entry) for entry in set_updates)
            ]
        elif set_file_input:
            if set_file:
                raise click.ClickException("--file cannot be combined with --set-file because each row may include its own file scope.")
            if set_blocked_reason or set_deprecated_reason:
                raise click.ClickException("--set-blocked-reason/--set-deprecated-reason cannot be combined with --set-file; provide per-row values in the file.")
            update_requests = parse_batch_update_file(repo_root, set_file_input)
        else:
            if set_criterion_id is None or set_status is None:
                raise click.ClickException("Both --set-criterion-id and --set-status are required for non-interactive update mode.")
            update_requests = [
                {
                    "criterion_id": set_criterion_id,
                    "status": set_status,
                    "file": set_file,
                    "blocked_reason": set_blocked_reason,
                    "deprecated_reason": set_deprecated_reason,
                }
            ]

        if (set_blocked_reason or set_deprecated_reason) and len(update_requests) != 1:
            raise click.ClickException("--set-blocked-reason/--set-deprecated-reason currently support single-target updates only.")

        update_results: list[dict[str, object]] = []
        for request in update_requests:
            criterion_id_value = str(request["criterion_id"])
            status_value = str(request["status"])
            row_file_filter = str(request["file"]) if request["file"] is not None else None
            normalized = normalize_status_input(status_value)

            blocked_reason = str(request["blocked_reason"]) if request["blocked_reason"] is not None else None
            deprecated_reason = str(request["deprecated_reason"]) if request["deprecated_reason"] is not None else None
            if "Blocked" not in normalized:
                blocked_reason = None
            if "Deprecated" not in normalized:
                deprecated_reason = None

            changed = apply_status_change_by_id(
                repo_root,
                domain_files,
                criterion_id=criterion_id_value,
                new_status_input=status_value,
                file_filter=row_file_filter,
                blocked_reason=blocked_reason,
                deprecated_reason=deprecated_reason,
                id_prefixes=id_prefixes,
                emit_output=not json_output,
            )
            update_results.append(
                {
                    "criterion_id": criterion_id_value,
                    "status": normalized,
                    "file": row_file_filter,
                    "changed": changed,
                }
            )

        _, table_rows = collect_summary_rows(domain_files, check_only=True, display_name_fn=display_name_from_h1)
        if json_output:
            payload = build_summary_payload(repo_root, resolved_criteria_dir, domain_files, [])
            payload["mode"] = "set"
            payload["updates"] = update_results
            click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            raise SystemExit(0)

        if summary_table:
            print_summary_table(table_rows, emoji_columns=emoji_columns)
        raise SystemExit(0)

    if json_output:
        payload = dict(summary_payload)
        payload["ok"] = True
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        raise SystemExit(0)

    if interactive and not check:
        # RQMD-INTERACTIVE-011: preflight write-permission gate
        check_files_writable(domain_files, repo_root)
        raise SystemExit(
            interactive_update_loop(
                repo_root,
                resolved_criteria_dir_input,
                domain_files,
                emoji_columns=emoji_columns,
                sort_files=False,
                sort_strategy=sort_strategy,
                id_prefixes=id_prefixes,
            )
        )


if __name__ == "__main__":
    main()