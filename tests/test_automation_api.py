from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from rqmd import cli


def test_RQMD_automation_001_check_only_mode_detects_needed_changes(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    target = repo_with_domain_docs / "docs" / "requirements" / "demo.md"
    before = target.read_text(encoding="utf-8")

    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--check",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 1
    assert target.read_text(encoding="utf-8") == before


def test_RQMD_automation_002_single_set_updates_criterion(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--set-criterion-id",
            "AC-HELLO-001",
            "--set-status",
            "done",
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text


def test_RQMD_automation_002b_single_set_updates_r_prefixed_requirement(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### R-HELLO-001: Hello requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--id-prefix",
            "R",
            "--set-criterion-id",
            "R-HELLO-001",
            "--set-status",
            "done",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    text = (domain / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text


def test_RQMD_automation_003_repeatable_set_bulk_updates(repo_with_domain_docs: Path) -> None:
    domain = repo_with_domain_docs / "docs" / "requirements"
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
            "docs/requirements",
            "--set",
            "AC-HELLO-001=implemented",
            "--set",
            "AC-HELLO-002=verified",
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    assert "🔧 Implemented" in (domain / "demo.md").read_text(encoding="utf-8")
    assert "✅ Verified" in (domain / "extra.md").read_text(encoding="utf-8")


def test_RQMD_automation_003b_repeatable_set_rejects_removed_legacy_status(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--set",
            "AC-HELLO-001=desktop-verified",
            "--no-summary-table",
        ],
    )

    assert result.exit_code != 0
    assert "Unrecognized status input" in result.output


def test_RQMD_automation_004_and_005_set_file_jsonl_with_alias_keys(repo_with_domain_docs: Path, tmp_path: Path) -> None:
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
            "docs/requirements",
            "--set-file",
            str(update_file),
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in text
    assert "**Blocked:** Pending" in text


@pytest.mark.parametrize("key_name", ["criterion_id", "id", "ac_id", "requirement_id", "r_id"])
def test_RQMD_automation_005b_set_file_accepts_all_id_alias_keys(
    repo_with_domain_docs: Path,
    tmp_path: Path,
    key_name: str,
) -> None:
    update_file = tmp_path / "updates.jsonl"
    row = {key_name: "AC-HELLO-001", "status": "verified"}
    update_file.write_text(json.dumps(row) + "\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--set-file",
            str(update_file),
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text


def test_RQMD_automation_004b_set_file_csv_and_tsv_apply_rows(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    csv_file = tmp_path / "updates.csv"
    csv_file.write_text("criterion_id,status\nAC-HELLO-001,blocked\n", encoding="utf-8")

    tsv_file = tmp_path / "updates.tsv"
    tsv_file.write_text("criterion_id\tstatus\nAC-HELLO-001\tverified\n", encoding="utf-8")

    runner = CliRunner()

    csv_result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--set-file",
            str(csv_file),
            "--no-summary-table",
        ],
    )
    assert csv_result.exit_code == 0
    text_after_csv = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in text_after_csv

    tsv_result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--set-file",
            str(tsv_file),
            "--no-summary-table",
        ],
    )
    assert tsv_result.exit_code == 0
    text_after_tsv = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text_after_tsv


def test_RQMD_automation_004c_set_file_jsonl_invalid_row_reports_path_and_line(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-HELLO-001: Hello requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    update_file = tmp_path / "bad.jsonl"
    update_file.write_text('{"status":"blocked"}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--set-file",
            str(update_file),
            "--no-summary-table",
        ],
    )

    assert result.exit_code != 0
    assert str(update_file) in result.output
    assert ":1" in result.output


def test_RQMD_automation_006_conflicting_mode_guardrails(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "updates.jsonl"
    update_file.write_text('{"criterion_id":"AC-HELLO-001","status":"done"}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--set",
            "AC-HELLO-001=done",
            "--set-file",
            str(update_file),
        ],
    )
    assert result.exit_code != 0
    assert "exactly one non-interactive update mode" in result.output


def test_RQMD_automation_007_file_scope_disambiguation(two_file_repo: Path) -> None:
    runner = CliRunner()

    ambiguous = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(two_file_repo),
            "--criteria-dir",
            "docs/requirements",
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
            "docs/requirements",
            "--set-criterion-id",
            "AC-OVERLAP-001",
            "--set-status",
            "done",
            "--file",
            "docs/requirements/first.md",
            "--no-summary-table",
        ],
    )
    assert scoped.exit_code == 0
    first_text = (two_file_repo / "docs" / "requirements" / "first.md").read_text(encoding="utf-8")
    second_text = (two_file_repo / "docs" / "requirements" / "second.md").read_text(encoding="utf-8")
    assert "✅ Verified" in first_text
    assert "✅ Verified" not in second_text


def test_RQMD_automation_008_filtered_tree_output(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--filter-status",
            "implemented",
            "--tree",
            "--no-interactive",
            "--no-summary-table",
        ],
    )
    assert result.exit_code == 0
    assert "AC-HELLO-001" in result.output


def test_RQMD_automation_008b_filtered_tree_output_supports_rqmd_prefix_by_default(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "core.md").write_text(
        """# Core Requirements

Scope: core.

### RQMD-CORE-001: Core behavior
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--filter-status",
            "Implemented",
            "--tree",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "RQMD-CORE-001" in result.output


def test_RQMD_automation_008c_filtered_tree_auto_detects_prefix_from_requirements_index(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)

    (repo / "docs" / "requirements" / "README.md").write_text(
        """# Requirements

## Domain Documents

- [Custom](custom.md)
""",
        encoding="utf-8",
    )
    (domain / "custom.md").write_text(
        """# Custom Requirements

Scope: custom.

### TEAM-CORE-001: Team custom criterion
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--filter-status",
            "Implemented",
            "--tree",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "TEAM-CORE-001" in result.output


def test_RQMD_automation_009_no_summary_table_suppresses_table(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
            "--no-interactive",
        ],
    )
    assert result.exit_code == 0
    assert "WaitVR" not in result.output
    assert "File" not in result.output


def test_RQMD_automation_008d_filtered_tree_accepts_plain_proposed_label(two_file_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(two_file_repo),
            "--criteria-dir",
            "docs/requirements",
            "--filter-status",
            "proposed",
            "--tree",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "second.md" in result.output
    assert "AC-OVERLAP-001" in result.output
    assert "first.md" not in result.output


def test_RQMD_automation_008e_filtered_json_output_for_proposed(two_file_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(two_file_repo),
            "--criteria-dir",
            "docs/requirements",
            "--filter-status",
            "proposed",
            "--json",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "💡 Proposed"
    assert payload["criteria_dir"] == "docs/requirements"
    assert payload["total"] == 1
    assert payload["files"][0]["path"].endswith("second.md")
    assert payload["files"][0]["criteria"][0]["id"] == "AC-OVERLAP-001"


def test_RQMD_automation_008f_json_summary_output_without_filter_status(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--json",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "summary"
    assert payload["ok"] is True
    assert payload["criteria_dir"] == "docs/requirements"
    assert payload["totals"]["🔧 Implemented"] >= 1


def test_RQMD_automation_008g_json_check_mode_reports_failure(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--check",
            "--json",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["mode"] == "check"
    assert payload["ok"] is False
    assert len(payload["changed_files"]) >= 1


def test_RQMD_automation_008h_json_set_mode_reports_updates(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--set-criterion-id",
            "AC-HELLO-001",
            "--set-status",
            "verified",
            "--json",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "set"
    assert payload["updates"][0]["criterion_id"] == "AC-HELLO-001"
    assert payload["updates"][0]["status"] == "✅ Verified"


def test_RQMD_automation_009b_summary_table_uses_five_status_headers(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--no-interactive",
        ],
    )

    assert result.exit_code == 0
    assert "P" in result.output
    assert "I" in result.output
    assert "Ver" in result.output
    assert "Blk" in result.output
    assert "Dep" in result.output
    assert "WaitVR" not in result.output
