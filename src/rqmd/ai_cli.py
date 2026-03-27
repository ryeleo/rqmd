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
from .markdown_io import (discover_project_root, format_path_display,
                          iter_domain_files, resolve_requirements_dir,
                          validate_files_readable)
from .req_parser import (extract_requirement_block_with_lines,
                         normalize_id_prefixes, parse_requirements,
                         resolve_id_prefixes)
from .status_model import normalize_status_input
from .status_update import apply_status_change_by_id

HISTORY_REPO_RELATIVE = Path(".rqmd") / "history" / "rqmd-history"
AUDIT_LOG_RELATIVE = HISTORY_REPO_RELATIVE / "audit.jsonl"


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
            "rqmd-ai --update RQMD-CORE-001=implemented",
            "rqmd-ai --update RQMD-CORE-001=implemented --write",
        ],
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
def main(
    json_output: bool,
    guide: bool,
    repo_root: Path,
    requirements_dir: str | None,
    id_prefixes: tuple[str, ...],
    export_ids: tuple[str, ...],
    export_files: tuple[str, ...],
    export_status: str | None,
    include_body: bool,
    include_domain_body: bool,
    max_domain_body_chars: int,
    set_entries: tuple[str, ...],
    file_scope: str | None,
    apply: bool,
) -> None:
    repo_root = _resolve_repo_root(repo_root)
    resolved_criteria_dir, _message = resolve_requirements_dir(repo_root, requirements_dir)
    try:
        resolved_prefixes_input = normalize_id_prefixes(id_prefixes) if id_prefixes else id_prefixes
        id_prefixes = resolve_id_prefixes(repo_root, str(resolved_criteria_dir), resolved_prefixes_input)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    domain_files = iter_domain_files(repo_root, str(resolved_criteria_dir))
    if not domain_files:
        raise click.ClickException(
            f"No requirement markdown files found under: {format_path_display(resolved_criteria_dir, repo_root)}"
        )
    validate_files_readable(domain_files, repo_root)

    if apply and not set_entries:
        raise click.ClickException("rqmd-ai --write requires at least one --update ID=STATUS update.")

    if guide:
        _emit(_build_guide_payload(repo_root, resolved_criteria_dir, read_only=(not apply)), json_output=json_output)
        return

    if set_entries:
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
        payload = _export_context(
            repo_root=repo_root,
            requirements_dir=resolved_criteria_dir,
            domain_files=domain_files,
            id_prefixes=id_prefixes,
            export_ids=export_ids,
            export_files=export_files,
            export_status=export_status,
            include_body=include_body,
            include_domain_body=include_domain_body,
            max_domain_body_chars=max_domain_body_chars,
        )
        _emit(payload, json_output=json_output)
        return

    _emit(_build_guide_payload(repo_root, resolved_criteria_dir, read_only=True), json_output=json_output)


if __name__ == "__main__":
    main()