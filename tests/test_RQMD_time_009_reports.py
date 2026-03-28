"""Tests for RQMD-TIME-009: Exportable temporal reports."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from rqmd.ai_cli import main as ai_main
from rqmd.history import HistoryManager
DOMAIN_V1 = """\
# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 💡 Proposed
"""

DOMAIN_V2 = """\
# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ✅ Verified

### RQMD-DEMO-002: Beta
- **Status:** 💡 Proposed
"""


def _setup_two_snapshots(tmp_path: Path) -> HistoryManager:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "demo.md"

    req_file.write_text(DOMAIN_V1, encoding="utf-8")
    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    manager.capture(command="baseline", actor="test")

    req_file.write_text(DOMAIN_V2, encoding="utf-8")
    manager.capture(command="update", actor="test", reason="V2 changes")

    return manager


def test_RQMD_time_009_state_report_json(tmp_path: Path) -> None:
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--history-report",
            "--history-ref",
            "0",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-report"
    assert payload["report_type"] == "state"
    assert payload["source"]["detached"] is True
    assert payload["summary"]["total_requirements"] == 1
    assert payload["summary"]["by_status"]["💡 Proposed"] == 1


def test_RQMD_time_009_compare_report_json(tmp_path: Path) -> None:
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--history-report",
            "--compare-refs",
            "0..1",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-report"
    assert payload["report_type"] == "compare"
    assert payload["summary"]["transitions"] == 1
    assert payload["summary"]["added"] == 1


def test_RQMD_time_009_report_requires_ref_or_compare(tmp_path: Path) -> None:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    (req_dir / "demo.md").write_text(DOMAIN_V1, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--history-report",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code != 0
    assert "requires either --history-ref or --compare-refs" in result.output


def test_RQMD_time_009_state_report_text_output(tmp_path: Path) -> None:
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--history-report",
            "--history-ref",
            "1",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "History Report" in result.output
    assert "Report Type: state" in result.output
    assert "Total Requirements:" in result.output
