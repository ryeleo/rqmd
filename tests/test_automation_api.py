from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from ac_cli import cli


def test_ac_acccli_automation_001_check_only_mode_detects_needed_changes(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    target = repo_with_domain_docs / "docs" / "acceptance-criteria" / "demo.md"
    before = target.read_text(encoding="utf-8")

    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--check",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 1
    assert target.read_text(encoding="utf-8") == before


def test_ac_acccli_automation_002_single_set_updates_criterion(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--set-criterion-id",
            "AC-HELLO-001",
            "--set-status",
            "done",
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "acceptance-criteria" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Done" in text


def test_ac_acccli_automation_003_repeatable_set_bulk_updates(repo_with_domain_docs: Path) -> None:
    domain = repo_with_domain_docs / "docs" / "acceptance-criteria"
    (domain / "extra.md").write_text(
        """# Extra Acceptance Criteria

Scope: extra.

### AC-HELLO-002: Another
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--set",
            "AC-HELLO-001=implemented",
            "--set",
            "AC-HELLO-002=desktop-verified",
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    assert "🔧 Implemented" in (domain / "demo.md").read_text(encoding="utf-8")
    assert "💻 Desktop-Verified" in (domain / "extra.md").read_text(encoding="utf-8")


def test_ac_acccli_automation_004_and_005_set_file_jsonl_with_alias_keys(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "updates.jsonl"
    rows = [
        {"id": "AC-HELLO-001", "status": "blocked", "blocked_reason": "Pending"},
    ]
    update_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--set-file",
            str(update_file),
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "acceptance-criteria" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in text
    assert "**Blocked:** Pending" in text


def test_ac_acccli_automation_006_conflicting_mode_guardrails(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "updates.jsonl"
    update_file.write_text('{"criterion_id":"AC-HELLO-001","status":"done"}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--set",
            "AC-HELLO-001=done",
            "--set-file",
            str(update_file),
        ],
    )
    assert result.exit_code != 0
    assert "exactly one non-interactive update mode" in result.output


def test_ac_acccli_automation_007_file_scope_disambiguation(two_file_repo: Path) -> None:
    runner = CliRunner()

    ambiguous = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(two_file_repo),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--set-criterion-id",
            "AC-OVERLAP-001",
            "--set-status",
            "done",
            "--no-summary-table",
        ],
    )
    assert ambiguous.exit_code != 0
    assert "matched multiple files" in ambiguous.output

    scoped = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(two_file_repo),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--set-criterion-id",
            "AC-OVERLAP-001",
            "--set-status",
            "done",
            "--file",
            "docs/acceptance-criteria/first.md",
            "--no-summary-table",
        ],
    )
    assert scoped.exit_code == 0
    first_text = (two_file_repo / "docs" / "acceptance-criteria" / "first.md").read_text(encoding="utf-8")
    second_text = (two_file_repo / "docs" / "acceptance-criteria" / "second.md").read_text(encoding="utf-8")
    assert "✅ Done" in first_text
    assert "✅ Done" not in second_text


def test_ac_acccli_automation_008_filtered_tree_output(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--filter-status",
            "implemented",
            "--tree",
            "--no-interactive",
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    assert "AC-HELLO-001" in result.output


def test_ac_acccli_automation_009_no_summary_table_suppresses_table(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/acceptance-criteria",
            "--no-summary-table",
            "--no-interactive",
        ],
    )
    assert result.exit_code == 0
    assert "WaitVR" not in result.output
    assert "File" not in result.output
