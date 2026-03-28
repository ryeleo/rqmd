"""AI CLI integration and export functions.

This module provides:
- Export endpoints for external AI agents (requirements, statuses, bodies)
- AI-agent-safe JSON output with optional domain body inclusion
- Audit logging of AI-driven status updates
- AI workflow guidance and execution tracking
- Domain body extraction with size management
- Read-only and apply mode support
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from .batch_inputs import parse_set_entry
from .constants import JSON_SCHEMA_VERSION
from .history import HistoryManager
from .markdown_io import (
    discover_project_root,
    format_path_display,
    iter_domain_files,
    resolve_requirements_dir,
    validate_files_readable,
)
from .req_parser import (
    extract_blocking_id,
    extract_requirement_block_with_lines,
    normalize_id_prefixes,
    parse_domain_priority_metadata,
    parse_requirements,
    resolve_id_prefixes,
)
from .status_model import normalize_status_input
from .status_update import apply_status_change_by_id

HISTORY_REPO_RELATIVE = Path(".rqmd") / "history" / "rqmd-history"
AUDIT_LOG_RELATIVE = HISTORY_REPO_RELATIVE / "audit.jsonl"

_BUNDLE_MINIMAL_FILES: dict[str, str] = {
    ".github/copilot-instructions.md": """# rqmd AI Contributor Instructions

Purpose:
- Keep requirement docs, summaries, and status lines synchronized.
- Prefer machine-readable workflows (`--as-json`) for automation.

Repository conventions:
- Requirements index: docs/requirements/README.md
- Domain docs: docs/requirements/*.md
- Verify-only pass: uv run rqmd --verify-summaries --no-walk --no-table

AI workflow defaults:
- Start with read-only context export via rqmd-ai.
- Propose updates before apply (`--update ...` without `--write`).
- Apply only after review with `--write`.

Useful commands:
- uv run rqmd-ai --as-json --dump-status proposed
- uv run rqmd-ai --as-json --dump-id RQMD-CORE-001 --include-requirement-body
- uv run rqmd-ai --as-json --update RQMD-CORE-001=implemented
- uv run rqmd-ai --as-json --write --update RQMD-CORE-001=implemented
""",
    ".github/agents/core.agent.md": """name: core
description: "Primary implementation mode for rqmd repository tasks."
tools: [read, search, edit, execute, todo, agent]
agents: [Explore]
argument-hint: "Describe the behavior change, affected files, and whether docs/requirements should be updated."
---

You are the core implementation agent for this repository.

Execution contract:
- Make focused edits with minimal behavior drift.
- Keep docs/requirements status and summary blocks synchronized.
- Keep README and automation docs aligned with shipped behavior.
- Run targeted tests, then full tests before completion.
- Update CHANGELOG.md under [Unreleased] for every shipped change.
""",
}

_BUNDLE_FULL_FILES: dict[str, str] = {
    ".github/agents/Explore.agent.md": """name: Explore
description: "Read-only exploration mode for locating files, symbols, tests, and requirement references."
tools: [read, search, execute]
agents: []
argument-hint: "Describe what to find and desired thoroughness (quick/medium/thorough)."
---

You are a read-only exploration agent.

Guidelines:
- Do not edit files.
- Prefer fast searches and concise evidence collection.
- Return file paths and line hints that unblock implementation quickly.
""",
    ".github/agents/README.md": """# rqmd Agent Bundle

This folder contains a standard AI agent bundle installed by:

`rqmd-ai --install-agent-bundle`

Presets:
- minimal: `.github/copilot-instructions.md`, `.github/agents/core.agent.md`
- full: minimal + `.github/agents/Explore.agent.md` and this README

Operational notes:
- Re-run is idempotent.
- Existing files are preserved unless `--overwrite-existing` is used.
""",
}


def _build_guide_payload(repo_root: Path, requirements_dir: Path, read_only: bool) -> dict[str, object]:
    return {
        "mode": "guide",
        "read_only": read_only,
        "repo_root": str(repo_root),
        "requirements_dir": format_path_display(requirements_dir, repo_root),
        "workflow": [
            "Export context with --dump-id/--dump-status/--dump-file.",
            "Draft updates using --update ID=STATUS without --write to preview.",
            "Apply only after review by adding --write.",
        ],
        "examples": [
            "rqmd-ai --as-json --dump-status proposed",
            "rqmd-ai --as-json --dump-id RQMD-CORE-001 --include-requirement-body",
            "rqmd-ai --as-json --dump-file ai-cli.md --include-domain-markdown",
            "rqmd-ai --as-json --dump-status proposed --history-ref 0",
            "rqmd-ai --update RQMD-CORE-001=implemented",
            "rqmd-ai --update RQMD-CORE-001=implemented --write",
        ],
    }


def _bundle_files_for_preset(preset: str) -> dict[str, str]:
    files = dict(_BUNDLE_MINIMAL_FILES)
    if preset == "full":
        files.update(_BUNDLE_FULL_FILES)
    return files


def _install_agent_bundle(
    repo_root: Path,
    preset: str,
    overwrite_existing: bool,
    dry_run: bool,
) -> dict[str, object]:
    files = _bundle_files_for_preset(preset)
    created_files: list[str] = []
    overwritten_files: list[str] = []
    skipped_existing: list[str] = []

    for rel_path, content in files.items():
        target = (repo_root / rel_path).resolve()
        exists = target.exists()

        if exists and not overwrite_existing:
            skipped_existing.append(rel_path)
            continue

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content.rstrip() + "\n", encoding="utf-8")

        if exists:
            overwritten_files.append(rel_path)
        else:
            created_files.append(rel_path)

    return {
        "mode": "install-agent-bundle",
        "read_only": dry_run,
        "preset": preset,
        "overwrite_existing": overwrite_existing,
        "dry_run": dry_run,
        "created_files": created_files,
        "overwritten_files": overwritten_files,
        "skipped_existing": skipped_existing,
        "changed_count": len(created_files) + len(overwritten_files),
    }


def _extract_domain_body(path: Path, id_prefixes: tuple[str, ...], max_chars: int) -> dict[str, object] | None:
    header_pattern = r"|".join(id_prefixes)
    requirement_header = re.compile(rf"^###\s+(?:{header_pattern})-[A-Z0-9-]+:\s*")

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None

    first_requirement_index: int | None = None
    for index, line in enumerate(lines):
        if requirement_header.match(line):
            first_requirement_index = index
            break

    if first_requirement_index is None or first_requirement_index <= 0:
        return None

    prelude = lines[:first_requirement_index]

    in_summary_block = False
    kept: list[str] = []
    for line in prelude:
        stripped = line.strip()
        if stripped == "<!-- acceptance-status-summary:start -->":
            in_summary_block = True
            continue
        if stripped == "<!-- acceptance-status-summary:end -->":
            in_summary_block = False
            continue
        if in_summary_block:
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("Scope:"):
            continue
        kept.append(line)

    body_markdown = "\n".join(kept).strip()
    if not body_markdown:
        return None

    char_count = len(body_markdown)
    truncated = False
    if char_count > max_chars:
        body_markdown = body_markdown[:max_chars].rstrip()
        truncated = True

    return {
        "markdown": body_markdown,
        "char_count": len(body_markdown),
        "truncated": truncated,
        "max_chars": max_chars,
    }


def _emit(payload: dict[str, object], json_output: bool) -> None:
    if json_output:
        if "schema_version" not in payload:
            payload["schema_version"] = JSON_SCHEMA_VERSION
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    mode = payload.get("mode", "unknown")
    click.echo(f"rqmd-ai mode: {mode}")
    read_only = payload.get("read_only")
    if isinstance(read_only, bool):
        click.echo(f"read-only: {'yes' if read_only else 'no'}")
    if mode == "guide":
        for item in payload.get("workflow", []):
            click.echo(f"- {item}")


def _resolve_repo_root(repo_root: Path) -> Path:
    if repo_root != Path("."):
        return repo_root.resolve()
    discovered, _source = discover_project_root(Path.cwd())
    return discovered


def _append_audit_record(repo_root: Path, record: dict[str, object]) -> str:
    audit_path = (repo_root / AUDIT_LOG_RELATIVE).resolve()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.write("\n")
    return format_path_display(audit_path, repo_root)


def _build_apply_audit_record(
    repo_root: Path,
    requirements_dir: Path,
    file_scope: str | None,
    updates: list[dict[str, object]],
    changed_count: int,
) -> dict[str, object]:
    created_at = datetime.now(timezone.utc).isoformat()
    decisions: list[dict[str, object]] = []
    for entry in updates:
        changed = bool(entry.get("changed"))
        decisions.append(
            {
                "id": entry.get("id"),
                "requested_status": entry.get("requested_status"),
                "normalized_status": entry.get("status"),
                "decision": "applied" if changed else "no-op",
            }
        )

    return {
        "event_id": f"rqmd-ai-{uuid4().hex}",
        "created_at": created_at,
        "backend": "rqmd-history",
        "command": "rqmd-ai",
        "mode": "apply",
        "inputs": {
            "repo_root": str(repo_root),
            "requirements_dir": format_path_display(requirements_dir, repo_root),
            "file_scope": file_scope,
            "update_count": len(updates),
            "updates": [
                {
                    "id": entry.get("id"),
                    "requested_status": entry.get("requested_status"),
                    "normalized_status": entry.get("status"),
                }
                for entry in updates
            ],
        },
        "decisions": decisions,
        "outputs": {
            "changed_count": changed_count,
        },
    }


def _resolve_history_view(
    repo_root: Path,
    requirements_dir: Path,
    history_ref: str | None,
) -> tuple[Path, list[Path], dict[str, object] | None, tempfile.TemporaryDirectory[str] | None, HistoryManager | None, dict[str, object] | None]:
    if not history_ref:
        domain_files = iter_domain_files(repo_root, str(requirements_dir))
        return repo_root, domain_files, None, None, None, None

    manager = HistoryManager(repo_root=repo_root, requirements_dir=requirements_dir)
    resolved = manager.resolve_ref(history_ref)
    if resolved is None:
        raise click.ClickException(f"Unknown --history-ref target: {history_ref}")

    tempdir = manager.materialize_snapshot_tempdir(str(resolved["commit"]))
    snapshot_root = Path(tempdir.name)
    domain_files = iter_domain_files(snapshot_root, manager.requirements_dir.as_posix())
    history_source = {
        "requested_ref": history_ref,
        "resolved_commit": resolved["commit"],
        "stable_id": manager.build_stable_history_id(str(resolved["commit"])),
        "entry_index": resolved.get("entry_index"),
        "timestamp": resolved.get("timestamp"),
        "command": resolved.get("command"),
        "reason": resolved.get("reason"),
        "detached": True,
    }
    return snapshot_root, domain_files, history_source, tempdir, manager, resolved


def _build_requirement_status_map(
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    repo_root: Path,
) -> dict[str, dict[str, object]]:
    mapping: dict[str, dict[str, object]] = {}
    for path in domain_files:
        for requirement in parse_requirements(path, id_prefixes=id_prefixes):
            req_id = str(requirement.get("id") or "")
            if not req_id:
                continue
            mapping[req_id] = {
                "id": req_id,
                "title": str(requirement.get("title") or ""),
                "status": requirement.get("status"),
                "blocked_reason": requirement.get("blocked_reason"),
                "path": format_path_display(path, repo_root),
            }
    return mapping


def _build_history_activity_payload(
    manager: HistoryManager | None,
    resolved_entry: dict[str, object] | None,
    current_domain_files: list[Path],
    current_repo_root: Path,
    id_prefixes: tuple[str, ...],
) -> dict[str, object] | None:
    if manager is None or resolved_entry is None:
        return None

    current_map = _build_requirement_status_map(
        current_domain_files,
        id_prefixes=id_prefixes,
        repo_root=current_repo_root,
    )

    entry_index_raw = resolved_entry.get("entry_index")
    entry_index = int(entry_index_raw) if isinstance(entry_index_raw, int) else None
    previous_map: dict[str, dict[str, object]] = {}

    previous_entry = None
    next_entry = None
    entries = manager.list_entries()
    if entry_index is not None and 0 <= entry_index < len(entries):
        if entry_index > 0:
            previous_entry = entries[entry_index - 1]
        if entry_index < len(entries) - 1:
            next_entry = entries[entry_index + 1]

    previous_tempdir: tempfile.TemporaryDirectory[str] | None = None
    if previous_entry is not None:
        previous_tempdir = manager.materialize_snapshot_tempdir(str(previous_entry["commit"]))
        previous_root = Path(previous_tempdir.name)
        previous_files = iter_domain_files(previous_root, manager.requirements_dir.as_posix())
        previous_map = _build_requirement_status_map(
            previous_files,
            id_prefixes=id_prefixes,
            repo_root=previous_root,
        )

    changes: list[dict[str, object]] = []
    for req_id in sorted(set(current_map).union(previous_map)):
        before = previous_map.get(req_id)
        after = current_map.get(req_id)
        if before == after:
            continue
        if before and after:
            if (
                before.get("status") == after.get("status")
                and before.get("blocked_reason") == after.get("blocked_reason")
            ):
                continue
        changes.append(
            {
                "id": req_id,
                "title": (after or before or {}).get("title"),
                "before": before,
                "after": after,
            }
        )

    if previous_tempdir is not None:
        previous_tempdir.cleanup()

    return {
        "entry": {
            "commit": resolved_entry.get("commit"),
            "stable_id": manager.build_stable_history_id(str(resolved_entry.get("commit"))),
            "entry_index": entry_index,
            "timestamp": resolved_entry.get("timestamp"),
            "command": resolved_entry.get("command"),
            "reason": resolved_entry.get("reason"),
            "actor": resolved_entry.get("actor"),
            "changed_files": list(resolved_entry.get("files") or []),
        },
        "neighbors": {
            "previous": {
                "entry_index": entry_index - 1 if previous_entry is not None and entry_index is not None else None,
                "commit": previous_entry.get("commit") if isinstance(previous_entry, dict) else None,
                "stable_id": (
                    manager.build_stable_history_id(str(previous_entry.get("commit")))
                    if isinstance(previous_entry, dict) and previous_entry.get("commit")
                    else None
                ),
                "timestamp": previous_entry.get("timestamp") if isinstance(previous_entry, dict) else None,
            },
            "next": {
                "entry_index": entry_index + 1 if next_entry is not None and entry_index is not None else None,
                "commit": next_entry.get("commit") if isinstance(next_entry, dict) else None,
                "stable_id": (
                    manager.build_stable_history_id(str(next_entry.get("commit")))
                    if isinstance(next_entry, dict) and next_entry.get("commit")
                    else None
                ),
                "timestamp": next_entry.get("timestamp") if isinstance(next_entry, dict) else None,
            },
        },
        "changed_requirements": changes,
    }


def _build_compare_payload(
    manager: HistoryManager,
    ref_a: str,
    ref_b: str,
    id_prefixes: tuple[str, ...],
) -> dict[str, object]:
    """Build a diff-oriented comparison payload between two history refs.

    Materializes both snapshots into temporary directories, builds requirement
    status maps for each, and returns a structured diff highlighting additions,
    removals, and status transitions.
    """
    pair = manager.resolve_two_refs(ref_a, ref_b)
    if pair is None:
        unknown = ref_a if manager.resolve_ref(ref_a) is None else ref_b
        raise click.ClickException(f"Unknown --compare-refs target: {unknown!r}")

    entry_a, entry_b = pair

    tempdir_a = manager.materialize_snapshot_tempdir(str(entry_a["commit"]))
    tempdir_b = manager.materialize_snapshot_tempdir(str(entry_b["commit"]))
    try:
        root_a = Path(tempdir_a.name)
        root_b = Path(tempdir_b.name)
        files_a = iter_domain_files(root_a, manager.requirements_dir.as_posix())
        files_b = iter_domain_files(root_b, manager.requirements_dir.as_posix())
        map_a = _build_requirement_status_map(files_a, id_prefixes=id_prefixes, repo_root=root_a)
        map_b = _build_requirement_status_map(files_b, id_prefixes=id_prefixes, repo_root=root_b)
    finally:
        tempdir_a.cleanup()
        tempdir_b.cleanup()

    all_ids = sorted(set(map_a).union(map_b))
    transitions: list[dict[str, object]] = []
    added: list[dict[str, object]] = []
    removed: list[dict[str, object]] = []
    unchanged_count = 0

    for req_id in all_ids:
        a = map_a.get(req_id)
        b = map_b.get(req_id)
        if a is None:
            added.append({"id": req_id, "title": (b or {}).get("title"), "status": (b or {}).get("status"), "after": b})
        elif b is None:
            removed.append({"id": req_id, "title": a.get("title"), "status": a.get("status"), "before": a})
        else:
            if a.get("status") != b.get("status") or a.get("blocked_reason") != b.get("blocked_reason"):
                transitions.append({
                    "id": req_id,
                    "title": b.get("title") or a.get("title"),
                    "before_status": a.get("status"),
                    "after_status": b.get("status"),
                    "before_blocked_reason": a.get("blocked_reason"),
                    "after_blocked_reason": b.get("blocked_reason"),
                })
            else:
                unchanged_count += 1

    def _entry_summary(entry: dict[str, object]) -> dict[str, object]:
        commit_value = str(entry.get("commit") or "")
        return {
            "entry_index": entry.get("entry_index"),
            "commit": entry.get("commit"),
            "stable_id": manager.build_stable_history_id(commit_value) if commit_value else None,
            "timestamp": entry.get("timestamp"),
            "command": entry.get("command"),
            "reason": entry.get("reason"),
            "actor": entry.get("actor"),
            "branch": entry.get("branch"),
        }

    return {
        "mode": "compare",
        "ref_a": _entry_summary(entry_a),
        "ref_b": _entry_summary(entry_b),
        "summary": {
            "transitions": len(transitions),
            "added": len(added),
            "removed": len(removed),
            "unchanged": unchanged_count,
            "total_a": len(map_a),
            "total_b": len(map_b),
        },
        "transitions": transitions,
        "added": added,
        "removed": removed,
    }


def _export_context(
    repo_root: Path,
    requirements_dir: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    export_ids: tuple[str, ...],
    export_files: tuple[str, ...],
    export_status: str | None,
    include_body: bool,
    include_domain_body: bool,
    max_domain_body_chars: int,
    history_source: dict[str, object] | None = None,
    history_activity: dict[str, object] | None = None,
) -> dict[str, object]:
    normalized_ids = {value.strip().upper() for value in export_ids if value.strip()}
    normalized_status: str | None = None
    if export_status:
        normalized_status = normalize_status_input(export_status)

    allowed_file_paths: set[Path] | None = None
    if export_files:
        allowed_file_paths = set()
        for token in export_files:
            raw = token.strip()
            if not raw:
                continue
            candidate = (repo_root / raw).resolve()
            if candidate.exists() and candidate.is_file():
                allowed_file_paths.add(candidate)
                continue

            basename_matches = [path for path in domain_files if path.name == raw]
            if basename_matches:
                allowed_file_paths.update(basename_matches)
                continue

            raise click.ClickException(f"Unknown --dump-file target: {token}")

    files_payload: list[dict[str, object]] = []
    total = 0
    for path in domain_files:
        if allowed_file_paths is not None and path not in allowed_file_paths:
            continue

        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        entries: list[dict[str, object]] = []
        for requirement in requirements:
            req_id = str(requirement["id"])
            if normalized_ids and req_id.upper() not in normalized_ids:
                continue
            if normalized_status and str(requirement.get("status")) != normalized_status:
                continue

            entry: dict[str, object] = {
                "id": req_id,
                "title": str(requirement.get("title") or ""),
                "status": requirement.get("status"),
                "priority": requirement.get("priority"),
                "flagged": requirement.get("flagged"),
                "sub_domain": requirement.get("sub_domain"),
            }
            blocked_reason = requirement.get("blocked_reason")
            if blocked_reason is not None:
                entry["blocked_reason"] = blocked_reason
                bid = extract_blocking_id(str(blocked_reason), id_prefixes)
                if bid is not None:
                    entry["blocking_id"] = bid
            if include_body:
                block, start_line, end_line = extract_requirement_block_with_lines(
                    path,
                    req_id,
                    id_prefixes=id_prefixes,
                )
                entry["body"] = {
                    "markdown": block,
                    "lines": {
                        "start": (start_line + 1) if isinstance(start_line, int) else None,
                        "end": (end_line + 1) if isinstance(end_line, int) else None,
                    },
                }

            entries.append(entry)

        if entries:
            file_payload: dict[str, object] = {
                "path": format_path_display(path, repo_root),
                "requirements": entries,
            }
            domain_priority_meta = parse_domain_priority_metadata(path, id_prefixes=id_prefixes)
            if domain_priority_meta["domain_priority"] is not None:
                file_payload["domain_priority"] = domain_priority_meta["domain_priority"]
            if domain_priority_meta["sub_section_priorities"]:
                file_payload["sub_section_priorities"] = domain_priority_meta["sub_section_priorities"]
            if include_domain_body:
                file_payload["domain_body"] = _extract_domain_body(
                    path,
                    id_prefixes=id_prefixes,
                    max_chars=max_domain_body_chars,
                )

            files_payload.append(
                file_payload
            )
            total += len(entries)

    return {
        "mode": "export-context",
        "read_only": True,
        "requirements_dir": format_path_display(requirements_dir, repo_root),
        "total": total,
        "files": files_payload,
        "history_source": history_source,
        "history_activity": history_activity,
    }


def _plan_or_apply_updates(
    repo_root: Path,
    requirements_dir: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    set_entries: tuple[str, ...],
    apply: bool,
    file_scope: str | None,
) -> dict[str, object]:
    updates = [parse_set_entry(entry) for entry in set_entries]
    payload_updates: list[dict[str, object]] = []

    changed_count = 0
    audit: dict[str, object] | None = None
    for req_id, status_input in updates:
        normalized = normalize_status_input(status_input)
        changed = False
        if apply:
            changed = apply_status_change_by_id(
                repo_root=repo_root,
                domain_files=domain_files,
                requirement_id=req_id,
                new_status_input=status_input,
                file_filter=file_scope,
                id_prefixes=id_prefixes,
                emit_output=False,
                dry_run=False,
            )
            if changed:
                changed_count += 1

        payload_updates.append(
            {
                "id": req_id,
                "requested_status": status_input,
                "status": normalized,
                "changed": changed,
            }
        )

    if apply:
        audit_record = _build_apply_audit_record(
            repo_root=repo_root,
            requirements_dir=requirements_dir,
            file_scope=file_scope,
            updates=payload_updates,
            changed_count=changed_count,
        )
        log_path = _append_audit_record(repo_root, audit_record)
        audit = {
            "backend": "rqmd-history",
            "event_id": audit_record["event_id"],
            "log_path": log_path,
        }

    return {
        "mode": "apply" if apply else "plan",
        "read_only": not apply,
        "requirements_dir": format_path_display(requirements_dir, repo_root),
        "update_count": len(payload_updates),
        "changed_count": changed_count,
        "updates": payload_updates,
        "audit": audit,
    }


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--as-json", "json_output", is_flag=True, help="Emit machine-readable JSON output.")
@click.option("--show-guide", "guide", is_flag=True, help="Print onboarding guidance for rqmd-ai workflows.")
@click.option(
    "--project-root",
    "repo_root",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path("."),
    show_default=True,
    help="Project root containing requirement documentation.",
)
@click.option(
    "--docs-dir",
    "requirements_dir",
    type=str,
    default=None,
    help="Directory (absolute or relative to --project-root) containing requirement markdown files.",
)
@click.option(
    "--id-namespace",
    "id_prefixes",
    multiple=True,
    default=(),
    help="Allowed requirement ID prefixes. Repeat or comma-separate values.",
)
@click.option("--dump-id", "export_ids", multiple=True, default=(), help="Export requirement context for one or more IDs.")
@click.option("--dump-file", "export_files", multiple=True, default=(), help="Export context only from one or more domain files.")
@click.option("--dump-status", "export_status", type=str, default=None, help="Export context filtered by status label or slug.")
@click.option("--history-ref", "history_ref", type=str, default=None, help="Export context from a detached history entry index or commit ref instead of the current working tree.")
@click.option("--compare-refs", "compare_refs", type=str, default=None, help="Compare two history entries by diff-oriented comparison. Format: 'A..B' or 'A B' where A and B are entry indices, commit refs, or 'head'/'latest'.")
@click.option("--include-requirement-body/--no-include-requirement-body", "include_body", default=True, help="Include requirement body markdown in exports.")
@click.option(
    "--include-domain-markdown/--no-include-domain-markdown",
    "include_domain_body",
    default=False,
    help="Include optional domain-level body content in export payloads.",
)
@click.option(
    "--max-domain-markdown-chars",
    "max_domain_body_chars",
    type=click.IntRange(min=1),
    default=4000,
    show_default=True,
    help="Maximum characters per exported domain-body markdown block.",
)
@click.option("--update", "set_entries", multiple=True, default=(), help="Planned status update in ID=STATUS format.")
@click.option("--scope-file", "file_scope", type=str, default=None, help="Optional file scope used with --update/--write.")
@click.option("--write", "apply", is_flag=True, help="Apply planned updates. Without this flag rqmd-ai remains read-only.")
@click.option("--install-agent-bundle", "install_bundle", is_flag=True, help="Install a standard agent/skill instruction bundle into the workspace.")
@click.option(
    "--bundle-preset",
    "bundle_preset",
    type=click.Choice(["minimal", "full"], case_sensitive=False),
    default="minimal",
    show_default=True,
    help="Bundle preset for --install-agent-bundle.",
)
@click.option("--overwrite-existing", "overwrite_existing", is_flag=True, help="Allow --install-agent-bundle to overwrite existing instruction files.")
@click.option("--dry-run", "dry_run", is_flag=True, help="Preview --install-agent-bundle changes without writing files.")
def main(
    json_output: bool,
    guide: bool,
    repo_root: Path,
    requirements_dir: str | None,
    id_prefixes: tuple[str, ...],
    export_ids: tuple[str, ...],
    export_files: tuple[str, ...],
    export_status: str | None,
    history_ref: str | None,
    compare_refs: str | None,
    include_body: bool,
    include_domain_body: bool,
    max_domain_body_chars: int,
    set_entries: tuple[str, ...],
    file_scope: str | None,
    apply: bool,
    install_bundle: bool,
    bundle_preset: str,
    overwrite_existing: bool,
    dry_run: bool,
) -> None:
    repo_root = _resolve_repo_root(repo_root)

    if install_bundle:
        if guide or set_entries or export_ids or export_files or export_status or apply:
            raise click.ClickException(
                "--install-agent-bundle cannot be combined with guide/export/update/apply options."
            )
        payload = _install_agent_bundle(
            repo_root=repo_root,
            preset=bundle_preset.lower(),
            overwrite_existing=overwrite_existing,
            dry_run=dry_run,
        )
        _emit(payload, json_output=json_output)
        return

    resolved_criteria_dir, _message = resolve_requirements_dir(repo_root, requirements_dir)
    try:
        resolved_prefixes_input = normalize_id_prefixes(id_prefixes) if id_prefixes else id_prefixes
        id_prefixes = resolve_id_prefixes(repo_root, str(resolved_criteria_dir), resolved_prefixes_input)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if compare_refs:
        if apply or set_entries:
            raise click.ClickException("--compare-refs is read-only; it cannot be combined with --write or --update.")
        # Parse "A..B" or "A B" format
        raw = compare_refs.strip()
        if ".." in raw:
            parts = raw.split("..", 1)
        else:
            parts = raw.split(None, 1)
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise click.ClickException(
                "--compare-refs requires two refs separated by '..' or a space, "
                f"for example '0..2' or '0 head'. Got: {compare_refs!r}"
            )
        ref_a, ref_b = parts[0].strip(), parts[1].strip()
        _compare_manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
        payload = _build_compare_payload(
            manager=_compare_manager,
            ref_a=ref_a,
            ref_b=ref_b,
            id_prefixes=id_prefixes,
        )
        _emit(payload, json_output=json_output)
        return

    effective_repo_root, domain_files, history_source, history_tempdir, history_manager, resolved_history_entry = _resolve_history_view(
        repo_root=repo_root,
        requirements_dir=resolved_criteria_dir,
        history_ref=history_ref,
    )
    effective_requirements_dir = resolved_criteria_dir
    if history_source is not None:
        effective_requirements_dir = effective_repo_root / resolved_criteria_dir.relative_to(repo_root)
    if not domain_files:
        raise click.ClickException(
            f"No requirement markdown files found under: {format_path_display(resolved_criteria_dir, repo_root)}"
        )
    validate_files_readable(domain_files, effective_repo_root)

    if apply and not set_entries:
        raise click.ClickException("rqmd-ai --write requires at least one --update ID=STATUS update.")
    if history_ref and apply:
        raise click.ClickException("--history-ref cannot be combined with --write.")
    if history_ref and set_entries:
        raise click.ClickException("--history-ref cannot be combined with --update; historical exports are read-only.")
    if guide:
        if history_tempdir is not None:
            history_tempdir.cleanup()
        _emit(_build_guide_payload(repo_root, resolved_criteria_dir, read_only=(not apply)), json_output=json_output)
        return

    if set_entries:
        if history_tempdir is not None:
            history_tempdir.cleanup()
        payload = _plan_or_apply_updates(
            repo_root=repo_root,
            requirements_dir=resolved_criteria_dir,
            domain_files=domain_files,
            id_prefixes=id_prefixes,
            set_entries=set_entries,
            apply=apply,
            file_scope=file_scope,
        )
        _emit(payload, json_output=json_output)
        return

    if export_ids or export_files or export_status:
        history_activity = _build_history_activity_payload(
            manager=history_manager,
            resolved_entry=resolved_history_entry,
            current_domain_files=domain_files,
            current_repo_root=effective_repo_root,
            id_prefixes=id_prefixes,
        )
        payload = _export_context(
            repo_root=effective_repo_root,
            requirements_dir=effective_requirements_dir,
            domain_files=domain_files,
            id_prefixes=id_prefixes,
            export_ids=export_ids,
            export_files=export_files,
            export_status=export_status,
            include_body=include_body,
            include_domain_body=include_domain_body,
            max_domain_body_chars=max_domain_body_chars,
            history_source=history_source,
            history_activity=history_activity,
        )
        _emit(payload, json_output=json_output)
        if history_tempdir is not None:
            history_tempdir.cleanup()
        return

    if history_tempdir is not None:
        history_tempdir.cleanup()
    _emit(_build_guide_payload(repo_root, resolved_criteria_dir, read_only=True), json_output=json_output)


if __name__ == "__main__":
    main()