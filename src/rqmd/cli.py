#!/usr/bin/env python

"""Requirements/requirements summary updater and fast interactive status editor.

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
    ↓ = next page, ↑ = previous page, u = up, q = quit.
- Requirement-level next/prev shortcuts at status menu:
    ↓ = next requirement, ↑ = previous requirement (history-aware).
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
- Update multiple requirements in one command via repeated --update ID=STATUS.
- Useful for automation and agent-driven workflows.

Examples:
- Check only (no writes):
    rqmd --verify-summaries
- Interactive mode with emoji headers:
    rqmd --emoji-headers
- Non-interactive single update:
    rqmd \
            --update-id R-TELEMETRY-LOG-001 \
            --update-status implemented
- Non-interactive bulk update:
    rqmd \
            --update R-STEELTARGET-AUDIO-004=implemented \
            --update R-STEELTARGET-AUDIO-005=verified
- Non-interactive batch update from file:
    rqmd \
            --update-file tmp/ac-updates.jsonl

Notes:
- This script expects markdown requirement sections to use "### <PREFIX>-..."
    headers and "- **Status:** ..." lines.
- Header prefixes are configurable with --id-namespace and default to AC and R.
- If click/tabulate are missing, install them with pip3.
"""

from __future__ import annotations

import json
import re
import readline  # noqa: F401 — activates arrow-key line editing in input()/click.prompt()
import sys
from datetime import datetime
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from . import menus as menus_mod
from . import workflows as workflows_mod
from .batch_inputs import (parse_batch_update_csv, parse_batch_update_file,
                           parse_batch_update_jsonl, parse_set_entry,
                           parse_set_flagged_entry, parse_set_priority_entry)
from .config import (load_config, load_priorities_file, load_statuses_file,
                     load_user_config, validate_config)
from .constants import (DEFAULT_ID_PREFIXES, DEFAULT_REQUIREMENTS_DIR,
                        ID_PREFIX_PATTERN, JSON_SCHEMA_VERSION, STATUS_ORDER,
                        STATUS_PATTERN, SUMMARY_END, SUMMARY_START)
from .history import HistoryManager, HistoryRestoreError
from .markdown_io import (auto_detect_requirements_dir, check_files_writable,
                          check_index_sync, discover_project_root,
                          display_name_from_h1, format_path_display,
                          initialize_requirements_scaffold, iter_domain_files,
                          iter_requirements_search_roots, parse_index_links,
                          resolve_requirements_dir, validate_files_readable)
from .menus import select_from_menu
from .priority_model import (configure_priority_catalog,
                             normalize_priority_input)
from .req_parser import (collect_requirements_by_filters,
                         collect_requirements_by_flagged,
                         collect_requirements_by_links,
                         collect_requirements_by_priority,
                         collect_requirements_by_status,
                         collect_requirements_by_sub_domain,
                         find_requirement_by_id, normalize_id_prefixes,
                         parse_requirements, resolve_id_prefixes)
from .rollup_config import compute_rollup_column_values, resolve_rollup_columns
from .status_model import (build_color_rollup_text, configure_status_catalog,
                           normalize_status_input, style_status_count,
                           style_status_label)
from .status_update import (apply_status_change_by_id, print_criterion_panel,
                            prompt_for_blocked_reason,
                            prompt_for_deprecated_reason,
                            update_criterion_status)
from .summary import (UnknownStatusValueError, build_summary_block,
                      build_summary_line, build_summary_table,
                      collect_summary_rows, count_statuses,
                      insert_or_replace_summary, normalize_status_lines,
                      print_custom_rollup_table, print_global_rollup_table,
                      print_summary_table, process_file)
from .target_selection import (complete_target_tokens, parse_target_token_file,
                               resolve_target_tokens)
from .workflows import (build_filtered_criteria_payload, build_summary_payload,
                        build_targeted_criteria_payload)
from .workflows import \
    focused_target_interactive_loop as focused_target_interactive_loop_impl
from .workflows import print_criteria_list, print_criteria_tree

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
    "iter_requirements_search_roots",
    "auto_detect_requirements_dir",
    "resolve_requirements_dir",
    "iter_domain_files",
    "validate_files_readable",
    "check_files_writable",
    "parse_index_links",
    "check_index_sync",
    "display_name_from_h1",
    "apply_background_preserving_styles",
    "file_sort_key_by_priority",
    "print_criterion_panel",
    "update_criterion_status",
    "prompt_for_blocked_reason",
    "prompt_for_deprecated_reason",
    "style_status_label",
    "build_color_rollup_text",
    "main",
]

apply_background_preserving_styles = menus_mod.apply_background_preserving_styles
file_sort_key_by_priority = menus_mod.file_sort_key_by_priority

_AMBIGUOUS_INPUT_PATTERN = re.compile(
    r"^Ambiguous (?P<field>[a-z_]+) input '(?P<input>.+)'\. Matches: (?P<matches>[^.]+)(?:\..*)?$",
    re.IGNORECASE,
)


def _detailed_flag_requested(args: list[str] | tuple[str, ...] | None) -> bool:
    tokens = list(sys.argv[1:] if args is None else args)
    for token in tokens:
        if token == "--detailed":
            return True
        if token.startswith("--"):
            continue
        if token.startswith("-") and len(token) > 1 and "v" in token[1:]:
            return True
    return False


def _collect_long_option_names(command: click.Command) -> list[str]:
    option_names: set[str] = set()
    for param in command.params:
        if not isinstance(param, click.Option):
            continue
        for opt in (*param.opts, *param.secondary_opts):
            if opt.startswith("--"):
                option_names.add(opt)
    return sorted(option_names)


def _expand_unique_long_option_prefixes(
    command: click.Command,
    args: list[str] | tuple[str, ...] | None,
) -> list[str] | None:
    if args is None:
        return None

    option_names = _collect_long_option_names(command)
    expanded: list[str] = []
    passthrough = False

    for token in args:
        if passthrough:
            expanded.append(token)
            continue
        if token == "--":
            passthrough = True
            expanded.append(token)
            continue
        if not token.startswith("--") or token == "---":
            expanded.append(token)
            continue

        option_token, separator, option_value = token.partition("=")
        if option_token in option_names:
            expanded.append(token)
            continue

        matches = [candidate for candidate in option_names if candidate.startswith(option_token)]
        if not matches:
            expanded.append(token)
            continue
        if len(matches) > 1:
            raise click.UsageError(
                f"Ambiguous option prefix '{option_token}'. Matches: {', '.join(matches)}."
            )

        resolved = matches[0]
        expanded.append(f"{resolved}{separator}{option_value}" if separator else resolved)

    return expanded


class FriendlyTopLevelCommand(click.Command):
    """Convert unexpected internal crashes into a friendly one-line CLI error.

    Click already handles expected user-facing errors via ClickException. This
    wrapper only catches truly unexpected exceptions in standalone CLI mode and
    emits a concise guidance line unless --detailed/-v is requested.
    """

    def main(
        self,
        args: list[str] | tuple[str, ...] | None = None,
        prog_name: str | None = None,
        complete_var: str | None = None,
        standalone_mode: bool = True,
        windows_expand_args: bool = True,
        **extra: object,
    ) -> object:
        try:
            expanded_args = _expand_unique_long_option_prefixes(self, args)
            return super().main(
                args=expanded_args,
                prog_name=prog_name,
                complete_var=complete_var,
                standalone_mode=standalone_mode,
                windows_expand_args=windows_expand_args,
                **extra,
            )
        except click.ClickException as exc:
            if not standalone_mode:
                raise
            exc.show()
            raise SystemExit(exc.exit_code)
        except click.Abort:
            raise
        except Exception as exc:
            if (not standalone_mode) or _detailed_flag_requested(args):
                raise
            message = str(exc).strip()
            detail = f" ({message})" if message else ""
            click.echo(
                f"Error: Unexpected internal error{detail}. Re-run with --detailed to show a traceback.",
                err=True,
            )
            raise SystemExit(1)


def _build_json_ambiguity_payload(mode: str, message: str) -> dict[str, object] | None:
    match = _AMBIGUOUS_INPUT_PATTERN.match(message.strip())
    if not match:
        return None

    raw_matches = match.group("matches").strip()
    candidates = [item.strip() for item in raw_matches.split(",") if item.strip()]
    return {
        "mode": mode,
        "ok": False,
        "error": {
            "type": "ambiguous-input",
            "field": match.group("field").lower(),
            "input": match.group("input"),
            "candidates": candidates,
            "message": message,
        },
    }


def _with_schema_version(payload: dict[str, object]) -> dict[str, object]:
    if "schema_version" not in payload:
        payload["schema_version"] = JSON_SCHEMA_VERSION
    return payload


def _emit_json_payload(payload: dict[str, object]) -> None:
    click.echo(json.dumps(_with_schema_version(payload), ensure_ascii=False, indent=2))


def _emit_json_ambiguity_error(mode: str, exc: click.ClickException) -> bool:
    payload = _build_json_ambiguity_payload(mode, str(exc))
    if payload is None:
        return False
    _emit_json_payload(payload)
    raise SystemExit(1)


def _build_unknown_status_payload(
    mode: str,
    exc: UnknownStatusValueError,
    repo_root: Path,
) -> dict[str, object]:
    source_file = None
    if exc.source_path is not None:
        source_file = format_path_display(exc.source_path, repo_root)

    return {
        "mode": mode,
        "ok": False,
        "error": {
            "type": "unknown-status",
            "field": "status",
            "input": exc.status_value,
            "source_file": source_file,
            "line": exc.line_number,
            "candidates": exc.suggestions,
            "message": str(exc),
            "remediation": [
                "Update status catalog configuration to include this status.",
                "Add an alias mapping to canonicalize imported status values.",
                "Run a one-time migration to replace unknown statuses in requirement docs.",
            ],
        },
    }


def _raise_unknown_status_error(
    mode: str,
    exc: UnknownStatusValueError,
    repo_root: Path,
    json_output: bool,
) -> None:
    if json_output:
        _emit_json_payload(_build_unknown_status_payload(mode, exc, repo_root))
        raise SystemExit(1)

    source = "<unknown file>"
    if exc.source_path is not None:
        source = format_path_display(exc.source_path, repo_root)
    suggestion_text = ", ".join(exc.suggestions) if exc.suggestions else "(no close matches)"
    raise click.ClickException(
        "Unknown status compatibility issue. "
        f"Found '{exc.status_value}' at {source}:{exc.line_number}. "
        f"Nearest configured statuses: {suggestion_text}. "
        "Remediation: update status catalog config, add alias mapping, or run a one-time migration."
    )


def _expand_filter_values(raw_values: tuple[str, ...]) -> tuple[str, ...]:
    """Expand repeatable/comma-separated filter values into a normalized tuple."""
    values: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        for part in str(raw).split(","):
            value = part.strip()
            if not value:
                continue
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            values.append(value)
    return tuple(values)


def _parse_prefix_rename_spec(raw: str) -> tuple[str, str]:
    spec = str(raw).strip()
    if "=" not in spec:
        raise click.ClickException("--rename-id-prefix requires OLD=NEW format, for example --rename-id-prefix AC=RQMD.")
    old_raw, new_raw = spec.split("=", 1)
    old_prefix = old_raw.strip().upper().rstrip("-")
    new_prefix = new_raw.strip().upper().rstrip("-")
    if not old_prefix or not new_prefix:
        raise click.ClickException("--rename-id-prefix requires both OLD and NEW prefixes.")
    if not ID_PREFIX_PATTERN.fullmatch(old_prefix) or not ID_PREFIX_PATTERN.fullmatch(new_prefix):
        raise click.ClickException("Invalid prefix in --rename-id-prefix; use uppercase letters/numbers only.")
    if old_prefix == new_prefix:
        raise click.ClickException("--rename-id-prefix OLD and NEW must be different.")
    return old_prefix, new_prefix


def _collect_requirement_ids_from_text(text: str) -> set[str]:
    return set(
        match.group("id")
        for match in re.finditer(
            r"^###\s+(?P<id>[A-Z][A-Z0-9]*-[A-Z0-9][A-Z0-9-]*)\s*:",
            text,
            flags=re.MULTILINE,
        )
    )


def _rename_requirement_id_prefix_in_text(text: str, old_prefix: str, new_prefix: str) -> tuple[str, int]:
    pattern = re.compile(rf"\b{re.escape(old_prefix)}-(?P<suffix>[A-Z0-9][A-Z0-9-]*)\b")
    return pattern.subn(lambda m: f"{new_prefix}-{m.group('suffix')}", text)


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


def infer_include_status_emojis(domain_files: list[Path]) -> bool:
    emoji_prefixes = tuple(label.split(" ", 1)[0] for label, _ in STATUS_ORDER)
    for path in domain_files:
        text = path.read_text(encoding="utf-8")
        for match in STATUS_PATTERN.finditer(text):
            raw = match.group("status").strip()
            if raw.startswith(emoji_prefixes):
                return True
    return False


def resolve_positional_domain_file_token(
    repo_root: Path,
    domain_files: list[Path],
    token: str,
) -> Path | None:
    raw = token.strip()
    if not raw:
        return None

    candidate_input = Path(raw).expanduser()
    candidate = candidate_input.resolve() if candidate_input.is_absolute() else (repo_root / candidate_input).resolve()
    domain_lookup = {path.resolve(): path for path in domain_files}
    return domain_lookup.get(candidate)


def looks_like_requirement_id_token(token: str, id_prefixes: tuple[str, ...]) -> bool:
    upper = token.strip().upper()
    return any(upper.startswith(f"{prefix}-") for prefix in id_prefixes)


def interactive_update_loop(
    repo_root: Path,
    requirements_dir: str,
    domain_files: list[Path],
    emoji_columns: bool,
    sort_files: bool,
    sort_strategy: str = "standard",
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
    initial_file_path: Path | None = None,
    zebra_bg: str | None = None,
) -> int:
    return workflows_mod.interactive_update_loop(
        repo_root=repo_root,
        criteria_dir=requirements_dir,
        domain_files=domain_files,
        emoji_columns=emoji_columns,
        sort_files=sort_files,
        sort_strategy=sort_strategy,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
        include_status_emojis=include_status_emojis,
        priority_mode=priority_mode,
        include_priority_summary=include_priority_summary,
        initial_file_path=initial_file_path,
        zebra_bg=zebra_bg,
    )


def filtered_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    target_status: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    resume_filter: bool = True,
    state_dir: str = "system-temp",
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
) -> int:
    return workflows_mod.filtered_interactive_loop(
        repo_root=repo_root,
        domain_files=domain_files,
        target_status=target_status,
        emoji_columns=emoji_columns,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
        resume_filter=resume_filter,
        state_dir=state_dir,
        include_status_emojis=include_status_emojis,
        priority_mode=priority_mode,
        include_priority_summary=include_priority_summary,
    )


def filtered_priority_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    target_priority: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    resume_filter: bool = True,
    state_dir: str = "system-temp",
    include_status_emojis: bool | None = None,
    priority_mode: bool = True,
    include_priority_summary: bool = False,
) -> int:
    return workflows_mod.filtered_priority_interactive_loop(
        repo_root=repo_root,
        domain_files=domain_files,
        target_priority=target_priority,
        emoji_columns=emoji_columns,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
        resume_filter=resume_filter,
        state_dir=state_dir,
        include_status_emojis=include_status_emojis,
        priority_mode=priority_mode,
        include_priority_summary=include_priority_summary,
    )


def lookup_criterion_interactive(
    repo_root: Path,
    domain_files: list[Path],
    requirement_id: str,
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
) -> int:
    return workflows_mod.lookup_criterion_interactive(
        repo_root=repo_root,
        domain_files=domain_files,
        requirement_id=requirement_id,
        emoji_columns=emoji_columns,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
        include_status_emojis=include_status_emojis,
        priority_mode=priority_mode,
        include_priority_summary=include_priority_summary,
    )


def focused_target_interactive_loop(
    repo_root: Path,
    domain_files: list[Path],
    selected_items: list[tuple[Path, dict[str, object]]],
    target_tokens: list[str],
    emoji_columns: bool,
    id_prefixes: tuple[str, ...] = DEFAULT_ID_PREFIXES,
    resume_filter: bool = True,
    state_dir: str = "system-temp",
    include_status_emojis: bool | None = None,
    priority_mode: bool = False,
    include_priority_summary: bool = False,
) -> int:
    return focused_target_interactive_loop_impl(
        repo_root=repo_root,
        domain_files=domain_files,
        selected_items=selected_items,
        target_tokens=target_tokens,
        emoji_columns=emoji_columns,
        id_prefixes=id_prefixes,
        select_from_menu_fn=select_from_menu,
        resume_filter=resume_filter,
        state_dir=state_dir,
        include_status_emojis=include_status_emojis,
        priority_mode=priority_mode,
        include_priority_summary=include_priority_summary,
    )


def shell_complete_target_tokens(
    ctx: click.Context,
    param: click.Parameter,
    incomplete: str,
) -> list[object]:
    del param
    try:
        raw_repo_root = ctx.params.get("repo_root")
        repo_root = Path(raw_repo_root).resolve() if raw_repo_root else discover_project_root(Path.cwd())[0]
        raw_criteria_dir = ctx.params.get("requirements_dir")
        resolved_criteria_dir, _message = resolve_requirements_dir(repo_root, raw_criteria_dir)
        raw_prefixes = tuple(ctx.params.get("id_prefixes") or ())
        resolved_prefixes = resolve_id_prefixes(repo_root, str(resolved_criteria_dir), raw_prefixes)
        domain_files = iter_domain_files(repo_root, str(resolved_criteria_dir))
        items = complete_target_tokens(repo_root, domain_files, resolved_prefixes, incomplete)
    except Exception:
        return []

    completion_module = getattr(click, "shell_completion", None)
    completion_item = getattr(completion_module, "CompletionItem", None) if completion_module is not None else None
    if completion_item is None:
        return items
    return [completion_item(item) for item in items]


def _parse_iso8601_filter(value: str, option_name: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise click.ClickException(
            f"Invalid {option_name} value {value!r}. Expected ISO-8601 datetime (for example 2026-03-28T16:20:00+00:00)."
        ) from exc


def _build_snapshot_status_map(
    history_manager: HistoryManager,
    commit_hash: str,
    id_prefixes: tuple[str, ...],
) -> dict[str, str | None]:
    tempdir = history_manager.materialize_snapshot_tempdir(commit_hash)
    try:
        root = Path(tempdir.name)
        domain_files = iter_domain_files(root, history_manager.requirements_dir.as_posix())
        mapping: dict[str, str | None] = {}
        for path in domain_files:
            for requirement in parse_requirements(path, id_prefixes=id_prefixes):
                req_id = str(requirement.get("id") or "")
                if req_id:
                    mapping[req_id] = requirement.get("status")
        return mapping
    finally:
        tempdir.cleanup()


def _enrich_timeline_nodes_with_change_metadata(
    history_manager: HistoryManager,
    timeline_nodes: dict[str, dict[str, object]],
    id_prefixes: tuple[str, ...],
) -> None:
    status_cache: dict[str, dict[str, str | None]] = {}

    def _status_map(commit_hash: str) -> dict[str, str | None]:
        if commit_hash not in status_cache:
            status_cache[commit_hash] = _build_snapshot_status_map(history_manager, commit_hash, id_prefixes)
        return status_cache[commit_hash]

    ordered_items = sorted(
        timeline_nodes.items(),
        key=lambda item: int(item[1].get("entry_index", -1)),
    )

    for commit_hash, node in ordered_items:
        parent_commit = str(node.get("parent_commit") or "")
        if not parent_commit:
            node["changed_requirement_ids"] = []
            node["status_transitions"] = []
            continue

        current_map = _status_map(commit_hash)
        parent_map = _status_map(parent_commit)

        changed_ids: list[str] = []
        transitions: list[dict[str, object]] = []
        for req_id in sorted(set(current_map).union(parent_map)):
            before_status = parent_map.get(req_id)
            after_status = current_map.get(req_id)
            if before_status == after_status:
                continue
            changed_ids.append(req_id)
            transitions.append(
                {
                    "id": req_id,
                    "before_status": before_status,
                    "after_status": after_status,
                }
            )

        node["changed_requirement_ids"] = changed_ids
        node["status_transitions"] = transitions


def _filter_timeline_nodes(
    timeline_nodes: dict[str, dict[str, object]],
    branch_filter: str | None,
    actor_filter: str | None,
    command_filter: str | None,
    file_filter: str | None,
    requirement_id_filter: str | None,
    transition_filter: str | None,
    from_filter: datetime | None,
    to_filter: datetime | None,
) -> dict[str, dict[str, object]]:
    def _contains_casefold(haystack: str | None, needle: str | None) -> bool:
        if not needle:
            return True
        if haystack is None:
            return False
        return needle.casefold() in haystack.casefold()

    before_filter: str | None = None
    after_filter: str | None = None
    if transition_filter:
        if "->" in transition_filter:
            before_raw, after_raw = transition_filter.split("->", 1)
            before_filter = before_raw.strip() or None
            after_filter = after_raw.strip() or None
        else:
            before_filter = transition_filter.strip() or None

    filtered: dict[str, dict[str, object]] = {}
    for commit_hash, node in timeline_nodes.items():
        if branch_filter and not _contains_casefold(str(node.get("branch") or ""), branch_filter):
            continue
        if actor_filter and not _contains_casefold(str(node.get("actor") or ""), actor_filter):
            continue
        if command_filter and not _contains_casefold(str(node.get("command") or ""), command_filter):
            continue

        files = [str(item) for item in (node.get("files") or [])]
        if file_filter and not any(file_filter.casefold() in value.casefold() for value in files):
            continue

        changed_ids = [str(item) for item in (node.get("changed_requirement_ids") or [])]
        if requirement_id_filter and not any(requirement_id_filter.casefold() == value.casefold() for value in changed_ids):
            continue

        transitions = node.get("status_transitions") or []
        if before_filter or after_filter:
            matched_transition = False
            for transition in transitions:
                if not isinstance(transition, dict):
                    continue
                before_value = str(transition.get("before_status") or "")
                after_value = str(transition.get("after_status") or "")
                if before_filter and not _contains_casefold(before_value, before_filter):
                    continue
                if after_filter and not _contains_casefold(after_value, after_filter):
                    continue
                matched_transition = True
                break
            if not matched_transition:
                continue

        timestamp_raw = str(node.get("timestamp") or "")
        if (from_filter or to_filter) and timestamp_raw:
            timestamp_value = _parse_iso8601_filter(timestamp_raw, "timeline node timestamp")
            if from_filter and timestamp_value < from_filter:
                continue
            if to_filter and timestamp_value > to_filter:
                continue
        elif from_filter or to_filter:
            continue

        filtered[commit_hash] = node

    return filtered


@click.command(
    cls=FriendlyTopLevelCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
    help=__doc__,
)
@click.argument(
    "targets",
    required=False,
    nargs=-1,
    metavar="[TARGET]...",
    shell_complete=shell_complete_target_tokens,
)
@click.option("--verify-summaries", "check", is_flag=True, help="Check whether summaries are up to date without writing changes.")
@click.option("-v", "--detailed", "verbose", is_flag=True, help="Show verbose output with full words.")
@click.option(
    "--emoji-headers",
    "emoji_columns",
    is_flag=True,
    help="Use emoji column headers in terse table output (may misalign in some terminals).",
)
@click.option(
    "--walk/--no-walk",
    "interactive",
    default=True,
    help="Open interactive file/requirement/status flow after summary table.",
)
@click.option(
    "--screen-write/--no-screen-write",
    "screen_write",
    default=None,
    help="Enable or disable full-screen redraw mode in interactive menus (default: enabled when TTY).",
)
@click.option(
    "-u",
    "--filesystem-order",
    "unsorted",
    is_flag=True,
    help="Deprecated compatibility alias; filesystem ordering is already the default for Select file.",
)
@click.option(
    "--update-status",
    "set_status",
    type=str,
    help="Non-interactive mode: target status (label, plain text, or slug, e.g. 'Implemented' or 'verified').",
)
@click.option(
    "--update-id",
    "set_requirement_id",
    type=str,
    help="Non-interactive mode: requirement id to update, for example R-TELEMETRY-LOG-001.",
)
@click.option(
    "--update",
    "set_updates",
    multiple=True,
    type=str,
    help="Non-interactive bulk mode: repeat ID=STATUS (for example --update R-FOO-001=implemented).",
)
@click.option(
    "--undo",
    "undo_last",
    is_flag=True,
    help="Non-interactive mode: restore the previous recorded catalog snapshot.",
)
@click.option(
    "--redo",
    "redo_last",
    is_flag=True,
    help="Non-interactive mode: reapply the next recorded catalog snapshot.",
)
@click.option(
    "--timeline",
    "show_timeline",
    is_flag=True,
    help="Display the history timeline showing branches and entry points (useful with --as-json for automation).",
)
@click.option(
    "--history",
    "show_history",
    is_flag=True,
    help="Display persistent history entries with cursor/head metadata (useful with --as-json for automation).",
)
@click.option(
    "--history-discard-branch",
    "history_discard_branch",
    type=str,
    default=None,
    help="Discard an alternate history branch by name (requires confirmation; use --force-yes for non-interactive automation).",
)
@click.option(
    "--history-discard-save-label",
    "history_discard_save_label",
    type=str,
    default=None,
    help="Optional label to save on a branch immediately before --history-discard-branch removes it from navigation.",
)
@click.option(
    "--history-label-branch",
    "history_label_branch",
    type=str,
    default=None,
    help="Set or update a human-readable label for a named history branch.",
)
@click.option(
    "--history-branch-label",
    "history_branch_label",
    type=str,
    default=None,
    help="Label text used with --history-label-branch.",
)
@click.option(
    "--history-gc",
    "history_gc",
    is_flag=True,
    help="Run maintenance garbage collection on the hidden history repository (requires confirmation; use --force-yes for automation).",
)
@click.option(
    "--history-prune-now",
    "history_prune_now",
    is_flag=True,
    help="Used with --history-gc to expire reflogs and prune immediately instead of using Git's default grace period.",
)
@click.option(
    "--history-checkout-branch",
    "history_checkout_branch",
    type=str,
    default=None,
    help="Checkout a named history branch and restore its HEAD snapshot into the working catalog.",
)
@click.option(
    "--history-cherry-pick",
    "history_cherry_pick",
    type=str,
    default=None,
    help="Apply a single history entry onto the current or target branch HEAD. Accepts entry index, commit hash/prefix, stable hid: id, or 'head'/'current'.",
)
@click.option(
    "--history-replay-branch",
    "history_replay_branch",
    type=str,
    default=None,
    help="Replay every commit from a named alternate history branch onto the current or target branch HEAD.",
)
@click.option(
    "--history-target-branch",
    "history_target_branch",
    type=str,
    default=None,
    help="Optional target branch for --history-cherry-pick or --history-replay-branch.",
)
@click.option(
    "--timeline-branch",
    "timeline_filter_branch",
    type=str,
    default=None,
    help="Filter --timeline output by branch name (case-insensitive contains match).",
)
@click.option(
    "--timeline-actor",
    "timeline_filter_actor",
    type=str,
    default=None,
    help="Filter --timeline output by actor metadata (case-insensitive contains match).",
)
@click.option(
    "--timeline-command",
    "timeline_filter_command",
    type=str,
    default=None,
    help="Filter --timeline output by command/operation type (case-insensitive contains match).",
)
@click.option(
    "--timeline-file",
    "timeline_filter_file",
    type=str,
    default=None,
    help="Filter --timeline output by changed file path token.",
)
@click.option(
    "--timeline-requirement-id",
    "timeline_filter_requirement_id",
    type=str,
    default=None,
    help="Filter --timeline output to entries that changed the specified requirement ID.",
)
@click.option(
    "--timeline-transition",
    "timeline_filter_transition",
    type=str,
    default=None,
    help="Filter --timeline output by transition token (for example 'Proposed->Implemented').",
)
@click.option(
    "--timeline-from",
    "timeline_filter_from",
    type=str,
    default=None,
    help="Filter --timeline output to entries at/after this ISO-8601 timestamp.",
)
@click.option(
    "--timeline-to",
    "timeline_filter_to",
    type=str,
    default=None,
    help="Filter --timeline output to entries at/before this ISO-8601 timestamp.",
)
@click.option(
    "--update-file",
    "set_file_input",
    type=str,
    help="Non-interactive batch mode: path to .jsonl/.csv/.tsv with rows containing requirement_id/requirement_id/id/req_id/r_id and status.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview mutation changes without writing files (applies to --update/--update-file/--update-priority/--update-flagged/--seed-priorities).",
)
@click.option(
    "--rename-id-prefix",
    "rename_id_prefix",
    type=str,
    default=None,
    help="One-time bulk rename: OLD=NEW to rewrite requirement ID prefixes across domain files (for example --rename-id-prefix AC=RQMD).",
)
@click.option(
    "--scope-file",
    "set_file",
    type=str,
    help="Optional file scope for non-interactive updates, repo-relative path such as docs/requirements/telemetry.md.",
)
@click.option(
    "--blocked-note",
    "set_blocked_reason",
    type=str,
    help="Optional reason text when setting status to Blocked in non-interactive mode.",
)
@click.option(
    "--deprecated-note",
    "set_deprecated_reason",
    type=str,
    help="Optional reason text when setting status to Deprecated in non-interactive mode.",
)
@click.option(
    "--update-priority",
    "set_priority_updates",
    multiple=True,
    type=str,
    help="Non-interactive priority mode: repeat ID=PRIORITY (for example --update-priority R-FOO-001=p0).",
)
@click.option(
    "--update-flagged",
    "set_flagged_updates",
    multiple=True,
    type=str,
    help="Non-interactive flagged mode: repeat ID=true|false (for example --update-flagged R-FOO-001=true).",
)
@click.option(
    "--focus-priority",
    "priority_mode",
    is_flag=True,
    help="Interactive mode: default to Priority focus instead of Status focus in entry panels.",
)
@click.option(
    "--priority-rollup",
    "show_priority_summary",
    is_flag=True,
    help="Include priority-aware aggregates (counts by priority level) in summary blocks.",
)
@click.option(
    "--status",
    "filter_status",
    multiple=True,
    type=str,
    help="Filter by status (repeatable/comma-separated).",
)
@click.option(
    "--priority",
    "filter_priority",
    multiple=True,
    type=str,
    help="Filter by priority (repeatable/comma-separated).",
)
@click.option(
    "--flagged",
    "filter_flagged",
    is_flag=True,
    help="Filter flagged requirements and print matches as tree/JSON in non-interactive workflows.",
)
@click.option(
    "--no-flag",
    "filter_no_flag",
    is_flag=True,
    help="Filter unflagged requirements (Flagged: false or missing).",
)
@click.option(
    "--has-link",
    "filter_has_link",
    is_flag=True,
    help="Filter requirements that have one or more links.",
)
@click.option(
    "--no-link",
    "filter_no_link",
    is_flag=True,
    help="Filter requirements that have no links.",
)
@click.option(
    "--sub-domain",
    "filter_sub_domain",
    multiple=True,
    type=str,
    help="Filter by subsection name using case-insensitive prefix matching (repeatable/comma-separated).",
)
@click.option(
    "--targets-file",
    "filter_ids_file",
    type=str,
    help="Path to a .txt/.conf/.md target list containing requirement IDs, domain tokens, and subsection tokens.",
)
@click.option(
    "--as-tree",
    "tree",
    is_flag=True,
    help="With --status: print a tree view only and exit instead of opening the interactive walk.",
)
@click.option(
    "--as-list",
    "list_output",
    is_flag=True,
    help="With filters or explicit target tokens: print a flat list and exit.",
)
@click.option(
    "--table/--no-table",
    "summary_table",
    default=True,
    help="Print the summary table output (disable in automation with --no-table).",
)
@click.option(
    "--sort-profile",
    "sort_strategy",
    type=click.Choice(workflows_mod.SORT_STRATEGY_NAMES, case_sensitive=False),
    default="standard",
    show_default=True,
    help="Select a named interactive sort strategy catalog.",
)
@click.option(
    "--theme",
    "theme",
    type=click.Choice(["light", "dark"], case_sensitive=False),
    default=None,
    help="Override terminal theme for interactive zebra striping (light or dark).",
)
@click.option(
    "--totals",
    "rollup_mode",
    is_flag=True,
    help="Print aggregate status totals across all requirement files and exit.",
)
@click.option(
    "--totals-map",
    "rollup_map_entries",
    multiple=True,
    type=str,
    help="Custom rollup column equation, repeatable (for example --totals-map 'C1=I+V').",
)
@click.option(
    "--totals-config",
    "rollup_config",
    type=str,
    default=None,
    help="Optional path to rollup config (.json/.yml/.yaml) containing rollup_map or rollup_equations.",
)
@click.option(
    "--as-json",
    "json_output",
    is_flag=True,
    help="Print machine-readable JSON output for non-interactive workflows.",
)
@click.option(
    "--include-requirement-body/--no-requirement-body",
    "include_body",
    default=True,
    help="With --as-json --status: include full requirement body and line metadata (disable with --no-requirement-body).",
)
@click.option(
    "--resume-walk/--no-resume-walk",
    "resume_filter",
    default=True,
    help="Resume filtered interactive walkthrough position across runs.",
)
@click.option(
    "--strip-status-icons",
    "strip_status_emojis",
    is_flag=True,
    help="One-time conversion: remove emoji prefixes from all status lines and regenerate summaries.",
)
@click.option(
    "--restore-status-icons",
    "restore_status_emojis",
    is_flag=True,
    help="One-time conversion: restore canonical emoji-prefixed status lines and regenerate summaries.",
)
@click.option(
    "--seed-priorities",
    "init_priorities",
    is_flag=True,
    help="One-time migration: add default priority lines to requirements missing them.",
)
@click.option(
    "--seed-priority",
    "default_priority",
    type=str,
    default="p3",
    show_default=True,
    help="Default priority used by --seed-priorities (for example p0, high, medium, low).",
)
@click.option(
    "--session-state-dir",
    "state_dir",
    type=str,
    default="system-temp",
    show_default=True,
    help="Directory for persisted workflow state: system-temp, project-local, or a custom path.",
)
@click.option(
    "--project-root",
    "repo_root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Project root containing requirement documentation.",
)
@click.option(
    "--status-config",
    "status_config",
    type=str,
    default=None,
    help="Path to a status catalog file (.yml, .yaml, or .json). Overrides .rqmd/statuses.yml auto-detection.",
)
@click.option(
    "--priorities-config",
    "priorities_config",
    type=str,
    default=None,
    help="Path to a priority catalog file (.yml, .yaml, or .json). Overrides .rqmd/priorities.yml auto-detection.",
)
@click.option(
    "--docs-dir",
    "requirements_dir",
    type=str,
    default=None,
    help="Directory (absolute or relative to --project-root) containing requirement markdown files. When omitted, rqmd auto-detects from the current working path.",
)
@click.option(
    "--id-namespace",
    "id_prefixes",
    multiple=True,
    default=(),
    help="Allowed header ID prefixes. Repeat or comma-separate values, for example --id-namespace R or --id-namespace AC,R.",
)
@click.option(
    "--verify-index",
    "check_index",
    is_flag=True,
    help="Check that the requirements index (README.md) links match actual domain files; report stale links and orphan files.",
)
@click.option(
    "--bootstrap",
    "init_scaffold",
    is_flag=True,
    help="Initialize docs scaffold (index + starter domain file) and exit.",
)
@click.option(
    "--force-yes",
    "--force-confirm",
    "confirm_yes",
    is_flag=True,
    help="Auto-confirm scaffold initialization (non-interactive friendly).",
)
@click.pass_context
def main(
    ctx: click.Context,
    check: bool,
    verbose: bool,
    emoji_columns: bool,
    interactive: bool,
    screen_write: bool | None,
    unsorted: bool,
    set_requirement_id: str | None,
    set_status: str | None,
    set_updates: tuple[str, ...],
    undo_last: bool,
    redo_last: bool,
    show_timeline: bool,
    show_history: bool,
    history_discard_branch: str | None,
    history_discard_save_label: str | None,
    history_label_branch: str | None,
    history_branch_label: str | None,
    history_gc: bool,
    history_prune_now: bool,
    history_checkout_branch: str | None,
    history_cherry_pick: str | None,
    history_replay_branch: str | None,
    history_target_branch: str | None,
    timeline_filter_branch: str | None,
    timeline_filter_actor: str | None,
    timeline_filter_command: str | None,
    timeline_filter_file: str | None,
    timeline_filter_requirement_id: str | None,
    timeline_filter_transition: str | None,
    timeline_filter_from: str | None,
    timeline_filter_to: str | None,
    dry_run: bool,
    set_file_input: str | None,
    rename_id_prefix: str | None,
    set_file: str | None,
    set_blocked_reason: str | None,
    set_deprecated_reason: str | None,
    set_priority_updates: tuple[str, ...],
    set_flagged_updates: tuple[str, ...],
    priority_mode: bool,
    show_priority_summary: bool,
    filter_status: tuple[str, ...],
    filter_priority: tuple[str, ...],
    filter_flagged: bool,
    filter_no_flag: bool,
    filter_has_link: bool,
    filter_no_link: bool,
    filter_sub_domain: tuple[str, ...],
    filter_ids_file: str | None,
    tree: bool,
    list_output: bool,
    summary_table: bool,
    sort_strategy: str,
    theme: str | None,
    rollup_mode: bool,
    rollup_map_entries: tuple[str, ...],
    rollup_config: str | None,
    json_output: bool,
    include_body: bool,
    resume_filter: bool,
    strip_status_emojis: bool,
    restore_status_emojis: bool,
    init_priorities: bool,
    default_priority: str,
    state_dir: str,
    repo_root: Path,
    requirements_dir: str | None,
    id_prefixes: tuple[str, ...],
    check_index: bool,
    init_scaffold: bool,
    confirm_yes: bool,
    targets: tuple[str, ...],
    status_config: str | None,
    priorities_config: str | None,
) -> None:
    repo_root_source = ctx.get_parameter_source("repo_root")
    repo_root_explicit = repo_root_source != click.core.ParameterSource.DEFAULT

    root_discovery_message: str | None = None
    if repo_root_explicit:
        repo_root = repo_root.resolve()
    else:
        discovered_root, discovered_source = discover_project_root(Path.cwd())
        repo_root = discovered_root
        root_discovery_message = (
            f"Auto-discovered project root: {repo_root} ({discovered_source})"
        )

    # Load project config from .rqmd.json
    try:
        config = load_config(repo_root)
        validate_config(config)
    except ValueError as exc:
        raise click.ClickException(f"Config error: {exc}") from exc

    try:
        standalone_statuses = load_statuses_file(repo_root, status_config)
        effective_statuses = standalone_statuses if standalone_statuses is not None else config.get("statuses")
        configure_status_catalog(effective_statuses)
    except ValueError as exc:
        raise click.ClickException(f"Config error: {exc}") from exc

    try:
        standalone_priorities = load_priorities_file(repo_root, priorities_config)
        effective_priorities = standalone_priorities if standalone_priorities is not None else config.get("priorities")
        configure_priority_catalog(effective_priorities)
    except ValueError as exc:
        raise click.ClickException(f"Config error: {exc}") from exc
    ctx.call_on_close(lambda: configure_priority_catalog(None))
    ctx.call_on_close(lambda: configure_status_catalog(None))

    # Apply config defaults (CLI flags override config file)
    if not requirements_dir and "requirements_dir" in config:
        requirements_dir = config["requirements_dir"]
    if not id_prefixes and "id_prefix" in config:
        id_prefixes = (config["id_prefix"],)
    if sort_strategy == "standard" and "sort_strategy" in config:
        sort_strategy = config["sort_strategy"]
    if state_dir == "system-temp" and "state_dir" in config:
        state_dir = config["state_dir"]

    # Resolve screen-write mode precedence: CLI > project config > user config > TTY default.
    user_config = load_user_config()

    def _coerce_bool(value: object) -> bool | None:
        return value if isinstance(value, bool) else None

    if screen_write is not None:
        screen_write_enabled = bool(screen_write)
    else:
        project_screen_write = _coerce_bool(config.get("screen_write"))
        user_screen_write = _coerce_bool(user_config.get("screen_write"))
        if project_screen_write is not None:
            screen_write_enabled = project_screen_write
        elif user_screen_write is not None:
            screen_write_enabled = user_screen_write
        else:
            screen_write_enabled = sys.stdout.isatty()

    menus_mod.reset_render_mode_controller()
    menus_mod.set_screen_write_enabled(screen_write_enabled)
    menus_mod.set_screen_write_forced(screen_write is not None)
    ctx.call_on_close(lambda: menus_mod.set_screen_write_forced(False))

    # Resolve interactive zebra striping color from theme detection.
    from .theme import detect_theme, is_accessible_zebra_bg, resolve_zebra_bg
    _detected_theme, _theme_source = detect_theme(
        cli_override=theme,
        config_override=str(config.get("theme") or ""),
    )
    zebra_bg = resolve_zebra_bg(
        _detected_theme,
        config_zebra_bg=str(config.get("ui", {}).get("zebra_bg") or "") or None,
    )
    colorized_redraw_enabled = is_accessible_zebra_bg(zebra_bg, _detected_theme)
    if not colorized_redraw_enabled:
        zebra_bg = None
    menus_mod.set_colorized_redraw_enabled(colorized_redraw_enabled)

    requested_init_prefix: str | None = None
    if id_prefixes:
        try:
            requested_init_prefix = normalize_id_prefixes(id_prefixes)[0]
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

    if unsorted and not json_output:
        click.echo(
            "Warning: --filesystem-order is deprecated and now acts as a compatibility alias because filesystem ordering is already the default.",
            err=True,
        )

    if root_discovery_message and not json_output:
        click.echo(root_discovery_message)

    if init_scaffold:
        if check or filter_status or filter_priority or filter_flagged or filter_no_flag or filter_has_link or filter_no_link or filter_sub_domain or filter_ids_file or set_requirement_id or set_status or set_updates or set_priority_updates or set_flagged_updates or set_file_input or set_file or undo_last or redo_last or tree or rollup_mode or targets:
            raise click.ClickException(
                "--bootstrap cannot be combined with --verify-summaries, --totals, positional ID, --filter-* / --as-tree, or --update-* options."
            )

        try:
            if requested_init_prefix:
                starter_prefix = requested_init_prefix
            elif confirm_yes:
                starter_prefix = "REQ"
            else:
                starter_prefix = prompt_for_init_prefix(default_prefix="REQ")
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

        created = initialize_requirements_scaffold(
            repo_root,
            requirements_dir or DEFAULT_REQUIREMENTS_DIR,
            starter_prefix=starter_prefix,
        )
        if json_output:
            payload = {
                "mode": "init",
                "requirements_dir": requirements_dir or DEFAULT_REQUIREMENTS_DIR,
                "starter_prefix": starter_prefix,
                "created_files": [format_path_display(path, repo_root) for path in created],
                "created_count": len(created),
            }
            _emit_json_payload(payload)
            raise SystemExit(0)

        if created:
            click.echo("Initialized requirement scaffold:")
            for path in created:
                click.echo(f"  + {path.relative_to(repo_root)}")
        else:
            click.echo("Requirement scaffold already present; no files created.")
        raise SystemExit(0)

    resolved_criteria_dir, criteria_dir_message = resolve_requirements_dir(repo_root, requirements_dir)
    resolved_requirements_dir_input = str(resolved_criteria_dir)
    if criteria_dir_message and not json_output:
        click.echo(criteria_dir_message)

    try:
        id_prefixes = resolve_id_prefixes(repo_root, resolved_requirements_dir_input, id_prefixes)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    domain_files = iter_domain_files(repo_root, resolved_requirements_dir_input)
    if not domain_files:
        missing_msg = f"No requirement markdown files found under: {format_path_display(resolved_criteria_dir, repo_root)}"
        hint_msg = "Hint: run 'rqmd --bootstrap' (interactive) or 'rqmd --bootstrap --force-yes' (automation) to create starter docs."

        if confirm_yes:
            starter_prefix = requested_init_prefix or "REQ"
            created = initialize_requirements_scaffold(
                repo_root,
                resolved_requirements_dir_input,
                starter_prefix=starter_prefix,
            )
            if created:
                click.echo("Initialized requirement scaffold:")
                for path in created:
                    click.echo(f"  + {path.relative_to(repo_root)}")
            else:
                click.echo("Requirement scaffold already present; no files created.")
            raise SystemExit(0)

        if (not sys.stdin.isatty()) or check or json_output or (not interactive):
            print(missing_msg, file=sys.stderr)
            print(hint_msg, file=sys.stderr)
            raise SystemExit(1)

        click.echo(missing_msg, err=True)
        should_init = click.confirm(
            "No requirement files found. Initialize a starter scaffold now?",
            default=False,
            show_default=True,
        )
        if not should_init:
            click.echo(hint_msg, err=True)
            raise SystemExit(1)

        try:
            starter_prefix = requested_init_prefix or prompt_for_init_prefix(default_prefix="REQ")
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc

        created = initialize_requirements_scaffold(
            repo_root,
            resolved_requirements_dir_input,
            starter_prefix=starter_prefix,
        )
        if created:
            click.echo("Initialized requirement scaffold:")
            for path in created:
                click.echo(f"  + {path.relative_to(repo_root)}")
        else:
            click.echo("Requirement scaffold already present; no files created.")
        raise SystemExit(0)

    # RQMD-PORTABILITY-009: validate files are readable before proceeding
    validate_files_readable(domain_files, repo_root)

    include_status_emojis = infer_include_status_emojis(domain_files)

    if rename_id_prefix:
        if (
            check
            or filter_status
            or filter_priority
            or filter_flagged
            or filter_no_flag
            or filter_has_link
            or filter_no_link
            or filter_sub_domain
            or filter_ids_file
            or set_requirement_id
            or set_status
            or set_updates
            or set_priority_updates
            or set_flagged_updates
            or set_file_input
            or set_file
            or undo_last
            or redo_last
            or tree
            or rollup_mode
            or targets
            or strip_status_emojis
            or restore_status_emojis
            or init_priorities
            or init_scaffold
        ):
            raise click.ClickException(
                "--rename-id-prefix cannot be combined with check/filter/update/tree/rollup/lookup/bootstrap or migration modes."
            )

        old_prefix, new_prefix = _parse_prefix_rename_spec(rename_id_prefix)
        changed_files: list[dict[str, object]] = []
        existing_new_ids: set[str] = set()
        rename_target_ids: set[str] = set()

        for path in domain_files:
            text = path.read_text(encoding="utf-8")
            ids = _collect_requirement_ids_from_text(text)
            existing_new_ids.update({rid for rid in ids if rid.startswith(f"{new_prefix}-")})
            rename_target_ids.update({rid for rid in ids if rid.startswith(f"{old_prefix}-")})

        projected_new_ids = {f"{new_prefix}-{rid.split('-', 1)[1]}" for rid in rename_target_ids}
        conflicts = sorted(existing_new_ids.intersection(projected_new_ids - rename_target_ids))
        if conflicts:
            preview = ", ".join(conflicts[:5])
            suffix = "..." if len(conflicts) > 5 else ""
            raise click.ClickException(
                "--rename-id-prefix conflict: target prefix already exists for one or more IDs "
                f"({preview}{suffix})."
            )

        total_replacements = 0
        for path in domain_files:
            original = path.read_text(encoding="utf-8")
            updated, replacements = _rename_requirement_id_prefix_in_text(original, old_prefix, new_prefix)
            if replacements == 0:
                continue
            total_replacements += replacements
            if not dry_run:
                path.write_text(updated, encoding="utf-8")
                process_file(
                    path,
                    check_only=False,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=show_priority_summary,
                )
            changed_files.append(
                {
                    "path": format_path_display(path, repo_root),
                    "replacements": replacements,
                }
            )

        payload = {
            "mode": "rename-id-prefix",
            "old_prefix": old_prefix,
            "new_prefix": new_prefix,
            "dry_run": dry_run,
            "changed_file_count": len(changed_files),
            "replacement_count": total_replacements,
            "files": changed_files,
        }
        if json_output:
            _emit_json_payload(payload)
        else:
            action = "Would update" if dry_run else "Updated"
            click.echo(f"{action} {len(changed_files)} file(s); {total_replacements} replacement(s).")
            for entry in changed_files:
                click.echo(f"  - {entry['path']}: {entry['replacements']}")
        raise SystemExit(0)

    if strip_status_emojis and restore_status_emojis:
        raise click.ClickException("Use either --strip-status-icons or --restore-status-icons, not both.")

    if init_priorities:
        if (
            check
            or filter_status
            or filter_priority
            or filter_flagged
            or filter_no_flag
            or filter_has_link
            or filter_no_link
            or filter_sub_domain
            or filter_ids_file
            or set_requirement_id
            or set_status
            or set_updates
            or set_priority_updates
            or set_flagged_updates
            or set_file_input
            or set_file
            or undo_last
            or redo_last
            or tree
            or rollup_mode
            or targets
            or strip_status_emojis
            or restore_status_emojis
        ):
            raise click.ClickException(
                "--seed-priorities cannot be combined with check/filter/set/tree/rollup/lookup or emoji strip/restore modes."
            )

        canonical_default_priority = normalize_priority_input(default_priority)

        changed_paths: list[Path] = []
        for path in domain_files:
            requirements = parse_requirements(path, id_prefixes=id_prefixes)
            missing = [r for r in requirements if r.get("priority_line") is None and isinstance(r.get("status_line"), int)]
            if not missing:
                continue

            lines = path.read_text(encoding="utf-8").splitlines()
            inserted = False
            for requirement in sorted(missing, key=lambda r: int(r["status_line"]), reverse=True):
                status_line = int(requirement["status_line"])
                blocked_line = requirement.get("blocked_reason_line")
                deprecated_line = requirement.get("deprecated_reason_line")

                insert_after = status_line
                if isinstance(blocked_line, int):
                    insert_after = max(insert_after, blocked_line)
                if isinstance(deprecated_line, int):
                    insert_after = max(insert_after, deprecated_line)

                lines.insert(insert_after + 1, f"- **Priority:** {canonical_default_priority}")
                inserted = True

            if inserted:
                if not dry_run:
                    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
                    try:
                        process_file(
                            path,
                            check_only=False,
                            include_status_emojis=include_status_emojis,
                            include_priority_summary=show_priority_summary,
                        )
                    except UnknownStatusValueError as exc:
                        _raise_unknown_status_error("init-priorities", exc, repo_root, json_output=json_output)
                changed_paths.append(path)

        try:
            _, table_rows = collect_summary_rows(
                domain_files,
                check_only=True,
                display_name_fn=display_name_from_h1,
                include_status_emojis=include_status_emojis,
                include_priority_summary=show_priority_summary,
            )
        except UnknownStatusValueError as exc:
            _raise_unknown_status_error("init-priorities", exc, repo_root, json_output=json_output)

        if json_output:
            payload = {
                "mode": "init-priorities",
                "requirements_dir": format_path_display(resolved_criteria_dir, repo_root),
                "default_priority": canonical_default_priority,
                "dry_run": dry_run,
                "changed_files": [format_path_display(path, repo_root) for path in changed_paths],
                "changed_count": len(changed_paths),
            }
            _emit_json_payload(payload)
            raise SystemExit(0)

        if summary_table:
            print_summary_table(table_rows, emoji_columns=emoji_columns)
        verb = "Would initialize" if dry_run else "Initialized"
        click.echo(f"{verb} priorities in {len(changed_paths)} file(s) using {canonical_default_priority}.")
        raise SystemExit(0)

    if strip_status_emojis or restore_status_emojis:
        if check or filter_status or filter_priority or filter_flagged or filter_no_flag or filter_has_link or filter_no_link or filter_sub_domain or filter_ids_file or set_requirement_id or set_status or set_updates or set_priority_updates or set_flagged_updates or set_file_input or set_file or undo_last or redo_last or tree or rollup_mode or targets:
            raise click.ClickException(
                "Emoji strip/restore modes cannot be combined with --verify-summaries, --totals, positional ID, --filter-* / --as-tree, or --update-* options."
            )

        include_status_emojis = not strip_status_emojis
        mode_name = "restore-status-emojis" if restore_status_emojis else "strip-status-emojis"
        try:
            changed_paths, table_rows = collect_summary_rows(
                domain_files,
                check_only=False,
                display_name_fn=display_name_from_h1,
                include_status_emojis=include_status_emojis,
                include_priority_summary=show_priority_summary,
            )
        except UnknownStatusValueError as exc:
            _raise_unknown_status_error(mode_name, exc, repo_root, json_output=json_output)
        if summary_table and not json_output:
            print_summary_table(table_rows, emoji_columns=emoji_columns)

        if json_output:
            payload = {
                "mode": mode_name,
                "requirements_dir": format_path_display(resolved_criteria_dir, repo_root),
                "changed_files": [format_path_display(path, repo_root) for path in changed_paths],
                "changed_count": len(changed_paths),
            }
            _emit_json_payload(payload)
            raise SystemExit(0)

        click.echo(f"Updated {len(changed_paths)} file(s) in {mode_name} mode.")
        raise SystemExit(0)

    # RQMD-CORE-013: --verify-index mode — compare index links with actual domain files
    if check_index:
        index_path = resolved_criteria_dir / "README.md"
        if not index_path.exists():
            click.echo(f"No requirements index found at: {format_path_display(index_path, repo_root)}", err=True)
            click.echo("  Hint: run 'rqmd --bootstrap' to create a starter scaffold.", err=True)
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

    explicit_target_tokens = list(targets)
    if filter_ids_file:
        explicit_target_tokens.extend(parse_target_token_file(repo_root, filter_ids_file))

    positional_domain_files: list[Path] = []
    if not filter_ids_file:
        seen_files: set[Path] = set()
        for token in targets:
            matched_path = resolve_positional_domain_file_token(repo_root, domain_files, token)
            if matched_path and matched_path not in seen_files:
                positional_domain_files.append(matched_path)
                seen_files.add(matched_path)

    if len(positional_domain_files) > 1:
        display = ", ".join(format_path_display(path, repo_root) for path in positional_domain_files)
        raise click.ClickException(f"Provide at most one positional domain file path at a time; got: {display}")

    positional_domain_file = positional_domain_files[0] if positional_domain_files else None
    if positional_domain_file and not filter_ids_file:
        explicit_target_tokens = [
            token
            for token in explicit_target_tokens
            if resolve_positional_domain_file_token(repo_root, domain_files, token) is None
        ]

    has_non_lookup_mode = bool(
        check
        or filter_status
        or filter_priority
        or filter_flagged
        or filter_no_flag
        or filter_has_link
        or filter_no_link
        or filter_sub_domain
        or set_requirement_id
        or set_status
        or set_updates
        or set_priority_updates
        or set_flagged_updates
        or set_file_input
        or set_file
        or tree
        or rollup_mode
        or json_output
        or not interactive
    )

    # Preserve legacy single-ID lookup mode and prioritize explicit ID lookup over positional file hints.
    if not filter_ids_file and not has_non_lookup_mode:
        for token in targets:
            exact_id_matches = []
            for path in domain_files:
                requirement = find_requirement_by_id(path, token, id_prefixes=id_prefixes)
                if requirement:
                    exact_id_matches.append((path, requirement))
            if len(exact_id_matches) == 1:
                raise SystemExit(
                    lookup_criterion_interactive(
                        repo_root,
                        domain_files,
                        requirement_id=token,
                        emoji_columns=emoji_columns,
                        id_prefixes=id_prefixes,
                        include_status_emojis=include_status_emojis,
                        priority_mode=priority_mode,
                        include_priority_summary=show_priority_summary,
                    )
                )

    if positional_domain_file and not filter_ids_file and not has_non_lookup_mode:
        unresolved_id_like = [
            token
            for token in targets
            if resolve_positional_domain_file_token(repo_root, domain_files, token) is None
            and looks_like_requirement_id_token(token, id_prefixes)
        ]
        if unresolved_id_like:
            missing = ", ".join(unresolved_id_like)
            click.echo(
                f"Warning: requirement ID not found ({missing}); opening {format_path_display(positional_domain_file, repo_root)} instead.",
                err=True,
            )

        raise SystemExit(
            interactive_update_loop(
                repo_root,
                resolved_requirements_dir_input,
                domain_files,
                emoji_columns=emoji_columns,
                sort_files=False,
                sort_strategy=sort_strategy,
                id_prefixes=id_prefixes,
                include_status_emojis=include_status_emojis,
                priority_mode=priority_mode,
                include_priority_summary=show_priority_summary,
                initial_file_path=positional_domain_file,
                zebra_bg=zebra_bg,
            )
        )

    if positional_domain_file and has_non_lookup_mode:
        domain_files = [positional_domain_file]

    if explicit_target_tokens:
        if check or filter_status or filter_priority or filter_flagged or filter_no_flag or filter_has_link or filter_no_link or filter_sub_domain or set_requirement_id or set_status or set_updates or set_priority_updates or set_flagged_updates or set_file_input or set_file or rollup_mode:
            raise click.ClickException(
                "Explicit target selection cannot be combined with --verify-summaries, --totals, --filter-*, or --update-* options."
            )
        selected_items = resolve_target_tokens(
            repo_root,
            domain_files,
            explicit_target_tokens,
            id_prefixes=id_prefixes,
        )

        if json_output:
            payload = build_targeted_criteria_payload(
                repo_root,
                resolved_criteria_dir,
                selected_items,
                explicit_target_tokens,
                include_body=include_body,
                id_prefixes=id_prefixes,
            )
            _emit_json_payload(payload)
            raise SystemExit(0)

        targeted_by_file: dict[Path, list[dict[str, object]]] = {}
        for path, requirement in selected_items:
            targeted_by_file.setdefault(path, []).append(requirement)

        if list_output:
            print_criteria_list(repo_root, targeted_by_file, ", ".join(explicit_target_tokens), filter_label="targets")
            raise SystemExit(0)

        if tree or not interactive:
            print_criteria_tree(repo_root, targeted_by_file, ", ".join(explicit_target_tokens), filter_label="targets")
            raise SystemExit(0)

        raise SystemExit(
            focused_target_interactive_loop(
                repo_root,
                domain_files,
                selected_items=selected_items,
                target_tokens=explicit_target_tokens,
                emoji_columns=emoji_columns,
                id_prefixes=id_prefixes,
                resume_filter=resume_filter,
                state_dir=state_dir,
                include_status_emojis=include_status_emojis,
                priority_mode=priority_mode,
                include_priority_summary=show_priority_summary,
            )
        )

    try:
        changed_paths, table_rows = collect_summary_rows(
            domain_files,
            check_only=(check or dry_run),
            display_name_fn=display_name_from_h1,
            include_status_emojis=include_status_emojis,
            include_priority_summary=show_priority_summary,
        )
    except UnknownStatusValueError as exc:
        mode_name = "check" if check else ("rollup" if rollup_mode else "summary")
        _raise_unknown_status_error(mode_name, exc, repo_root, json_output=json_output)

    path_to_row = {path: row for path, row in zip(domain_files, table_rows)}
    file_rows_for_sort: list[tuple[Path, dict[str, int], str]] = []
    for path in domain_files:
        row = path_to_row[path]
        counts = {
            label: int(row[index + 1])
            for index, (label, _slug) in enumerate(STATUS_ORDER)
        }
        file_rows_for_sort.append((path, counts, display_name_from_h1(path)))

    ordered_file_rows = workflows_mod.sort_file_rows_for_strategy(
        file_rows_for_sort,
        sort_strategy=sort_strategy,
    )
    ordered_paths = [path for path, _counts, _label in ordered_file_rows]
    table_rows = [path_to_row[path] for path in ordered_paths]

    summary_payload = build_summary_payload(repo_root, resolved_criteria_dir, domain_files, changed_paths)

    if summary_table and verbose and not json_output and not rollup_mode:
        for row, path in zip(table_rows, ordered_paths):
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
        if check or filter_status or filter_priority or filter_flagged or filter_no_flag or filter_has_link or filter_no_link or set_requirement_id or set_status or set_updates or set_priority_updates or set_flagged_updates or set_file_input or set_file or tree:
            raise click.ClickException("--totals cannot be combined with --verify-summaries, --status, --as-tree, or --update-* options.")
        rollup_columns, rollup_source = resolve_rollup_columns(
            repo_root,
            cli_rollup_map=rollup_map_entries,
            rollup_config_path=rollup_config,
        )
        rollup_column_values = compute_rollup_column_values(summary_payload["totals"], rollup_columns)

        if json_output:
            payload = {
                "mode": "rollup",
                "requirements_dir": format_path_display(resolved_criteria_dir, repo_root),
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
            _emit_json_payload(payload)
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
            _emit_json_payload(payload)
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

    status_filters_raw = _expand_filter_values(filter_status)
    priority_filters_raw = _expand_filter_values(filter_priority)
    sub_domain_filters_raw = _expand_filter_values(filter_sub_domain)

    has_filter_mode = bool(
        status_filters_raw or priority_filters_raw or filter_flagged or filter_no_flag or filter_has_link or filter_no_link or sub_domain_filters_raw
    )

    if filter_flagged and filter_no_flag:
        raise click.ClickException("--flagged and --no-flag are mutually exclusive.")
    if filter_has_link and filter_no_link:
        raise click.ClickException("--has-link and --no-link are mutually exclusive.")

    # --as-tree/--as-list without an active filter mode is a no-op guard
    if (tree or list_output) and not (has_filter_mode or explicit_target_tokens):
        raise click.ClickException("--as-tree/--as-list requires --status, --priority, --flagged/--no-flag, --has-link/--no-link, --sub-domain, or explicit target tokens.")

    if has_filter_mode:
        if check or set_requirement_id or set_status or set_updates or set_priority_updates or set_flagged_updates or set_file_input or set_file:
            raise click.ClickException("Filters cannot be combined with --verify-summaries or mutation options.")

        normalized_status_filters: list[str] = []
        for raw_status in status_filters_raw:
            try:
                normalized_status_filters.append(normalize_status_input(raw_status))
            except click.ClickException as exc:
                mode_name = "filter-status" if len(status_filters_raw) == 1 else "filter-combined"
                if json_output and _emit_json_ambiguity_error(mode_name, exc):
                    raise SystemExit(1)
                raise

        normalized_priority_filters: list[str] = []
        for raw_priority in priority_filters_raw:
            try:
                normalized_priority_filters.append(normalize_priority_input(raw_priority))
            except click.ClickException as exc:
                mode_name = "filter-priority" if len(priority_filters_raw) == 1 else "filter-combined"
                if json_output and _emit_json_ambiguity_error(mode_name, exc):
                    raise SystemExit(1)
                raise

        is_status_only_single = (
            len(normalized_status_filters) == 1
            and not normalized_priority_filters
            and not filter_flagged
            and not filter_no_flag
            and not filter_has_link
            and not filter_no_link
            and not sub_domain_filters_raw
        )
        is_priority_only_single = (
            len(normalized_priority_filters) == 1
            and not normalized_status_filters
            and not filter_flagged
            and not filter_no_flag
            and not filter_has_link
            and not filter_no_link
            and not sub_domain_filters_raw
        )
        is_flagged_only = (
            filter_flagged
            and not normalized_status_filters
            and not normalized_priority_filters
            and not filter_has_link
            and not filter_no_link
            and not sub_domain_filters_raw
        )
        is_sub_domain_only_single = (
            len(sub_domain_filters_raw) == 1
            and not normalized_status_filters
            and not normalized_priority_filters
            and not filter_flagged
            and not filter_no_flag
        )
        is_no_flag_only = (
            filter_no_flag
            and not normalized_status_filters
            and not normalized_priority_filters
            and not filter_has_link
            and not filter_no_link
            and not sub_domain_filters_raw
        )
        is_has_link_only = (
            filter_has_link
            and not normalized_status_filters
            and not normalized_priority_filters
            and not filter_flagged
            and not filter_no_flag
            and not sub_domain_filters_raw
        )
        is_no_link_only = (
            filter_no_link
            and not normalized_status_filters
            and not normalized_priority_filters
            and not filter_flagged
            and not filter_no_flag
            and not sub_domain_filters_raw
        )

        # Legacy single-filter behavior: keep existing modes, payload keys, and
        # interactive walk behavior for status/priority.
        if is_status_only_single:
            normalized_status = normalized_status_filters[0]
            criteria_by_file = collect_requirements_by_status(
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
                    include_body=include_body,
                    id_prefixes=id_prefixes,
                )
                _emit_json_payload(payload)
                raise SystemExit(0)
            if list_output:
                print_criteria_list(repo_root, criteria_by_file, normalized_status, filter_label="status")
                raise SystemExit(0)
            if tree or not interactive:
                print_criteria_tree(repo_root, criteria_by_file, normalized_status, filter_label="status")
                raise SystemExit(0)
            raise SystemExit(
                filtered_interactive_loop(
                    repo_root,
                    domain_files,
                    target_status=normalized_status,
                    emoji_columns=emoji_columns,
                    id_prefixes=id_prefixes,
                    resume_filter=resume_filter,
                    state_dir=state_dir,
                    include_status_emojis=include_status_emojis,
                    priority_mode=priority_mode,
                    include_priority_summary=show_priority_summary,
                )
            )

        if is_priority_only_single:
            normalized_priority = normalized_priority_filters[0]
            criteria_by_file = collect_requirements_by_priority(
                repo_root,
                domain_files,
                normalized_priority,
                id_prefixes=id_prefixes,
            )
            if json_output:
                payload = build_filtered_criteria_payload(
                    repo_root,
                    resolved_criteria_dir,
                    criteria_by_file,
                    normalized_priority,
                    include_body=include_body,
                    id_prefixes=id_prefixes,
                    filter_mode="filter-priority",
                    filter_label="priority",
                )
                _emit_json_payload(payload)
                raise SystemExit(0)
            if list_output:
                print_criteria_list(repo_root, criteria_by_file, normalized_priority, filter_label="priority")
                raise SystemExit(0)
            if tree or not interactive:
                print_criteria_tree(repo_root, criteria_by_file, normalized_priority, filter_label="priority")
                raise SystemExit(0)
            raise SystemExit(
                filtered_priority_interactive_loop(
                    repo_root,
                    domain_files,
                    target_priority=normalized_priority,
                    emoji_columns=emoji_columns,
                    id_prefixes=id_prefixes,
                    resume_filter=resume_filter,
                    state_dir=state_dir,
                    include_status_emojis=include_status_emojis,
                    priority_mode=priority_mode,
                    include_priority_summary=show_priority_summary,
                )
            )

        if is_flagged_only:
            criteria_by_file = collect_requirements_by_flagged(
                repo_root,
                domain_files,
                True,
                id_prefixes=id_prefixes,
            )

            if json_output:
                payload = build_filtered_criteria_payload(
                    repo_root,
                    resolved_criteria_dir,
                    criteria_by_file,
                    True,
                    include_body=include_body,
                    id_prefixes=id_prefixes,
                    filter_mode="filter-flagged",
                    filter_label="flagged",
                )
                _emit_json_payload(payload)
                raise SystemExit(0)

            if list_output:
                print_criteria_list(repo_root, criteria_by_file, "flagged=true", filter_label="flagged")
                raise SystemExit(0)

            print_criteria_tree(repo_root, criteria_by_file, "flagged=true", filter_label="flagged")
            raise SystemExit(0)

        if is_no_flag_only:
            criteria_by_file = collect_requirements_by_flagged(
                repo_root,
                domain_files,
                False,
                id_prefixes=id_prefixes,
            )

            if json_output:
                payload = build_filtered_criteria_payload(
                    repo_root,
                    resolved_criteria_dir,
                    criteria_by_file,
                    False,
                    include_body=include_body,
                    id_prefixes=id_prefixes,
                    filter_mode="filter-flagged",
                    filter_label="flagged",
                )
                _emit_json_payload(payload)
                raise SystemExit(0)

            if list_output:
                print_criteria_list(repo_root, criteria_by_file, "flagged=false", filter_label="flagged")
                raise SystemExit(0)

            print_criteria_tree(repo_root, criteria_by_file, "flagged=false", filter_label="flagged")
            raise SystemExit(0)

        if is_has_link_only:
            criteria_by_file = collect_requirements_by_links(
                repo_root,
                domain_files,
                True,
                id_prefixes=id_prefixes,
            )

            if json_output:
                payload = build_filtered_criteria_payload(
                    repo_root,
                    resolved_criteria_dir,
                    criteria_by_file,
                    {"has_link": True, "no_link": False},
                    include_body=include_body,
                    id_prefixes=id_prefixes,
                    filter_mode="filter-links",
                    filter_label="links",
                )
                _emit_json_payload(payload)
                raise SystemExit(0)

            if list_output:
                print_criteria_list(repo_root, criteria_by_file, "has-link=true", filter_label="links")
                raise SystemExit(0)

            print_criteria_tree(repo_root, criteria_by_file, "has-link=true", filter_label="links")
            raise SystemExit(0)

        if is_no_link_only:
            criteria_by_file = collect_requirements_by_links(
                repo_root,
                domain_files,
                False,
                id_prefixes=id_prefixes,
            )

            if json_output:
                payload = build_filtered_criteria_payload(
                    repo_root,
                    resolved_criteria_dir,
                    criteria_by_file,
                    {"has_link": False, "no_link": True},
                    include_body=include_body,
                    id_prefixes=id_prefixes,
                    filter_mode="filter-links",
                    filter_label="links",
                )
                _emit_json_payload(payload)
                raise SystemExit(0)

            if list_output:
                print_criteria_list(repo_root, criteria_by_file, "has-link=false", filter_label="links")
                raise SystemExit(0)

            print_criteria_tree(repo_root, criteria_by_file, "has-link=false", filter_label="links")
            raise SystemExit(0)

        if is_sub_domain_only_single:
            sub_domain_value = sub_domain_filters_raw[0]
            criteria_by_file = collect_requirements_by_sub_domain(
                repo_root,
                domain_files,
                sub_domain_value,
                id_prefixes=id_prefixes,
            )

            if json_output:
                payload = build_filtered_criteria_payload(
                    repo_root,
                    resolved_criteria_dir,
                    criteria_by_file,
                    sub_domain_value,
                    include_body=include_body,
                    id_prefixes=id_prefixes,
                    filter_mode="filter-sub-domain",
                    filter_label="sub_domain",
                )
                _emit_json_payload(payload)
                raise SystemExit(0)

            if list_output:
                print_criteria_list(repo_root, criteria_by_file, sub_domain_value, filter_label="sub_domain")
                raise SystemExit(0)

            print_criteria_tree(repo_root, criteria_by_file, sub_domain_value, filter_label="sub_domain")
            raise SystemExit(0)

        # Combined filter mode:
        # - OR across different filter families
        # - AND within each family
        criteria_by_file = collect_requirements_by_filters(
            repo_root,
            domain_files,
            status_filters=tuple(normalized_status_filters),
            priority_filters=tuple(normalized_priority_filters),
            flagged_filters=(True,) if filter_flagged else ((False,) if filter_no_flag else ()),
            link_filters=(True,) if filter_has_link else ((False,) if filter_no_link else ()),
            sub_domain_filters=tuple(sub_domain_filters_raw),
            id_prefixes=id_prefixes,
        )

        filter_summary: dict[str, object] = {
            "status": normalized_status_filters,
            "priority": normalized_priority_filters,
            "flagged": True if filter_flagged else (False if filter_no_flag else None),
            "links": True if filter_has_link else (False if filter_no_link else None),
            "sub_domain": list(sub_domain_filters_raw),
            "logic": {
                "across_flags": "or",
                "within_flag": "and",
            },
        }

        label_parts: list[str] = []
        if normalized_status_filters:
            label_parts.append(f"status={'+'.join(normalized_status_filters)}")
        if normalized_priority_filters:
            label_parts.append(f"priority={'+'.join(normalized_priority_filters)}")
        if filter_flagged:
            label_parts.append("flagged=true")
        if filter_no_flag:
            label_parts.append("flagged=false")
        if filter_has_link:
            label_parts.append("has-link=true")
        if filter_no_link:
            label_parts.append("has-link=false")
        if sub_domain_filters_raw:
            label_parts.append(f"sub-domain={'+'.join(sub_domain_filters_raw)}")
        combined_label = " | ".join(label_parts) if label_parts else "combined filters"

        if json_output:
            payload = build_filtered_criteria_payload(
                repo_root,
                resolved_criteria_dir,
                criteria_by_file,
                filter_summary,
                include_body=include_body,
                id_prefixes=id_prefixes,
                filter_mode="filter-combined",
                filter_label="filters",
            )
            _emit_json_payload(payload)
            raise SystemExit(0)

        if list_output:
            print_criteria_list(repo_root, criteria_by_file, combined_label, filter_label="combined")
            raise SystemExit(0)

        if tree or not interactive:
            print_criteria_tree(repo_root, criteria_by_file, combined_label, filter_label="combined")
            raise SystemExit(0)

        selected_items: list[tuple[Path, dict[str, object]]] = []
        for path in domain_files:
            for requirement in criteria_by_file.get(path, []):
                selected_items.append((path, requirement))

        target_tokens: list[str] = []
        target_tokens.extend(f"status:{value}" for value in normalized_status_filters)
        target_tokens.extend(f"priority:{value}" for value in normalized_priority_filters)
        if filter_flagged:
            target_tokens.append("flagged:true")
        if filter_no_flag:
            target_tokens.append("flagged:false")
        if filter_has_link:
            target_tokens.append("has-link:true")
        if filter_no_link:
            target_tokens.append("has-link:false")
        target_tokens.extend(f"sub-domain:{value}" for value in sub_domain_filters_raw)

        raise SystemExit(
            focused_target_interactive_loop(
                repo_root,
                domain_files,
                selected_items=selected_items,
                target_tokens=target_tokens,
                emoji_columns=emoji_columns,
                id_prefixes=id_prefixes,
                resume_filter=resume_filter,
                state_dir=state_dir,
                include_status_emojis=include_status_emojis,
                priority_mode=priority_mode,
                include_priority_summary=show_priority_summary,
            )
        )

    timeline_filter_requested = bool(
        timeline_filter_branch
        or timeline_filter_actor
        or timeline_filter_command
        or timeline_filter_file
        or timeline_filter_requirement_id
        or timeline_filter_transition
        or timeline_filter_from
        or timeline_filter_to
    )
    if timeline_filter_requested and not show_timeline:
        raise click.ClickException("--timeline-* filters require --timeline.")
    if history_target_branch and not (history_cherry_pick or history_replay_branch):
        raise click.ClickException(
            "--history-target-branch requires --history-cherry-pick or --history-replay-branch."
        )
    if history_discard_save_label and not history_discard_branch:
        raise click.ClickException("--history-discard-save-label requires --history-discard-branch.")
    if history_label_branch and not history_branch_label:
        raise click.ClickException("--history-label-branch requires --history-branch-label.")
    if history_branch_label and not history_label_branch:
        raise click.ClickException("--history-branch-label requires --history-label-branch.")
    if history_prune_now and not history_gc:
        raise click.ClickException("--history-prune-now requires --history-gc.")

    non_interactive_requested = bool(
        set_requirement_id
        or set_status
        or set_updates
        or set_priority_updates
        or set_flagged_updates
        or set_file_input
        or set_file
        or undo_last
        or redo_last
        or show_timeline
        or show_history
        or history_discard_branch
        or history_label_branch
        or history_gc
        or history_checkout_branch
        or history_cherry_pick
        or history_replay_branch
    )
    if non_interactive_requested and positional_domain_file and not set_file and not set_file_input:
        set_file = format_path_display(positional_domain_file, repo_root)

    if non_interactive_requested:
        if check:
            raise click.ClickException("--verify-summaries cannot be combined with --update-id/--update-status.")
        mode_count = (
            int(bool(set_updates))
            + int(bool(set_priority_updates))
            + int(bool(set_flagged_updates))
            + int(bool(set_file_input))
            + int(bool(set_requirement_id or set_status))
            + int(bool(undo_last))
            + int(bool(redo_last))
            + int(bool(show_timeline))
            + int(bool(show_history))
            + int(bool(history_discard_branch))
            + int(bool(history_label_branch))
            + int(bool(history_gc))
            + int(bool(history_checkout_branch))
            + int(bool(history_cherry_pick))
            + int(bool(history_replay_branch))
        )
        if mode_count > 1:
            raise click.ClickException(
                "Use exactly one non-interactive update mode: --undo, --redo, --timeline, --history, --history-discard-branch, --history-label-branch, --history-gc, --history-checkout-branch, --history-cherry-pick, --history-replay-branch, --update-file, --update ID=STATUS (repeatable), --update-priority ID=PRIORITY (repeatable), --update-flagged ID=true|false (repeatable), or --update-id with --update-status."
            )

        if history_label_branch:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            branch_name = history_label_branch.strip()
            label_text = str(history_branch_label or "").strip()
            branches = history_manager.get_branches()
            if branch_name not in branches:
                raise click.ClickException(f"Unknown history branch: {history_label_branch!r}")

            updated = history_manager.label_branch(branch_name, label_text)
            payload = {
                "mode": "history-label-branch",
                "branch": branch_name,
                "label": label_text,
                "updated": updated,
                "branches": history_manager.get_branches(),
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                if updated:
                    click.echo(f"Labeled history branch '{branch_name}' as '{label_text}'.")
                else:
                    click.echo(f"No branch label updated for '{branch_name}'.")
            raise SystemExit(0)

        if history_gc:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            confirmed = bool(confirm_yes)
            existing_stats = history_manager.get_storage_stats()
            if not confirmed:
                if not sys.stdin.isatty() or json_output:
                    raise click.ClickException(
                        "History garbage collection requires confirmation. Re-run with --force-yes."
                    )
                prune_label = " with immediate prune" if history_prune_now else ""
                confirmed = click.confirm(
                    (
                        f"Run history garbage collection{prune_label}? "
                        "This may permanently remove expired reflog objects from .rqmd/history/rqmd-history."
                    ),
                    default=False,
                    show_default=True,
                )

            if not confirmed:
                payload = {
                    "mode": "history-gc",
                    "ran": False,
                    "cancelled": True,
                    "prune_now": history_prune_now,
                    "before": existing_stats,
                    "after": existing_stats,
                }
                if json_output:
                    _emit_json_payload(payload)
                else:
                    click.echo("History garbage collection cancelled.")
                raise SystemExit(0)

            gc_result = history_manager.garbage_collect(prune_now=history_prune_now)
            payload = {
                "mode": "history-gc",
                "ran": True,
                "cancelled": False,
                **gc_result,
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                before = payload["before"]
                after = payload["after"]
                click.echo(
                    "History gc completed "
                    f"(loose objects: {before.get('count', 0)} -> {after.get('count', 0)}, "
                    f"packs: {before.get('packs', 0)} -> {after.get('packs', 0)})."
                )
            raise SystemExit(0)

        if history_cherry_pick:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            source_ref = history_cherry_pick.strip()
            resolved_entry = history_manager.resolve_ref(source_ref)
            if resolved_entry is None:
                raise click.ClickException(f"Unknown history entry reference: {history_cherry_pick!r}")

            target_branch = history_target_branch.strip() if history_target_branch else None
            if target_branch:
                branches = history_manager.get_branches()
                if target_branch not in branches:
                    raise click.ClickException(f"Unknown history branch: {history_target_branch!r}")

            commit_hash = str(resolved_entry.get("commit") or "")
            new_commit = history_manager.cherry_pick(commit_hash, target_branch=target_branch)
            current_branches = history_manager.get_branches()
            active_branch = next(
                (
                    name
                    for name, branch in current_branches.items()
                    if branch.get("is_current")
                ),
                "main",
            )
            payload = {
                "mode": "history-cherry-pick",
                "source_ref": source_ref,
                "source_commit": commit_hash,
                "source_entry_index": resolved_entry.get("entry_index"),
                "target_branch": target_branch or active_branch,
                "changed": new_commit is not None,
                "commit": new_commit,
                "branches": current_branches,
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                if new_commit is None:
                    click.echo(f"No cherry-pick applied for history ref '{source_ref}'.")
                else:
                    branch_label = payload["target_branch"] or "current"
                    click.echo(
                        f"Cherry-picked history ref '{source_ref}' onto '{branch_label}' as {new_commit}."
                    )
            raise SystemExit(0)

        if history_replay_branch:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            source_branch = history_replay_branch.strip()
            branches = history_manager.get_branches()
            if source_branch not in branches:
                raise click.ClickException(f"Unknown history branch: {history_replay_branch!r}")

            target_branch = history_target_branch.strip() if history_target_branch else None
            if target_branch and target_branch not in branches:
                raise click.ClickException(f"Unknown history branch: {history_target_branch!r}")

            replayed_commits = history_manager.replay_branch(source_branch, onto_branch=target_branch)
            current_branches = history_manager.get_branches()
            active_branch = next(
                (
                    name
                    for name, branch in current_branches.items()
                    if branch.get("is_current")
                ),
                "main",
            )
            payload = {
                "mode": "history-replay-branch",
                "source_branch": source_branch,
                "target_branch": target_branch or active_branch,
                "changed": bool(replayed_commits),
                "replayed_commits": replayed_commits or [],
                "replayed_count": len(replayed_commits or []),
                "branches": current_branches,
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                if not replayed_commits:
                    click.echo(f"No replay applied from history branch '{source_branch}'.")
                else:
                    click.echo(
                        f"Replayed {len(replayed_commits)} history commits from '{source_branch}' onto '{payload['target_branch']}'."
                    )
            raise SystemExit(0)

        if history_checkout_branch:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            branch_name = history_checkout_branch.strip()
            branches = history_manager.get_branches()
            if branch_name not in branches:
                raise click.ClickException(f"Unknown history branch: {history_checkout_branch!r}")

            commit_hash = history_manager.checkout_branch(branch_name)
            payload = {
                "mode": "history-checkout-branch",
                "branch": branch_name,
                "changed": commit_hash is not None,
                "commit": commit_hash,
                "branches": history_manager.get_branches(),
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                if commit_hash is None:
                    click.echo(f"No checkout performed for history branch '{branch_name}'.")
                else:
                    click.echo(f"Checked out history branch '{branch_name}' at {commit_hash}.")
            raise SystemExit(0)

        if history_discard_branch:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            branches = history_manager.get_branches()
            branch_name = history_discard_branch.strip()
            if branch_name not in branches:
                raise click.ClickException(f"Unknown history branch: {history_discard_branch!r}")

            branch_info = branches[branch_name]
            confirmed = bool(confirm_yes)
            if not confirmed:
                if not sys.stdin.isatty() or json_output:
                    raise click.ClickException(
                        "Discarding history branches requires confirmation. Re-run with --force-yes."
                    )
                confirmed = click.confirm(
                    (
                        f"Discard history branch '{branch_name}' "
                        f"({branch_info.get('entry_count', 0)} entries)? This cannot be undone."
                    ),
                    default=False,
                    show_default=True,
                )

            if not confirmed:
                payload = {
                    "mode": "history-discard-branch",
                    "branch": branch_name,
                    "saved_label": None,
                    "discarded": False,
                    "cancelled": True,
                    "branches": history_manager.get_branches(),
                }
                if json_output:
                    _emit_json_payload(payload)
                else:
                    click.echo("Branch discard cancelled.")
                raise SystemExit(0)

            saved_label = None
            if history_discard_save_label:
                label_text = history_discard_save_label.strip()
                if label_text:
                    history_manager.label_branch(branch_name, label_text)
                    saved_label = label_text

            discarded = history_manager.discard_branch(branch_name)
            payload = {
                "mode": "history-discard-branch",
                "branch": branch_name,
                "saved_label": saved_label,
                "discarded": discarded,
                "cancelled": False,
                "branches": history_manager.get_branches(),
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                if discarded:
                    if saved_label:
                        click.echo(
                            f"Saved label '{saved_label}' and discarded history branch '{branch_name}'."
                        )
                    else:
                        click.echo(f"Discarded history branch '{branch_name}'.")
                else:
                    click.echo(f"No branch discarded for '{branch_name}'.")
            raise SystemExit(0)

        if show_history:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            entries = history_manager.list_entries()
            timeline_graph = history_manager.get_timeline_graph()
            cursor = int(timeline_graph.get("cursor", -1))
            current_branch = str(timeline_graph.get("current_branch") or "main")

            entries_payload: list[dict[str, object]] = []
            for index, entry in enumerate(entries):
                commit = str(entry.get("commit") or "")
                entries_payload.append(
                    {
                        "entry_index": index,
                        "commit": commit,
                        "stable_id": history_manager.build_stable_history_id(commit) if commit else None,
                        "timestamp": entry.get("timestamp"),
                        "command": entry.get("command"),
                        "actor": entry.get("actor"),
                        "reason": entry.get("reason"),
                        "branch": entry.get("branch"),
                        "parent_commit": entry.get("parent_commit"),
                        "files": list(entry.get("files") or []),
                        "delta": entry.get("delta"),
                        "is_current_head": index == cursor,
                    }
                )

            payload = {
                "mode": "history-log",
                "requirements_dir": format_path_display(resolved_criteria_dir, repo_root),
                "entries_count": len(entries_payload),
                "cursor": cursor,
                "current_branch": current_branch,
                "can_undo": history_manager.can_undo(),
                "can_redo": history_manager.can_redo(),
                "entries": entries_payload,
            }

            if json_output:
                _emit_json_payload(payload)
            else:
                click.echo("=== History ===", err=False)
                click.echo(f"Entries: {payload['entries_count']}", err=False)
                click.echo(f"Current branch: {payload['current_branch']}", err=False)
                click.echo(f"Cursor: {payload['cursor']}", err=False)
                for item in entries_payload:
                    marker = " [HEAD]" if item["is_current_head"] else ""
                    delta = item.get("delta") if isinstance(item.get("delta"), dict) else {}
                    additions = int(delta.get("additions", 0)) if isinstance(delta, dict) else 0
                    deletions = int(delta.get("deletions", 0)) if isinstance(delta, dict) else 0
                    files_changed = int(delta.get("files_changed", 0)) if isinstance(delta, dict) else 0
                    reason = f": {item['reason']}" if item.get("reason") else ""
                    click.echo(
                        f"  {item['entry_index']}: {item['command']}{reason} ({item['branch']}) {item['commit']} +{additions}/-{deletions} {files_changed}f{marker}",
                        err=False,
                    )
            raise SystemExit(0)

        if undo_last or redo_last:
            if set_file or set_file_input or set_blocked_reason or set_deprecated_reason:
                raise click.ClickException("--undo/--redo cannot be combined with file-scoped update inputs or status note options.")

            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            try:
                commit_hash = history_manager.undo() if undo_last else history_manager.redo()
            except HistoryRestoreError as exc:
                raise click.ClickException(str(exc)) from exc

            mode_name = "undo" if undo_last else "redo"
            payload = {
                "mode": mode_name,
                "requirements_dir": format_path_display(resolved_criteria_dir, repo_root),
                "changed": commit_hash is not None,
                "commit": commit_hash,
                "can_undo": history_manager.can_undo(),
                "can_redo": history_manager.can_redo(),
                "history_depth": len(history_manager.list_entries()),
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                if commit_hash is None:
                    click.echo(f"No {mode_name} history available.")
                else:
                    verb = "Undid" if undo_last else "Redid"
                    click.echo(f"{verb} catalog to history commit {commit_hash}.")
            raise SystemExit(0)

        if show_timeline:
            history_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
            timeline_graph = history_manager.get_timeline_graph()
            timeline_nodes = {
                commit: dict(node)
                for commit, node in timeline_graph.get("nodes", {}).items()
            }

            _enrich_timeline_nodes_with_change_metadata(
                history_manager,
                timeline_nodes,
                id_prefixes=id_prefixes,
            )

            from_filter = _parse_iso8601_filter(timeline_filter_from, "--timeline-from") if timeline_filter_from else None
            to_filter = _parse_iso8601_filter(timeline_filter_to, "--timeline-to") if timeline_filter_to else None
            filtered_nodes = _filter_timeline_nodes(
                timeline_nodes,
                branch_filter=timeline_filter_branch,
                actor_filter=timeline_filter_actor,
                command_filter=timeline_filter_command,
                file_filter=timeline_filter_file,
                requirement_id_filter=timeline_filter_requirement_id,
                transition_filter=timeline_filter_transition,
                from_filter=from_filter,
                to_filter=to_filter,
            )

            timeline_graph["nodes"] = filtered_nodes
            timeline_graph["entries_count_filtered"] = len(filtered_nodes)
            timeline_graph["filters"] = {
                "branch": timeline_filter_branch,
                "actor": timeline_filter_actor,
                "command": timeline_filter_command,
                "file": timeline_filter_file,
                "requirement_id": timeline_filter_requirement_id,
                "transition": timeline_filter_transition,
                "from": timeline_filter_from,
                "to": timeline_filter_to,
            }

            branches = history_manager.get_branches()
            payload = {
                "timeline": timeline_graph,
                "branches": branches,
            }
            if json_output:
                _emit_json_payload(payload)
            else:
                # Display timeline in human-readable format
                click.echo("=== Timeline ===", err=False)
                click.echo(f"Entries: {timeline_graph['entries_count']}", err=False)
                click.echo(f"Entries (filtered): {timeline_graph['entries_count_filtered']}", err=False)
                click.echo(f"Current branch: {timeline_graph['current_branch']}", err=False)
                click.echo(f"Current head: {timeline_graph['cursor']}", err=False)
                click.echo("\n=== Branches ===", err=False)
                for branch_name, branch_info in branches.items():
                    marker = " (current)" if branch_info["is_current"] else ""
                    click.echo(f"  {branch_name}: {branch_info['entry_count']} entries{marker}", err=False)
                click.echo("\n=== Timeline Entries ===", err=False)
                ordered_nodes = sorted(
                    timeline_graph["nodes"].items(),
                    key=lambda item: int(item[1].get("entry_index", -1)),
                )
                for _commit, node in ordered_nodes:
                    marker = " [HEAD]" if node["is_current_head"] else ""
                    branch_label = f" ({node['branch']})" if node['branch'] != "main" else ""
                    click.echo(f"  {node['entry_index']}: {node['command']}{branch_label}{marker}", err=False)
            raise SystemExit(0)
        if set_updates:
            update_requests = [
                {
                    "requirement_id": cid,
                    "status": status,
                    "priority": None,
                    "flagged": None,
                    "file": set_file,
                    "blocked_reason": None,
                    "deprecated_reason": None,
                }
                for cid, status in (parse_set_entry(entry) for entry in set_updates)
            ]
        elif set_priority_updates:
            if set_file_input:
                raise click.ClickException("--update-priority cannot be combined with --update-file.")
            update_requests = [
                {
                    "requirement_id": cid,
                    "status": None,
                    "priority": priority,
                    "flagged": None,
                    "file": set_file,
                    "blocked_reason": None,
                    "deprecated_reason": None,
                }
                for cid, priority in (parse_set_priority_entry(entry) for entry in set_priority_updates)
            ]
        elif set_flagged_updates:
            if set_file_input:
                raise click.ClickException("--update-flagged cannot be combined with --update-file.")
            update_requests = [
                {
                    "requirement_id": cid,
                    "status": None,
                    "priority": None,
                    "flagged": flagged,
                    "file": set_file,
                    "blocked_reason": None,
                    "deprecated_reason": None,
                }
                for cid, flagged in (parse_set_flagged_entry(entry) for entry in set_flagged_updates)
            ]
        elif set_file_input:
            if set_file:
                raise click.ClickException("--scope-file cannot be combined with --update-file because each row may include its own file scope.")
            if set_blocked_reason or set_deprecated_reason:
                raise click.ClickException("--blocked-note/--deprecated-note cannot be combined with --update-file; provide per-row values in the file.")
            update_requests = parse_batch_update_file(repo_root, set_file_input)
        else:
            if set_requirement_id is None or set_status is None:
                raise click.ClickException("Both --update-id and --update-status are required for non-interactive update mode.")
            update_requests = [
                {
                    "requirement_id": set_requirement_id,
                    "status": set_status,
                    "priority": None,
                    "flagged": None,
                    "file": set_file,
                    "blocked_reason": set_blocked_reason,
                    "deprecated_reason": set_deprecated_reason,
                }
            ]

        if (set_blocked_reason or set_deprecated_reason) and len(update_requests) != 1:
            raise click.ClickException("--blocked-note/--deprecated-note currently support single-target updates only.")

        update_results: list[dict[str, object]] = []
        batch_mode = bool(set_file_input)
        allow_partial_failures = batch_mode and len(update_requests) > 1
        had_row_failures = False
        changed_files: set[Path] = set()
        for row_number, request in enumerate(update_requests, start=1):
            requirement_id_value = str(request["requirement_id"])
            status_value = str(request["status"]) if request["status"] is not None else None
            priority_value = str(request["priority"]) if request.get("priority") is not None else None
            flagged_value = request.get("flagged") if isinstance(request.get("flagged"), bool) else None
            row_file_filter = str(request["file"]) if request["file"] is not None else None
            normalized_status: str | None = None

            try:
                normalized_status = normalize_status_input(status_value) if status_value is not None else None

                blocked_reason = str(request["blocked_reason"]) if request["blocked_reason"] is not None else None
                deprecated_reason = str(request["deprecated_reason"]) if request["deprecated_reason"] is not None else None
                if normalized_status is None or "Blocked" not in normalized_status:
                    blocked_reason = None
                if normalized_status is None or "Deprecated" not in normalized_status:
                    deprecated_reason = None

                changed_path: Path | None = None
                if row_file_filter:
                    candidate = (repo_root / row_file_filter).resolve()
                    if candidate.exists():
                        changed_path = candidate
                else:
                    for path in domain_files:
                        if find_requirement_by_id(path, requirement_id_value, id_prefixes=id_prefixes):
                            changed_path = path
                            break

                changed = apply_status_change_by_id(
                    repo_root,
                    domain_files,
                    requirement_id=requirement_id_value,
                    new_status_input=status_value,
                    file_filter=row_file_filter,
                    blocked_reason=blocked_reason,
                    deprecated_reason=deprecated_reason,
                    new_priority_input=priority_value,
                    new_flagged_value=flagged_value,
                    include_status_emojis=include_status_emojis,
                    include_priority_summary=show_priority_summary,
                    id_prefixes=id_prefixes,
                    emit_output=not json_output,
                    dry_run=dry_run,
                )
                if changed and changed_path is not None:
                    changed_files.add(changed_path)
                update_results.append(
                    {
                        "row": row_number,
                        "requirement_id": requirement_id_value,
                        "status": normalized_status,
                        "priority": priority_value,
                        "flagged": flagged_value,
                        "file": row_file_filter,
                        "changed": changed,
                        "ok": True,
                        "error": None,
                    }
                )
            except click.ClickException as exc:
                if not allow_partial_failures:
                    if json_output and _emit_json_ambiguity_error("set", exc):
                        raise SystemExit(1)
                    raise
                had_row_failures = True
                update_results.append(
                    {
                        "row": row_number,
                        "requirement_id": requirement_id_value,
                        "status": status_value,
                        "priority": priority_value,
                        "flagged": flagged_value,
                        "file": row_file_filter,
                        "changed": False,
                        "ok": False,
                        "error": str(exc),
                    }
                )

        try:
            _, table_rows = collect_summary_rows(
                domain_files,
                check_only=True,
                display_name_fn=display_name_from_h1,
                include_status_emojis=include_status_emojis,
                include_priority_summary=show_priority_summary,
            )
        except UnknownStatusValueError as exc:
            mode_name = "set"
            if set_priority_updates and not set_updates and not set_flagged_updates:
                mode_name = "set-priority"
            elif set_flagged_updates and not set_updates and not set_priority_updates:
                mode_name = "set-flagged"
            _raise_unknown_status_error(mode_name, exc, repo_root, json_output=json_output)
        if json_output:
            payload = build_summary_payload(repo_root, resolved_criteria_dir, domain_files, sorted(changed_files))
            payload["dry_run"] = dry_run
            if set_priority_updates and not set_updates and not set_flagged_updates:
                payload["mode"] = "set-priority"
            elif set_flagged_updates and not set_updates and not set_priority_updates:
                payload["mode"] = "set-flagged"
            else:
                payload["mode"] = "set"
            payload["updates"] = update_results
            if allow_partial_failures:
                failed_count = sum(1 for row in update_results if not bool(row.get("ok")))
                payload["ok"] = failed_count == 0
                payload["batch"] = {
                    "total": len(update_results),
                    "succeeded": len(update_results) - failed_count,
                    "failed": failed_count,
                }
            _emit_json_payload(payload)
            raise SystemExit(1 if had_row_failures else 0)

        if allow_partial_failures:
            failed_rows = [row for row in update_results if not bool(row.get("ok"))]
            succeeded_count = len(update_results) - len(failed_rows)
            click.echo(
                f"Batch row results: {succeeded_count} succeeded, {len(failed_rows)} failed."
            )
            for row in failed_rows:
                click.echo(
                    f"Row {row['row']} ({row['requirement_id']}): {row['error']}",
                    err=True,
                )

        if summary_table:
            print_summary_table(table_rows, emoji_columns=emoji_columns)
        raise SystemExit(1 if had_row_failures else 0)

    if json_output:
        payload = dict(summary_payload)
        payload["ok"] = True
        _emit_json_payload(payload)
        raise SystemExit(0)

    if interactive and not check:
        # RQMD-INTERACTIVE-011: preflight write-permission gate
        check_files_writable(domain_files, repo_root)
        raise SystemExit(
            interactive_update_loop(
                repo_root,
                resolved_requirements_dir_input,
                domain_files,
                emoji_columns=emoji_columns,
                sort_files=False,
                sort_strategy=sort_strategy,
                id_prefixes=id_prefixes,
                include_status_emojis=include_status_emojis,
                priority_mode=priority_mode,
                include_priority_summary=show_priority_summary,
                zebra_bg=zebra_bg,
            )
        )


if __name__ == "__main__":
    main()
