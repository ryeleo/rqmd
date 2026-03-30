from __future__ import annotations

import json
import re
from pathlib import Path

from click.testing import CliRunner

from rqmd.ai_cli import main
from rqmd.cli import main as rqmd_main
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
    _assert_schema_version(payload)


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
    assert payload["changed_count"] == 2
    assert ".github/copilot-instructions.md" in payload["created_files"]
    assert ".github/agents/core.agent.md" in payload["created_files"]
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
    assert first_payload["changed_count"] == 4
    assert (repo / ".github" / "copilot-instructions.md").exists()

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
    assert len(second_payload["skipped_existing"]) == 4

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
    assert "custom" not in custom.read_text(encoding="utf-8")


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
    assert payload["changed_count"] == 2


def test_RQMD_TIME_001_export_context_from_history_entry(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain = criteria_dir / "demo.md"
    _write_demo_domain(domain)

    runner = CliRunner()
    applied = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "RQMD-DEMO-001",
            "--update-status",
            "verified",
            "--no-walk",
            "--no-table",
        ],
    )
    assert applied.exit_code == 0

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
            "--history-ref",
            "0",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)
    assert payload["mode"] == "export-context"
    assert payload["history_source"]["detached"] is True
    assert payload["history_source"]["entry_index"] == 0
    assert str(payload["history_source"]["stable_id"]).startswith("hid:")
    assert payload["total"] == 1
    assert payload["files"][0]["requirements"][0]["status"] == "💡 Proposed"
    assert "✅ Verified" in domain.read_text(encoding="utf-8")


def test_RQMD_TIME_008_history_ref_accepts_stable_id(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain = criteria_dir / "demo.md"
    _write_demo_domain(domain)

    runner = CliRunner()
    applied = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "RQMD-DEMO-001",
            "--update-status",
            "verified",
            "--no-walk",
            "--no-table",
        ],
    )
    assert applied.exit_code == 0

    first_payload_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--dump-status",
            "proposed",
            "--history-ref",
            "0",
        ],
    )
    assert first_payload_result.exit_code == 0
    first_payload = json.loads(first_payload_result.output)
    stable_id = str(first_payload["history_source"]["stable_id"])

    stable_ref_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--dump-status",
            "proposed",
            "--history-ref",
            stable_id,
        ],
    )
    assert stable_ref_result.exit_code == 0
    stable_payload = json.loads(stable_ref_result.output)
    assert stable_payload["history_source"]["entry_index"] == 0
    assert stable_payload["history_source"]["stable_id"] == stable_id


def test_RQMD_TIME_001_rejects_unknown_history_ref(tmp_path: Path) -> None:
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
            "--history-ref",
            "999",
        ],
    )

    assert result.exit_code != 0
    assert "Unknown --history-ref target" in result.output


def test_RQMD_TIME_003_history_ref_rejects_write_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    bootstrap = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "RQMD-DEMO-001",
            "--update-status",
            "verified",
            "--no-walk",
            "--no-table",
        ],
    )
    assert bootstrap.exit_code == 0

    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--history-ref",
            "0",
            "--write",
            "--update",
            "RQMD-DEMO-001=implemented",
        ],
    )

    assert result.exit_code != 0
    assert "--history-ref cannot be combined with --write" in result.output


def test_RQMD_TIME_003_history_ref_rejects_update_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    bootstrap = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "RQMD-DEMO-001",
            "--update-status",
            "verified",
            "--no-walk",
            "--no-table",
        ],
    )
    assert bootstrap.exit_code == 0

    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--history-ref",
            "0",
            "--update",
            "RQMD-DEMO-001=implemented",
        ],
    )

    assert result.exit_code != 0
    assert "--history-ref cannot be combined with --update; historical exports are read-only." in result.output


def test_RQMD_TIME_004_history_activity_shows_before_after_and_neighbors(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain = criteria_dir / "demo.md"
    _write_demo_domain(domain)

    runner = CliRunner()
    applied = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "RQMD-DEMO-001",
            "--update-status",
            "verified",
            "--no-walk",
            "--no-table",
        ],
    )
    assert applied.exit_code == 0

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
            "--history-ref",
            "1",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)

    activity = payload["history_activity"]
    assert activity is not None
    assert activity["entry"]["entry_index"] == 1
    assert activity["neighbors"]["previous"]["entry_index"] == 0
    assert activity["neighbors"]["next"]["entry_index"] is None

    changed = activity["changed_requirements"]
    assert len(changed) == 1
    assert changed[0]["id"] == "RQMD-DEMO-001"
    assert changed[0]["before"]["status"] == "💡 Proposed"
    assert changed[0]["after"]["status"] == "✅ Verified"
