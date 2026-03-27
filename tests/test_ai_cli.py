from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rqmd.ai_cli import main


def _write_demo_domain(path: Path) -> None:
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
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "guide"
    assert payload["read_only"] is True


def test_RQMD_AI_004_export_context_filtered_by_status(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    _write_demo_domain(criteria_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--json",
            "--export-status",
            "proposed",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "export-context"
    assert payload["total"] == 1
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
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--json",
            "--set",
            "RQMD-DEMO-001=verified",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "plan"
    assert payload["read_only"] is True
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
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--apply",
        ],
    )
    assert missing.exit_code != 0
    assert "requires at least one --set" in missing.output

    applied = runner.invoke(
        main,
        [
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--json",
            "--apply",
            "--set",
            "RQMD-DEMO-001=verified",
        ],
    )
    assert applied.exit_code == 0
    payload = json.loads(applied.output)
    assert payload["mode"] == "apply"
    assert payload["read_only"] is False
    assert payload["changed_count"] == 1

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
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--json",
            "--export-id",
            "RQMD-DEMO-001",
            "--include-domain-body",
            "--max-domain-body-chars",
            "24",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
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
            "--repo-root",
            str(repo),
            "--requirements-dir",
            "docs/requirements",
            "--json",
            "--apply",
            "--set",
            "RQMD-DEMO-001=verified",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "apply"
    assert payload["audit"] is not None
    assert payload["audit"]["backend"] == "rqmd-history"

    audit_log = repo / ".rqmd" / "history" / "rqmd-history" / "audit.jsonl"
    assert audit_log.exists()
    lines = [line for line in audit_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines
    record = json.loads(lines[-1])
    assert record["backend"] == "rqmd-history"
    assert record["mode"] == "apply"
    assert record["inputs"]["update_count"] == 1
    assert record["outputs"]["changed_count"] == 1
    assert record["decisions"][0]["decision"] == "applied"
