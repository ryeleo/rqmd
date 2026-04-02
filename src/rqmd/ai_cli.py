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

import importlib.resources
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from importlib import metadata as importlib_metadata
from pathlib import Path
from urllib.parse import unquote, urlparse
from uuid import uuid4

import yaml

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)

from .batch_inputs import parse_set_entry
from .config import load_config, load_priorities_file, validate_config
from .constants import JSON_SCHEMA_VERSION, PRIORITY_ORDER, REQUIREMENTS_INDEX_NAME
from .history import HistoryManager
from .json_speedups import dumps_json
from .markdown_io import (
    discover_project_root,
    format_path_display,
    initialize_requirements_scaffold,
    iter_domain_files,
    load_init_yaml,
    preview_project_config_scaffold,
    preview_requirements_scaffold,
    render_legacy_issue_domain,
    render_legacy_source_domain,
    render_legacy_workflow_domain,
    render_requirements_index,
    render_startup_message,
    resolve_requirements_dir,
    validate_files_readable,
)
from .priority_model import configure_priority_catalog
from .req_parser import (
    extract_blocking_id,
    extract_requirement_block_with_lines,
    find_duplicate_requirement_ids,
    normalize_id_prefixes,
    parse_domain_priority_metadata,
    parse_requirements,
    resolve_id_prefixes,
)
from .status_model import normalize_status_input
from .status_update import apply_status_change_by_id
from .summary import process_file

HISTORY_REPO_RELATIVE = Path(".rqmd") / "history" / "rqmd-history"
AUDIT_LOG_RELATIVE = HISTORY_REPO_RELATIVE / "audit.jsonl"

_WORKFLOW_MODE_SKILLS: dict[str, str] = {
    "general": "rqmd-export-context",
    "brainstorm": "rqmd-brainstorm",
    "implement": "rqmd-implement",
    "init": "rqmd-init",
    "init-legacy": "rqmd-init",
}

_BUNDLE_RESOURCE_ROOT = ("resources", "bundle")
_GENERATED_PROJECT_SKILL_PATHS = (
    ".github/skills/dev/SKILL.md",
    ".github/skills/test/SKILL.md",
)

def _editable_source_path_from_distribution() -> Path | None:
    try:
        distribution = importlib_metadata.distribution("rqmd")
    except importlib_metadata.PackageNotFoundError:
        return None

    direct_url_text = distribution.read_text("direct_url.json")
    if not direct_url_text:
        return None

    try:
        payload = json.loads(direct_url_text)
    except json.JSONDecodeError:
        return None

    dir_info = payload.get("dir_info")
    url = payload.get("url")
    if not isinstance(dir_info, dict) or dir_info.get("editable") is not True or not isinstance(url, str):
        return None

    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None

    if parsed.netloc:
        candidate = f"//{parsed.netloc}{parsed.path}"
    else:
        candidate = parsed.path
    return Path(unquote(candidate)).resolve()


def _build_version_output(command_name: str) -> str:
    try:
        version = importlib_metadata.version("rqmd")
    except importlib_metadata.PackageNotFoundError:
        version = "unknown"

    lines = [f"{command_name} {version}"]
    editable_source = _editable_source_path_from_distribution()
    if editable_source is not None:
        lines.append(f"editable source: {editable_source}")
        lines.append(f"package path: {Path(__file__).resolve().parent}")
    return "\n".join(lines)


def _handle_version_option(
    ctx: click.Context,
    _param: click.Parameter,
    value: bool,
) -> None:
    if not value or ctx.resilient_parsing:
        return
    click.echo(_build_version_output("rqmd-ai"))
    ctx.exit()


def _bundle_resource_base() -> object:
    return importlib.resources.files("rqmd").joinpath(*_BUNDLE_RESOURCE_ROOT)


def _read_bundle_manifest(preset: str) -> tuple[str, ...]:
    manifest = _bundle_resource_base().joinpath(f"{preset}.txt")
    lines = manifest.read_text(encoding="utf-8").splitlines()
    entries = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]
    return tuple(entries)


def _read_bundle_resource_file(relative_path: str) -> str:
    resource = _bundle_resource_base().joinpath(*relative_path.split("/"))
    return resource.read_text(encoding="utf-8")


def _read_text_if_exists(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(markdown_text: str) -> dict[str, object]:
    if not markdown_text.startswith("---\n"):
        return {}

    closing_index = markdown_text.find("\n---\n", 4)
    if closing_index == -1:
        return {}

    frontmatter_text = markdown_text[4:closing_index]
    data = yaml.safe_load(frontmatter_text)
    return data if isinstance(data, dict) else {}


def _parse_skill_frontmatter(markdown_text: str) -> dict[str, object]:
    return _parse_frontmatter(markdown_text)


def _load_skill_frontmatter(skill_name: str) -> tuple[str, dict[str, object]]:
    relative_path = f".github/skills/{skill_name}/SKILL.md"
    frontmatter = _parse_frontmatter(_read_bundle_resource_file(relative_path))
    return relative_path, frontmatter


def _load_workflow_guide(workflow_mode: str) -> dict[str, object]:
    skill_name = _WORKFLOW_MODE_SKILLS[workflow_mode]
    relative_path, frontmatter = _load_skill_frontmatter(skill_name)

    metadata = frontmatter.get("metadata")
    guide = metadata.get("guide") if isinstance(metadata, dict) else None
    summary = guide.get("summary") if isinstance(guide, dict) else None
    workflow = guide.get("workflow") if isinstance(guide, dict) else None
    examples = guide.get("examples") if isinstance(guide, dict) else None
    if not isinstance(summary, str) or not isinstance(workflow, list) or not isinstance(examples, list):
        raise click.ClickException(
            f"Bundle workflow guide metadata missing or invalid for mode '{workflow_mode}' in {relative_path}."
        )

    batch_policy = guide.get("batch_policy") if isinstance(guide, dict) else None
    validation_checks = guide.get("validation_checks") if isinstance(guide, dict) else None
    return {
        "summary": summary,
        "workflow": [str(item) for item in workflow],
        "examples": [str(item) for item in examples],
        "batch_policy": batch_policy if isinstance(batch_policy, dict) else None,
        "validation_checks": [str(item) for item in validation_checks] if isinstance(validation_checks, list) else None,
    }


def _load_runtime_priority_labels(repo_root: Path) -> tuple[str, ...]:
    try:
        config = load_config(repo_root)
        validate_config(config)
        standalone_priorities = load_priorities_file(repo_root, None)
        effective_priorities = standalone_priorities if standalone_priorities is not None else config.get("priorities")
        configure_priority_catalog(effective_priorities)
        return tuple(label for label, _slug in PRIORITY_ORDER)
    except ValueError as exc:
        raise click.ClickException(f"Config error: {exc}") from exc
    finally:
        configure_priority_catalog(None)


def _load_brainstorm_rules() -> dict[str, object]:
    relative_path, frontmatter = _load_skill_frontmatter("rqmd-brainstorm")
    metadata = frontmatter.get("metadata")
    brainstorm = metadata.get("brainstorm") if isinstance(metadata, dict) else None
    if not isinstance(brainstorm, dict):
        raise click.ClickException(
            f"Bundle brainstorm metadata missing or invalid in {relative_path}."
        )

    default_target_file = brainstorm.get("default_target_file")
    default_priority_rank = brainstorm.get("default_priority_rank")
    proposal_title = brainstorm.get("proposal_title")
    proposal_sort = brainstorm.get("proposal_sort")
    section_targets_raw = brainstorm.get("section_targets")
    priority_hints_raw = brainstorm.get("priority_hints")
    if not isinstance(default_target_file, str) or not isinstance(default_priority_rank, int):
        raise click.ClickException(
            f"Bundle brainstorm metadata missing default target or priority in {relative_path}."
        )
    if not isinstance(proposal_title, dict) or not isinstance(proposal_sort, dict):
        raise click.ClickException(
            f"Bundle brainstorm metadata missing proposal title or sort configuration in {relative_path}."
        )
    if not isinstance(section_targets_raw, list) or not isinstance(priority_hints_raw, list):
        raise click.ClickException(
            f"Bundle brainstorm metadata missing section targets or priority hints in {relative_path}."
        )

    max_words = proposal_title.get("max_words")
    max_chars = proposal_title.get("max_chars")
    if not isinstance(max_words, int) or not isinstance(max_chars, int) or max_words <= 0 or max_chars <= 0:
        raise click.ClickException(
            f"Bundle brainstorm metadata has invalid proposal title configuration in {relative_path}."
        )
    priority_source = proposal_sort.get("priority_source")
    if priority_source != "runtime-catalog":
        raise click.ClickException(
            f"Bundle brainstorm metadata has invalid proposal sort configuration in {relative_path}."
        )

    section_targets: list[tuple[tuple[str, ...], str]] = []
    for item in section_targets_raw:
        if not isinstance(item, dict):
            raise click.ClickException(f"Invalid brainstorm section target entry in {relative_path}.")
        tokens = item.get("tokens")
        target_file = item.get("target_file")
        if not isinstance(tokens, list) or not isinstance(target_file, str):
            raise click.ClickException(f"Invalid brainstorm section target entry in {relative_path}.")
        normalized_tokens = tuple(str(token).casefold() for token in tokens if str(token).strip())
        if normalized_tokens:
            section_targets.append((normalized_tokens, target_file))

    priority_hints: list[tuple[tuple[str, ...], int]] = []
    for item in priority_hints_raw:
        if not isinstance(item, dict):
            raise click.ClickException(f"Invalid brainstorm priority hint entry in {relative_path}.")
        tokens = item.get("tokens")
        priority_rank = item.get("priority_rank")
        if not isinstance(tokens, list) or not isinstance(priority_rank, int):
            raise click.ClickException(f"Invalid brainstorm priority hint entry in {relative_path}.")
        normalized_tokens = tuple(str(token).casefold() for token in tokens if str(token).strip())
        if normalized_tokens:
            priority_hints.append((normalized_tokens, priority_rank))

    return {
        "default_target_file": default_target_file,
        "default_priority_rank": default_priority_rank,
        "proposal_title": {
            "max_words": max_words,
            "max_chars": max_chars,
        },
        "proposal_sort": {
            "priority_source": priority_source,
        },
        "section_targets": tuple(section_targets),
        "priority_hints": tuple(priority_hints),
    }


def _load_legacy_init_rules() -> dict[str, object]:
    relative_path, frontmatter = _load_skill_frontmatter("rqmd-init")
    metadata = frontmatter.get("metadata")
    legacy_init = metadata.get("legacy_init") if isinstance(metadata, dict) else None
    if not isinstance(legacy_init, dict):
        raise click.ClickException(
            f"Bundle legacy-init metadata missing or invalid in {relative_path}."
        )

    default_requirements_dir = legacy_init.get("default_requirements_dir")
    max_domain_files = legacy_init.get("max_domain_files")
    max_issue_requirements = legacy_init.get("max_issue_requirements")
    max_source_areas = legacy_init.get("max_source_areas")
    if (
        not isinstance(default_requirements_dir, str)
        or not isinstance(max_domain_files, int)
        or not isinstance(max_issue_requirements, int)
        or not isinstance(max_source_areas, int)
    ):
        raise click.ClickException(
            f"Bundle legacy-init metadata missing or invalid in {relative_path}."
        )
    return {
        "default_requirements_dir": default_requirements_dir,
        "max_domain_files": max_domain_files,
        "max_issue_requirements": max_issue_requirements,
        "max_source_areas": max_source_areas,
    }


def _shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts if str(part).strip())


def _default_json_artifact_path(repo_root: Path, name: str) -> Path:
    return (repo_root / "tmp" / f"{name}.json").resolve()


def _serialize_json_payload(payload: dict[str, object]) -> str:
    if "schema_version" not in payload:
        payload["schema_version"] = JSON_SCHEMA_VERSION
    return dumps_json(payload, indent=2)


def _write_json_payload_file(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_serialize_json_payload(payload) + "\n", encoding="utf-8")


def _resolve_init_requirements_dir(repo_root: Path, requirements_dir_input: str | None) -> Path:
    rules = _load_legacy_init_rules()
    criteria_dir = Path(requirements_dir_input or str(rules["default_requirements_dir"]))
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()
    return criteria_dir


def _detect_init_strategy(
    repo_root: Path,
    requirements_dir_input: str | None,
    *,
    force_legacy: bool = False,
) -> dict[str, object]:
    criteria_dir = _resolve_init_requirements_dir(repo_root, requirements_dir_input)
    reasons: list[str] = []

    existing_markdown = sorted(criteria_dir.glob("*.md")) if criteria_dir.exists() else []
    if existing_markdown:
        reasons.append(
            render_startup_message(
                "init-strategy-existing-markdown.md",
                {"REQUIREMENTS_DIR": format_path_display(criteria_dir, repo_root)},
            ).strip()
        )

    established_markers = (
        (repo_root / "src").exists(),
        (repo_root / "app").exists(),
        (repo_root / "lib").exists(),
        (repo_root / "tests").exists(),
        (repo_root / "test").exists(),
        (repo_root / "docs").exists(),
        (repo_root / "README.md").exists(),
        (repo_root / "pyproject.toml").exists(),
        (repo_root / "package.json").exists(),
        (repo_root / "Cargo.toml").exists(),
        (repo_root / "go.mod").exists(),
    )
    marker_count = sum(1 for present in established_markers if present)
    if marker_count:
        reasons.append(
            render_startup_message(
                "init-strategy-marker-count.md",
                {"MARKER_COUNT": str(marker_count)},
            ).strip()
        )

    selected = "legacy-init" if force_legacy or existing_markdown or marker_count >= 2 else "starter-scaffold"
    if force_legacy:
        reasons.insert(0, render_startup_message("init-strategy-force-legacy.md").strip())
    if not reasons:
        reasons.append(render_startup_message("init-strategy-starter-default.md").strip())

    return {
        "selected": selected,
        "heuristic": "override" if force_legacy else "auto",
        "reasons": reasons,
        "requirements_dir": format_path_display(criteria_dir, repo_root),
    }


def _build_starter_init_chat_questions(
    repo_root: Path,
    requirements_dir: Path,
    id_prefixes: tuple[str, ...],
) -> list[dict[str, object]]:
    inferred_prefix = id_prefixes[0] if id_prefixes else "REQ"
    requirements_dir_config = _STARTER_INIT_FIELD_CONFIGS["requirements_dir"]
    id_prefix_config = _STARTER_INIT_FIELD_CONFIGS["id_prefix"]
    starter_notes_config = _STARTER_INIT_FIELD_CONFIGS["starter_notes"]
    return [
        _build_interview_question(
            field="requirements_dir",
            group_id=str(requirements_dir_config["group"]),
            label=str(requirements_dir_config["label"]),
            prompt=str(requirements_dir_config["prompt"]),
            inferred_answers=[requirements_dir.as_posix()],
            allow_multiple=bool(requirements_dir_config["allow_multiple"]),
            allow_custom=bool(requirements_dir_config["allow_custom"]),
            allow_skip=bool(requirements_dir_config["allow_skip"]),
            first_selected_is_canonical=bool(requirements_dir_config["first_selected_is_canonical"]),
            custom_answer_prompt=str(requirements_dir_config["custom_answer_prompt"]),
            suggested_options=_legacy_init_requirements_dir_options(repo_root, requirements_dir),
        ),
        _build_id_prefix_question(
            repo_root=repo_root,
            group_id=str(id_prefix_config["group"]),
            prompt=str(id_prefix_config["prompt"]),
            inferred_prefix=inferred_prefix,
        ),
        _build_interview_question(
            field="starter_notes",
            group_id=str(starter_notes_config["group"]),
            label=str(starter_notes_config["label"]),
            prompt=str(starter_notes_config["prompt"]),
            inferred_answers=[],
            allow_multiple=bool(starter_notes_config["allow_multiple"]),
            allow_custom=bool(starter_notes_config["allow_custom"]),
            allow_skip=bool(starter_notes_config["allow_skip"]),
            first_selected_is_canonical=bool(starter_notes_config["first_selected_is_canonical"]),
            custom_answer_prompt=str(starter_notes_config["custom_answer_prompt"]),
        ),
    ]


def _derive_project_specific_prefix(repo_root: Path) -> str | None:
    tokens = [segment for segment in re.split(r"[^A-Za-z0-9]+", repo_root.name.upper()) if segment]
    if not tokens:
        return None

    candidate = "".join(tokens)
    if len(candidate) < 3:
        candidate = "".join(token[:3] for token in tokens)
    candidate = re.sub(r"[^A-Z0-9]", "", candidate)
    if len(candidate) < 3:
        return None
    return candidate[:8]


def _build_id_prefix_question(
    *,
    repo_root: Path,
    group_id: str,
    prompt: str,
    inferred_prefix: str,
) -> dict[str, object]:
    project_specific_prefix = _derive_project_specific_prefix(repo_root)
    recommended_values: list[str] = []
    inferred_prefix_recommended = True
    inferred_description = _ID_PREFIX_INFERRED_DESCRIPTION
    suggested_options: list[dict[str, str]] = []

    if project_specific_prefix and project_specific_prefix.casefold() != inferred_prefix.casefold():
        suggested_options.append(
            {
                "value": project_specific_prefix,
                "label": project_specific_prefix,
                "description": _ID_PREFIX_PROJECT_SPECIFIC_DESCRIPTION,
                "recommended": True,
            }
        )
        recommended_values.append(project_specific_prefix)
        inferred_prefix_recommended = False
        inferred_description = _ID_PREFIX_INFERRED_DESCRIPTION_WHEN_PROJECT_SPECIFIC
    else:
        recommended_values.append(inferred_prefix)

    base_option_values = {
        str(option.get("value") or "").strip().casefold()
        for option in _ID_PREFIX_BASE_OPTIONS
        if str(option.get("value") or "").strip()
    }
    if inferred_prefix.casefold() not in base_option_values:
        suggested_options.append(
            {
                "value": inferred_prefix,
                "label": inferred_prefix,
                "description": inferred_description,
                "recommended": inferred_prefix_recommended,
            }
        )
    suggested_options.extend(_ID_PREFIX_BASE_OPTIONS)

    rendered_prompt = prompt
    if _ID_PREFIX_PROMPT_SUFFIX:
        rendered_prompt = f"{prompt} {_ID_PREFIX_PROMPT_SUFFIX}".strip()

    return _build_interview_question(
        field="id_prefix",
        group_id=group_id,
        label=_ID_PREFIX_QUESTION_LABEL,
        prompt=rendered_prompt,
        inferred_answers=[inferred_prefix],
        allow_multiple=False,
        allow_custom=True,
        allow_skip=False,
        first_selected_is_canonical=True,
        custom_answer_prompt=_ID_PREFIX_CUSTOM_ANSWER_PROMPT,
        suggested_options=tuple(suggested_options),
        recommended_values=recommended_values,
        safe_default_values=["REQ"],
    )


def _build_starter_init_payload(
    repo_root: Path,
    requirements_dir_input: str | None,
    id_prefixes: tuple[str, ...],
    apply: bool,
    chat_mode: bool,
    interview_answers: tuple[str, ...] = (),
) -> dict[str, object]:
    rules = _load_legacy_init_rules()
    starter_answer_map = _collect_interview_answers(interview_answers, _STARTER_INIT_CHAT_FIELDS)
    criteria_dir = Path(
        requirements_dir_input
        or str(starter_answer_map.get("requirements_dir", [str(rules["default_requirements_dir"])])[0])
    )
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()

    prefix = id_prefixes[0] if id_prefixes else str(starter_answer_map.get("id_prefix", ["REQ"])[0]).strip().upper().rstrip("-")
    proposed_files = preview_requirements_scaffold(repo_root, str(criteria_dir), prefix)
    questions = _build_starter_init_chat_questions(repo_root, criteria_dir.relative_to(repo_root), id_prefixes or (prefix,))
    payload = {
        "mode": "starter-init-apply" if apply else "starter-init-plan",
        "workflow_mode": "init",
        "read_only": not apply,
        "repo_root": str(repo_root),
        "requirements_dir": criteria_dir.relative_to(repo_root).as_posix(),
        "starter_prefix": prefix,
        "proposed_files": proposed_files,
        "total_files": len(proposed_files),
        "interaction_contract": _build_interview_interaction_contract(),
        "interview": _build_interview_payload(
            enabled=chat_mode,
            questions=questions,
            applied_answers=starter_answer_map,
        ),
    }
    if apply:
        created_files = initialize_requirements_scaffold(repo_root, str(criteria_dir), prefix)
        payload["created_files"] = [format_path_display(path, repo_root) for path in created_files]
        payload["changed_count"] = len(created_files)
    return payload


def _build_rqmd_ai_init_command(
    repo_root: Path,
    requirements_dir_input: str | None,
    id_prefixes: tuple[str, ...],
    *,
    chat_mode: bool,
    force_legacy: bool,
    apply: bool = False,
    json_output_file: Path | None = None,
) -> str:
    parts = ["rqmd-ai", "init"]
    if chat_mode:
        parts.append("--chat")
    parts.append("--json")
    parts.extend(["--project-root", str(repo_root)])
    if force_legacy:
        parts.append("--legacy")
    if requirements_dir_input:
        parts.extend(["--docs-dir", requirements_dir_input])
    for prefix in id_prefixes:
        parts.extend(["--id-namespace", prefix])
    if apply:
        parts.append("--write")
    if json_output_file is not None:
        parts.extend(["--json-output-file", str(json_output_file)])
    return _shell_join(parts)


def _build_bundle_follow_up_command(repo_root: Path, *, json_output_file: Path | None = None) -> str:
    parts = [
        "rqmd-ai",
        "install",
        "--bundle-preset",
        "full",
        "--chat",
        "--json",
        "--dry-run",
        "--project-root",
        str(repo_root),
    ]
    if json_output_file is not None:
        parts.extend(["--json-output-file", str(json_output_file)])
    return _shell_join(
        parts
    )


def _build_init_handoff_prompt(
    repo_root: Path,
    *,
    init_command: str,
    apply_command: str,
    strategy: dict[str, object],
    bundle_state: dict[str, object],
) -> str:
    init_artifact_path = _default_json_artifact_path(repo_root, "rqmd-ai-init-preview")
    bundle_artifact_path = _default_json_artifact_path(repo_root, "rqmd-ai-bundle-preview")
    sections = [
        render_startup_message(
            "init-handoff-base.md",
            {
                "REPO_ROOT": str(repo_root),
                "INIT_COMMAND": init_command,
                "INIT_ARTIFACT_COMMAND": f"{init_command} --json-output-file {shlex.quote(str(init_artifact_path))}",
                "APPLY_COMMAND": apply_command,
            },
        ).rstrip()
    ]

    if not bool(bundle_state.get("installed")):
        bundle_command = _build_bundle_follow_up_command(repo_root)
        sections.append(
            render_startup_message(
                "init-handoff-bundle-followup.md",
                {
                    "BUNDLE_STEP": "9",
                    "BUNDLE_ARTIFACT_STEP": "10",
                    "BUNDLE_SKILLS_STEP": "11",
                    "BUNDLE_APPLY_STEP": "12",
                    "BUNDLE_STATE": str(bundle_state.get("state", "absent")),
                    "BUNDLE_COMMAND": bundle_command,
                    "BUNDLE_ARTIFACT_COMMAND": f"{bundle_command} --json-output-file {shlex.quote(str(bundle_artifact_path))}",
                },
            ).rstrip()
        )
        final_step = 13
    else:
        final_step = 9

    sections.append(
        render_startup_message(
            "init-handoff-tail.md",
            {
                "VERIFY_STEP": str(final_step),
                "READY_STEP": str(final_step + 1),
                "STRATEGY": str(strategy.get("selected", "unknown")),
            },
        ).rstrip()
    )
    return "\n".join(section for section in sections if section.strip())


def _build_or_apply_init_payload(
    repo_root: Path,
    requirements_dir_input: str | None,
    id_prefixes: tuple[str, ...],
    apply: bool,
    *,
    chat_mode: bool = False,
    interview_answers: tuple[str, ...] = (),
    force_legacy: bool = False,
) -> dict[str, object]:
    strategy = _detect_init_strategy(
        repo_root,
        requirements_dir_input,
        force_legacy=force_legacy,
    )
    bundle_state = _detect_workspace_bundle_state(repo_root)

    if strategy["selected"] == "legacy-init":
        payload = _build_or_apply_legacy_init_payload(
            repo_root=repo_root,
            requirements_dir_input=requirements_dir_input,
            id_prefixes=id_prefixes,
            apply=apply,
            chat_mode=chat_mode,
            interview_answers=interview_answers,
        )
    else:
        payload = _build_starter_init_payload(
            repo_root=repo_root,
            requirements_dir_input=requirements_dir_input,
            id_prefixes=id_prefixes,
            apply=apply,
            chat_mode=chat_mode,
            interview_answers=interview_answers,
        )

    init_command = _build_rqmd_ai_init_command(
        repo_root,
        requirements_dir_input,
        id_prefixes,
        chat_mode=True,
        force_legacy=force_legacy,
        apply=False,
    )
    apply_command = _build_rqmd_ai_init_command(
        repo_root,
        requirements_dir_input,
        id_prefixes,
        chat_mode=True,
        force_legacy=force_legacy,
        apply=True,
    )
    init_artifact_path = _default_json_artifact_path(repo_root, "rqmd-ai-init-preview")
    apply_artifact_path = _default_json_artifact_path(repo_root, "rqmd-ai-init-apply")
    bundle_artifact_path = _default_json_artifact_path(repo_root, "rqmd-ai-bundle-preview")
    payload["mode"] = "init-chat" if chat_mode and not apply else ("init-apply" if apply else "init-plan")
    payload["workflow_mode"] = "init"
    payload["strategy"] = strategy
    payload["bundle_installation"] = bundle_state
    payload["compatibility"] = {
        "legacy_workflow_mode": "init-legacy",
        "legacy_flag": "--legacy",
    }
    if chat_mode:
        payload["handoff_prompt"] = _build_init_handoff_prompt(
            repo_root,
            init_command=init_command,
            apply_command=apply_command,
            strategy=strategy,
            bundle_state=bundle_state,
        )
        payload["suggested_commands"] = {
            "init_preview": init_command,
            "init_apply": apply_command,
            "bundle_preview": _build_bundle_follow_up_command(repo_root),
            "init_preview_artifact": _build_rqmd_ai_init_command(
                repo_root,
                requirements_dir_input,
                id_prefixes,
                chat_mode=True,
                force_legacy=force_legacy,
                apply=False,
                json_output_file=init_artifact_path,
            ),
            "init_apply_artifact": _build_rqmd_ai_init_command(
                repo_root,
                requirements_dir_input,
                id_prefixes,
                chat_mode=True,
                force_legacy=force_legacy,
                apply=True,
                json_output_file=apply_artifact_path,
            ),
            "bundle_preview_artifact": _build_bundle_follow_up_command(
                repo_root,
                json_output_file=bundle_artifact_path,
            ),
        }
    return payload


def _priority_label_for_rank(priority_labels: tuple[str, ...], rank: int) -> str:
    if not priority_labels:
        raise click.ClickException("No priorities configured for brainstorm proposal generation.")
    if rank < 0:
        return priority_labels[max(len(priority_labels) + rank, 0)]
    if rank >= len(priority_labels):
        return priority_labels[-1]
    return priority_labels[rank]


def _bundle_definition_kind(relative_path: str) -> str | None:
    if relative_path == ".github/copilot-instructions.md":
        return "instruction"
    if relative_path.startswith(".github/prompts/") and relative_path.endswith(".prompt.md"):
        return "prompt"
    if relative_path.startswith(".github/skills/") and relative_path.endswith("/SKILL.md"):
        return "skill"
    if relative_path.startswith(".github/agents/") and relative_path.endswith(".agent.md"):
        return "agent"
    return None


def _build_packaged_bundle_definitions(preset: str = "full") -> dict[str, object]:
    entries: list[dict[str, str]] = []
    for relative_path in _read_bundle_manifest(preset):
        kind = _bundle_definition_kind(relative_path)
        if kind is None:
            continue
        entries.append(
            {
                "path": relative_path,
                "kind": kind,
                "content": _read_bundle_resource_file(relative_path),
            }
        )
    return {
        "source": "packaged-resources",
        "preset": preset,
        "files": entries,
    }


def _workspace_definition_files(repo_root: Path) -> list[str]:
    root = repo_root / ".github"
    results: list[str] = []

    instructions_path = root / "copilot-instructions.md"
    if instructions_path.exists():
        results.append(".github/copilot-instructions.md")

    prompts_root = root / "prompts"
    if prompts_root.exists():
        for path in sorted(prompts_root.glob("*.prompt.md")):
            results.append(path.relative_to(repo_root).as_posix())

    skills_root = root / "skills"
    if skills_root.exists():
        for path in sorted(skills_root.glob("*/SKILL.md")):
            results.append(path.relative_to(repo_root).as_posix())

    agents_root = root / "agents"
    if agents_root.exists():
        for path in sorted(agents_root.glob("*.agent.md")):
            results.append(path.relative_to(repo_root).as_posix())

    return results


def _append_unique(items: list[str], value: str | None) -> None:
    if value and value not in items:
        items.append(value)


def _format_command(command: str) -> str:
    return f"`{command}`"


def _extract_make_targets(repo_root: Path) -> set[str]:
    makefile = repo_root / "Makefile"
    text = _read_text_if_exists(makefile)
    if text is None:
        return set()

    targets: set[str] = set()
    for line in text.splitlines():
        if not line or line.startswith(("\t", " ", "#")):
            continue
        match = re.match(r"^(?P<target>[A-Za-z0-9_.-]+)\s*:", line)
        if match:
            targets.add(match.group("target"))
    return targets


def _load_package_json_scripts(repo_root: Path) -> dict[str, str]:
    package_json = repo_root / "package.json"
    text = _read_text_if_exists(package_json)
    if text is None:
        return {}

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    scripts = data.get("scripts") if isinstance(data, dict) else None
    if not isinstance(scripts, dict):
        return {}
    return {
        str(name): str(command)
        for name, command in scripts.items()
        if isinstance(name, str) and isinstance(command, str)
    }


def _markdown_list(items: list[str], fallback: str) -> str:
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def _render_bundle_template(relative_path: str, replacements: dict[str, str]) -> str:
    content = _read_bundle_resource_file(relative_path)
    for key, value in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def _expect_init_mapping(value: object, *, message: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise click.ClickException(message)
    return {str(key): item for key, item in value.items()}


def _expect_init_list(value: object, *, message: str) -> list[object]:
    if not isinstance(value, list):
        raise click.ClickException(message)
    return list(value)


def _load_init_field_section(section_name: str) -> tuple[tuple[str, ...], dict[str, dict[str, object]]]:
    section = _expect_init_mapping(
        _INIT_INTERVIEW_CONFIG.get(section_name),
        message=f"Invalid init interview config: missing {section_name} mapping.",
    )
    field_order = _expect_init_list(
        section.get("field_order"),
        message=(
            f"Invalid init interview config: {section_name} field_order/fields must be present."
        ),
    )
    fields = _expect_init_mapping(
        section.get("fields"),
        message=(
            f"Invalid init interview config: {section_name} field_order/fields must be present."
        ),
    )
    return (
        tuple(str(item) for item in field_order if str(item).strip()),
        {
            field_name: dict(field_config)
            for field_name, field_config in fields.items()
            if isinstance(field_config, dict)
        },
    )


def _load_init_option_sets(section_name: str) -> dict[str, tuple[dict[str, str], ...]]:
    section = _expect_init_mapping(
        _INIT_INTERVIEW_CONFIG.get(section_name),
        message=f"Invalid init interview config: missing {section_name} mapping.",
    )
    raw_option_sets = _expect_init_mapping(
        section.get("option_sets"),
        message=f"Invalid init interview config: {section_name} option_sets must be a mapping.",
    )
    return {
        str(key): tuple(
            {
                str(option_key): str(option_value)
                for option_key, option_value in option.items()
            }
            for option in value
            if isinstance(option, dict)
        )
        for key, value in raw_option_sets.items()
        if isinstance(value, list)
    }


def _load_init_option_list(section_name: str, option_key: str) -> tuple[dict[str, str], ...]:
    section = _expect_init_mapping(
        _INIT_INTERVIEW_CONFIG.get(section_name),
        message=f"Invalid init interview config: missing {section_name} mapping.",
    )
    raw_options = _expect_init_list(
        section.get(option_key),
        message=f"Invalid init interview config: {section_name} {option_key} must be a list.",
    )
    return tuple(
        {
            str(raw_key): str(raw_value)
            for raw_key, raw_value in option.items()
        }
        for option in raw_options
        if isinstance(option, dict)
    )


_INIT_INTERVIEW_CONFIG = load_init_yaml("init-interview.yml")
if not isinstance(_INIT_INTERVIEW_CONFIG, dict):
    raise click.ClickException("Invalid init interview config: expected a mapping in init-interview.yml.")

_RAW_INTERVIEW_GROUP_LABELS = _expect_init_mapping(
    _INIT_INTERVIEW_CONFIG.get("group_labels"),
    message="Invalid init interview config: missing group_labels mapping.",
)
_INTERVIEW_GROUP_LABELS: dict[str, str] = {
    str(key): str(value)
    for key, value in _RAW_INTERVIEW_GROUP_LABELS.items()
}

_RAW_INTERVIEW_GROUP_ORDER = _expect_init_list(
    _INIT_INTERVIEW_CONFIG.get("group_order"),
    message="Invalid init interview config: missing group_order list.",
)
_INTERVIEW_GROUP_ORDER: tuple[str, ...] = tuple(
    str(item) for item in _RAW_INTERVIEW_GROUP_ORDER if str(item).strip()
)

_RAW_INTERACTION_CONTRACT = _expect_init_mapping(
    _INIT_INTERVIEW_CONFIG.get("interaction_contract"),
    message="Invalid init interview config: missing interaction_contract mapping.",
)
_RAW_INTERACTION_CONTRACT_INSTRUCTIONS = _expect_init_list(
    _RAW_INTERACTION_CONTRACT.get("instructions"),
    message="Invalid init interview config: interaction_contract instructions must be a list.",
)
_INTERVIEW_INTERACTION_CONTRACT: dict[str, object] = {
    "interaction_mode": str(_RAW_INTERACTION_CONTRACT.get("interaction_mode") or ""),
    "preferred_ui": str(_RAW_INTERACTION_CONTRACT.get("preferred_ui") or ""),
    "presentation": str(_RAW_INTERACTION_CONTRACT.get("presentation") or ""),
    "next_action": str(_RAW_INTERACTION_CONTRACT.get("next_action") or ""),
    "confirmation_policy": str(_RAW_INTERACTION_CONTRACT.get("confirmation_policy") or ""),
    "selection_behavior": str(_RAW_INTERACTION_CONTRACT.get("selection_behavior") or ""),
    "instructions": [str(item) for item in _RAW_INTERACTION_CONTRACT_INSTRUCTIONS if str(item).strip()],
}

_RAW_ID_PREFIX_QUESTION = _expect_init_mapping(
    _INIT_INTERVIEW_CONFIG.get("id_prefix_question"),
    message="Invalid init interview config: missing id_prefix_question mapping.",
)
_ID_PREFIX_QUESTION_LABEL = str(_RAW_ID_PREFIX_QUESTION.get("label") or "Requirement ID prefix")
_ID_PREFIX_PROMPT_SUFFIX = str(_RAW_ID_PREFIX_QUESTION.get("prompt_suffix") or "")
_ID_PREFIX_CUSTOM_ANSWER_PROMPT = str(_RAW_ID_PREFIX_QUESTION.get("custom_answer_prompt") or "")
_ID_PREFIX_PROJECT_SPECIFIC_DESCRIPTION = str(
    _RAW_ID_PREFIX_QUESTION.get("project_specific_description") or ""
)
_ID_PREFIX_INFERRED_DESCRIPTION = str(_RAW_ID_PREFIX_QUESTION.get("inferred_description") or "")
_ID_PREFIX_INFERRED_DESCRIPTION_WHEN_PROJECT_SPECIFIC = str(
    _RAW_ID_PREFIX_QUESTION.get("inferred_description_when_project_specific") or ""
)
_ID_PREFIX_BASE_OPTIONS = _load_init_option_list("id_prefix_question", "options")

_BOOTSTRAP_CHAT_FIELDS, _BOOTSTRAP_CHAT_FIELD_CONFIGS = _load_init_field_section("bootstrap")
_STARTER_INIT_CHAT_FIELDS, _STARTER_INIT_FIELD_CONFIGS = _load_init_field_section("starter_init")
_LEGACY_INIT_CHAT_FIELDS, _LEGACY_INIT_FIELD_CONFIGS = _load_init_field_section("legacy_init")
_LEGACY_INIT_OPTION_SETS = _load_init_option_sets("legacy_init")


def _build_interview_question(
    *,
    field: str,
    group_id: str,
    label: str,
    prompt: str,
    inferred_answers: list[str],
    allow_multiple: bool,
    allow_custom: bool,
    allow_skip: bool,
    first_selected_is_canonical: bool,
    custom_answer_prompt: str | None = None,
    suggested_options: tuple[dict[str, str], ...] = (),
    detected_from: tuple[str, ...] | list[str] = (),
    recommended_values: tuple[str, ...] | list[str] = (),
    safe_default_values: tuple[str, ...] | list[str] = (),
) -> dict[str, object]:
    options: list[dict[str, object]] = []
    seen: set[str] = set()
    option_index_by_key: dict[str, int] = {}
    normalized_recommended = {str(value).strip().casefold() for value in recommended_values if str(value).strip()}
    normalized_safe_defaults = {str(value).strip().casefold() for value in safe_default_values if str(value).strip()}
    normalized_detected_from = [str(item).strip() for item in detected_from if str(item).strip()]

    def add_option(
        *,
        value: str,
        label_text: str | None = None,
        kind: str,
        description: str | None = None,
        recommended: bool | None = None,
        safe_default: bool | None = None,
    ) -> None:
        text = str(value).strip()
        if not text:
            return
        normalized = text.casefold()
        if normalized in seen:
            existing = options[option_index_by_key[normalized]]
            if label_text and (existing.get("label") in {None, "", text} or existing.get("kind") == "inferred"):
                existing["label"] = label_text
            if description and (not existing.get("description") or (kind == "suggested" and existing.get("kind") == "inferred")):
                existing["description"] = description
            if kind == "suggested" and existing.get("kind") == "inferred":
                existing["kind"] = "suggested"
            if kind == "inferred" and normalized_detected_from:
                existing_detected = existing.get("detected_from")
                merged_detected = list(existing_detected) if isinstance(existing_detected, list) else []
                for item in normalized_detected_from:
                    if item not in merged_detected:
                        merged_detected.append(item)
                if merged_detected:
                    existing["detected_from"] = merged_detected
            if recommended is True or normalized in normalized_recommended:
                existing["recommended"] = True
            if safe_default is True or normalized in normalized_safe_defaults:
                existing["safe_default"] = True
            return
        seen.add(normalized)
        option: dict[str, object] = {
            "value": text,
            "label": str(label_text or text),
            "kind": kind,
            "recommended": (normalized in normalized_recommended) if recommended is None else bool(recommended),
            "safe_default": (normalized in normalized_safe_defaults) if safe_default is None else bool(safe_default),
        }
        if description:
            option["description"] = description
        if kind == "inferred" and normalized_detected_from:
            option["detected_from"] = list(normalized_detected_from)
        options.append(option)
        option_index_by_key[normalized] = len(options) - 1

    for item in inferred_answers:
        add_option(value=item, kind="inferred")
    for option in suggested_options:
        add_option(
            value=str(option.get("value") or ""),
            label_text=str(option.get("label") or "") or None,
            kind="suggested",
            description=str(option.get("description") or "") or None,
            recommended=bool(option.get("recommended")) if "recommended" in option else None,
            safe_default=bool(option.get("safe_default")) if "safe_default" in option else None,
        )

    default_checked_values = [
        str(option["value"])
        for option in options
        if allow_multiple and (option.get("kind") == "suggested" or option.get("recommended") is True)
    ]

    return {
        "field": field,
        "group_id": group_id,
        "group_label": _INTERVIEW_GROUP_LABELS[group_id],
        "label": label,
        "prompt": prompt,
        "selection_model": {
            "allow_multiple": allow_multiple,
            "allow_custom": allow_custom,
            "allow_skip": allow_skip,
            "first_selected_is_canonical": first_selected_is_canonical,
        },
        "custom_answer_prompt": custom_answer_prompt,
        "options": options,
        "inferred_answers": [str(item) for item in inferred_answers if str(item).strip()],
        "option_annotations": {
            "recommended_values": [str(item) for item in recommended_values if str(item).strip()],
            "safe_default_values": [str(item) for item in safe_default_values if str(item).strip()],
            "detected_from": list(normalized_detected_from),
            "default_checked_values": default_checked_values,
        },
    }


def _group_interview_questions(questions: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[str, object]] = {}
    ordered_groups: list[str] = []
    for question in questions:
        group_id = str(question["group_id"])
        if group_id not in grouped:
            grouped[group_id] = {
                "id": group_id,
                "label": str(question["group_label"]),
                "questions": [],
            }
            ordered_groups.append(group_id)
        grouped[group_id]["questions"].append(question)
    ordered = [group_id for group_id in _INTERVIEW_GROUP_ORDER if group_id in grouped]
    ordered.extend(group_id for group_id in ordered_groups if group_id not in ordered)
    return [grouped[group_id] for group_id in ordered]


def _build_interview_interaction_contract() -> dict[str, object]:
    return {
        **_INTERVIEW_INTERACTION_CONTRACT,
        "instructions": list(_INTERVIEW_INTERACTION_CONTRACT["instructions"]),
    }


def _build_interview_flow(question_groups: list[dict[str, object]]) -> list[dict[str, object]]:
    flow: list[dict[str, object]] = []
    for step_index, group in enumerate(question_groups, start=1):
        questions = group.get("questions") if isinstance(group.get("questions"), list) else []
        flow.append(
            {
                "step": step_index,
                "group_id": str(group.get("id") or ""),
                "group_label": str(group.get("label") or ""),
                "presentation": "one-question-at-a-time",
                "preferred_ui": "multi-choice",
                "question_fields": [
                    str(question.get("field") or "")
                    for question in questions
                    if isinstance(question, dict) and str(question.get("field") or "").strip()
                ],
                "questions": [
                    {
                        "field": str(question.get("field") or ""),
                        "label": str(question.get("label") or ""),
                        "allow_multiple": bool((question.get("selection_model") or {}).get("allow_multiple")),
                        "allow_custom": bool((question.get("selection_model") or {}).get("allow_custom")),
                        "allow_skip": bool((question.get("selection_model") or {}).get("allow_skip")),
                        "default_checked_values": list((question.get("option_annotations") or {}).get("default_checked_values") or []),
                    }
                    for question in questions
                    if isinstance(question, dict)
                ],
            }
        )
    return flow


def _build_interview_payload(
    *,
    enabled: bool,
    questions: list[dict[str, object]],
    applied_answers: dict[str, list[str]],
    extras: dict[str, object] | None = None,
) -> dict[str, object]:
    question_groups = _group_interview_questions(questions) if enabled else []
    payload: dict[str, object] = {
        "enabled": enabled,
        "questions": questions if enabled else [],
        "question_groups": question_groups,
        "applied_answers": applied_answers,
        "interaction_contract": _build_interview_interaction_contract(),
        "flow": _build_interview_flow(question_groups) if enabled else [],
    }
    if extras:
        payload.update(extras)
    return payload


def _detect_project_command_hints(repo_root: Path) -> dict[str, list[str]]:
    detected_sources: list[str] = []

    dev_environment: list[str] = []
    dev_build: list[str] = []
    dev_run: list[str] = []
    dev_smoke: list[str] = []

    test_primary: list[str] = []
    test_integration: list[str] = []
    test_lint: list[str] = []
    notes: list[str] = []

    package_scripts = _load_package_json_scripts(repo_root)
    if package_scripts:
        _append_unique(detected_sources, "package.json scripts")
        for script_name in ("dev", "start", "serve"):
            if script_name in package_scripts:
                _append_unique(dev_run, _format_command(f"npm run {script_name}"))
        for script_name in ("build",):
            if script_name in package_scripts:
                _append_unique(dev_build, _format_command(f"npm run {script_name}"))
        for script_name in ("smoke",):
            if script_name in package_scripts:
                _append_unique(dev_smoke, _format_command(f"npm run {script_name}"))
        for script_name in ("test", "test:unit", "unit"):
            if script_name in package_scripts:
                _append_unique(test_primary, _format_command(f"npm run {script_name}"))
        for script_name in ("test:integration", "integration", "e2e"):
            if script_name in package_scripts:
                _append_unique(test_integration, _format_command(f"npm run {script_name}"))
        for script_name in ("lint", "check"):
            if script_name in package_scripts:
                _append_unique(test_lint, _format_command(f"npm run {script_name}"))
        if (repo_root / "package-lock.json").exists() or (repo_root / "pnpm-lock.yaml").exists() or (repo_root / "yarn.lock").exists():
            _append_unique(dev_environment, _format_command("npm install"))

    make_targets = _extract_make_targets(repo_root)
    if make_targets:
        _append_unique(detected_sources, "Makefile targets")
        for target in ("dev", "run", "start"):
            if target in make_targets:
                _append_unique(dev_run, _format_command(f"make {target}"))
        for target in ("build",):
            if target in make_targets:
                _append_unique(dev_build, _format_command(f"make {target}"))
        for target in ("smoke",):
            if target in make_targets:
                _append_unique(dev_smoke, _format_command(f"make {target}"))
        for target in ("test", "check"):
            if target in make_targets:
                _append_unique(test_primary, _format_command(f"make {target}"))
        for target in ("integration", "e2e", "ci"):
            if target in make_targets:
                _append_unique(test_integration, _format_command(f"make {target}"))
        for target in ("lint",):
            if target in make_targets:
                _append_unique(test_lint, _format_command(f"make {target}"))

    pyproject_text = _read_text_if_exists(repo_root / "pyproject.toml")
    if pyproject_text is not None:
        _append_unique(detected_sources, "pyproject.toml")
        if (repo_root / "uv.lock").exists() or "uv run" in pyproject_text:
            _append_unique(dev_environment, _format_command("uv sync --extra dev"))
        elif "[project]" in pyproject_text or "[build-system]" in pyproject_text:
            _append_unique(dev_environment, _format_command("python -m pip install -e ."))

    if (repo_root / "tests").exists() or (repo_root / "pytest.ini").exists() or (pyproject_text and "pytest" in pyproject_text):
        if (repo_root / "uv.lock").exists() or (pyproject_text and "[tool.pytest.ini_options]" in pyproject_text):
            _append_unique(test_primary, _format_command("uv run --extra dev pytest -q"))
        else:
            _append_unique(test_primary, _format_command("pytest -q"))

    smoke_script = repo_root / "scripts" / "local-smoke.sh"
    if smoke_script.exists():
        _append_unique(detected_sources, "scripts/local-smoke.sh")
        _append_unique(dev_smoke, _format_command("./scripts/local-smoke.sh"))

    if (repo_root / "manage.py").exists():
        _append_unique(detected_sources, "manage.py")
        _append_unique(dev_run, _format_command("python manage.py runserver"))
        _append_unique(test_primary, _format_command("python manage.py test"))

    if (repo_root / "Cargo.toml").exists():
        _append_unique(detected_sources, "Cargo.toml")
        _append_unique(dev_build, _format_command("cargo build"))
        _append_unique(test_primary, _format_command("cargo test"))

    if (repo_root / "go.mod").exists():
        _append_unique(detected_sources, "go.mod")
        _append_unique(dev_build, _format_command("go build ./..."))
        _append_unique(test_primary, _format_command("go test ./..."))

    if not test_integration and dev_smoke:
        notes.append("Smoke coverage was detected under the development skill; keep `/test` focused on repeatable automated checks.")
    if not detected_sources:
        notes.append("No common project-command sources were detected automatically; replace the placeholders below with the repository's real commands.")
    else:
        notes.append("Review the generated commands and tighten them to the repository's canonical workflows before relying on them in automation.")

    result = {
        "detected_sources": detected_sources,
        "dev_environment": dev_environment,
        "dev_build": dev_build,
        "dev_run": dev_run,
        "dev_smoke": dev_smoke,
        "test_primary": test_primary,
        "test_integration": test_integration,
        "test_lint": test_lint,
        "notes": notes,
    }
    result["field_detected_from"] = {
        field: list(detected_sources)
        for field in _BOOTSTRAP_CHAT_FIELDS
        if field != "notes" and result.get(field)
    }
    return result


def _render_project_skill_content_from_hints(hints: dict[str, list[str]]) -> dict[str, str]:
    return {
        ".github/skills/dev/SKILL.md": _render_bundle_template(
            "templates/dev-skill.md",
            {
                "DETECTED_SOURCES": _markdown_list(hints["detected_sources"], "No common command source files were detected automatically."),
                "ENVIRONMENT_SETUP": _markdown_list(hints["dev_environment"], "No canonical environment setup command was detected yet. Replace this with the repository's real setup step."),
                "BUILD_COMMANDS": _markdown_list(hints["dev_build"], "No canonical build command was detected yet. Replace this with the repository's real build step."),
                "RUN_COMMANDS": _markdown_list(hints["dev_run"], "No canonical run or dev-server command was detected yet. Replace this with the repository's real run step."),
                "SMOKE_COMMANDS": _markdown_list(hints["dev_smoke"], "No smoke-test command was detected yet. Add the repository's primary smoke path here if one exists."),
                "NOTES": _markdown_list(hints["notes"], "Review and edit this generated skill after bootstrap."),
            },
        ),
        ".github/skills/test/SKILL.md": _render_bundle_template(
            "templates/test-skill.md",
            {
                "DETECTED_SOURCES": _markdown_list(hints["detected_sources"], "No common command source files were detected automatically."),
                "PRIMARY_TEST_COMMANDS": _markdown_list(hints["test_primary"], "No primary automated test command was detected yet. Replace this with the repository's real test command."),
                "INTEGRATION_TEST_COMMANDS": _markdown_list(hints["test_integration"], "No dedicated integration or end-to-end test command was detected yet. Add one here if the repository has it."),
                "LINT_AND_CHECK_COMMANDS": _markdown_list(hints["test_lint"], "No lint or check command was detected yet. Add one here if the repository uses it."),
                "NOTES": _markdown_list(hints["notes"], "Review and edit this generated skill after bootstrap."),
            },
        ),
    }


def _infer_project_skill_content(repo_root: Path) -> dict[str, str]:
    hints = _detect_project_command_hints(repo_root)
    return _render_project_skill_content_from_hints(hints)


def _parse_interview_answer_entry(raw: str, allowed_fields: tuple[str, ...]) -> tuple[str, str]:
    text = str(raw).strip()
    if "=" not in text:
        raise click.ClickException(
            "--answer must use FIELD=VALUE format, for example --answer dev_run='npm run dev'."
        )
    field_raw, value_raw = text.split("=", 1)
    field = field_raw.strip().lower()
    value = value_raw.strip()
    if field not in allowed_fields:
        allowed = ", ".join(allowed_fields)
        raise click.ClickException(
            f"Unknown --answer field {field_raw!r}. Allowed fields: {allowed}."
        )
    if not value:
        raise click.ClickException(f"--answer {field}=... requires a non-empty value.")
    return field, value


def _collect_interview_answers(
    interview_answers: tuple[str, ...],
    allowed_fields: tuple[str, ...],
) -> dict[str, list[str]]:
    collected_answers: dict[str, list[str]] = {field: [] for field in allowed_fields}
    for raw in interview_answers:
        field, value = _parse_interview_answer_entry(raw, allowed_fields)
        collected_answers[field].append(value)
    return {field: values for field, values in collected_answers.items() if values}


def _apply_command_answers(
    hints: dict[str, list[str]],
    collected_answers: dict[str, list[str]],
) -> dict[str, list[str]]:
    updated: dict[str, list[str]] = {
        key: list(value) if isinstance(value, list) else []
        for key, value in hints.items()
    }
    for field in _BOOTSTRAP_CHAT_FIELDS:
        values = collected_answers.get(field, [])
        if values:
            updated[field] = list(values)
    return updated


def _build_bootstrap_chat_questions(hints: dict[str, list[str]]) -> list[dict[str, object]]:
    questions: list[dict[str, object]] = []
    field_detected_from = hints.get("field_detected_from") if isinstance(hints.get("field_detected_from"), dict) else {}
    for field in _BOOTSTRAP_CHAT_FIELDS:
        inferred = hints.get(field) if isinstance(hints.get(field), list) else []
        config = _BOOTSTRAP_CHAT_FIELD_CONFIGS[field]
        questions.append(
            _build_interview_question(
                field=field,
                group_id=str(config["group"]),
                label=str(config["label"]),
                prompt=str(config["prompt"]),
                inferred_answers=[str(item) for item in inferred if str(item).strip()],
                allow_multiple=bool(config["allow_multiple"]),
                allow_custom=bool(config["allow_custom"]),
                allow_skip=bool(config["allow_skip"]),
                first_selected_is_canonical=bool(config["first_selected_is_canonical"]),
                custom_answer_prompt=str(config["custom_answer_prompt"]),
                detected_from=list(field_detected_from.get(field, [])) if isinstance(field_detected_from, dict) else [],
                recommended_values=[str(item) for item in inferred if str(item).strip()],
                safe_default_values=[str(inferred[0])] if inferred and field != "notes" else [],
            )
        )
    return questions


def _legacy_init_requirements_dir_options(
    repo_root: Path,
    default_dir: Path,
) -> tuple[dict[str, str], ...]:
    candidates: list[str] = []
    for candidate in (
        default_dir.as_posix(),
        "docs/requirements",
        "requirements",
        "docs/reqs",
    ):
        if candidate not in candidates:
            candidates.append(candidate)
    return tuple(
        {
            "value": value,
            "label": value,
            "description": (
                "Already exists in this repository."
                if (repo_root / value).exists()
                else "Suggested starter location for the rqmd catalog."
            ),
            "recommended": value == default_dir.as_posix(),
            "safe_default": value == "docs/requirements",
        }
        for value in candidates
    )


def _build_legacy_init_chat_questions(
    repo_root: Path,
    requirements_dir: Path,
    id_prefixes: tuple[str, ...],
    command_hints: dict[str, list[str]],
    source_areas: list[dict[str, str]],
    issue_context: dict[str, object],
) -> list[dict[str, object]]:
    questions: list[dict[str, object]] = []

    inferred_prefix = id_prefixes[0] if id_prefixes else "REQ"
    requirements_dir_config = _LEGACY_INIT_FIELD_CONFIGS["requirements_dir"]
    questions.append(
        _build_interview_question(
            field="requirements_dir",
            group_id=str(requirements_dir_config["group"]),
            label=str(requirements_dir_config["label"]),
            prompt=str(requirements_dir_config["prompt"]),
            inferred_answers=[requirements_dir.as_posix()],
            allow_multiple=bool(requirements_dir_config["allow_multiple"]),
            allow_custom=bool(requirements_dir_config["allow_custom"]),
            allow_skip=bool(requirements_dir_config["allow_skip"]),
            first_selected_is_canonical=bool(requirements_dir_config["first_selected_is_canonical"]),
            custom_answer_prompt=str(requirements_dir_config["custom_answer_prompt"]),
            suggested_options=_legacy_init_requirements_dir_options(repo_root, requirements_dir),
        )
    )
    id_prefix_config = _LEGACY_INIT_FIELD_CONFIGS["id_prefix"]
    questions.append(
        _build_id_prefix_question(
            repo_root=repo_root,
            group_id=str(id_prefix_config["group"]),
            prompt=str(id_prefix_config["prompt"]),
            inferred_prefix=inferred_prefix,
        )
    )

    questions.extend(_build_bootstrap_chat_questions(command_hints))

    issue_mode = "use-gh-if-available" if bool(issue_context.get("used")) or str(issue_context.get("reason") or "") != "gh CLI not found" else "skip-gh-issues"
    for field in _LEGACY_INIT_CHAT_FIELDS[2:]:
        inferred_answers: list[str] = []
        suggested_options = _LEGACY_INIT_OPTION_SETS.get(field, ())
        config = _LEGACY_INIT_FIELD_CONFIGS[field]
        if field == "docs_review":
            inferred_answers = ["use-current-docs", "readmes-first"]
        elif field == "source_grokking":
            inferred_answers = ["focused-pass"]
        elif field == "test_grokking":
            inferred_answers = ["focused-tests"]
        elif field == "domain_focus":
            inferred_answers = [str(area["title"]) for area in source_areas]
            suggested_options = tuple(
                {
                    "value": str(area["title"]),
                    "label": str(area["title"]),
                    "description": f"Detected from `{area['evidence']}`.",
                    "recommended": True,
                }
                for area in source_areas
            )
        elif field == "issue_backlog":
            inferred_answers = [issue_mode]
        elif field == "legacy_notes":
            inferred_answers = [
                "Review the generated starter catalog before treating it as source of truth.",
            ]
        questions.append(
            _build_interview_question(
                field=field,
                group_id=str(config["group"]),
                label=str(config["label"]),
                prompt=str(config["prompt"]),
                inferred_answers=inferred_answers,
                allow_multiple=bool(config["allow_multiple"]),
                allow_custom=bool(config["allow_custom"]),
                allow_skip=bool(config["allow_skip"]),
                first_selected_is_canonical=bool(config["first_selected_is_canonical"]),
                custom_answer_prompt=str(config["custom_answer_prompt"]),
                suggested_options=suggested_options,
                detected_from=[str(area["evidence"]) for area in source_areas] if field == "domain_focus" else [],
                recommended_values=inferred_answers,
                safe_default_values=(
                    ["readmes-first"]
                    if field == "docs_review"
                    else ["focused-pass"]
                    if field == "source_grokking"
                    else ["focused-tests"]
                    if field == "test_grokking"
                    else [issue_mode]
                    if field == "issue_backlog"
                    else []
                ),
            )
        )
    return questions


def _match_domain_focus_answers(
    source_areas: list[dict[str, str]],
    values: list[str],
) -> list[dict[str, str]]:
    if not values:
        return source_areas
    matched: list[dict[str, str]] = []
    seen_titles: set[str] = set()
    area_lookup = {
        str(area["title"]).casefold(): area
        for area in source_areas
    }
    slug_lookup = {
        str(area["slug"]).casefold(): area
        for area in source_areas
    }
    for raw in values:
        key = str(raw).strip().casefold()
        if not key:
            continue
        area = area_lookup.get(key) or slug_lookup.get(key)
        if area is None:
            title = str(raw).strip()
            slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-") or "custom-domain"
            area = {
                "title": title,
                "slug": slug,
                "evidence": "bootstrap interview",
            }
        title_key = str(area["title"]).casefold()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        matched.append(area)
    return matched or source_areas


def _slugify_token(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "legacy"


def _title_from_token(value: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", value)
    return " ".join(part.capitalize() for part in parts if part) or "Legacy"


def _allocate_sequential_id(prefix: str, next_number: int) -> tuple[str, int]:
    return f"{prefix}-{next_number:03d}", next_number + 1


def _detect_legacy_source_areas(repo_root: Path, max_source_areas: int) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen_slugs: set[str] = set()

    def add_candidate(raw_name: str, evidence: str) -> None:
        slug = _slugify_token(raw_name)
        if slug in seen_slugs:
            return
        seen_slugs.add(slug)
        candidates.append(
            {
                "slug": slug,
                "title": _title_from_token(raw_name),
                "evidence": evidence,
            }
        )

    src_root = repo_root / "src"
    if src_root.exists():
        for path in sorted(src_root.iterdir()):
            if len(candidates) >= max_source_areas:
                break
            if path.is_dir() and not path.name.startswith((".", "__")):
                add_candidate(path.name, f"src/{path.name}")

    if not candidates:
        for dirname in ("app", "apps", "lib", "server", "client", "backend", "frontend"):
            path = repo_root / dirname
            if path.is_dir():
                add_candidate(dirname, dirname)
            if len(candidates) >= max_source_areas:
                break

    if not candidates:
        add_candidate(repo_root.name, repo_root.name)

    return candidates[:max_source_areas]


def _collect_github_issue_context(repo_root: Path, max_issue_requirements: int) -> dict[str, object]:
    gh_executable = shutil.which("gh")
    if gh_executable is None:
        return {
            "available": False,
            "used": False,
            "reason": "gh CLI not found",
            "issues": [],
        }

    try:
        result = subprocess.run(
            [
                gh_executable,
                "issue",
                "list",
                "--limit",
                str(max_issue_requirements),
                "--json",
                "number,title,labels,state",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {
            "available": True,
            "used": False,
            "reason": str(exc),
            "issues": [],
        }

    if result.returncode != 0:
        return {
            "available": True,
            "used": False,
            "reason": (result.stderr or result.stdout or "gh issue list failed").strip(),
            "issues": [],
        }

    try:
        data = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        return {
            "available": True,
            "used": False,
            "reason": "gh returned invalid JSON",
            "issues": [],
        }

    issues: list[dict[str, object]] = []
    if isinstance(data, list):
        for item in data[:max_issue_requirements]:
            if not isinstance(item, dict):
                continue
            labels = item.get("labels") if isinstance(item.get("labels"), list) else []
            issues.append(
                {
                    "number": int(item.get("number") or 0),
                    "title": str(item.get("title") or "").strip(),
                    "state": str(item.get("state") or "open"),
                    "labels": [str(label.get("name") or "") for label in labels if isinstance(label, dict)],
                }
            )
    return {
        "available": True,
        "used": bool(issues),
        "reason": None if issues else "gh returned no issues",
        "issues": issues,
    }


def _build_legacy_init_readme(
    requirements_dir: Path,
    starter_prefix: str,
    domain_files: list[dict[str, str]],
    interview_notes: dict[str, list[str]] | None = None,
) -> str:
    notes = interview_notes or {}
    legacy_preferences: list[str] = []
    for field in ("docs_review", "source_grokking", "test_grokking", "issue_backlog", "legacy_notes"):
        for item in notes.get(field, []):
            text = str(item).strip()
            if text:
                legacy_preferences.append(text)
    extra_sections = [
        render_startup_message("legacy-readme-seeded-note.md").strip()
    ]
    if legacy_preferences:
        extra_sections.append(
            render_startup_message(
                "legacy-readme-interview-notes.md",
                {
                    "NOTES_BULLETS": _markdown_list(legacy_preferences, "")
                },
            ).strip()
        )
    return render_requirements_index(
        index_display=f"{requirements_dir.as_posix()}/{REQUIREMENTS_INDEX_NAME}",
        criteria_dir_display=requirements_dir.as_posix(),
        starter_display=f"{requirements_dir.as_posix()}/starter.md",
        starter_prefix=starter_prefix,
        requirement_document_entries=domain_files,
        extra_sections=extra_sections,
    )


def _build_legacy_init_files(
    repo_root: Path,
    requirements_dir: Path,
    id_prefixes: tuple[str, ...],
    interview_answers: tuple[str, ...] = (),
) -> dict[str, object]:
    rules = _load_legacy_init_rules()
    command_hints = _detect_project_command_hints(repo_root)
    source_areas = _detect_legacy_source_areas(repo_root, int(rules["max_source_areas"]))
    issue_context = _collect_github_issue_context(repo_root, int(rules["max_issue_requirements"]))
    legacy_answer_map = _collect_interview_answers(
        interview_answers,
        _BOOTSTRAP_CHAT_FIELDS + _LEGACY_INIT_CHAT_FIELDS,
    )

    prefix = id_prefixes[0] if id_prefixes else str(legacy_answer_map.get("id_prefix", ["REQ"])[0]).strip().upper().rstrip("-")
    next_number = 1
    command_hints = _apply_command_answers(command_hints, legacy_answer_map)
    source_areas = _match_domain_focus_answers(source_areas, legacy_answer_map.get("domain_focus", []))
    if any(value == "skip-gh-issues" for value in legacy_answer_map.get("issue_backlog", [])):
        issue_context = {
            "used": False,
            "reason": "skipped by bootstrap interview",
            "issues": [],
        }

    proposed_files: list[dict[str, str]] = []

    source_domain_entries: list[dict[str, str]] = []
    for area in source_areas:
        requirement_id, next_number = _allocate_sequential_id(prefix, next_number)
        relative_path = f"{requirements_dir.as_posix()}/{area['slug']}.md"
        source_domain_entries.append(
            {
                "path": relative_path,
                "title": f"{area['title']} Requirements",
                "description": f"initial seed derived from detected repository area `{area['evidence']}`",
                "content": render_legacy_source_domain(
                    title=area["title"],
                    scope=f"initial legacy-init seed derived from `{area['evidence']}`.",
                    evidence=area["evidence"],
                    requirement_id=requirement_id,
                ),
            }
        )

    workflow_ids = []
    for _index in range(2):
        requirement_id, next_number = _allocate_sequential_id(prefix, next_number)
        workflow_ids.append(requirement_id)
    workflow_entry = {
        "path": f"{requirements_dir.as_posix()}/developer-workflows.md",
        "title": "Developer Workflows Requirements",
        "description": "seeded from detected build, run, smoke, and validation commands",
        "content": render_legacy_workflow_domain(
            scope="initial legacy-init seed for the repository's canonical developer workflows.",
            setup_id=workflow_ids[0],
            validation_id=workflow_ids[1],
            setup_commands=command_hints["dev_environment"] + command_hints["dev_build"] + command_hints["dev_run"],
            validation_commands=command_hints["dev_smoke"] + command_hints["test_primary"] + command_hints["test_integration"] + command_hints["test_lint"],
        ),
    }

    issue_entry: dict[str, str] | None = None
    issues = issue_context.get("issues") if isinstance(issue_context.get("issues"), list) else []
    if issues:
        issue_ids: list[str] = []
        for _issue in issues:
            requirement_id, next_number = _allocate_sequential_id(prefix, next_number)
            issue_ids.append(requirement_id)
        issue_entry = {
            "path": f"{requirements_dir.as_posix()}/issue-backlog.md",
            "title": "Issue Backlog Requirements",
            "description": "seeded from GitHub issues discovered via gh CLI",
            "content": render_legacy_issue_domain(
                scope="initial legacy-init seed from the repository's GitHub issue backlog.",
                issues=issues,
                requirement_ids=issue_ids,
            ),
        }

    selected_domains = source_domain_entries[: max(int(rules["max_domain_files"]) - 1, 1)]
    domain_files_for_index = [*selected_domains, workflow_entry]
    if issue_entry is not None and len(domain_files_for_index) < int(rules["max_domain_files"]):
        domain_files_for_index.append(issue_entry)

    readme_content = _build_legacy_init_readme(
        requirements_dir,
        prefix,
        domain_files_for_index,
        interview_notes=legacy_answer_map,
    )
    config_entry = preview_project_config_scaffold(
        repo_root,
        requirements_dir.as_posix(),
        prefix,
    )
    if config_entry is not None:
        proposed_files.append(config_entry)

    proposed_files.append(
        {
            "path": f"{requirements_dir.as_posix()}/{REQUIREMENTS_INDEX_NAME}",
            "title": "Requirements Index",
            "description": "legacy-init index for the generated requirement seeds",
            "content": readme_content,
        }
    )
    proposed_files.extend(domain_files_for_index)

    return {
        "requirements_dir": requirements_dir.as_posix(),
        "starter_prefix": prefix,
        "detected_context": {
            "source_areas": source_areas,
            "detected_command_sources": command_hints["detected_sources"],
        },
        "issue_discovery": issue_context,
        "proposed_files": proposed_files,
        "interview_answers": legacy_answer_map,
    }


def _write_legacy_init_files(repo_root: Path, proposed_files: list[dict[str, str]]) -> list[str]:
    created_files: list[str] = []
    domain_paths: list[Path] = []
    for entry in proposed_files:
        relative_path = str(entry["path"])
        content = str(entry["content"])
        target = repo_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        created_files.append(relative_path)
        if target.suffix == ".md" and target.name != REQUIREMENTS_INDEX_NAME:
            domain_paths.append(target)
    for domain_path in domain_paths:
        process_file(domain_path, check_only=False)
    return created_files


def _build_or_apply_legacy_init_payload(
    repo_root: Path,
    requirements_dir_input: str | None,
    id_prefixes: tuple[str, ...],
    apply: bool,
    chat_mode: bool = False,
    interview_answers: tuple[str, ...] = (),
) -> dict[str, object]:
    rules = _load_legacy_init_rules()
    legacy_answer_map = _collect_interview_answers(
        interview_answers,
        _BOOTSTRAP_CHAT_FIELDS + _LEGACY_INIT_CHAT_FIELDS,
    )
    criteria_dir = Path(
        requirements_dir_input
        or str(legacy_answer_map.get("requirements_dir", [str(rules["default_requirements_dir"])] )[0])
    )
    if not criteria_dir.is_absolute():
        criteria_dir = (repo_root / criteria_dir).resolve()

    existing_markdown = sorted(criteria_dir.glob("*.md")) if criteria_dir.exists() else []
    if apply and existing_markdown:
        display = ", ".join(format_path_display(path, repo_root) for path in existing_markdown)
        raise click.ClickException(
            "--workflow-mode init-legacy --write requires an empty target requirements directory. "
            f"Found existing markdown files: {display}"
        )

    plan = _build_legacy_init_files(
        repo_root=repo_root,
        requirements_dir=criteria_dir.relative_to(repo_root),
        id_prefixes=id_prefixes,
        interview_answers=interview_answers,
    )
    legacy_questions = _build_legacy_init_chat_questions(
        repo_root=repo_root,
        requirements_dir=criteria_dir.relative_to(repo_root),
        id_prefixes=id_prefixes or (plan["starter_prefix"],),
        command_hints=_detect_project_command_hints(repo_root),
        source_areas=list(plan["detected_context"].get("source_areas", [])),
        issue_context=plan["issue_discovery"],
    )
    payload = {
        "mode": "legacy-init-plan",
        "workflow_mode": "init-legacy",
        "read_only": not apply,
        "repo_root": str(repo_root),
        "requirements_dir": plan["requirements_dir"],
        "starter_prefix": plan["starter_prefix"],
        "detected_context": plan["detected_context"],
        "issue_discovery": plan["issue_discovery"],
        "proposed_files": plan["proposed_files"],
        "total_files": len(plan["proposed_files"]),
        "interaction_contract": _build_interview_interaction_contract(),
        "interview": _build_interview_payload(
            enabled=chat_mode,
            questions=legacy_questions,
            applied_answers=plan.get("interview_answers", {}),
            extras={
                "detected_sources": list(plan["detected_context"].get("detected_command_sources", [])),
                "detected_source_areas": [
                    str(area.get("title") or "")
                    for area in plan["detected_context"].get("source_areas", [])
                    if str(area.get("title") or "").strip()
                ],
            },
        ),
    }
    if apply:
        payload["created_files"] = _write_legacy_init_files(repo_root, plan["proposed_files"])
        payload["changed_count"] = len(payload["created_files"])
        payload["mode"] = "legacy-init-apply"
    return payload


def _detect_workspace_bundle_state(repo_root: Path) -> dict[str, object]:
    minimal_manifest = _read_bundle_manifest("minimal")
    full_manifest = _read_bundle_manifest("full")

    def existing_entries(entries: tuple[str, ...]) -> list[str]:
        return [
            relative_path
            for relative_path in entries
            if (repo_root / relative_path).exists()
        ]

    existing_minimal = existing_entries(minimal_manifest)
    existing_full = existing_entries(full_manifest)
    definition_files = _workspace_definition_files(repo_root)

    if len(existing_full) == len(full_manifest):
        return {
            "installed": True,
            "preset": "full",
            "state": "full",
            "active_definition_files": definition_files,
        }
    if len(existing_minimal) == len(minimal_manifest):
        return {
            "installed": True,
            "preset": "minimal",
            "state": "minimal",
            "active_definition_files": definition_files,
        }
    if definition_files:
        return {
            "installed": False,
            "preset": None,
            "state": "partial",
            "active_definition_files": definition_files,
        }
    return {
        "installed": False,
        "preset": None,
        "state": "absent",
        "active_definition_files": [],
    }


def _build_guide_payload(
    repo_root: Path,
    requirements_dir: Path,
    read_only: bool,
    workflow_mode: str,
) -> dict[str, object]:
    guide = _load_workflow_guide(workflow_mode)
    bundle_state = _detect_workspace_bundle_state(repo_root)
    payload = {
        "mode": "guide",
        "workflow_mode": workflow_mode,
        "read_only": read_only,
        "repo_root": str(repo_root),
        "requirements_dir": format_path_display(requirements_dir, repo_root),
        "summary": guide["summary"],
        "workflow": guide["workflow"],
        "examples": guide["examples"],
        "batch_policy": guide.get("batch_policy"),
        "validation_checks": guide.get("validation_checks"),
        "bundle_installation": bundle_state,
    }
    if not bool(bundle_state.get("installed")):
        payload["bundled_definitions"] = _build_packaged_bundle_definitions("full")
    return payload


def _bundle_files_for_preset(preset: str) -> dict[str, str]:
    return {
        relative_path: _read_bundle_resource_file(relative_path)
        for relative_path in _read_bundle_manifest(preset)
    }


def _resolve_brainstorm_file(repo_root: Path, brainstorm_file: str | None) -> Path:
    candidate = Path(brainstorm_file) if brainstorm_file else repo_root / "docs" / "brainstorm.md"
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    if not candidate.exists() or not candidate.is_file():
        raise click.ClickException(f"Brainstorm file not found: {candidate}")
    return candidate


def _extract_brainstorm_blocks(brainstorm_path: Path) -> list[dict[str, str | None]]:
    blocks: list[dict[str, str | None]] = []
    current_section: str | None = None
    current_subsection: str | None = None
    paragraph_lines: list[str] = []
    in_code_block = False

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        text = " ".join(line.strip() for line in paragraph_lines if line.strip()).strip()
        paragraph_lines.clear()
        if not text or text == "##":
            return
        blocks.append(
            {
                "section": current_section,
                "subsection": current_subsection,
                "text": text,
            }
        )

    for raw_line in brainstorm_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            current_section = stripped[3:].strip()
            current_subsection = None
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            current_subsection = stripped[4:].strip()
            continue
        if not stripped:
            flush_paragraph()
            continue
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            blocks.append(
                {
                    "section": current_section,
                    "subsection": current_subsection,
                    "text": re.sub(r"^(?:[-*]|\d+\.)\s+", "", stripped).strip(),
                }
            )
            continue
        paragraph_lines.append(stripped)

    flush_paragraph()
    return blocks


def _suggest_priority_for_brainstorm(
    text: str,
    section: str | None,
    subsection: str | None,
    priority_labels: tuple[str, ...],
) -> str:
    rules = _load_brainstorm_rules()
    haystack = " ".join(filter(None, [section, subsection, text])).casefold()
    for tokens, priority_rank in rules["priority_hints"]:
        if any(token in haystack for token in tokens):
            return _priority_label_for_rank(priority_labels, priority_rank)
    return _priority_label_for_rank(priority_labels, int(rules["default_priority_rank"]))


def _suggest_target_doc_for_brainstorm(
    text: str,
    section: str | None,
    subsection: str | None,
    domain_paths_by_name: dict[str, Path],
) -> Path:
    rules = _load_brainstorm_rules()
    haystack = " ".join(filter(None, [section, subsection, text])).casefold()
    for tokens, filename in rules["section_targets"]:
        if any(token in haystack for token in tokens):
            target = domain_paths_by_name.get(filename)
            if target is not None:
                return target
    fallback = domain_paths_by_name.get(str(rules["default_target_file"]))
    if fallback is None:
        raise click.ClickException(
            f"Could not locate {rules['default_target_file']} while building brainstorm suggestions."
        )
    return fallback


def _proposal_title_from_text(text: str) -> str:
    rules = _load_brainstorm_rules()
    title_rules = rules["proposal_title"]
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return "Untitled brainstorm proposal"
    head = re.split(r"[.!?]", cleaned, maxsplit=1)[0].strip()
    words = head.split()
    max_words = int(title_rules["max_words"])
    max_chars = int(title_rules["max_chars"])
    if len(words) > max_words:
        head = " ".join(words[:max_words]).rstrip(" ,;:")
    return head[:max_chars].rstrip(" ,;:")


def _build_brainstorm_plan_payload(
    repo_root: Path,
    requirements_dir: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    brainstorm_path: Path,
) -> dict[str, object]:
    runtime_priority_labels = _load_runtime_priority_labels(repo_root)
    domain_paths_by_name = {path.name: path for path in domain_files}
    next_id_by_path: dict[Path, tuple[str, int]] = {}

    for path in domain_files:
        prefix = "RQMD"
        next_number = 1
        requirements = parse_requirements(path, id_prefixes=id_prefixes)
        for requirement in requirements:
            req_id = str(requirement.get("id") or "")
            match = re.match(r"^(?P<prefix>.+)-(?P<number>\d+)$", req_id)
            if not match:
                continue
            prefix = match.group("prefix")
            next_number = max(next_number, int(match.group("number")) + 1)
        next_id_by_path[path] = (prefix, next_number)

    proposals: list[dict[str, object]] = []
    for block in _extract_brainstorm_blocks(brainstorm_path):
        text = str(block.get("text") or "").strip()
        if not text:
            continue

        target_path = _suggest_target_doc_for_brainstorm(
            text=text,
            section=str(block.get("section") or ""),
            subsection=str(block.get("subsection") or ""),
            domain_paths_by_name=domain_paths_by_name,
        )
        prefix, next_number = next_id_by_path[target_path]
        suggested_id = f"{prefix}-{next_number:03d}"
        next_id_by_path[target_path] = (prefix, next_number + 1)
        priority = _suggest_priority_for_brainstorm(
            text=text,
            section=str(block.get("section") or ""),
            subsection=str(block.get("subsection") or ""),
            priority_labels=runtime_priority_labels,
        )

        proposals.append(
            {
                "source": {
                    "section": block.get("section"),
                    "subsection": block.get("subsection"),
                    "text": text,
                },
                "proposal": {
                    "title": _proposal_title_from_text(text),
                    "target_file": format_path_display(target_path, repo_root),
                    "suggested_id": suggested_id,
                    "status": "💡 Proposed",
                    "priority": priority,
                },
            }
        )

    configured_priority_order = runtime_priority_labels
    priority_order = {
        priority: index
        for index, priority in enumerate(configured_priority_order)
    }
    proposals.sort(
        key=lambda item: (
            priority_order.get(str(item["proposal"]["priority"]), 99),
            str(item["proposal"]["target_file"]),
            str(item["proposal"]["suggested_id"]),
        )
    )
    for index, item in enumerate(proposals, start=1):
        item["rank"] = index

    return {
        "mode": "brainstorm-plan",
        "workflow_mode": "brainstorm",
        "read_only": True,
        "repo_root": str(repo_root),
        "requirements_dir": format_path_display(requirements_dir, repo_root),
        "source_file": format_path_display(brainstorm_path, repo_root),
        "total_proposals": len(proposals),
        "proposal_sort": {
            "priority_order": list(configured_priority_order),
        },
        "proposals": proposals,
    }


def _install_agent_bundle(
    repo_root: Path,
    preset: str,
    overwrite_existing: bool,
    dry_run: bool,
    chat_mode: bool = False,
    interview_answers: tuple[str, ...] = (),
) -> dict[str, object]:
    files = _bundle_files_for_preset(preset)
    detected_hints = _detect_project_command_hints(repo_root)
    applied_answers = _collect_interview_answers(interview_answers, _BOOTSTRAP_CHAT_FIELDS)
    resolved_hints = _apply_command_answers(detected_hints, applied_answers)
    generated_skill_files = _render_project_skill_content_from_hints(resolved_hints)
    files.update(generated_skill_files)
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

    bootstrap_questions = _build_bootstrap_chat_questions(detected_hints)
    return {
        "mode": "install-agent-bundle",
        "read_only": dry_run,
        "preset": preset,
        "overwrite_existing": overwrite_existing,
        "dry_run": dry_run,
        "interaction_contract": _build_interview_interaction_contract(),
        "interview": _build_interview_payload(
            enabled=chat_mode,
            questions=bootstrap_questions,
            applied_answers=applied_answers,
            extras={
                "detected_sources": list(detected_hints.get("detected_sources", [])),
            },
        ),
        "generated_skill_files": sorted(generated_skill_files),
        "generated_skill_previews": [
            {"path": path, "content": content}
            for path, content in sorted(generated_skill_files.items())
        ] if chat_mode else [],
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


def _emit(payload: dict[str, object], json_output: bool, json_output_file: Path | None = None) -> None:
    if json_output_file is not None:
        _write_json_payload_file(payload, json_output_file)

    if json_output:
        click.echo(_serialize_json_payload(payload))
        return

    mode = payload.get("mode", "unknown")
    if mode in {"init-chat", "init-plan", "init-apply"}:
        strategy = payload.get("strategy")
        if isinstance(strategy, dict):
            click.echo(f"rqmd-ai init: {strategy.get('selected', 'unknown')}")
            for reason in strategy.get("reasons", []):
                click.echo(f"- {reason}")
        if payload.get("read_only") is True:
            click.echo(render_startup_message("preview-only.md").rstrip())
        prompt = payload.get("handoff_prompt")
        if isinstance(prompt, str) and prompt.strip():
            click.echo("")
            click.echo(render_startup_message("chat-handoff-heading.md").rstrip())
            click.echo("")
            click.echo(prompt)
        return
    if mode in {"legacy-init-plan", "legacy-init-apply"}:
        click.echo(f"rqmd-ai legacy init: {payload.get('requirements_dir')}")
        if payload.get("read_only") is True:
            click.echo(render_startup_message("preview-only.md").rstrip())
        issue_discovery = payload.get("issue_discovery")
        issue_details = issue_discovery if isinstance(issue_discovery, dict) else {}
        issue_status = "used" if issue_details.get("used") else issue_details.get("reason", "not used")
        click.echo(f"GitHub issue discovery: {issue_status}")
        if mode == "legacy-init-plan":
            click.echo(f"proposed files: {payload.get('total_files')}")
            for item in payload.get("proposed_files", []):
                if isinstance(item, dict):
                    click.echo(f"- {item.get('path')}: {item.get('description')}")
        else:
            for path in payload.get("created_files", []):
                click.echo(f"- created {path}")
        return

    click.echo(f"rqmd-ai mode: {mode}")
    read_only = payload.get("read_only")
    if isinstance(read_only, bool):
        click.echo(f"read-only: {'yes' if read_only else 'no'}")
    if mode == "guide":
        workflow_mode = payload.get("workflow_mode")
        if workflow_mode:
            click.echo(f"workflow mode: {workflow_mode}")
        summary = payload.get("summary")
        if summary:
            click.echo(str(summary))
        for item in payload.get("workflow", []):
            click.echo(f"- {item}")
        validation_checks = payload.get("validation_checks")
        if isinstance(validation_checks, list) and validation_checks:
            click.echo("validation checks:")
            for item in validation_checks:
                click.echo(f"- {item}")
        bundle_installation = payload.get("bundle_installation")
        if isinstance(bundle_installation, dict):
            click.echo(f"workspace bundle: {bundle_installation.get('state', 'unknown')}")
        bundled_definitions = payload.get("bundled_definitions")
        if isinstance(bundled_definitions, dict):
            files = bundled_definitions.get("files")
            if isinstance(files, list):
                click.echo(f"packaged definitions embedded: {len(files)}")
        return
    if mode == "brainstorm-plan":
        click.echo(f"source file: {payload.get('source_file')}")
        click.echo(f"total proposals: {payload.get('total_proposals')}")
        for item in payload.get("proposals", []):
            if not isinstance(item, dict):
                continue
            proposal = item.get("proposal") if isinstance(item.get("proposal"), dict) else {}
            click.echo(
                f"- #{item.get('rank')} {proposal.get('suggested_id')} [{proposal.get('priority')}] -> {proposal.get('target_file')}: {proposal.get('title')}"
            )
        return

def _emit_history_report(
    payload: dict[str, object],
    json_output: bool,
    json_output_file: Path | None = None,
) -> None:
    if json_output:
        _emit(payload, json_output=True, json_output_file=json_output_file)
        return

    if json_output_file is not None:
        _write_json_payload_file(payload, json_output_file)

    report_type = str(payload.get("report_type") or "unknown")
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    source = payload.get("source") if isinstance(payload.get("source"), dict) else {}

    click.echo("History Report")
    click.echo(f"Report Type: {report_type}")
    if source:
        click.echo(f"Source: {source}")

    if report_type == "state":
        click.echo(f"Total Requirements: {summary.get('total_requirements', 0)}")
        click.echo(f"Total Files: {summary.get('total_files', 0)}")
        by_status = summary.get("by_status") if isinstance(summary.get("by_status"), dict) else {}
        if by_status:
            click.echo("By Status:")
            for label, count in by_status.items():
                click.echo(f"- {label}: {count}")
        return

    if report_type == "compare":
        click.echo(f"Transitions: {summary.get('transitions', 0)}")
        click.echo(f"Added: {summary.get('added', 0)}")
        click.echo(f"Removed: {summary.get('removed', 0)}")
        click.echo(f"Unchanged: {summary.get('unchanged', 0)}")


def _raise_duplicate_id_error(
    repo_root: Path,
    duplicates: dict[str, list[tuple[Path, int]]],
) -> None:
    duplicate_parts: list[str] = []
    for requirement_id in sorted(duplicates):
        locations = ", ".join(
            f"{format_path_display(path, repo_root)}:{line_number}"
            for path, line_number in duplicates[requirement_id]
        )
        duplicate_parts.append(f"{requirement_id} [{locations}]")
    raise click.ClickException(f"Duplicate requirement IDs found: {'; '.join(duplicate_parts)}")


def _build_history_state_report_payload(
    repo_root: Path,
    requirements_dir: Path,
    domain_files: list[Path],
    id_prefixes: tuple[str, ...],
    history_source: dict[str, object] | None,
) -> dict[str, object]:
    by_status: dict[str, int] = {}
    requirements: list[dict[str, object]] = []

    for path in domain_files:
        for requirement in parse_requirements(path, id_prefixes=id_prefixes):
            status = str(requirement.get("status") or "")
            if status:
                by_status[status] = by_status.get(status, 0) + 1
            requirements.append(
                {
                    "id": requirement.get("id"),
                    "title": requirement.get("title"),
                    "status": requirement.get("status"),
                    "priority": requirement.get("priority"),
                    "path": format_path_display(path, repo_root),
                }
            )

    return {
        "mode": "history-report",
        "report_type": "state",
        "source": history_source
        if history_source is not None
        else {
            "requested_ref": "current",
            "detached": False,
        },
        "requirements_dir": format_path_display(requirements_dir, repo_root),
        "summary": {
            "total_files": len(domain_files),
            "total_requirements": len(requirements),
            "by_status": dict(sorted(by_status.items(), key=lambda item: item[0])),
        },
        "requirements": requirements,
    }


def _build_history_compare_report_payload(
    compare_payload: dict[str, object],
    ref_a: str,
    ref_b: str,
) -> dict[str, object]:
    return {
        "mode": "history-report",
        "report_type": "compare",
        "source": {
            "requested_compare_refs": f"{ref_a}..{ref_b}",
            "detached": True,
            "ref_a": compare_payload.get("ref_a"),
            "ref_b": compare_payload.get("ref_b"),
        },
        "summary": compare_payload.get("summary"),
        "transitions": compare_payload.get("transitions"),
        "added": compare_payload.get("added"),
        "removed": compare_payload.get("removed"),
    }


def _build_history_action_preview_payload(
    manager: HistoryManager,
    action_spec: str,
    id_prefixes: tuple[str, ...],
) -> dict[str, object]:
    raw = action_spec.strip()
    if ":" not in raw:
        raise click.ClickException(
            "--history-action must be in ACTION:ARGS format (for example restore:0, replay:0..3, cherry-pick:1,2)."
        )

    action_raw, args_raw = raw.split(":", 1)
    action = action_raw.strip().casefold()
    args_value = args_raw.strip()
    if not action or not args_value:
        raise click.ClickException(
            "--history-action must include both action and args (for example restore:0)."
        )

    if action == "restore":
        target = manager.resolve_ref(args_value)
        if target is None:
            raise click.ClickException(f"Unknown --history-action restore target: {args_value!r}")
        compare_payload = _build_compare_payload(
            manager=manager,
            ref_a="head",
            ref_b=args_value,
            id_prefixes=id_prefixes,
        )
        return {
            "mode": "history-action-preview",
            "action": "restore",
            "source": {
                "requested": action_spec,
                "target_ref": args_value,
            },
            "target": compare_payload.get("ref_b"),
            "current": compare_payload.get("ref_a"),
            "preview": {
                "summary": compare_payload.get("summary"),
                "transitions": compare_payload.get("transitions"),
                "added": compare_payload.get("added"),
                "removed": compare_payload.get("removed"),
            },
        }

    if action == "replay":
        if ".." in args_value:
            left, right = args_value.split("..", 1)
            ref_a = left.strip()
            ref_b = right.strip()
        else:
            parts = args_value.split(None, 1)
            if len(parts) != 2:
                raise click.ClickException(
                    "replay args must include two refs in 'A..B' or 'A B' format."
                )
            ref_a, ref_b = parts[0].strip(), parts[1].strip()

        pair = manager.resolve_two_refs(ref_a, ref_b)
        if pair is None:
            raise click.ClickException(f"Unknown --history-action replay range: {args_value!r}")
        entry_a, entry_b = pair
        idx_a = int(entry_a.get("entry_index", -1))
        idx_b = int(entry_b.get("entry_index", -1))
        if idx_a < 0 or idx_b < 0:
            raise click.ClickException("Replay preview requires refs that resolve to indexed history entries.")
        if idx_b <= idx_a:
            raise click.ClickException("Replay preview requires an increasing range where end is after start.")

        compare_payload = _build_compare_payload(
            manager=manager,
            ref_a=ref_a,
            ref_b=ref_b,
            id_prefixes=id_prefixes,
        )
        entries = manager.list_entries()[idx_a + 1 : idx_b + 1]
        replay_steps = [
            {
                "entry_index": idx_a + 1 + offset,
                "commit": item.get("commit"),
                "stable_id": manager.build_stable_history_id(str(item.get("commit") or "")) if item.get("commit") else None,
                "command": item.get("command"),
                "actor": item.get("actor"),
                "branch": item.get("branch"),
                "files": list(item.get("files") or []),
            }
            for offset, item in enumerate(entries)
        ]

        return {
            "mode": "history-action-preview",
            "action": "replay",
            "source": {
                "requested": action_spec,
                "range": {
                    "start": compare_payload.get("ref_a"),
                    "end": compare_payload.get("ref_b"),
                },
            },
            "steps": replay_steps,
            "preview": {
                "summary": compare_payload.get("summary"),
                "transitions": compare_payload.get("transitions"),
                "added": compare_payload.get("added"),
                "removed": compare_payload.get("removed"),
            },
        }

    if action == "cherry-pick":
        tokens = [token.strip() for token in args_value.split(",") if token.strip()]
        if not tokens:
            raise click.ClickException("cherry-pick args must include one or more refs separated by commas.")

        picks: list[dict[str, object]] = []
        total_transitions = 0
        total_added = 0
        total_removed = 0

        for token in tokens:
            entry = manager.resolve_ref(token)
            if entry is None:
                raise click.ClickException(f"Unknown --history-action cherry-pick target: {token!r}")

            parent_ref = str(entry.get("parent_commit") or "")
            preview: dict[str, object]
            if not parent_ref:
                preview = {
                    "summary": {
                        "transitions": 0,
                        "added": 0,
                        "removed": 0,
                        "unchanged": 0,
                        "total_a": 0,
                        "total_b": 0,
                    },
                    "transitions": [],
                    "added": [],
                    "removed": [],
                }
            else:
                compare_payload = _build_compare_payload(
                    manager=manager,
                    ref_a=parent_ref,
                    ref_b=str(entry.get("commit") or ""),
                    id_prefixes=id_prefixes,
                )
                preview = {
                    "summary": compare_payload.get("summary"),
                    "transitions": compare_payload.get("transitions"),
                    "added": compare_payload.get("added"),
                    "removed": compare_payload.get("removed"),
                }

            summary = preview.get("summary") if isinstance(preview.get("summary"), dict) else {}
            total_transitions += int(summary.get("transitions", 0))
            total_added += int(summary.get("added", 0))
            total_removed += int(summary.get("removed", 0))

            picks.append(
                {
                    "requested_ref": token,
                    "entry": {
                        "entry_index": entry.get("entry_index"),
                        "commit": entry.get("commit"),
                        "stable_id": manager.build_stable_history_id(str(entry.get("commit") or "")) if entry.get("commit") else None,
                        "timestamp": entry.get("timestamp"),
                        "command": entry.get("command"),
                        "actor": entry.get("actor"),
                        "branch": entry.get("branch"),
                        "parent_commit": entry.get("parent_commit"),
                    },
                    "preview": preview,
                }
            )

        return {
            "mode": "history-action-preview",
            "action": "cherry-pick",
            "source": {
                "requested": action_spec,
            },
            "picks": picks,
            "preview_totals": {
                "transitions": total_transitions,
                "added": total_added,
                "removed": total_removed,
            },
        }

    raise click.ClickException(
        "Unsupported --history-action action. Use one of: restore, replay, cherry-pick."
    )


def _resolve_repo_root(repo_root: Path) -> Path:
    if repo_root != Path("."):
        return repo_root.resolve()
    discovered, _source = discover_project_root(Path.cwd())
    return discovered


def _append_audit_record(repo_root: Path, record: dict[str, object]) -> str:
    audit_path = (repo_root / AUDIT_LOG_RELATIVE).resolve()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    line = dumps_json(record, sort_keys=True)
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
                "history_entry": entry.get("history_entry"),
            }
        )

    history_entries = [
        entry.get("history_entry")
        for entry in updates
        if isinstance(entry.get("history_entry"), dict)
    ]

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
            "history_entries": history_entries,
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
    history_manager = HistoryManager(repo_root=repo_root, requirements_dir=requirements_dir) if apply else None
    for req_id, status_input in updates:
        normalized = normalize_status_input(status_input)
        changed = False
        history_entry: dict[str, object] | None = None
        if apply:
            before_entries = history_manager.list_entries() if history_manager is not None else []
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
                if history_manager is not None:
                    after_entries = history_manager.list_entries()
                    if len(after_entries) > len(before_entries):
                        latest_entry = after_entries[-1]
                        commit_hash = str(latest_entry.get("commit") or "")
                        history_entry = {
                            "entry_index": len(after_entries) - 1,
                            "commit": commit_hash,
                            "stable_id": history_manager.build_stable_history_id(commit_hash) if commit_hash else None,
                            "timestamp": latest_entry.get("timestamp"),
                            "command": latest_entry.get("command"),
                            "branch": latest_entry.get("branch"),
                        }

        payload_updates.append(
            {
                "id": req_id,
                "requested_status": status_input,
                "status": normalized,
                "changed": changed,
                "history_entry": history_entry,
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
@click.argument("command_name", required=False)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_handle_version_option,
    help="Show the installed rqmd-ai version and editable source path when applicable.",
)
@click.option("--json", "--as-json", "json_output", is_flag=True, help="Emit machine-readable JSON output.")
@click.option(
    "--json-output-file",
    "json_output_file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Also write the JSON payload to a file. Useful when a terminal wrapper truncates stdout.",
)
@click.option("--show-guide", "guide", is_flag=True, help="Print onboarding guidance for rqmd-ai workflows.")
@click.option(
    "--workflow-mode",
    "workflow_mode",
    type=click.Choice(["general", "brainstorm", "implement", "init", "init-legacy"], case_sensitive=False),
    default="general",
    show_default=True,
    help="Guide variant to emit for rqmd-ai workflow sequencing.",
)
@click.option(
    "--brainstorm-file",
    "brainstorm_file",
    type=str,
    default=None,
    help="Optional markdown note file used by --workflow-mode brainstorm. Defaults to docs/brainstorm.md under --project-root.",
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
@click.option("--history-action", "history_action", type=str, default=None, help="Preview restore/replay/cherry-pick actions. Format: restore:REF | replay:A..B | cherry-pick:REF1,REF2.")
@click.option("--history-report", "history_report", is_flag=True, help="Emit temporal report payloads for a selected --history-ref or --compare-refs range.")
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
@click.option("--install-agent-bundle", "install_bundle", is_flag=True, help="Legacy flag equivalent of `rqmd-ai install`.")
@click.option(
    "--bundle-preset",
    "bundle_preset",
    type=click.Choice(["minimal", "full"], case_sensitive=False),
    default="full",
    show_default=True,
    help="Bundle preset for `rqmd-ai install` / --install-agent-bundle.",
)
@click.option(
    "--chat/--no-chat",
    "chat_mode",
    default=None,
    help="Emit the chat-first interview flow. Enabled by default for `rqmd-ai init`.",
)
@click.option(
    "--answer",
    "interview_answers",
    multiple=True,
    help="Answer one interview field using FIELD=VALUE. Repeat to select multiple suggestions or add custom values.",
)
@click.option(
    "--legacy",
    "force_legacy_init",
    is_flag=True,
    help="Force the compatibility legacy-init strategy when using the unified `rqmd-ai init` entrypoint.",
)
@click.option("--overwrite-existing", "overwrite_existing", is_flag=True, help="Allow --install-agent-bundle to overwrite existing instruction files.")
@click.option("--dry-run", "dry_run", is_flag=True, help="Preview --install-agent-bundle changes without writing files.")
def main(
    command_name: str | None,
    json_output: bool,
    json_output_file: Path | None,
    guide: bool,
    workflow_mode: str,
    brainstorm_file: str | None,
    repo_root: Path,
    requirements_dir: str | None,
    id_prefixes: tuple[str, ...],
    export_ids: tuple[str, ...],
    export_files: tuple[str, ...],
    export_status: str | None,
    history_ref: str | None,
    compare_refs: str | None,
    history_action: str | None,
    history_report: bool,
    include_body: bool,
    include_domain_body: bool,
    max_domain_body_chars: int,
    set_entries: tuple[str, ...],
    file_scope: str | None,
    apply: bool,
    install_bundle: bool,
    bundle_preset: str,
    chat_mode: bool | None,
    interview_answers: tuple[str, ...],
    force_legacy_init: bool,
    overwrite_existing: bool,
    dry_run: bool,
) -> None:
    repo_root = _resolve_repo_root(repo_root)
    workflow_mode = workflow_mode.lower()
    if command_name:
        normalized_command = command_name.strip().lower()
        if normalized_command in {"install", "i"}:
            install_bundle = True
        elif normalized_command == "init":
            workflow_mode = "init"
        else:
            raise click.ClickException(f"Unknown rqmd-ai command: {command_name}")
    if chat_mode is None:
        chat_mode = workflow_mode == "init"
    if brainstorm_file is not None and workflow_mode != "brainstorm":
        raise click.ClickException("--brainstorm-file can only be used with --workflow-mode brainstorm.")

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
            chat_mode=chat_mode,
            interview_answers=interview_answers,
        )
        _emit(payload, json_output=json_output, json_output_file=json_output_file)
        return

    if workflow_mode in {"init", "init-legacy"} and guide:
        rules = _load_legacy_init_rules()
        guide_requirements_dir = Path(requirements_dir or str(rules["default_requirements_dir"]))
        if not guide_requirements_dir.is_absolute():
            guide_requirements_dir = repo_root / guide_requirements_dir
        _emit(
            _build_guide_payload(
                repo_root,
                guide_requirements_dir,
                read_only=not apply,
                workflow_mode=workflow_mode,
            ),
            json_output=json_output,
            json_output_file=json_output_file,
        )
        return

    if workflow_mode == "init":
        if brainstorm_file is not None:
            raise click.ClickException("--brainstorm-file cannot be combined with --workflow-mode init.")
        if set_entries or export_ids or export_files or export_status or history_ref or compare_refs or history_action or history_report:
            raise click.ClickException(
                "--workflow-mode init is an onboarding surface and cannot be combined with export, update, or history options."
            )
        payload = _build_or_apply_init_payload(
            repo_root=repo_root,
            requirements_dir_input=requirements_dir,
            id_prefixes=id_prefixes,
            apply=apply,
            chat_mode=chat_mode,
            interview_answers=interview_answers,
            force_legacy=force_legacy_init,
        )
        _emit(payload, json_output=json_output, json_output_file=json_output_file)
        return

    if workflow_mode == "init-legacy":
        if brainstorm_file is not None:
            raise click.ClickException("--brainstorm-file cannot be combined with --workflow-mode init-legacy.")
        if set_entries or export_ids or export_files or export_status or history_ref or compare_refs or history_action or history_report:
            raise click.ClickException(
                "--workflow-mode init-legacy is a bootstrap surface and cannot be combined with export, update, or history options."
            )
        payload = _build_or_apply_legacy_init_payload(
            repo_root=repo_root,
            requirements_dir_input=requirements_dir,
            id_prefixes=id_prefixes,
            apply=apply,
            chat_mode=chat_mode,
            interview_answers=interview_answers,
        )
        _emit(payload, json_output=json_output, json_output_file=json_output_file)
        return

    resolved_criteria_dir, _message = resolve_requirements_dir(repo_root, requirements_dir)
    try:
        resolved_prefixes_input = normalize_id_prefixes(id_prefixes) if id_prefixes else id_prefixes
        id_prefixes = resolve_id_prefixes(repo_root, str(resolved_criteria_dir), resolved_prefixes_input)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc

    if history_report:
        if guide or apply or set_entries or workflow_mode != "general":
            raise click.ClickException("--history-report is read-only and cannot be combined with --show-guide, --write, or --update.")
        if not history_ref and not compare_refs:
            raise click.ClickException("--history-report requires either --history-ref or --compare-refs.")

    if history_action:
        if apply or set_entries or guide or workflow_mode != "general":
            raise click.ClickException("--history-action is read-only and cannot be combined with --show-guide, --write, or --update.")
        if history_ref or compare_refs or history_report:
            raise click.ClickException("--history-action cannot be combined with --history-ref, --compare-refs, or --history-report.")
        manager = HistoryManager(repo_root=repo_root, requirements_dir=resolved_criteria_dir)
        payload = _build_history_action_preview_payload(
            manager=manager,
            action_spec=history_action,
            id_prefixes=id_prefixes,
        )
        _emit(payload, json_output=json_output, json_output_file=json_output_file)
        return

    if compare_refs:
        if apply or set_entries or workflow_mode != "general":
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
        if history_report:
            _emit_history_report(
                _build_history_compare_report_payload(payload, ref_a=ref_a, ref_b=ref_b),
                json_output=json_output,
                json_output_file=json_output_file,
            )
        else:
            _emit(payload, json_output=json_output, json_output_file=json_output_file)
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
    duplicates = find_duplicate_requirement_ids(domain_files, id_prefixes=id_prefixes)
    if duplicates:
        _raise_duplicate_id_error(effective_repo_root, duplicates)

    if apply and not set_entries:
        raise click.ClickException("rqmd-ai --write requires at least one --update ID=STATUS update.")
    if workflow_mode != "general" and (apply or set_entries or export_ids or export_files or export_status or history_ref):
        raise click.ClickException(
            "--workflow-mode brainstorm|implement is a guidance surface and cannot be combined with export, update, history, or apply options."
        )
    if history_ref and apply:
        raise click.ClickException("--history-ref cannot be combined with --write.")
    if history_ref and set_entries:
        raise click.ClickException("--history-ref cannot be combined with --update; historical exports are read-only.")
    if history_report:
        payload = _build_history_state_report_payload(
            repo_root=effective_repo_root,
            requirements_dir=effective_requirements_dir,
            domain_files=domain_files,
            id_prefixes=id_prefixes,
            history_source=history_source,
        )
        _emit_history_report(payload, json_output=json_output, json_output_file=json_output_file)
        if history_tempdir is not None:
            history_tempdir.cleanup()
        return

    if workflow_mode == "brainstorm":
        brainstorm_path = _resolve_brainstorm_file(repo_root, brainstorm_file)
        payload = _build_brainstorm_plan_payload(
            repo_root=repo_root,
            requirements_dir=resolved_criteria_dir,
            domain_files=domain_files,
            id_prefixes=id_prefixes,
            brainstorm_path=brainstorm_path,
        )
        if history_tempdir is not None:
            history_tempdir.cleanup()
        _emit(payload, json_output=json_output, json_output_file=json_output_file)
        return

    if guide:
        if history_tempdir is not None:
            history_tempdir.cleanup()
        _emit(
            _build_guide_payload(
                repo_root,
                resolved_criteria_dir,
                read_only=(not apply),
                workflow_mode=workflow_mode,
            ),
            json_output=json_output,
            json_output_file=json_output_file,
        )
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
        _emit(payload, json_output=json_output, json_output_file=json_output_file)
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
        _emit(payload, json_output=json_output, json_output_file=json_output_file)
        if history_tempdir is not None:
            history_tempdir.cleanup()
        return

    if history_tempdir is not None:
        history_tempdir.cleanup()
    _emit(
        _build_guide_payload(
            repo_root,
            resolved_criteria_dir,
            read_only=True,
            workflow_mode=workflow_mode,
        ),
        json_output=json_output,
        json_output_file=json_output_file,
    )


if __name__ == "__main__":
    main()