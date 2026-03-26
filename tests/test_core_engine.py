from __future__ import annotations

from pathlib import Path

from ac_cli import cli


def test_ac_acccli_core_001_iter_domain_files_sorted_and_markdown_only(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "acceptance-criteria"
    domain_dir.mkdir(parents=True)
    (domain_dir / "z.md").write_text("# Z\n", encoding="utf-8")
    (domain_dir / "a.md").write_text("# A\n", encoding="utf-8")
    (domain_dir / "note.txt").write_text("ignore", encoding="utf-8")

    files = cli.iter_domain_files(repo, "docs/acceptance-criteria")
    assert [p.name for p in files] == ["a.md", "z.md"]


def test_ac_acccli_core_002_and_007_parse_and_find_criterion() -> None:
    text = """# Demo Acceptance Criteria

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented

### AC-DEMO-002: Second
- **Status:** 💡 Proposed
"""
    # Use a temp file under pytest temp path semantics via mkdtemp-like Path creation.
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path = Path(td) / "demo.md"
        path.write_text(text, encoding="utf-8")
        criteria = cli.parse_criteria(path)
        assert [c["id"] for c in criteria] == ["AC-DEMO-001", "AC-DEMO-002"]
        assert cli.find_criterion_by_id(path, "ac-demo-002")["title"] == "Second"


def test_ac_acccli_core_003_normalize_status_aliases() -> None:
    original = """### AC-DEMO-001: First
- **Status:** ✅ Verified
"""
    normalized, changed = cli.normalize_status_lines(original)
    assert changed is True
    assert "- **Status:** ✅ Done" in normalized


def test_ac_acccli_core_004_and_005_insert_or_replace_summary_block() -> None:
    text = """# Demo Acceptance Criteria

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented
"""
    counts = {label: 0 for label, _ in cli.STATUS_ORDER}
    counts["🔧 Implemented"] = 1

    inserted = cli.insert_or_replace_summary(text, cli.build_summary_block(counts))
    assert cli.SUMMARY_START in inserted
    assert "Summary: 0💡 1🔧" in inserted

    replaced = cli.insert_or_replace_summary(inserted.replace("Summary:", "Summary: stale "), cli.build_summary_block(counts))
    assert replaced.count(cli.SUMMARY_START) == 1
    assert "Summary: 0💡 1🔧" in replaced


def test_ac_acccli_core_006_count_statuses_model() -> None:
    text = "\n".join(
        [
            "- **Status:** 💡 Proposed",
            "- **Status:** 🔧 Implemented",
            "- **Status:** 💻 Desktop-Verified",
            "- **Status:** 🎮 VR-Verified",
            "- **Status:** ✅ Done",
            "- **Status:** ⛔ Blocked",
            "- **Status:** 🗑️ Deprecated",
        ]
    )
    counts = cli.count_statuses(text)
    assert counts["💡 Proposed"] == 1
    assert counts["🔧 Implemented"] == 1
    assert counts["💻 Desktop-Verified"] == 1
    assert counts["🎮 VR-Verified"] == 1
    assert counts["✅ Done"] == 1
    assert counts["⛔ Blocked"] == 1
    assert counts["🗑️ Deprecated"] == 1


def test_ac_acccli_core_008_process_file_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "demo.md"
    path.write_text(
        """# Demo Acceptance Criteria

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    changed_first, _ = cli.process_file(path, check_only=False)
    changed_second, _ = cli.process_file(path, check_only=False)
    assert changed_first is True
    assert changed_second is False


def test_ac_acccli_core_010_update_status_handles_blocked_and_deprecated_reasons(tmp_path: Path) -> None:
    path = tmp_path / "demo.md"
    path.write_text(
        """# Demo Acceptance Criteria

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    criterion = cli.find_criterion_by_id(path, "AC-DEMO-001")

    changed = cli.update_criterion_status(path, criterion, "⛔ Blocked", blocked_reason="Need API")
    assert changed is True
    blocked_text = path.read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in blocked_text
    assert "**Blocked:** Need API" in blocked_text

    criterion = cli.find_criterion_by_id(path, "AC-DEMO-001")
    changed = cli.update_criterion_status(path, criterion, "🗑️ Deprecated", deprecated_reason="Replaced")
    assert changed is True
    deprecated_text = path.read_text(encoding="utf-8")
    assert "- **Status:** 🗑️ Deprecated" in deprecated_text
    assert "**Blocked:**" not in deprecated_text
    assert "**Deprecated:** Replaced" in deprecated_text
