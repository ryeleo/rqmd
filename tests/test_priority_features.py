"""Tests for priority-focused CLI and interactive behavior."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner
from rqmd import cli
from rqmd.req_parser import parse_requirements
from rqmd.summary import (
    build_summary_block,
    collect_summary_rows,
    count_priorities,
    process_file,
)


@pytest.fixture
def sample_file_with_priorities(tmp_path: Path) -> Path:
    """Create a sample requirements file with multiple priorities."""
    content = """\
# Requirements

### AC-001: Basic requirement
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical

Some description.

### AC-002: Medium priority
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium

More text.

### AC-003: Low priority
- **Status:** ✅ Verified
- **Priority:** 🟢 P3 - Low

Final requirement.
"""
    path = tmp_path / "test.md"
    path.write_text(content)
    return path


class TestRQMDPriority005SummaryIntegration:
    def test_count_priorities_extracts_all_levels(self, sample_file_with_priorities: Path):
        content = sample_file_with_priorities.read_text()
        counts = count_priorities(content)

        assert counts.get("🔴 P0 - Critical", 0) == 1
        assert counts.get("🟡 P2 - Medium", 0) == 1
        assert counts.get("🟢 P3 - Low", 0) == 1
        assert counts.get("🟠 P1 - High", 0) == 0

    def test_build_summary_block_without_priorities(self, sample_file_with_priorities: Path):
        counts = {"💡 Proposed": 1, "🔧 Implemented": 1, "✅ Verified": 1, "⛔ Blocked": 0, "🗑️ Deprecated": 0}

        summary = build_summary_block(counts, priority_counts=None)

        assert "Summary:" in summary
        assert "Priorities:" not in summary
        assert "<!-- acceptance-status-summary:start -->" in summary

    def test_build_summary_block_with_priorities(self, sample_file_with_priorities: Path):
        counts = {"💡 Proposed": 1, "🔧 Implemented": 1, "✅ Verified": 1, "⛔ Blocked": 0, "🗑️ Deprecated": 0}
        priority_counts = {"🔴 P0 - Critical": 1, "🟠 P1 - High": 0, "🟡 P2 - Medium": 1, "🟢 P3 - Low": 1}

        summary = build_summary_block(counts, priority_counts=priority_counts)

        assert "Summary:" in summary
        assert "Priorities:" in summary
        assert "1🔴" in summary
        assert "1🟡" in summary
        assert "1🟢" in summary

    def test_process_file_writes_priority_summary_when_flag_set(self, sample_file_with_priorities: Path):
        changed, _counts = process_file(
            sample_file_with_priorities,
            check_only=False,
            include_priority_summary=True,
        )

        content = sample_file_with_priorities.read_text()
        assert changed is True
        assert "Priorities: 1🔴 0🟠 1🟡 1🟢" in content

    def test_collect_summary_rows_writes_priority_summaries(self, sample_file_with_priorities: Path, tmp_path: Path):
        file2_content = """\
# Test 2

### AC-501: Another requirement
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical
"""
        file2_path = tmp_path / "test2.md"
        file2_path.write_text(file2_content)

        changed_paths, rows = collect_summary_rows(
            [sample_file_with_priorities, file2_path],
            check_only=False,
            display_name_fn=lambda p: p.name,
            include_priority_summary=True,
        )

        assert len(changed_paths) == 2
        assert len(rows) == 2
        assert "Priorities:" in file2_path.read_text(encoding="utf-8")


class TestRQMDPriority004ModeFlag:
    def test_cli_help_lists_priority_flags(self):
        runner = CliRunner()
        result = runner.invoke(cli.main, ["--help"])

        assert result.exit_code == 0
        assert "--update-priority" in result.output
        assert "--focus-priority" in result.output
        assert "--priority-rollup" in result.output
        assert "--seed-priorities" in result.output

    def test_cli_set_priority_updates_existing_and_missing_priority(self, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Existing priority
- **Status:** 💡 Proposed
- **Priority:** 🟢 P3 - Low

### AC-002: Missing priority
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
                "--update-priority",
                "AC-001=p0",
                "--update-priority",
                "AC-002=medium",
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        text = (criteria_dir / "demo.md").read_text(encoding="utf-8")
        assert "- **Priority:** 🔴 P0 - Critical" in text
        assert "- **Priority:** 🟡 P2 - Medium" in text

    def test_cli_set_priority_json_output_reports_changes(self, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Existing priority
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
                "--update-priority",
                "AC-001=high",
                "--as-json",
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mode"] == "set-priority"
        assert payload["changed_files"] == ["docs/requirements/demo.md"]
        assert payload["updates"][0]["priority"] == "high"
        assert payload["updates"][0]["changed"] is True

    def test_priority_field_extraction_in_criteria(self, sample_file_with_priorities: Path):
        requirements = parse_requirements(sample_file_with_priorities, id_prefixes=("AC",))

        assert len(requirements) == 3
        assert requirements[0]["id"] == "AC-001"
        assert "🔴 P0 - Critical" in requirements[0].get("priority", "")
        assert requirements[1]["id"] == "AC-002"
        assert "🟡 P2 - Medium" in requirements[1].get("priority", "")

    def test_lookup_priority_mode_starts_on_priority_panel(self, sample_file_with_priorities: Path, monkeypatch):
        titles: list[str] = []

        def fake_select(title, options, **kwargs):
            titles.append(title)
            return None

        monkeypatch.setattr(cli, "select_from_menu", fake_select)

        result = cli.lookup_criterion_interactive(
            repo_root=sample_file_with_priorities.parent,
            domain_files=[sample_file_with_priorities],
            requirement_id="AC-001",
            emoji_columns=False,
            id_prefixes=("AC",),
            priority_mode=True,
        )

        assert result == 0
        assert titles
        assert titles[0].startswith("Set priority for AC-001")

    def test_main_forwards_priority_mode_to_interactive_wrapper(self, monkeypatch, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Demo
- **Status:** 💡 Proposed
""",
            encoding="utf-8",
        )

        captured: dict[str, object] = {}

        def fake_loop(repo_root, criteria_dir, domain_files, emoji_columns, sort_files, sort_strategy, id_prefixes, include_status_emojis, priority_mode, include_priority_summary, **kwargs):
            captured["priority_mode"] = priority_mode
            captured["include_priority_summary"] = include_priority_summary
            return 0

        monkeypatch.setattr(cli, "interactive_update_loop", fake_loop)

        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--project-root",
                str(repo),
                "--docs-dir",
                "docs/requirements",
                "--focus-priority",
                "--priority-rollup",
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        assert captured["priority_mode"] is True
        assert captured["include_priority_summary"] is True

    def test_filter_priority_json_output(self, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Hot path
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical

### AC-002: Nice to have
- **Status:** 💡 Proposed
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
                "--priority",
                "critical",
                "--as-json",
                "--no-walk",
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mode"] == "filter-priority"
        assert payload["priority"] == "🔴 P0 - Critical"

    def test_filter_priority_json_output_accepts_prefix_token(self, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Hot path
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical

### AC-002: Medium item
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
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
                "--priority",
                "M",
                "--as-json",
                "--no-walk",
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mode"] == "filter-priority"
        assert payload["priority"] == "🟡 P2 - Medium"
        assert payload["total"] == 1

    def test_filter_priority_rejects_ambiguous_prefix(self, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Hot path
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical

### AC-002: Medium item
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
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
                "--priority",
                "P",
                "--as-json",
                "--no-walk",
                "--no-table",
            ],
        )

        assert result.exit_code != 0
        assert "Ambiguous priority input" in result.output
        assert "🔴 P0 - Critical" in result.output
        assert "🟡 P2 - Medium" in result.output

    def test_init_priorities_dry_run_does_not_modify_file(self, tmp_path: Path):
        repo = tmp_path / "repo"
        domain = repo / "docs" / "requirements"
        domain.mkdir(parents=True)

        target = domain / "demo.md"
        target.write_text(
            """# Demo Requirement

Scope: demo.

### AC-001: Missing priority
- **Status:** 🔧 Implemented
""",
            encoding="utf-8",
        )
        before = target.read_text(encoding="utf-8")

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
                "p2",
                "--dry-run",
                "--as-json",
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["mode"] == "init-priorities"
        assert payload["dry_run"] is True
        assert payload["changed_count"] == 1
        assert target.read_text(encoding="utf-8") == before

    def test_init_priorities_adds_default_and_is_idempotent(self, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        target = criteria_dir / "demo.md"
        target.write_text(
            """# Demo Requirements

### AC-001: Missing priority
- **Status:** 💡 Proposed

### AC-002: Existing priority
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
""",
            encoding="utf-8",
        )

        runner = CliRunner()
        first = runner.invoke(
            cli.main,
            [
                "--project-root",
                str(repo),
                "--docs-dir",
                "docs/requirements",
                "--seed-priorities",
                "--seed-priority",
                "medium",
                "--no-table",
            ],
        )
        assert first.exit_code == 0

        updated = target.read_text(encoding="utf-8")
        assert "### AC-001: Missing priority" in updated
        assert "- **Priority:** 🟡 P2 - Medium" in updated
        assert "- **Priority:** 🟠 P1 - High" in updated

        second = runner.invoke(
            cli.main,
            [
                "--project-root",
                str(repo),
                "--docs-dir",
                "docs/requirements",
                "--seed-priorities",
                "--seed-priority",
                "medium",
                "--as-json",
                "--no-table",
            ],
        )
        assert second.exit_code == 0
        payload = json.loads(second.output)
        assert payload["mode"] == "init-priorities"
        assert payload["changed_count"] == 0

    def test_init_priorities_rejects_incompatible_modes(self, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Missing priority
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
                "--verify-summaries",
                "--no-table",
            ],
        )

        assert result.exit_code != 0
        assert "--seed-priorities cannot be combined" in result.output

    def test_requirement_menu_cycles_to_priority_sort(self, monkeypatch, tmp_path: Path):
        repo = tmp_path / "repo"
        criteria_dir = repo / "docs" / "requirements"
        criteria_dir.mkdir(parents=True)
        (criteria_dir / "demo.md").write_text(
            """# Demo Requirements

### AC-001: Low priority
- **Status:** 💡 Proposed
- **Priority:** 🟢 P3 - Low

### AC-002: Critical priority
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical
""",
            encoding="utf-8",
        )

        state = {"requirement_calls": 0, "file_calls": 0}
        captured: dict[str, object] = {}

        def fake_select(title, options, **kwargs):
            if title.startswith("Select file"):
                state["file_calls"] += 1
                return 0 if state["file_calls"] == 1 else None
            if title.startswith("Select requirement in"):
                state["requirement_calls"] += 1
                if state["requirement_calls"] == 1:
                    return "cycle-sort"
                captured["title"] = title
                captured["options"] = list(options)
                return "up"
            return None

        monkeypatch.setattr(cli, "select_from_menu", fake_select)

        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--project-root",
                str(repo),
                "--docs-dir",
                "docs/requirements",
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        assert "\x1b[1mpriority ↓\x1b[0m" in str(captured["title"])
        assert "Critical priority" in captured["options"][0]
        assert "Low priority" in captured["options"][1]


class TestPriorityParsingConsistency:
    def test_missing_priority_field_parsed_as_none(self, tmp_path: Path):
        content = """\
# Requirements

### AC-001: No priority
- **Status:** 💡 Proposed

Description.
"""
        path = tmp_path / "test.md"
        path.write_text(content)

        requirements = parse_requirements(path, id_prefixes=("AC",))
        assert len(requirements) == 1
        assert requirements[0]["priority"] is None

    def test_priority_line_number_tracking(self, tmp_path: Path):
        content = """\
# Requirements

### AC-001: Test
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical

Text.
"""
        path = tmp_path / "test.md"
        path.write_text(content)

        requirements = parse_requirements(path, id_prefixes=("AC",))
        assert requirements[0]["priority_line"] is not None
        assert isinstance(requirements[0]["priority_line"], int)
        assert requirements[0]["priority_line"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
