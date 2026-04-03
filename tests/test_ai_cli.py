from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from click.testing import CliRunner

from rqmd import ai_cli
from rqmd.ai_cli import _parse_frontmatter, _parse_skill_frontmatter, main
from rqmd.constants import JSON_SCHEMA_VERSION
from rqmd.history import HistoryManager


def _assert_schema_version(payload: dict[str, object]) -> None:
    assert payload["schema_version"] == JSON_SCHEMA_VERSION
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(payload["schema_version"]))


def _write_demo_domain(path: Path) -> None:
    """Write a simple demo domain file for testing.

    Args:
        path: Path where the domain file should be written.
    """
    path.write_text(
        """# Demo Requirements

Scope: demo.

### RQMD-DEMO-001: First
- **Status:** 💡 Proposed

### RQMD-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )


def _write_domain_with_body(path: Path) -> None:
    """Write a demo domain file with domain body content for testing.

    Args:
        path: Path where the domain file should be written.
    """
    path.write_text(
        """# Demo Requirements

Scope: demo.

Domain note line one.
Domain note line two.

### RQMD-DEMO-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )


def _assert_default_closeout_guidance(text: str) -> None:
    assert "# What got done" in text
    assert "# Up next" in text
    assert "# Direction" in text
    assert "not fenced code blocks" in text


def _assert_dual_requirement_guidance(text: str) -> None:
    assert "prefer a short user-story block" in text
    assert "Given/When/Then acceptance bullets" in text
    assert "keep them semantically aligned" in text


def _assert_json_output_capture_guidance(text: str) -> None:
    assert "run commands in the foreground" in text
    assert "parse stdout as JSON" in text
    assert "keeping stderr separate" in text


def test_RQMD_AI_001_and_002_default_guide_is_read_only_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "guide"
    assert payload["workflow_mode"] == "general"
    assert payload["read_only"] is True
    assert payload["tooling"]["json_schema_version"] == JSON_SCHEMA_VERSION
    assert re.fullmatch(r"\d+\.\d+\.\d+|unknown", str(payload["tooling"]["rqmd_version"]))
    assert payload["bundle_installation"]["installed"] is False
    assert payload["bundle_installation"]["state"] == "absent"
    assert payload["bundle_installation"]["metadata_file"] is None
    assert payload["bundle_installation"]["installed_by_rqmd_version"] is None
    assert payload["bundle_installation"]["matches_running_rqmd_version"] is None
    assert payload["bundled_definitions"]["source"] == "packaged-resources"
    bundled_paths = {entry["path"] for entry in payload["bundled_definitions"]["files"]}
    assert ".github/prompts/brainstorm.prompt.md" in bundled_paths
    assert ".github/prompts/commit-and-go.prompt.md" in bundled_paths
    assert ".github/prompts/docs-pass.prompt.md" in bundled_paths
    assert ".github/prompts/go.prompt.md" in bundled_paths
    assert ".github/prompts/next.prompt.md" in bundled_paths
    assert ".github/prompts/pin.prompt.md" in bundled_paths
    assert ".github/prompts/ship-check.prompt.md" in bundled_paths
    assert ".github/skills/rqmd-export-context/SKILL.md" in bundled_paths
    assert ".github/skills/rqmd-pin/SKILL.md" in bundled_paths
    assert ".github/agents/rqmd-dev.agent.md" in bundled_paths
    _assert_schema_version(payload)


def test_RQMD_AI_001b_json_alias_emits_read_only_guide(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "guide"
    assert payload["workflow_mode"] == "general"
    assert payload["read_only"] is True
    _assert_schema_version(payload)


def test_RQMD_AI_001c_version_option_reports_installed_version(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(ai_cli.importlib_metadata, "version", lambda _name: "9.8.7")
    monkeypatch.setattr(ai_cli, "_editable_source_path_from_distribution", lambda: None)

    result = runner.invoke(main, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "rqmd-ai 9.8.7"


def test_RQMD_AI_001d_version_option_reports_editable_source_path(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    editable_root = tmp_path / "editable-repo"
    editable_root.mkdir()

    monkeypatch.setattr(ai_cli.importlib_metadata, "version", lambda _name: "1.2.3")
    monkeypatch.setattr(ai_cli, "_editable_source_path_from_distribution", lambda: editable_root)

    result = runner.invoke(main, ["--version"])

    assert result.exit_code == 0
    assert "rqmd-ai 1.2.3" in result.output
    assert f"editable source: {editable_root}" in result.output
    assert "package path:" in result.output


def test_RQMD_AI_001e_init_chat_prefers_starter_scaffold_for_sparse_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "init-chat"
    assert payload["workflow_mode"] == "init"
    assert payload["strategy"]["selected"] == "starter-scaffold"
    assert payload["strategy"]["reasons"] == [
        "no strong established-project signals were detected, so starter scaffold mode was selected"
    ]
    assert payload["interview"]["enabled"] is True
    assert payload["handoff_prompt"]
    assert payload["interaction_contract"]["preferred_ui"] == "multi-choice"
    assert payload["interaction_contract"]["confirmation_policy"] == "defer-recaps-until-review"
    assert payload["interview"]["interaction_contract"]["presentation"] == "one-question-at-a-time"
    assert payload["interview"]["interaction_contract"]["instructions"][0] == (
        "Present each question as an interactive multi-choice selection instead of paraphrasing the payload."
    )
    assert payload["interview"]["flow"]
    assert payload["interview"]["flow"][0]["presentation"] == "one-question-at-a-time"
    proposed_paths = [entry["path"] for entry in payload["proposed_files"]]
    assert ".rqmd.yml" in proposed_paths
    assert payload["suggested_commands"]["init_preview"].startswith("rqmd-ai init --chat --json")
    assert payload["suggested_commands"]["bundle_preview"].startswith("rqmd-ai install --bundle-preset minimal --chat --json --dry-run")
    assert payload["suggested_commands"]["init_preview_artifact"].startswith("rqmd-ai init --chat --json")
    assert "--json-output-file" in payload["suggested_commands"]["init_preview_artifact"]
    assert "--json-output-file" in payload["handoff_prompt"]
    assert "one-question-at-a-time multi-choice interview" in payload["handoff_prompt"]
    assert "avoid recapping all prior answers after each question" in payload["handoff_prompt"]
    assert "Because the rqmd Copilot bundle is currently `absent`" in payload["handoff_prompt"]
    assert "Use that bundle interview to generate or refine the project-local `/dev` and `/test` skills" in payload["handoff_prompt"]
    assert "uv run" not in payload["handoff_prompt"]
    _assert_schema_version(payload)


def test_RQMD_AI_001f_init_chat_handoff_prompt_skips_bundle_followup_when_bundle_installed(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    monkeypatch.setattr(
        ai_cli,
        "_detect_workspace_bundle_state",
        lambda _repo_root: {
            "installed": True,
            "state": "minimal",
            "preset": "minimal",
            "active_definition_files": [],
            "metadata_file": None,
            "bundle_metadata": None,
            "installed_by_rqmd_version": None,
            "matches_running_rqmd_version": None,
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["bundle_installation"]["installed"] is True
    assert "Because the rqmd Copilot bundle is currently" not in payload["handoff_prompt"]
    assert "Use that bundle interview to generate or refine the project-local `/dev` and `/test` skills" not in payload["handoff_prompt"]
    assert "9. Finish by running `rqmd --verify-summaries --no-walk --no-table`." in payload["handoff_prompt"]
    assert "10. Tell the user the rqmd catalog is ready for refinement passes." in payload["handoff_prompt"]
    _assert_schema_version(payload)


def test_RQMD_AI_001g_json_output_file_writes_artifact_without_redirect(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    output_path = repo / "tmp" / "rqmd-init-preview.json"

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json-output-file",
            str(output_path),
            "init",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "rqmd-ai init: starter-scaffold" in result.output
    assert "Preview only. Nothing has been written yet." in result.output
    assert "Paste this into your AI chat:" in result.output
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "init-chat"
    assert payload["workflow_mode"] == "init"
    assert payload["interview"]["enabled"] is True
    _assert_schema_version(payload)


def test_RQMD_AI_022c_init_legacy_non_json_output_uses_shared_preview_messages(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "ac_cli").mkdir(parents=True)
    (repo / "src" / "ac_cli" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")

    monkeypatch.setattr("rqmd.ai_cli.shutil.which", lambda name: None)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "init",
            "--legacy",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "rqmd-ai init:" in result.output
    assert "Preview only. Nothing has been written yet." in result.output
    assert "Paste this into your AI chat:" in result.output


def test_RQMD_AI_001f_init_chat_can_force_legacy_strategy(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "demo").mkdir(parents=True)
    (repo / "src" / "demo" / "app.py").write_text("print('demo')\n", encoding="utf-8")

    monkeypatch.setattr("rqmd.ai_cli.shutil.which", lambda name: None)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
            "--legacy",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["workflow_mode"] == "init"
    assert payload["strategy"]["selected"] == "legacy-init"
    assert payload["strategy"]["reasons"][0] == "explicit `--legacy` override requested"
    assert payload["compatibility"]["legacy_flag"] == "--legacy"
    assert payload["proposed_files"]
    _assert_schema_version(payload)


def test_RQMD_AI_017_default_guide_suppresses_packaged_definitions_when_bundle_installed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    install_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )
    assert install_result.exit_code == 0
    _assert_default_closeout_guidance(
        (repo / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    )
    _assert_dual_requirement_guidance(
        (repo / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    )
    _assert_json_output_capture_guidance(
        (repo / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    )

    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "guide"
    assert payload["bundle_installation"]["installed"] is True
    assert payload["bundle_installation"]["preset"] == "minimal"
    assert payload["bundle_installation"]["state"] == "minimal"
    assert ".github/skills/rqmd-export-context/SKILL.md" in payload["bundle_installation"]["active_definition_files"]
    assert "bundled_definitions" not in payload
    _assert_schema_version(payload)


def test_RQMD_AI_duplicate_ids_fail_export(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "one.md").write_text(
        """# One

Scope: demo.

### REQ-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    (criteria_dir / "two.md").write_text(
        """# Two

Scope: demo.

### REQ-001: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--id-namespace",
            "REQ",
            "--json",
            "--dump-status",
            "proposed",
        ],
    )

    assert result.exit_code != 0
    assert "Duplicate requirement IDs found" in result.output
    assert "REQ-001" in result.output


def test_RQMD_AI_015_implement_workflow_mode_emits_batch_guidance_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--workflow-mode",
            "implement",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "guide"
    assert payload["workflow_mode"] == "implement"
    assert payload["batch_policy"]["max_items"] == 3
    assert payload["batch_policy"]["selection_order"] == "highest-priority proposed first"
    assert "full test suite passes" in payload["validation_checks"]
    assert any("highest-priority 1-3 items" in step for step in payload["workflow"])
    _assert_schema_version(payload)


def test_RQMD_AI_015_workflow_mode_rejects_update_combinations(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--workflow-mode",
            "implement",
            "--update",
            "RQMD-DEMO-001=verified",
        ],
    )

    assert result.exit_code != 0
    assert "guidance surface" in result.output


def test_RQMD_AI_022_init_legacy_guide_works_without_existing_requirements_docs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--as-json",
            "--show-guide",
            "--workflow-mode",
            "init-legacy",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "guide"
    assert payload["workflow_mode"] == "init-legacy"
    assert payload["requirements_dir"] == "docs/requirements"
    _assert_schema_version(payload)


def test_RQMD_AI_023_init_legacy_plan_seeds_reviewable_requirements(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "ac_cli").mkdir(parents=True)
    (repo / "src" / "ac_cli" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts" / "local-smoke.sh").write_text("#!/bin/sh\necho smoke\n", encoding="utf-8")
    (repo / "package.json").write_text(
        json.dumps(
            {
                "name": "demo-app",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "test": "vitest run",
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr("rqmd.ai_cli.shutil.which", lambda name: None)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--as-json",
            "--workflow-mode",
            "init-legacy",
            "--id-namespace",
            "RQMD",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "legacy-init-plan"
    assert payload["read_only"] is True
    assert payload["requirements_dir"] == "docs/requirements"
    assert payload["starter_prefix"] == "RQMD"
    assert payload["status_scheme"] == "canonical"
    assert payload["issue_discovery"]["used"] is False
    assert payload["issue_discovery"]["reason"] == "gh CLI not found"
    proposed_paths = [entry["path"] for entry in payload["proposed_files"]]
    assert ".rqmd.yml" in proposed_paths
    assert "docs/requirements/README.md" in proposed_paths
    assert "docs/requirements/developer-workflows.md" in proposed_paths
    config_entry = next(entry for entry in payload["proposed_files"] if entry["path"] == ".rqmd.yml")
    assert "id_prefix: RQMD" in config_entry["content"]
    assert "name: Janky" in config_entry["content"]
    workflow_entry = next(entry for entry in payload["proposed_files"] if entry["path"] == "docs/requirements/developer-workflows.md")
    assert "This file was generated by `rqmd-ai init --chat --legacy` from detected repository commands." in workflow_entry["content"]
    assert "npm run dev" in workflow_entry["content"]
    assert "npm run build" in workflow_entry["content"]
    assert "npm run test" in workflow_entry["content"]
    assert not (repo / "docs" / "requirements").exists()
    _assert_schema_version(payload)


def test_RQMD_AI_024_init_legacy_apply_can_seed_issue_backlog_from_gh(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "ac_cli").mkdir(parents=True)
    (repo / "src" / "ac_cli" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")

    monkeypatch.setattr("rqmd.ai_cli.shutil.which", lambda name: "/usr/bin/gh")
    monkeypatch.setattr(
        "rqmd.ai_cli.subprocess.run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "number": 17,
                        "title": "Document missing automation contract",
                        "state": "OPEN",
                        "labels": [{"name": "docs"}, {"name": "automation"}],
                    }
                ]
            ),
            stderr="",
        ),
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--as-json",
            "--workflow-mode",
            "init-legacy",
            "--write",
            "--id-namespace",
            "RQMD",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "legacy-init-apply"
    assert payload["read_only"] is False
    assert payload["issue_discovery"]["used"] is True
    assert ".rqmd.yml" in payload["created_files"]
    assert "docs/requirements/issue-backlog.md" in payload["created_files"]
    config_text = (repo / ".rqmd.yml").read_text(encoding="utf-8")
    assert "id_prefix: RQMD" in config_text
    issue_backlog = (repo / "docs" / "requirements" / "issue-backlog.md").read_text(encoding="utf-8")
    assert "This file was generated from GitHub issues discovered during `rqmd-ai init --chat --legacy`." in issue_backlog
    assert "GitHub issue #17" in issue_backlog
    assert "Issue labels: docs, automation" in issue_backlog
    index_text = (repo / "docs" / "requirements" / "README.md").read_text(encoding="utf-8")
    assert "Issue Backlog Requirements" in index_text
    assert "Generated from resources/init/README.md." in index_text
    assert "## Schema Reference" in index_text
    assert "This section is intentionally included in the generated requirements index" in index_text
    _assert_schema_version(payload)


def test_RQMD_AI_023_init_legacy_write_requires_empty_target_dir(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text("# Existing\n", encoding="utf-8")

    monkeypatch.setattr("rqmd.ai_cli.shutil.which", lambda name: None)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--workflow-mode",
            "init-legacy",
            "--write",
        ],
    )

    assert result.exit_code != 0
    assert "requires an empty target requirements directory" in result.output


def test_RQMD_AI_014_brainstorm_mode_builds_ranked_proposals_from_note_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")
    (criteria_dir / "ai-cli.md").write_text(
        "# AI CLI Requirement\n\n"
        "Scope: demo.\n\n"
        "### RQMD-AI-001: Existing\n"
        "- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )
    (criteria_dir / "core-engine.md").write_text(
        "# Core Engine Requirement\n\n"
        "Scope: demo.\n\n"
        "### RQMD-CORE-001: Existing\n"
        "- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )
    brainstorm = repo / "notes.md"
    brainstorm.write_text(
        "## AI Workflow\n\n"
        "Brainstorm mode should promote notes into ranked requirement proposals.\n\n"
        "## Performance Improvements\n\n"
        "Maybe use Rust to accelerate parsing and JSON export.\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--workflow-mode",
            "brainstorm",
            "--brainstorm-file",
            str(brainstorm),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "brainstorm-plan"
    assert payload["workflow_mode"] == "brainstorm"
    assert payload["source_file"] == "notes.md"
    assert payload["total_proposals"] == 2
    assert payload["proposal_sort"]["priority_order"] == [
        "🔴 P0 - Critical",
        "🟠 P1 - High",
        "🟡 P2 - Medium",
        "🟢 P3 - Low",
    ]
    _assert_schema_version(payload)

    first = payload["proposals"][0]
    second = payload["proposals"][1]
    assert first["rank"] == 1
    assert first["proposal"]["status"] == "💡 Proposed"
    assert first["proposal"]["priority"] == "🟠 P1 - High"
    assert first["proposal"]["target_file"] == "docs/requirements/ai-cli.md"
    assert first["proposal"]["suggested_id"] == "RQMD-AI-002"
    assert second["proposal"]["target_file"] == "docs/requirements/core-engine.md"
    assert second["proposal"]["suggested_id"] == "RQMD-CORE-002"
    assert second["proposal"]["priority"] == "🟢 P3 - Low"


def test_RQMD_AI_bundle_skill_files_match_checked_in_workspace_copies() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    resource_root = repo_root / "src" / "rqmd" / "resources" / "bundle" / ".github" / "skills"
    workspace_root = repo_root / ".github" / "skills"

    resource_files = sorted(resource_root.glob("*/SKILL.md"))
    assert resource_files

    for resource_file in resource_files:
        relative = resource_file.relative_to(resource_root)
        workspace_file = workspace_root / relative
        assert workspace_file.exists(), f"Missing workspace skill copy for {relative.as_posix()}"
        assert workspace_file.read_text(encoding="utf-8") == resource_file.read_text(encoding="utf-8")


def test_RQMD_AI_bundle_prompt_files_match_checked_in_workspace_copies() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    resource_root = repo_root / "src" / "rqmd" / "resources" / "bundle" / ".github" / "prompts"
    workspace_root = repo_root / ".github" / "prompts"

    resource_files = sorted(resource_root.glob("*.prompt.md"))
    assert resource_files

    for resource_file in resource_files:
        relative = resource_file.relative_to(resource_root)
        workspace_file = workspace_root / relative
        assert workspace_file.exists(), f"Missing workspace prompt copy for {relative.as_posix()}"
        assert workspace_file.read_text(encoding="utf-8") == resource_file.read_text(encoding="utf-8")


def test_RQMD_AI_bundle_prompt_files_have_valid_frontmatter_and_guidance() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    resource_root = repo_root / "src" / "rqmd" / "resources" / "bundle" / ".github" / "prompts"

    resource_files = sorted(resource_root.glob("*.prompt.md"))
    assert resource_files

    for resource_file in resource_files:
        text = resource_file.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(text)
        assert isinstance(frontmatter.get("name"), str) and frontmatter["name"].strip()
        assert isinstance(frontmatter.get("description"), str) and frontmatter["description"].strip()
        assert isinstance(frontmatter.get("argument-hint"), str) and frontmatter["argument-hint"].strip()
        assert frontmatter.get("agent") == "rqmd-dev"
        assert "rqmd" in text.lower()
        assert text.count("- ") >= 3


def test_RQMD_AI_bundle_skill_files_expose_structured_guide_metadata() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    resource_root = repo_root / "src" / "rqmd" / "resources" / "bundle" / ".github" / "skills"

    resource_files = sorted(resource_root.glob("*/SKILL.md"))
    assert resource_files

    for resource_file in resource_files:
        frontmatter = _parse_skill_frontmatter(resource_file.read_text(encoding="utf-8"))
        metadata = frontmatter.get("metadata")
        assert isinstance(metadata, dict), f"Missing metadata block in {resource_file.name}"
        guide = metadata.get("guide")
        assert isinstance(guide, dict), f"Missing metadata.guide in {resource_file.name}"
        assert isinstance(guide.get("summary"), str) and guide["summary"].strip()
        assert isinstance(guide.get("workflow"), list) and guide["workflow"]
        assert isinstance(guide.get("examples"), list) and guide["examples"]


def test_RQMD_AI_bundle_agent_files_have_valid_frontmatter_and_guidance_sections() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    resource_root = repo_root / "src" / "rqmd" / "resources" / "bundle" / ".github" / "agents"

    resource_files = sorted(resource_root.glob("rqmd-*.agent.md"))
    assert resource_files

    for resource_file in resource_files:
        text = resource_file.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(text)
        assert isinstance(frontmatter.get("name"), str) and frontmatter["name"].strip()
        assert isinstance(frontmatter.get("description"), str) and frontmatter["description"].strip()
        assert isinstance(frontmatter.get("argument-hint"), str) and frontmatter["argument-hint"].strip()
        assert isinstance(frontmatter.get("tools"), list) and frontmatter["tools"]
        assert "Use this agent when" in text
        assert ("Execution contract:" in text) or ("Primary responsibilities:" in text)


def test_RQMD_AI_workspace_agent_files_have_valid_frontmatter_and_guidance_sections() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = repo_root / ".github" / "agents"

    workspace_files = sorted(workspace_root.glob("rqmd-*.agent.md"))
    assert workspace_files

    for workspace_file in workspace_files:
        text = workspace_file.read_text(encoding="utf-8")
        frontmatter = _parse_frontmatter(text)
        assert isinstance(frontmatter.get("name"), str) and frontmatter["name"].strip()
        assert isinstance(frontmatter.get("description"), str) and frontmatter["description"].strip()
        assert isinstance(frontmatter.get("argument-hint"), str) and frontmatter["argument-hint"].strip()
        assert isinstance(frontmatter.get("tools"), list) and frontmatter["tools"]
        assert "Use this agent when" in text
        assert ("Execution contract:" in text) or ("Primary responsibilities:" in text)


def test_RQMD_AI_014_brainstorm_skill_metadata_drives_title_limits() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    skill_path = repo_root / "src" / "rqmd" / "resources" / "bundle" / ".github" / "skills" / "rqmd-brainstorm" / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8")
    assert "max_words: 10" in skill_text
    assert "max_chars: 96" in skill_text
    assert "priority_source: runtime-catalog" in skill_text


def test_RQMD_AI_014_brainstorm_mode_uses_runtime_priority_catalog(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")
    (criteria_dir / "ai-cli.md").write_text(
        "# AI CLI Requirement\n\n"
        "Scope: demo.\n\n"
        "### RQMD-AI-001: Existing\n"
        "- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )
    (repo / ".rqmd").mkdir(parents=True)
    (repo / ".rqmd" / "priorities.yml").write_text(
        """
- name: Urgent
  shortcode: urgent
  emoji: "!!"
- name: Planned
  shortcode: planned
  emoji: "->"
- name: Later
  shortcode: later
  emoji: ".."
""".strip()
        + "\n",
        encoding="utf-8",
    )
    brainstorm = repo / "notes.md"
    brainstorm.write_text(
        "## AI Workflow\n\n"
        "Brainstorm mode should promote notes into ranked requirement proposals.\n\n"
        "## Misc\n\n"
        "Capture one softer follow-up.\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--json",
            "--workflow-mode",
            "brainstorm",
            "--brainstorm-file",
            str(brainstorm),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["proposal_sort"]["priority_order"] == [
        "!! Urgent",
        "-> Planned",
        ".. Later",
    ]
    assert payload["proposals"][0]["proposal"]["priority"] == "-> Planned"
    assert payload["proposals"][1]["proposal"]["priority"] == ".. Later"


def test_RQMD_AI_014_brainstorm_file_requires_brainstorm_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")
    brainstorm = repo / "notes.md"
    brainstorm.write_text("## Notes\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--brainstorm-file",
            str(brainstorm),
        ],
    )

    assert result.exit_code != 0
    assert "only be used with --workflow-mode brainstorm" in result.output


def test_RQMD_AI_004_export_context_filtered_by_status(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--dump-status",
            "proposed",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "export-context"
    assert payload["total"] == 1
    _assert_schema_version(payload)
    req = payload["files"][0]["requirements"][0]
    assert req["id"] == "RQMD-DEMO-001"


def test_RQMD_AI_005_plan_preview_no_apply_does_not_write(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain = criteria_dir / "demo.md"
    _write_demo_domain(domain)

    before = domain.read_text(encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--update",
            "RQMD-DEMO-001=verified",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "plan"
    assert payload["read_only"] is True
    _assert_schema_version(payload)
    assert domain.read_text(encoding="utf-8") == before


def test_RQMD_AI_006_apply_requires_set_and_applies_update(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain = criteria_dir / "demo.md"
    _write_demo_domain(domain)

    runner = CliRunner()
    missing = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--write",
        ],
    )
    assert missing.exit_code != 0
    assert "requires at least one --update" in missing.output

    applied = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--write",
            "--update",
            "RQMD-DEMO-001=verified",
        ],
    )
    assert applied.exit_code == 0
    payload = json.loads(applied.output)
    assert payload["mode"] == "apply"
    assert payload["read_only"] is False
    assert payload["changed_count"] == 1
    _assert_schema_version(payload)

    text = domain.read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text


def test_RQMD_AI_011_export_can_include_bounded_domain_body(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain = criteria_dir / "demo.md"
    _write_domain_with_body(domain)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--dump-id",
            "RQMD-DEMO-001",
            "--include-domain-markdown",
            "--max-domain-markdown-chars",
            "24",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    file_payload = payload["files"][0]
    assert "domain_body" in file_payload
    domain_body = file_payload["domain_body"]
    assert domain_body is not None
    assert domain_body["truncated"] is True
    assert domain_body["max_chars"] == 24
    assert len(domain_body["markdown"]) <= 24


def test_RQMD_AI_010_apply_emits_structured_audit_record(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain = criteria_dir / "demo.md"
    _write_demo_domain(domain)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--write",
            "--update",
            "RQMD-DEMO-001=verified",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "apply"
    assert payload["audit"] is not None
    _assert_schema_version(payload)
    assert payload["audit"]["backend"] == "rqmd-history"
    assert payload["updates"][0]["history_entry"] is not None
    assert str(payload["updates"][0]["history_entry"]["stable_id"]).startswith("hid:")

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    resolved = manager.resolve_ref(str(payload["updates"][0]["history_entry"]["entry_index"]))
    assert resolved is not None
    assert resolved["commit"] == payload["updates"][0]["history_entry"]["commit"]

    audit_log = repo / ".rqmd" / "history" / "rqmd-history" / "audit.jsonl"
    assert audit_log.exists()
    lines = [line for line in audit_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    record = json.loads(lines[-1])
    assert record["backend"] == "rqmd-history"
    assert record["mode"] == "apply"
    assert record["inputs"]["update_count"] == 1
    assert record["outputs"]["changed_count"] == 1
    assert record["outputs"]["history_entries"]
    assert record["decisions"][0]["decision"] == "applied"
    assert record["decisions"][0]["history_entry"] is not None
    assert str(record["decisions"][0]["history_entry"]["stable_id"]).startswith("hid:")


def test_RQMD_AI_012_install_bundle_dry_run_preview(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--install-agent-bundle",
            "--bundle-preset",
            "minimal",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["mode"] == "install-agent-bundle"
    assert payload["dry_run"] is True
    assert payload["preset"] == "minimal"
    assert payload["changed_count"] == 25
    assert payload["metadata_file"] == ".github/rqmd-bundle.json"
    assert payload["generated_skill_files"] == [
        ".github/skills/dev/SKILL.md",
        ".github/skills/test/SKILL.md",
    ]
    assert ".github/copilot-instructions.md" in payload["created_files"]
    assert ".github/rqmd-bundle.json" in payload["created_files"]
    assert ".github/agents/rqmd-dev.agent.md" in payload["created_files"]
    assert ".github/prompts/brainstorm.prompt.md" in payload["created_files"]
    assert ".github/prompts/commit-and-go.prompt.md" in payload["created_files"]
    assert ".github/prompts/docs-pass.prompt.md" in payload["created_files"]
    assert ".github/prompts/go.prompt.md" in payload["created_files"]
    assert ".github/prompts/next.prompt.md" in payload["created_files"]
    assert ".github/prompts/pin.prompt.md" in payload["created_files"]
    assert ".github/prompts/ship-check.prompt.md" in payload["created_files"]
    assert ".github/skills/dev/SKILL.md" in payload["created_files"]
    assert ".github/skills/test/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-brainstorm/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-triage/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-export-context/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-implement/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-init/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-init-legacy/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-status-maintenance/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-docs/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-doc-sync/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-changelog/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-pin/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-bundle/SKILL.md" in payload["created_files"]
    assert ".github/skills/rqmd-verify/SKILL.md" in payload["created_files"]
    assert not (repo / ".github" / "copilot-instructions.md").exists()


def test_RQMD_AI_012_install_bundle_idempotent_and_overwrite_controls(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()

    first = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--install-agent-bundle",
            "--bundle-preset",
            "full",
        ],
    )
    assert first.exit_code == 0
    first_payload = json.loads(first.output)
    assert first_payload["changed_count"] == 26
    assert (repo / ".github" / "copilot-instructions.md").exists()
    metadata_path = repo / ".github" / "rqmd-bundle.json"
    assert metadata_path.exists()
    metadata_payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata_payload["bundle_metadata_version"] == 1
    assert metadata_payload["bundle_preset"] == "full"
    assert metadata_payload["json_schema_version"] == JSON_SCHEMA_VERSION
    assert isinstance(metadata_payload["managed_files"], dict)
    assert ".github/copilot-instructions.md" in metadata_payload["managed_files"]
    assert re.fullmatch(r"\d+\.\d+\.\d+|unknown", str(metadata_payload["rqmd_version"]))
    _assert_default_closeout_guidance(
        (repo / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    )
    _assert_dual_requirement_guidance(
        (repo / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    )
    assert ".github/agents/rqmd-requirements.agent.md" not in first_payload["created_files"]
    assert ".github/agents/rqmd-docs.agent.md" not in first_payload["created_files"]
    assert ".github/agents/rqmd-history.agent.md" not in first_payload["created_files"]
    assert ".github/agents/rqmd-dev-longrunning.agent.md" not in first_payload["created_files"]
    assert ".github/agents/rqmd-dev-easy.agent.md" not in first_payload["created_files"]
    assert ".github/agents/README.md" in first_payload["created_files"]
    assert ".github/prompts/brainstorm.prompt.md" in first_payload["created_files"]
    assert ".github/prompts/commit-and-go.prompt.md" in first_payload["created_files"]
    assert ".github/prompts/docs-pass.prompt.md" in first_payload["created_files"]
    assert ".github/prompts/go.prompt.md" in first_payload["created_files"]
    assert ".github/prompts/next.prompt.md" in first_payload["created_files"]
    assert ".github/prompts/pin.prompt.md" in first_payload["created_files"]
    assert ".github/prompts/ship-check.prompt.md" in first_payload["created_files"]
    assert ".github/agents/rqmd-bundle-maintainer.agent.md" not in first_payload["created_files"]
    assert ".github/skills/rqmd-init/SKILL.md" in first_payload["created_files"]
    assert ".github/skills/rqmd-init-legacy/SKILL.md" in first_payload["created_files"]
    assert ".github/skills/dev/SKILL.md" in first_payload["created_files"]
    assert ".github/skills/test/SKILL.md" in first_payload["created_files"]

    second = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--install-agent-bundle",
            "--bundle-preset",
            "full",
        ],
    )
    assert second.exit_code == 0
    second_payload = json.loads(second.output)
    _assert_schema_version(second_payload)
    assert second_payload["changed_count"] == 0
    assert len(second_payload["skipped_existing"]) == 26

    custom = repo / ".github" / "copilot-instructions.md"
    custom.write_text("# custom\n", encoding="utf-8")
    overwrite = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--install-agent-bundle",
            "--overwrite-existing",
        ],
    )
    assert overwrite.exit_code == 0
    overwrite_payload = json.loads(overwrite.output)
    _assert_schema_version(overwrite_payload)
    assert ".github/copilot-instructions.md" in overwrite_payload["overwritten_files"]
    assert ".github/rqmd-bundle.json" in overwrite_payload["overwritten_files"]
    assert custom.read_text(encoding="utf-8") != "# custom\n"
    _assert_default_closeout_guidance(custom.read_text(encoding="utf-8"))
    _assert_dual_requirement_guidance(custom.read_text(encoding="utf-8"))
    _assert_json_output_capture_guidance(custom.read_text(encoding="utf-8"))


def test_RQMD_AI_012_install_bundle_without_requirements_docs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--as-json",
            "--install-agent-bundle",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["mode"] == "install-agent-bundle"
    assert payload["changed_count"] == 25


def test_RQMD_AI_012_install_bundle_positional_alias(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--as-json",
            "i",
            "--bundle-preset",
            "minimal",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["mode"] == "install-agent-bundle"
    assert payload["preset"] == "minimal"
    assert payload["changed_count"] == 25


def test_RQMD_AI_012_install_bundle_text_output_lists_created_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "rqmd-ai mode: install-agent-bundle" in result.output
    assert "operation: install" in result.output
    assert "created files:" in result.output
    assert ".github/rqmd-bundle.json" in result.output
    assert ".github/copilot-instructions.md" in result.output


def test_RQMD_AI_012_install_bundle_text_output_lists_skipped_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    first = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )
    assert first.exit_code == 0, first.output

    second = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )

    assert second.exit_code == 0, second.output
    assert "changed files: 0" in second.output
    assert "skipped existing files:" in second.output
    assert "Re-run with `--overwrite-existing` to refresh the managed bundle files." in second.output


def test_RQMD_AI_012_reinstall_command_overwrites_existing_bundle(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    initial = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
        ],
    )
    assert initial.exit_code == 0

    reinstall = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "reinstall",
        ],
    )
    assert reinstall.exit_code == 0
    payload = json.loads(reinstall.output)
    assert payload["operation"] == "reinstall"
    assert payload["preset"] == "minimal"
    assert payload["changed_count"] == 25
    assert ".github/copilot-instructions.md" in payload["overwritten_files"]


def test_RQMD_AI_012_upgrade_command_preserves_installed_preset(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    install_full = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
            "--bundle-preset",
            "full",
        ],
    )
    assert install_full.exit_code == 0

    upgrade = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "upgrade",
        ],
    )
    assert upgrade.exit_code == 0
    payload = json.loads(upgrade.output)
    assert payload["operation"] == "upgrade"
    assert payload["preset"] == "full"
    assert payload["changed_count"] == 26


def test_RQMD_AI_012_upgrade_protects_customized_bundle_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    install = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )
    assert install.exit_code == 0

    custom_file = repo / ".github" / "copilot-instructions.md"
    custom_file.write_text("# my custom instructions\n", encoding="utf-8")

    upgrade = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "upgrade",
        ],
    )
    assert upgrade.exit_code == 0
    payload = json.loads(upgrade.output)
    assert payload["operation"] == "upgrade"
    assert ".github/copilot-instructions.md" in payload["protected_existing"]
    assert ".github/copilot-instructions.md" not in payload["overwritten_files"]
    assert custom_file.read_text(encoding="utf-8") == "# my custom instructions\n"


def test_RQMD_AI_012_reinstall_removes_only_rqmd_managed_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    install = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
            "--bundle-preset",
            "full",
        ],
    )
    assert install.exit_code == 0

    unrelated_file = repo / ".github" / "my-team-notes.md"
    unrelated_file.parent.mkdir(parents=True, exist_ok=True)
    unrelated_file.write_text("keep me\n", encoding="utf-8")

    reinstall = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "reinstall",
            "--bundle-preset",
            "minimal",
        ],
    )
    assert reinstall.exit_code == 0
    payload = json.loads(reinstall.output)
    assert payload["operation"] == "reinstall"
    assert ".github/agents/README.md" in payload["removed_files"]
    assert unrelated_file.exists()


def test_RQMD_AI_012_installed_bundle_reports_bundle_metadata_and_version_match(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    install_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--json",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )
    assert install_result.exit_code == 0

    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    bundle_installation = payload["bundle_installation"]
    assert bundle_installation["metadata_file"] == ".github/rqmd-bundle.json"
    assert bundle_installation["bundle_metadata"]["bundle_preset"] == "minimal"
    assert bundle_installation["bundle_metadata"]["json_schema_version"] == JSON_SCHEMA_VERSION
    assert bundle_installation["installed_by_rqmd_version"] == payload["tooling"]["rqmd_version"]
    assert bundle_installation["matches_running_rqmd_version"] is True


def test_RQMD_AI_019_install_bundle_generates_project_dev_and_test_skills(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")
    (repo / "package.json").write_text(
        json.dumps(
            {
                "name": "demo-app",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "test": "vitest run",
                },
            }
        ),
        encoding="utf-8",
    )
    smoke_dir = repo / "scripts"
    smoke_dir.mkdir(parents=True)
    (smoke_dir / "local-smoke.sh").write_text("#!/bin/sh\necho smoke\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--as-json",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert ".github/skills/dev/SKILL.md" in payload["created_files"]
    assert ".github/skills/test/SKILL.md" in payload["created_files"]

    dev_skill = (repo / ".github" / "skills" / "dev" / "SKILL.md").read_text(encoding="utf-8")
    test_skill = (repo / ".github" / "skills" / "test" / "SKILL.md").read_text(encoding="utf-8")
    assert "npm run dev" in dev_skill
    assert "npm run build" in dev_skill
    assert "./scripts/local-smoke.sh" in dev_skill
    assert "package.json scripts" in dev_skill
    assert "npm run test" in test_skill


def test_RQMD_AI_020_install_bundle_chat_exposes_interview_and_previews(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")
    (repo / "package.json").write_text(
        json.dumps(
            {
                "name": "demo-app",
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "test": "vitest run",
                },
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
            "--bundle-preset",
            "minimal",
            "--chat",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["mode"] == "install-agent-bundle"
    assert payload["interview"]["enabled"] is True
    assert payload["interview"]["detected_sources"] == ["package.json scripts"]
    assert payload["interview"]["interaction_contract"]["next_action"] == "collect-answers-before-rerun"
    assert payload["interview"]["flow"]
    questions = payload["interview"]["questions"]
    question_groups = payload["interview"]["question_groups"]
    assert [group["id"] for group in question_groups] == [
        "developer_workflows",
        "validation_workflows",
        "review_notes",
    ]
    dev_run_question = next(item for item in questions if item["field"] == "dev_run")
    assert dev_run_question["label"] == "Run or dev-server commands"
    assert dev_run_question["prompt"] == "Which run or dev-server commands should /dev use?"
    assert dev_run_question["custom_answer_prompt"] == "Add another custom command."
    assert dev_run_question["selection_model"]["allow_multiple"] is True
    assert dev_run_question["selection_model"]["allow_custom"] is True
    assert dev_run_question["selection_model"]["allow_skip"] is True
    assert dev_run_question["selection_model"]["first_selected_is_canonical"] is True
    assert dev_run_question["option_annotations"]["detected_from"] == ["package.json scripts"]
    assert dev_run_question["option_annotations"]["default_checked_values"] == ["`npm run dev`"]
    dev_run_option = next(option for option in dev_run_question["options"] if option["value"] == "`npm run dev`")
    assert dev_run_option["recommended"] is True
    assert dev_run_option["safe_default"] is True
    assert dev_run_option["detected_from"] == ["package.json scripts"]
    notes_question = next(item for item in questions if item["field"] == "notes")
    assert notes_question["label"] == "Bootstrap notes"
    assert notes_question["prompt"] == "What review notes or caveats should be carried into the generated skills?"
    assert notes_question["custom_answer_prompt"] == "Add another command or note."
    preview_map = {entry["path"]: entry["content"] for entry in payload["generated_skill_previews"]}
    assert ".github/skills/dev/SKILL.md" in preview_map
    assert "npm run dev" in preview_map[".github/skills/dev/SKILL.md"]
    assert "npm run test" in preview_map[".github/skills/test/SKILL.md"]


def test_RQMD_AI_020_install_bundle_chat_applies_answer_overrides(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")
    (repo / "package.json").write_text(
        json.dumps({"name": "demo-app", "scripts": {"dev": "vite"}}),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
            "--bundle-preset",
            "minimal",
            "--chat",
            "--answer",
            "dev_run=python -m demo.app",
            "--answer",
            "test_primary=pytest -q",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["interview"]["applied_answers"]["dev_run"] == ["python -m demo.app"]
    assert payload["interview"]["applied_answers"]["test_primary"] == ["pytest -q"]
    preview_map = {entry["path"]: entry["content"] for entry in payload["generated_skill_previews"]}
    assert "python -m demo.app" in preview_map[".github/skills/dev/SKILL.md"]
    assert "pytest -q" in preview_map[".github/skills/test/SKILL.md"]


def test_RQMD_AI_022_init_legacy_chat_exposes_grouped_interview(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "ac_cli").mkdir(parents=True)
    (repo / "src" / "ac_cli" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (repo / "tests").mkdir(parents=True)
    (repo / "tests" / "test_demo.py").write_text("def test_demo():\n    assert True\n", encoding="utf-8")

    monkeypatch.setattr("rqmd.ai_cli.shutil.which", lambda name: None)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
            "--legacy",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["mode"] == "init-chat"
    assert payload["interview"]["enabled"] is True
    assert payload["interview"]["interaction_contract"]["preferred_ui"] == "multi-choice"
    assert payload["interview"]["flow"]
    assert [group["id"] for group in payload["interview"]["question_groups"]] == [
        "catalog_setup",
        "developer_workflows",
        "validation_workflows",
        "repository_understanding",
        "backlog_sources",
        "review_notes",
    ]
    requirements_dir_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "requirements_dir"
    )
    assert requirements_dir_question["selection_model"]["allow_multiple"] is False
    assert requirements_dir_question["selection_model"]["allow_custom"] is True
    id_prefix_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "id_prefix"
    )
    assert id_prefix_question["label"] == "Requirement ID prefix"
    assert "project-specific key" in id_prefix_question["prompt"]
    assert "project-specific" in str(id_prefix_question["custom_answer_prompt"])
    assert any(option["value"] == "REPO" and option["recommended"] is True for option in id_prefix_question["options"])
    req_option = next(option for option in id_prefix_question["options"] if option["value"] == "REQ")
    assert req_option["description"] == (
        "Generic sequential requirement prefix. Use this if you do not want a project-specific key yet."
    )
    assert req_option["safe_default"] is True
    docs_dir_option = next(option for option in requirements_dir_question["options"] if option["value"] == "docs/requirements")
    assert docs_dir_option["safe_default"] is True
    domain_focus_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "domain_focus"
    )
    assert domain_focus_question["selection_model"]["allow_multiple"] is True
    assert domain_focus_question["option_annotations"]["detected_from"]
    assert any(option["recommended"] is True for option in domain_focus_question["options"])
    assert domain_focus_question["option_annotations"]["default_checked_values"]
    docs_review_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "docs_review"
    )
    assert docs_review_question["label"] == "Docs review strategy"
    assert "first-pass catalog" in docs_review_question["prompt"]
    assert docs_review_question["custom_answer_prompt"] == "Add a custom docs-review note or rule."
    assert any(
        option["value"] == "use-current-docs"
        and option["label"] == "Use the current docs as source material"
        for option in docs_review_question["options"]
    )
    assert payload["interview"]["detected_source_areas"]


def test_RQMD_AI_022b_init_starter_chat_recommends_project_specific_prefix(tmp_path: Path) -> None:
    repo = tmp_path / "ac-cli"
    repo.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    id_prefix_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "id_prefix"
    )
    assert id_prefix_question["label"] == "Requirement ID prefix"
    assert "project-specific key" in id_prefix_question["prompt"]
    assert "project-specific" in str(id_prefix_question["custom_answer_prompt"])
    assert any(option["value"] == "ACCLI" and option["recommended"] is True for option in id_prefix_question["options"])
    req_option = next(option for option in id_prefix_question["options"] if option["value"] == "REQ")
    assert req_option["description"] == (
        "Generic sequential requirement prefix. Use this if you do not want a project-specific key yet."
    )
    assert req_option["safe_default"] is True
    requirements_dir_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "requirements_dir"
    )
    assert requirements_dir_question["label"] == "Requirements directory"
    assert requirements_dir_question["prompt"] == "Where should rqmd create the starter requirements catalog?"
    assert requirements_dir_question["custom_answer_prompt"] == "Type a custom requirements directory path."
    starter_notes_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "starter_notes"
    )
    assert starter_notes_question["label"] == "Starter scaffold notes"
    assert starter_notes_question["prompt"] == "What notes should guide the first refinement pass after the starter scaffold is created?"
    assert starter_notes_question["custom_answer_prompt"] == "Add another starter note."
    status_scheme_question = next(
        item for item in payload["interview"]["questions"] if item["field"] == "status_scheme"
    )
    assert status_scheme_question["label"] == "Status scheme"
    assert status_scheme_question["selection_model"]["allow_custom"] is True
    assert any(option["value"] == "canonical" and option["recommended"] is True for option in status_scheme_question["options"])
    assert any(option["value"] == "lean" for option in status_scheme_question["options"])
    assert any(option["value"] == "delivery" for option in status_scheme_question["options"])


def test_RQMD_AI_023_init_legacy_answers_override_plan(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    (repo / "src" / "ac_cli").mkdir(parents=True)
    (repo / "src" / "ac_cli" / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (repo / "package.json").write_text(
        json.dumps({"name": "demo-app", "scripts": {"dev": "vite"}}),
        encoding="utf-8",
    )

    monkeypatch.setattr("rqmd.ai_cli.shutil.which", lambda name: None)

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
            "--legacy",
            "--answer",
            "requirements_dir=requirements",
            "--answer",
            "id_prefix=AC",
            "--answer",
            "status_scheme=lean",
            "--answer",
            "dev_run=python -m demo.app",
            "--answer",
            "issue_backlog=skip-gh-issues",
            "--answer",
            "domain_focus=Custom Domain",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["requirements_dir"] == "requirements"
    assert payload["starter_prefix"] == "AC"
    assert payload["status_scheme"] == "lean"
    assert payload["issue_discovery"]["used"] is False
    assert payload["issue_discovery"]["reason"] == "skipped by bootstrap interview"
    workflow_entry = next(entry for entry in payload["proposed_files"] if entry["path"] == "requirements/developer-workflows.md")
    assert "This file was generated by `rqmd-ai init --chat --legacy` from detected repository commands." in workflow_entry["content"]
    assert "python -m demo.app" in workflow_entry["content"]
    assert "requirements/custom-domain.md" in [entry["path"] for entry in payload["proposed_files"]]
    domain_entry = next(entry for entry in payload["proposed_files"] if entry["path"] == "requirements/custom-domain.md")
    assert "This file was generated by `rqmd-ai init --chat --legacy` as a starting point." in domain_entry["content"]
    readme_entry = next(entry for entry in payload["proposed_files"] if entry["path"] == "requirements/README.md")
    assert "These files were seeded from the repository's current structure, workflows, and optional issue backlog." in readme_entry["content"]
    assert "Bootstrap Interview Notes" in readme_entry["content"]
    assert "Generated from resources/init/README.md." in readme_entry["content"]
    assert "## Project Tooling Metadata" in readme_entry["content"]
    assert "## Schema Reference" in readme_entry["content"]
    assert "filter-sub-domain" in readme_entry["content"]
    config_entry = next(entry for entry in payload["proposed_files"] if entry["path"] == ".rqmd.yml")
    assert "name: In Progress" in config_entry["content"]
    assert "name: Janky" not in config_entry["content"]


def test_RQMD_AI_022c_init_starter_can_copy_status_scheme_from_existing_file(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    source = tmp_path / "old-project"
    source.mkdir(parents=True)
    source_config = source / ".rqmd.yml"
    source_config.write_text(
        """statuses:
  - name: Planned
    shortcode: PLN
    emoji: "📝"
  - name: QA Verified
    shortcode: QAV
    emoji: "🧪"
priorities:
  - name: P1 - Important
    shortcode: P1
    emoji: "🔥"
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
            "--write",
            "--answer",
            f"status_scheme={source_config}",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["status_scheme"].startswith("copy:")
    config_text = (repo / ".rqmd.yml").read_text(encoding="utf-8")
    assert "name: Planned" in config_text
    assert "name: QA Verified" in config_text
    assert "name: Proposed" not in config_text


def test_RQMD_AI_017_installed_bundle_reports_generated_dev_and_test_skills(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    install_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--json",
            "install",
            "--bundle-preset",
            "minimal",
        ],
    )
    assert install_result.exit_code == 0

    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert ".github/prompts/brainstorm.prompt.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/prompts/commit-and-go.prompt.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/prompts/docs-pass.prompt.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/prompts/go.prompt.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/prompts/next.prompt.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/prompts/pin.prompt.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/prompts/ship-check.prompt.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/skills/dev/SKILL.md" in payload["bundle_installation"]["active_definition_files"]
    assert ".github/skills/test/SKILL.md" in payload["bundle_installation"]["active_definition_files"]


