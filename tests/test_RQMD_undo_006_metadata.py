from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rqmd.cli import main as rqmd_main
from rqmd.history import HistoryManager


def _write_domain(path: Path, status: str) -> None:
    path.write_text(
        f"""# Demo Requirements

### RQMD-DEMO-001: First
- **Status:** {status}
""",
        encoding="utf-8",
    )


def test_RQMD_undo_006_history_entries_include_provenance_and_delta(tmp_path: Path) -> None:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "demo.md"

    _write_domain(req_file, "💡 Proposed")
    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    manager.capture(command="baseline", actor="tester", reason="seed")

    _write_domain(req_file, "✅ Verified")
    manager.capture(command="set-status", actor="tester", reason="verification")

    entries = manager.list_entries()
    assert len(entries) == 2

    latest = entries[-1]
    assert latest["actor"] == "tester"
    assert latest["command"] == "set-status"
    assert latest["reason"] == "verification"
    assert latest["files"] == ["docs/requirements/demo.md"]

    delta = latest.get("delta")
    assert isinstance(delta, dict)
    assert delta["files_changed"] >= 1
    assert delta["additions"] >= 1
    assert isinstance(delta["files"], list)
    assert any(item["path"] == "docs/requirements/demo.md" for item in delta["files"])


def test_RQMD_undo_006_history_cli_json_includes_delta_payload(tmp_path: Path) -> None:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "demo.md"

    _write_domain(req_file, "💡 Proposed")
    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    manager.capture(command="baseline", actor="tester")

    _write_domain(req_file, "🔧 Implemented")
    manager.capture(command="implemented", actor="tester")

    runner = CliRunner()
    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-log"
    assert payload["entries_count"] == 2
    assert payload["entries"][1]["delta"] is not None
    assert payload["entries"][1]["delta"]["files_changed"] >= 1
