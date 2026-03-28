"""Tests for RQMD-TIME-005: Compare historical points and branches."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rqmd.ai_cli import main as ai_main
from rqmd.history import HistoryManager


DOMAIN_V1 = """\
# Demo Requirements

### DEMO-001: Alpha
- **Status:** 💡 Proposed

### DEMO-002: Beta
- **Status:** 🔧 Implemented
"""

DOMAIN_V2 = """\
# Demo Requirements

### DEMO-001: Alpha
- **Status:** ✅ Verified

### DEMO-002: Beta
- **Status:** 🔧 Implemented

### DEMO-003: Gamma
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


def test_RQMD_time_005_compare_json_shape(tmp_path: Path) -> None:
    """compare_refs payload contains expected top-level keys."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..1", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "compare"
    assert "ref_a" in payload
    assert "ref_b" in payload
    assert "summary" in payload
    assert "transitions" in payload
    assert "added" in payload
    assert "removed" in payload


def test_RQMD_time_005_compare_detects_transition(tmp_path: Path) -> None:
    """DEMO-001 Proposed→Verified is captured as a transition."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..1", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)

    transitions = payload["transitions"]
    assert len(transitions) == 1
    t = transitions[0]
    assert t["id"] == "DEMO-001"
    assert "Proposed" in str(t["before_status"])
    assert "Verified" in str(t["after_status"])


def test_RQMD_time_005_compare_detects_added(tmp_path: Path) -> None:
    """DEMO-003 added in V2 appears in the 'added' list."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..1", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)

    added_ids = [r["id"] for r in payload["added"]]
    assert "DEMO-003" in added_ids


def test_RQMD_time_005_compare_unchanged_not_in_transitions(tmp_path: Path) -> None:
    """DEMO-002 is unchanged between V1 and V2; it should not appear in transitions."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..1", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)

    all_changed_ids = (
        [t["id"] for t in payload["transitions"]]
        + [r["id"] for r in payload["added"]]
        + [r["id"] for r in payload["removed"]]
    )
    assert "DEMO-002" not in all_changed_ids
    assert payload["summary"]["unchanged"] == 1


def test_RQMD_time_005_compare_summary_totals(tmp_path: Path) -> None:
    """Summary totals add up correctly."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..1", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    s = payload["summary"]
    assert s["total_a"] == 2   # V1: DEMO-001, DEMO-002
    assert s["total_b"] == 3   # V2: DEMO-001, DEMO-002, DEMO-003
    assert s["transitions"] == 1
    assert s["added"] == 1
    assert s["removed"] == 0
    assert s["unchanged"] == 1


def test_RQMD_time_005_compare_space_separated_refs(tmp_path: Path) -> None:
    """'0 1' format (space-separated) is accepted as well as dotdot."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0 1", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "compare"


def test_RQMD_time_005_compare_unknown_ref_error(tmp_path: Path) -> None:
    """An unknown ref produces a clear ClickException."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..99", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code != 0
    assert "Unknown" in result.output or "Unknown" in (result.output or "")


def test_RQMD_time_005_compare_invalid_format_error(tmp_path: Path) -> None:
    """A malformed --compare-refs value produces a clear error."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "just_one_ref", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code != 0


def test_RQMD_time_005_compare_head_keyword(tmp_path: Path) -> None:
    """'0..head' compares earliest snapshot to current cursor position."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..head", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "compare"
    # ref_b should be entry_index 1 (the HEAD after two captures)
    assert payload["ref_b"]["entry_index"] == 1


def test_RQMD_time_005_compare_latest_keyword(tmp_path: Path) -> None:
    """'0..latest' resolves to the last entry."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..latest", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ref_b"]["entry_index"] == 1


def test_RQMD_time_005_compare_stable_ids_as_refs(tmp_path: Path) -> None:
    """Stable history ids (hid:<commit>) are accepted by --compare-refs."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()

    baseline = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--compare-refs",
            "0..1",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--id-namespace",
            "DEMO",
        ],
    )
    assert baseline.exit_code == 0
    baseline_payload = json.loads(baseline.output)
    ref_a = baseline_payload["ref_a"]["stable_id"]
    ref_b = baseline_payload["ref_b"]["stable_id"]

    stable = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--compare-refs",
            f"{ref_a}..{ref_b}",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--id-namespace",
            "DEMO",
        ],
    )
    assert stable.exit_code == 0
    stable_payload = json.loads(stable.output)
    assert stable_payload["ref_a"]["stable_id"] == ref_a
    assert stable_payload["ref_b"]["stable_id"] == ref_b


def test_RQMD_time_005_ref_a_details_present(tmp_path: Path) -> None:
    """ref_a and ref_b both contain commit, entry_index, timestamp metadata."""
    _setup_two_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        ["--as-json", "--compare-refs", "0..1", "--project-root", str(tmp_path), "--docs-dir", "docs/requirements", "--id-namespace", "DEMO"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    for key in ("entry_index", "commit", "stable_id", "timestamp", "command"):
        assert key in payload["ref_a"], f"Missing key {key} in ref_a"
        assert key in payload["ref_b"], f"Missing key {key} in ref_b"
    assert str(payload["ref_a"]["stable_id"]).startswith("hid:")
    assert str(payload["ref_b"]["stable_id"]).startswith("hid:")
    assert payload["ref_a"]["entry_index"] == 0
    assert payload["ref_b"]["entry_index"] == 1
