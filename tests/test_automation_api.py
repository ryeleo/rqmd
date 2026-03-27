from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from click.testing import CliRunner
from rqmd import cli
from rqmd.constants import JSON_SCHEMA_VERSION


def _assert_schema_version(payload: dict[str, object]) -> None:
    assert payload["schema_version"] == JSON_SCHEMA_VERSION
    assert re.fullmatch(r"\d+\.\d+\.\d+", str(payload["schema_version"]))


def test_RQMD_automation_001_check_only_mode_detects_needed_changes(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    target = repo_with_domain_docs / "docs" / "requirements" / "demo.md"
    before = target.read_text(encoding="utf-8")

    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--verify-summaries",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    assert target.read_text(encoding="utf-8") == before


def test_RQMD_automation_002_single_set_updates_criterion(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-HELLO-001",
            "--update-status",
            "done",
            "--no-table",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--id-namespace",
            "R",
            "--update-id",
            "R-HELLO-001",
            "--update-status",
            "done",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    text = (domain / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text


def test_RQMD_core_014_auto_detected_prefix_supports_set_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)

    (domain / "README.md").write_text(
        """# Requirements

## Domain Documents

- [Core](core.md)
""",
        encoding="utf-8",
    )
    (domain / "core.md").write_text(
        """# Core Requirements

Scope: core.

### TEAM-CORE-001: Team custom requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "TEAM-CORE-001",
            "--update-status",
            "Implemented",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    text = (domain / "core.md").read_text(encoding="utf-8")
    assert "- **Status:** 🔧 Implemented" in text


def test_RQMD_automation_003_repeatable_set_bulk_updates(repo_with_domain_docs: Path) -> None:
    domain = repo_with_domain_docs / "docs" / "requirements"
    (domain / "extra.md").write_text(
        """# Extra Requirement

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
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update",
            "AC-HELLO-001=implemented",
            "--update",
            "AC-HELLO-002=verified",
            "--no-table",
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
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update",
            "AC-HELLO-001=desktop-verified",
            "--no-table",
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
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--no-table",
        ],
    )
    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in text
    assert "**Blocked:** Pending" in text


@pytest.mark.parametrize("key_name", ["requirement_id", "id", "req_id", "requirement_id", "r_id"])
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
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text


def test_RQMD_automation_004b_set_file_csv_and_tsv_apply_rows(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    csv_file = tmp_path / "updates.csv"
    csv_file.write_text("requirement_id,status\nAC-HELLO-001,blocked\n", encoding="utf-8")

    tsv_file = tmp_path / "updates.tsv"
    tsv_file.write_text("requirement_id\tstatus\nAC-HELLO-001\tverified\n", encoding="utf-8")

    runner = CliRunner()

    csv_result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(csv_file),
            "--no-table",
        ],
    )
    assert csv_result.exit_code == 0
    text_after_csv = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in text_after_csv

    tsv_result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(tsv_file),
            "--no-table",
        ],
    )
    assert tsv_result.exit_code == 0
    text_after_tsv = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in text_after_tsv


def test_RQMD_priority_009_set_file_jsonl_accepts_priority_only_rows(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "priority-updates.jsonl"
    rows = [
        {"id": "AC-HELLO-001", "priority": "p0"},
    ]
    update_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Priority:** 🔴 P0 - Critical" in text


def test_RQMD_priority_009_set_file_jsonl_applies_status_and_priority_together(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "priority-and-status.jsonl"
    rows = [
        {"id": "AC-HELLO-001", "status": "implemented", "priority": "medium"},
    ]
    update_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** 🔧 Implemented" in text
    assert "- **Priority:** 🟡 P2 - Medium" in text


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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--no-table",
        ],
    )

    assert result.exit_code != 0
    assert str(update_file) in result.output
    assert ":1" in result.output


def test_RQMD_automation_006_conflicting_mode_guardrails(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "updates.jsonl"
    update_file.write_text('{"requirement_id":"AC-HELLO-001","status":"done"}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update",
            "AC-HELLO-001=done",
            "--update-file",
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
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-OVERLAP-001",
            "--update-status",
            "done",
            "--no-table",
        ],
    )
    assert ambiguous.exit_code != 0
    assert "matched multiple files" in ambiguous.output

    scoped = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-OVERLAP-001",
            "--update-status",
            "done",
            "--scope-file",
            "docs/requirements/first.md",
            "--no-table",
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
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "implemented",
            "--as-tree",
            "--no-walk",
            "--no-table",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "Implemented",
            "--as-tree",
            "--no-walk",
            "--no-table",
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

### TEAM-CORE-001: Team custom requirement
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "Implemented",
            "--as-tree",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "TEAM-CORE-001" in result.output


def test_RQMD_automation_009_no_summary_table_suppresses_table(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
            "--no-walk",
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
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--as-tree",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "second.md" in result.output
    assert "AC-OVERLAP-001" in result.output
    assert "first.md" not in result.output


def test_RQMD_automation_008d_filtered_tree_accepts_status_prefix_token(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    (domain_dir / "demo.md").write_text(
        """# Demo Requirement

Scope: demo.

### AC-ONE-001: Verified item
- **Status:** ✅ Verified

### AC-ONE-002: Proposed item
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "Ver",
            "--as-tree",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "AC-ONE-001" in result.output
    assert "AC-ONE-002" not in result.output


def test_RQMD_automation_008d_filtered_tree_status_prefix_d_matches_deprecated(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    (domain_dir / "demo.md").write_text(
        """# Demo Requirement

Scope: demo.

### AC-ONE-001: Verified item
- **Status:** ✅ Verified

### AC-ONE-002: Deprecated item
- **Status:** 🗑️ Deprecated
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "D",
            "--as-tree",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "AC-ONE-002" in result.output
    assert "AC-ONE-001" not in result.output


def test_RQMD_automation_008e_filtered_json_output_for_proposed(two_file_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "💡 Proposed"
    assert payload["requirements_dir"] == "docs/requirements"
    assert payload["total"] == 1
    assert payload["files"][0]["path"].endswith("second.md")
    assert payload["files"][0]["requirements"][0]["id"] == "AC-OVERLAP-001"
    body = payload["files"][0]["requirements"][0]["body"]
    assert "### AC-OVERLAP-001: Shared ID" in body["markdown"]
    assert isinstance(body["lines"]["header"], int)
    assert isinstance(body["lines"]["status"], int)


def test_RQMD_automation_008e_filtered_json_output_supports_no_body(two_file_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--as-json",
            "--no-requirement-body",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    requirement = payload["files"][0]["requirements"][0]
    assert requirement["id"] == "AC-OVERLAP-001"
    assert "body" not in requirement


def test_RQMD_automation_008f_json_summary_output_without_filter_status(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "summary"
    assert payload["ok"] is True
    assert payload["requirements_dir"] == "docs/requirements"
    assert payload["totals"]["🔧 Implemented"] >= 1


def test_RQMD_automation_008g_json_check_mode_reports_failure(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--verify-summaries",
            "--as-json",
            "--no-walk",
            "--no-table",
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
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-HELLO-001",
            "--update-status",
            "verified",
            "--as-json",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "set"
    assert payload["updates"][0]["requirement_id"] == "AC-HELLO-001"
    assert payload["updates"][0]["status"] == "✅ Verified"


def test_RQMD_rollup_005_text_mode_prints_global_totals(repo_with_domain_docs: Path) -> None:
    domain = repo_with_domain_docs / "docs" / "requirements"
    (domain / "extra.md").write_text(
        """# Extra Requirement

Scope: extra.

### AC-EXTRA-001: Extra requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--totals",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    assert "All files" in result.output
    assert "P" in result.output
    assert "I" in result.output
    assert "Demo Domain" not in result.output


def test_RQMD_rollup_005_json_mode_reports_global_totals(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--totals",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "rollup"
    assert payload["requirements_dir"] == "docs/requirements"
    assert payload["file_count"] >= 1
    assert payload["totals"]["🔧 Implemented"] >= 1


def test_RQMD_rollup_001_json_totals_match_live_file_counts(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--totals",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)

    files = cli.iter_domain_files(repo_with_domain_docs, "docs/requirements")
    expected = {label: 0 for label, _ in cli.STATUS_ORDER}
    for path in files:
        counts = cli.count_statuses(path.read_text(encoding="utf-8"))
        for label in expected:
            expected[label] += counts[label]

    assert payload["mode"] == "rollup"
    assert payload["totals"] == expected


def test_RQMD_rollup_007_cli_rollup_map_equations_apply_in_text_mode(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--totals",
            "--totals-map",
            "C1=I+V",
            "--totals-map",
            "C2=P",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    assert "All files" in result.output
    assert "C1" in result.output
    assert "C2" in result.output
    assert "Ver" not in result.output


def test_RQMD_rollup_007_json_mode_includes_custom_columns_from_config(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    config = tmp_path / "rollup.json"
    config.write_text(
        json.dumps(
            {
                "rollup_map": {
                    "InFlight": ["implemented", "verified"],
                    "Pending": ["proposed"],
                }
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--totals",
            "--totals-config",
            str(config),
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "rollup"
    assert payload["rollup_source"] == str(config)
    labels = [column["label"] for column in payload["rollup_columns"]]
    assert labels == ["InFlight", "Pending"]
    assert payload["rollup_columns"][0]["statuses"] == ["🔧 Implemented", "✅ Verified"]


def test_RQMD_rollup_007_cli_map_takes_precedence_over_rollup_config(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    config = tmp_path / "rollup.json"
    config.write_text(
        json.dumps({"rollup_map": {"FromConfig": ["proposed"]}}),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--totals",
            "--totals-config",
            str(config),
            "--totals-map",
            "FromCli=I+V",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["rollup_source"] == "cli"
    assert [column["label"] for column in payload["rollup_columns"]] == ["FromCli"]


def test_RQMD_automation_010_filter_status_implemented_json_entries_match_live_requirements() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    runner = CliRunner()
    id_prefixes = cli.resolve_id_prefixes(repo_root, "docs/requirements", ())

    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_root),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "Implemented",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-status"
    assert payload["status"] == "🔧 Implemented"

    flattened = [
        (file_entry["path"], requirement["id"], requirement["title"])
        for file_entry in payload["files"]
        for requirement in file_entry["requirements"]
    ]
    assert payload["total"] == len(flattened)

    seen_ids: set[tuple[str, str]] = set()
    for rel_path, requirement_id, requirement_title in flattened:
        assert (rel_path, requirement_id) not in seen_ids
        seen_ids.add((rel_path, requirement_id))

        file_path = repo_root / rel_path
        assert file_path.exists()

        parsed = cli.parse_requirements(file_path, id_prefixes=id_prefixes)
        matching = [item for item in parsed if str(item["id"]) == requirement_id]
        assert len(matching) == 1
        assert str(matching[0]["status"]) == "🔧 Implemented"
        assert str(matching[0]["title"]) == requirement_title


def test_RQMD_automation_011_filter_status_json_empty_result_has_zero_total(two_file_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "blocked",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-status"
    assert payload["status"] == "⛔ Blocked"
    assert payload["total"] == 0
    assert payload["files"] == []


def test_RQMD_automation_combined_filters_or_across_flags(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Proposed item
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium

### AC-DEMO-002: Critical item
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical

### AC-DEMO-003: Other item
- **Status:** ✅ Verified
- **Priority:** 🟢 P3 - Low
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--priority",
            "p0",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-combined"
    assert payload["filters"]["logic"] == {"across_flags": "or", "within_flag": "and"}
    ids = [entry["id"] for entry in payload["files"][0]["requirements"]]
    assert ids == ["AC-DEMO-001", "AC-DEMO-002"]


def test_RQMD_automation_combined_filters_default_to_interactive_walk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Proposed item
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium

### AC-DEMO-002: Critical item
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
""",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_loop(*_args, **kwargs):
        selected_items = kwargs["selected_items"]
        captured["ids"] = [str(requirement["id"]) for _path, requirement in selected_items]
        captured["tokens"] = list(kwargs["target_tokens"])
        return 0

    monkeypatch.setattr(cli, "focused_target_interactive_loop", fake_loop)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--priority",
            "p0",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert captured["ids"] == ["AC-DEMO-001", "AC-DEMO-002"]
    assert "status:💡 Proposed" in captured["tokens"]
    assert "priority:🔴 P0 - Critical" in captured["tokens"]


def test_RQMD_automation_combined_filters_and_within_same_flag(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Proposed item
- **Status:** 💡 Proposed

### AC-DEMO-002: Implemented item
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--status",
            "implemented",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-combined"
    assert payload["filters"]["status"] == ["💡 Proposed", "🔧 Implemented"]
    assert payload["total"] == 0
    assert payload["files"] == []


def test_RQMD_automation_013_filter_status_json_is_sorted_by_requirement_id(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-010: Later ID
- **Status:** 💡 Proposed

### AC-DEMO-002: Earlier ID
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    ids = [entry["id"] for entry in payload["files"][0]["requirements"]]
    assert ids == ["AC-DEMO-002", "AC-DEMO-010"]


def test_RQMD_automation_015_update_file_text_mode_reports_partial_failures(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "updates.jsonl"
    update_file.write_text(
        "\n".join(
            [
                '{"requirement_id":"AC-HELLO-001","status":"implemented"}',
                '{"requirement_id":"AC-MISSING-999","status":"verified"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    assert "Batch row results: 1 succeeded, 1 failed." in result.output
    assert "Row 2 (AC-MISSING-999):" in result.output
    assert "not found" in result.output

    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Status:** 🔧 Implemented" in text


def test_RQMD_automation_015_update_file_json_mode_reports_partial_failures(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "updates.jsonl"
    update_file.write_text(
        "\n".join(
            [
                '{"requirement_id":"AC-HELLO-001","status":"implemented"}',
                '{"requirement_id":"AC-MISSING-999","status":"verified"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--as-json",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["mode"] == "set"
    assert payload["ok"] is False
    assert payload["batch"] == {"total": 2, "succeeded": 1, "failed": 1}
    assert len(payload["updates"]) == 2
    assert payload["updates"][0]["ok"] is True
    assert payload["updates"][1]["ok"] is False
    assert "not found" in str(payload["updates"][1]["error"])


def test_RQMD_automation_023_and_024_filter_flagged_json(two_file_repo: Path) -> None:
    first = two_file_repo / "docs" / "requirements" / "first.md"
    first.write_text(
        first.read_text(encoding="utf-8") + "\n- **Flagged:** true\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--flagged",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-flagged"
    assert payload["flagged"] is True
    assert payload["total"] == 1
    requirement = payload["files"][0]["requirements"][0]
    assert requirement["id"] == "AC-OVERLAP-001"
    assert requirement["flagged"] is True


def test_RQMD_automation_024_filter_flagged_json_empty(two_file_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--flagged",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-flagged"
    assert payload["flagged"] is True
    assert payload["total"] == 0
    assert payload["files"] == []


def test_RQMD_automation_034_filter_no_flag_json_includes_unset(two_file_repo: Path) -> None:
    first = two_file_repo / "docs" / "requirements" / "first.md"
    first.write_text(
        first.read_text(encoding="utf-8") + "\n- **Flagged:** true\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--no-flag",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-flagged"
    assert payload["flagged"] is False
    assert payload["total"] == 1
    assert payload["files"][0]["path"].endswith("second.md")
    requirement = payload["files"][0]["requirements"][0]
    assert requirement["id"] == "AC-OVERLAP-001"
    assert requirement.get("flagged") is not True


def test_RQMD_automation_034_no_flag_and_flagged_are_mutually_exclusive(two_file_repo: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(two_file_repo),
            "--docs-dir",
            "docs/requirements",
            "--flagged",
            "--no-flag",
            "--no-table",
        ],
    )

    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_RQMD_automation_034_combined_filter_with_no_flag(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Proposed and unflagged (unset)
- **Status:** 💡 Proposed

### AC-DEMO-002: Implemented and flagged
- **Status:** 🔧 Implemented
- **Flagged:** true

### AC-DEMO-003: Proposed and explicitly unflagged
- **Status:** 💡 Proposed
- **Flagged:** false
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "implemented",
            "--no-flag",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-combined"
    assert payload["filters"]["flagged"] is False
    # OR-across-flags: implemented item OR unflagged items
    ids = [entry["id"] for entry in payload["files"][0]["requirements"]]
    assert ids == ["AC-DEMO-001", "AC-DEMO-002", "AC-DEMO-003"]


def test_RQMD_automation_032_filter_has_link_json(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Linked item
- **Status:** 💡 Proposed
- **Links:**
  - https://example.com/ticket/1

### AC-DEMO-002: Unlinked item
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--has-link",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-links"
    assert payload["links"] == {"has_link": True, "no_link": False}
    assert payload["total"] == 1
    requirement = payload["files"][0]["requirements"][0]
    assert requirement["id"] == "AC-DEMO-001"
    assert requirement["links"][0]["url"] == "https://example.com/ticket/1"


def test_RQMD_automation_032_filter_no_link_json_includes_missing_links(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Linked item
- **Status:** 💡 Proposed
- **Links:**
  - [Ticket](https://example.com/ticket/1)

### AC-DEMO-002: Unlinked item
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-link",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-links"
    assert payload["links"] == {"has_link": False, "no_link": True}
    assert payload["total"] == 1
    requirement = payload["files"][0]["requirements"][0]
    assert requirement["id"] == "AC-DEMO-002"
    assert "links" not in requirement


def test_RQMD_automation_032_has_link_and_no_link_are_mutually_exclusive(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Item
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--has-link",
            "--no-link",
            "--no-table",
        ],
    )

    assert result.exit_code != 0
    assert "mutually exclusive" in result.output.lower()


def test_RQMD_automation_032_combined_filter_with_has_link(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Linked proposed
- **Status:** 💡 Proposed
- **Links:**
  - https://example.com/1

### AC-DEMO-002: Linked implemented
- **Status:** 🔧 Implemented
- **Links:**
  - https://example.com/2

### AC-DEMO-003: Unlinked verified
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "verified",
            "--has-link",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-combined"
    assert payload["filters"]["links"] is True
    ids = [entry["id"] for entry in payload["files"][0]["requirements"]]
    assert ids == ["AC-DEMO-001", "AC-DEMO-002", "AC-DEMO-003"]


def test_RQMD_automation_029_filter_sub_domain_json_includes_metadata(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

## Query API
Read-only routes.

### AC-DEMO-001: Get record
- **Status:** ✅ Verified

### AC-DEMO-002: Search records
- **Status:** 💡 Proposed

## Mutation API

### AC-DEMO-003: Create record
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--sub-domain",
            "que",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-sub-domain"
    assert payload["sub_domain"] == "que"
    assert payload["sub_domain_match_count"] == 2
    assert payload["total"] == 2
    assert [item["id"] for item in payload["files"][0]["requirements"]] == ["AC-DEMO-001", "AC-DEMO-002"]
    assert all(item["sub_domain"] == "Query API" for item in payload["files"][0]["requirements"])
    assert payload["files"][0]["sub_sections"] == [
        {"name": "Query API", "count": 2, "body": "Read-only routes."},
        {"name": "Mutation API", "count": 1},
    ]


def test_RQMD_automation_029b_filter_sub_domain_json_empty_result_has_zero_total(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

## Query API

### AC-DEMO-001: Get record
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--sub-domain",
            "mutation",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-sub-domain"
    assert payload["sub_domain"] == "mutation"
    assert payload["sub_domain_match_count"] == 0
    assert payload["total"] == 0
    assert payload["files"] == []


def test_RQMD_automation_030_json_includes_sub_domain_null_and_sub_sections(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Root requirement
- **Status:** 💡 Proposed

## Query API

### AC-DEMO-002: Query requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-status"
    assert payload["total"] == 2
    assert payload["files"][0]["sub_sections"] == [{"name": "Query API", "count": 1}]

    requirements = payload["files"][0]["requirements"]
    by_id = {entry["id"]: entry for entry in requirements}
    assert "sub_domain" in by_id["AC-DEMO-001"]
    assert by_id["AC-DEMO-001"]["sub_domain"] is None
    assert by_id["AC-DEMO-002"]["sub_domain"] == "Query API"


@pytest.mark.parametrize(
    "args",
    [
        ["--as-json", "--no-walk", "--no-table"],
        ["--status", "proposed", "--as-json", "--no-walk", "--no-table"],
        ["--totals", "--as-json", "--no-walk", "--no-table"],
        [
            "--update-id",
            "AC-HELLO-001",
            "--update-status",
            "implemented",
            "--as-json",
            "--no-table",
        ],
    ],
)
def test_RQMD_automation_033_json_payloads_include_schema_version(
    repo_with_domain_docs: Path,
    args: list[str],
) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            *args,
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    _assert_schema_version(payload)


def test_RQMD_automation_033_init_json_payload_includes_schema_version(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--bootstrap",
            "--force-yes",
            "--as-json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "init"
    _assert_schema_version(payload)


def test_RQMD_automation_033_init_priorities_json_payload_includes_schema_version(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--seed-priorities",
            "--seed-priority",
            "p1",
            "--as-json",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "init-priorities"
    _assert_schema_version(payload)


def test_RQMD_automation_029c_filter_sub_domain_list_output(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

## Query API

### AC-DEMO-001: Get item
- **Status:** ✅ Verified

### AC-DEMO-002: Search item
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--sub-domain",
            "query",
            "--as-list",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "docs/requirements/demo.md::AC-DEMO-001: Get item" in result.output
    assert "docs/requirements/demo.md::AC-DEMO-002: Search item" in result.output


def test_RQMD_automation_027c_explicit_targets_list_output(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** ✅ Verified

### AC-DEMO-002: Second
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "AC-DEMO-002",
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-list",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "docs/requirements/demo.md::AC-DEMO-002: Second" in result.output
    assert "AC-DEMO-001" not in result.output


def test_RQMD_automation_027_filter_ids_file_json_expands_domain_and_subsection_tokens(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

## Query API

### AC-DEMO-001: Get item
- **Status:** ✅ Verified

### AC-DEMO-002: Search item
- **Status:** 💡 Proposed

## Mutation API

### AC-DEMO-003: Create item
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    (domain / "other.md").write_text(
        """# Other Requirements

Scope: other.

### AC-OTHER-001: Other item
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    target_file = tmp_path / "focus.txt"
    target_file.write_text(
        "demo  # whole domain\nQuery  AC-OTHER-001\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--targets-file",
            str(target_file),
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-targets"
    assert payload["targets"] == ["demo", "Query", "AC-OTHER-001"]
    assert payload["total"] == 4
    assert [file_entry["path"] for file_entry in payload["files"]] == [
        "docs/requirements/demo.md",
        "docs/requirements/other.md",
    ]
    demo_ids = [item["id"] for item in payload["files"][0]["requirements"]]
    assert demo_ids == ["AC-DEMO-001", "AC-DEMO-002", "AC-DEMO-003"]
    assert payload["files"][1]["requirements"][0]["id"] == "AC-OTHER-001"


def test_RQMD_automation_027b_positional_target_tree_rejects_invalid_token(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "no-such-target",
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--as-tree",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code != 0
    assert "Unrecognized target tokens" in result.output


def test_RQMD_automation_025_set_flagged_and_json_mode(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-flagged",
            "AC-HELLO-001=true",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "set-flagged"
    assert payload["updates"][0]["requirement_id"] == "AC-HELLO-001"
    assert payload["updates"][0]["flagged"] is True

    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Flagged:** true" in text


def test_RQMD_automation_025_set_file_accepts_flagged_rows(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    update_file = tmp_path / "flagged-updates.jsonl"
    update_file.write_text('{"id":"AC-HELLO-001","flagged":"false"}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    text = (repo_with_domain_docs / "docs" / "requirements" / "demo.md").read_text(encoding="utf-8")
    assert "- **Flagged:** false" in text


def test_RQMD_automation_022_filter_priority_json_returns_ambiguity_payload(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--priority",
            "P",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["mode"] == "filter-priority"
    assert payload["ok"] is False
    assert payload["error"]["type"] == "ambiguous-input"
    assert payload["error"]["field"] == "priority"
    assert payload["error"]["input"] == "P"
    assert "🔴 P0 - Critical" in payload["error"]["candidates"]
    assert "🟢 P3 - Low" in payload["error"]["candidates"]


def test_RQMD_automation_017_json_no_interactive_never_prompts(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    def fail_confirm(*_args, **_kwargs):
        raise AssertionError("click.confirm should not be called in JSON/non-interactive mode")

    monkeypatch.setattr(cli.click, "confirm", fail_confirm)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    assert "Requirement docs directory not found" in result.output


def test_RQMD_automation_014_set_dry_run_does_not_write(repo_with_domain_docs: Path) -> None:
    target = repo_with_domain_docs / "docs" / "requirements" / "demo.md"
    before = target.read_text(encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-HELLO-001",
            "--update-status",
            "verified",
            "--dry-run",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    assert "Would update AC-HELLO-001" in result.output
    assert target.read_text(encoding="utf-8") == before


def test_RQMD_automation_014_set_file_dry_run_does_not_write(repo_with_domain_docs: Path, tmp_path: Path) -> None:
    target = repo_with_domain_docs / "docs" / "requirements" / "demo.md"
    before = target.read_text(encoding="utf-8")

    update_file = tmp_path / "updates.jsonl"
    update_file.write_text('{"id":"AC-HELLO-001","status":"blocked"}\n', encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-file",
            str(update_file),
            "--dry-run",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    assert "Would update AC-HELLO-001" in result.output
    assert target.read_text(encoding="utf-8") == before


def test_RQMD_automation_014_set_flagged_dry_run_json_reports_without_write(repo_with_domain_docs: Path) -> None:
    target = repo_with_domain_docs / "docs" / "requirements" / "demo.md"
    before = target.read_text(encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--update-flagged",
            "AC-HELLO-001=true",
            "--dry-run",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "set-flagged"
    assert payload["dry_run"] is True
    assert payload["updates"][0]["flagged"] is True
    assert target.read_text(encoding="utf-8") == before


def test_RQMD_automation_021_ambiguous_status_prefix_error_includes_recommendation() -> None:
    """Test that a status ambiguity error message contains candidate list and 'Use one of:' suffix.

    Uses configure_status_catalog to inject two statuses sharing a 'b' prefix, forcing ambiguity.
    """
    from rqmd.status_model import coerce_status_label, configure_status_catalog

    configure_status_catalog([
        {"name": "Bright", "shortcode": "bright", "emoji": "💡"},
        {"name": "Blocked", "shortcode": "blocked", "emoji": "⛔"},
    ])
    try:
        try:
            coerce_status_label("b")
            raise AssertionError("Expected ValueError for ambiguous 'b'")
        except ValueError as exc:
            err = str(exc)
            assert "Ambiguous" in err, f"Expected 'Ambiguous' in: {err}"
            assert "Use one of:" in err, f"Expected 'Use one of:' in: {err}"
    finally:
        configure_status_catalog(None)


def test_RQMD_automation_021_ambiguous_priority_prefix_error_includes_recommendation(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--priority",
            "P",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code != 0
    assert "Ambiguous" in result.output
    assert "Use one of:" in result.output


def test_RQMD_automation_026_filter_json_domain_entry_includes_scope(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "implemented",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["files"], "Expected at least one domain file in payload"
    domain = payload["files"][0]
    assert "scope" in domain, "Domain entry must include 'scope' field"
    assert domain["scope"] == "demo requirements"


def test_RQMD_automation_026_filter_json_domain_entry_includes_domain_body(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    (domain_dir / "demo.md").write_text(
        """# Demo Domain Requirement

Scope: example scope.

This is a freeform domain body paragraph.

### AC-DEMO-001: A requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "proposed",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    domain = payload["files"][0]
    assert "domain_body" in domain, "Domain entry must include 'domain_body' field"
    assert "freeform domain body" in (domain["domain_body"] or "")


def test_RQMD_automation_026_domain_body_is_none_when_no_preamble(repo_with_domain_docs: Path) -> None:
    """When there is no freeform content before the first requirement, domain_body is None."""
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--status",
            "implemented",
            "--as-json",
            "--no-table",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    domain = payload["files"][0]
    # The sample fixture has no body content between Scope and first requirement.
    assert domain["domain_body"] is None


def test_RQMD_automation_026_summary_json_domain_entry_includes_scope(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "summary"
    domain = payload["files"][0]
    assert "scope" in domain, "Summary domain entry must include 'scope' field"
    assert domain["scope"] == "demo requirements"
    assert "domain_body" in domain, "Summary domain entry must include 'domain_body' field"


def test_RQMD_automation_009b_summary_table_uses_five_status_headers(repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    assert "P" in result.output
    assert "I" in result.output
    assert "Ver" in result.output
    assert "Blk" in result.output
    assert "Dep" in result.output
    assert "WaitVR" not in result.output


def test_RQMD_sorting_initial_summary_table_matches_default_app_order(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "a.md").write_text(
        """# Alpha Domain Requirement

Scope: alpha.

### AC-ALPHA-001: Alpha requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    (domain / "b.md").write_text(
        """# Bravo Domain Requirement

Scope: bravo.

### AC-BRAVO-001: Bravo requirement
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    assert result.output.find("Bravo Domain") < result.output.find("Alpha Domain")


def test_RQMD_sorting_initial_summary_table_honors_status_focus_strategy(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "z.md").write_text(
        """# Zulu Domain Requirement

Scope: zulu.

### AC-ZULU-001: Zulu requirement
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    (domain / "a.md").write_text(
        """# Alpha Domain Requirement

Scope: alpha.

### AC-ALPHA-001: Alpha requirement
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--sort-profile",
            "status-focus",
            "--no-walk",
        ],
    )

    assert result.exit_code == 0
    assert result.output.find("Alpha Domain") < result.output.find("Zulu Domain")


def test_RQMD_automation_027_deduplication_collapses_repeated_tokens(tmp_path: Path) -> None:
    """When the same requirement ID appears multiple times via different tokens, it appears once in output."""
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Item one
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    # Pass AC-DEMO-001 twice and also domain stem 'demo' (which expands to AC-DEMO-001).
    target_file = tmp_path / "focus.txt"
    target_file.write_text("AC-DEMO-001\ndemo\nAC-DEMO-001\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--targets-file",
            str(target_file),
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    ids = [r["id"] for r in payload["files"][0]["requirements"]]
    assert ids.count("AC-DEMO-001") == 1, "Duplicate requirement must be deduplicated"
    assert payload["total"] == 1


def test_RQMD_automation_028_targets_file_comment_only_lines_are_ignored(tmp_path: Path) -> None:
    """Full-line comments starting with # are skipped; only real tokens are parsed."""
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Item one
- **Status:** ✅ Verified

### AC-DEMO-002: Item two
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    target_file = tmp_path / "focus.txt"
    target_file.write_text(
        "# This is a comment — should be ignored\nAC-DEMO-001  # inline comment\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--targets-file",
            str(target_file),
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    ids = [r["id"] for r in payload["files"][0]["requirements"]]
    assert ids == ["AC-DEMO-001"]
    assert "AC-DEMO-002" not in ids


def test_RQMD_automation_028_targets_file_comma_separated_tokens(tmp_path: Path) -> None:
    """Comma-separated tokens on a single line are each parsed as separate tokens."""
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Item one
- **Status:** ✅ Verified

### AC-DEMO-002: Item two
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    target_file = tmp_path / "focus.txt"
    target_file.write_text("AC-DEMO-001, AC-DEMO-002\n", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--targets-file",
            str(target_file),
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["total"] == 2
    ids = [r["id"] for r in payload["files"][0]["requirements"]]
    assert "AC-DEMO-001" in ids
    assert "AC-DEMO-002" in ids


# ─── RQMD-AUTOMATION-019: Unique-prefix argument/value abbreviations ────────────


_UNIQUE_STATUS_PREFIX_CASES = [
    ("P", "💡 Proposed"),
    ("Pro", "💡 Proposed"),
    ("I", "🔧 Implemented"),
    ("Impl", "🔧 Implemented"),
    ("V", "✅ Verified"),
    ("Ver", "✅ Verified"),
    ("B", "⛔ Blocked"),
    ("Bl", "⛔ Blocked"),
    ("D", "🗑️ Deprecated"),
    ("Dep", "🗑️ Deprecated"),
]


@pytest.mark.parametrize("prefix,expected_canonical", _UNIQUE_STATUS_PREFIX_CASES)
def test_RQMD_automation_019_update_status_prefix_resolves_to_canonical(
    prefix: str, expected_canonical: str, tmp_path: Path
) -> None:
    """Unique status value prefix in --update-status resolves to the canonical label."""
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Target
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "AC-DEMO-001",
            "--update-status",
            prefix,
            "--as-json",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["updates"][0]["requirement_id"] == "AC-DEMO-001"
    assert payload["updates"][0]["status"] == expected_canonical


@pytest.mark.parametrize("prefix,expected_canonical", _UNIQUE_STATUS_PREFIX_CASES)
def test_RQMD_automation_019_status_filter_prefix_resolves_to_canonical(
    prefix: str, expected_canonical: str, tmp_path: Path
) -> None:
    """Unique status value prefix in --status filter resolves to the canonical label."""
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        f"""# Demo Requirements

Scope: demo.

### AC-DEMO-001: Target
- **Status:** {expected_canonical}
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--status",
            prefix,
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == expected_canonical
    assert payload["total"] == 1
    assert payload["files"][0]["requirements"][0]["id"] == "AC-DEMO-001"


# ─── RQMD-AUTOMATION-019/020: Option-name prefix abbreviation ────────────────


# ─── RQMD-AUTOMATION-020: Ambiguous option-prefix error contract ─────────────


def test_RQMD_automation_020_ambiguous_option_prefix_fails_with_candidate_list(tmp_path: Path) -> None:
    """Ambiguous prefix `--as` (matches --as-json, --as-list, --as-tree) exits non-zero
    and includes candidate option names in the error output."""
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Target
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--as",  # ambiguous: --as-json, --as-list, --as-tree all share this prefix
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code != 0
    # Click lists candidate options in the error output when abbreviation is ambiguous.
    candidates_mentioned = sum(
        1 for opt in ("--as-json", "--as-list", "--as-tree") if opt in result.output
    )
    assert candidates_mentioned >= 2

