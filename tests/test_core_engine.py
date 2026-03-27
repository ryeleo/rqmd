from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rqmd import cli


def test_RQMD_core_001_iter_domain_files_sorted_and_markdown_only(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    (domain_dir / "z.md").write_text("# Z\n", encoding="utf-8")
    (domain_dir / "a.md").write_text("# A\n", encoding="utf-8")
    (domain_dir / "note.txt").write_text("ignore", encoding="utf-8")

    files = cli.iter_domain_files(repo, "docs/requirements")
    assert [p.name for p in files] == ["a.md", "z.md"]


def test_RQMD_core_002_and_007_parse_and_find_criterion() -> None:
    text = """# Demo Requirement

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
        requirements = cli.parse_requirements(path)
        assert [c["id"] for c in requirements] == ["AC-DEMO-001", "AC-DEMO-002"]
        assert cli.find_requirement_by_id(path, "ac-demo-002")["title"] == "Second"


def test_RQMD_core_002b_parse_requirement_ids_with_configured_prefix() -> None:
    text = """# Demo Requirements

Scope: demo.

### R-DEMO-001: First
- **Status:** 🔧 Implemented
"""

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path = Path(td) / "demo.md"
        path.write_text(text, encoding="utf-8")
        requirements = cli.parse_requirements(path, id_prefixes=("R",))
        assert [c["id"] for c in requirements] == ["R-DEMO-001"]
        assert cli.find_requirement_by_id(path, "r-demo-001", id_prefixes=("R",))["title"] == "First"


def test_RQMD_core_020_parse_h2_subsections_into_sub_domain_metadata() -> None:
    text = """# Demo Requirements

Scope: demo.

### AC-DEMO-000: No subsection
- **Status:** 💡 Proposed

##   Query   API   
Notes about query behavior.

### AC-DEMO-001: Read model
- **Status:** ✅ Verified

## Mutation API

### AC-DEMO-002: Write model
- **Status:** 🔧 Implemented
"""

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path = Path(td) / "demo.md"
        path.write_text(text, encoding="utf-8")
        requirements = cli.parse_requirements(path)

    assert requirements[0]["sub_domain"] is None
    assert requirements[1]["sub_domain"] == "Query API"
    assert requirements[2]["sub_domain"] == "Mutation API"


def test_RQMD_core_003_normalize_status_aliases() -> None:
    original = """### AC-DEMO-001: First
- **Status:** ✅ Done
"""
    normalized, changed = cli.normalize_status_lines(original)
    assert changed is True
    assert "- **Status:** ✅ Verified" in normalized


def test_RQMD_core_004_and_005_insert_or_replace_summary_block() -> None:
    text = """# Demo Requirement

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


def test_RQMD_core_006_count_statuses_model() -> None:
    text = "\n".join(
        [
            "- **Status:** 💡 Proposed",
            "- **Status:** 🔧 Implemented",
            "- **Status:** ✅ Verified",
            "- **Status:** ⛔ Blocked",
            "- **Status:** 🗑️ Deprecated",
        ]
    )
    counts = cli.count_statuses(text)
    assert counts["💡 Proposed"] == 1
    assert counts["🔧 Implemented"] == 1
    assert counts["✅ Verified"] == 1
    assert counts["⛔ Blocked"] == 1
    assert counts["🗑️ Deprecated"] == 1


def test_RQMD_core_006b_build_summary_block_uses_five_status_order() -> None:
    counts = {label: 0 for label, _ in cli.STATUS_ORDER}
    counts["💡 Proposed"] = 2
    counts["🔧 Implemented"] = 3
    counts["✅ Verified"] = 4
    counts["⛔ Blocked"] = 1
    counts["🗑️ Deprecated"] = 5

    summary = cli.build_summary_block(counts)
    assert "Summary: 2💡 3🔧 4✅ 1⛔ 5🗑️" in summary


def test_RQMD_core_008_process_file_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "demo.md"
    path.write_text(
        """# Demo Requirement

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


def test_RQMD_core_009_missing_domain_docs_handling(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs" / "requirements").mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--verify-summaries",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    assert "No requirement markdown files found under" in result.output
    assert "rqmd --bootstrap --force-yes" in result.output


def test_RQMD_core_009_missing_domain_docs_yes_initializes_scaffold(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs" / "requirements").mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--force-yes",
        ],
    )

    assert result.exit_code == 0
    assert (repo / "docs" / "requirements" / "README.md").exists()
    starter = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")
    assert "### REQ-HELLO-001: Replace this starter requirement" in starter


def test_RQMD_core_009_init_yes_skips_prompt_and_uses_default_prefix(tmp_path: Path) -> None:
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
        ],
    )

    assert result.exit_code == 0
    starter = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")
    assert "### REQ-HELLO-001: Replace this starter requirement" in starter


def test_RQMD_core_011e_init_yes_json_payload_is_idempotent(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    runner = CliRunner()

    first = runner.invoke(
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
    assert first.exit_code == 0
    first_payload = json.loads(first.output)
    assert first_payload["mode"] == "init"
    assert first_payload["starter_prefix"] == "REQ"
    assert first_payload["created_count"] == 2
    assert sorted(first_payload["created_files"]) == [
        "docs/requirements/README.md",
        "docs/requirements/starter.md",
    ]

    second = runner.invoke(
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
    assert second.exit_code == 0
    second_payload = json.loads(second.output)
    assert second_payload["mode"] == "init"
    assert second_payload["created_count"] == 0
    assert second_payload["created_files"] == []


def test_RQMD_core_010_update_status_handles_blocked_and_deprecated_reasons(tmp_path: Path) -> None:
    path = tmp_path / "demo.md"
    path.write_text(
        """# Demo Requirement

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    requirement = cli.find_requirement_by_id(path, "AC-DEMO-001")

    changed = cli.update_criterion_status(path, requirement, "⛔ Blocked", blocked_reason="Need API")
    assert changed is True
    blocked_text = path.read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in blocked_text
    assert "**Blocked:** Need API" in blocked_text

    requirement = cli.find_requirement_by_id(path, "AC-DEMO-001")
    changed = cli.update_criterion_status(path, requirement, "🗑️ Deprecated", deprecated_reason="Replaced")
    assert changed is True
    deprecated_text = path.read_text(encoding="utf-8")
    assert "- **Status:** 🗑️ Deprecated" in deprecated_text
    assert "**Blocked:**" not in deprecated_text
    assert "**Deprecated:** Replaced" in deprecated_text


def test_RQMD_core_011_and_012_init_scaffold_creates_index_and_starter(tmp_path: Path) -> None:
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
        ],
        input="\n",
    )

    assert result.exit_code == 0
    index_path = repo / "docs" / "requirements" / "README.md"
    starter_path = repo / "docs" / "requirements" / "starter.md"
    assert index_path.exists()
    assert starter_path.exists()

    starter_text = starter_path.read_text(encoding="utf-8")
    assert "### REQ-HELLO-001: Replace this starter requirement" in starter_text
    assert "placeholder" in starter_text.lower()
    assert cli.SUMMARY_START in starter_text


def test_RQMD_core_012b_init_scaffold_allows_custom_starter_key(tmp_path: Path) -> None:
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
        ],
        input="TEAM\n",
    )

    assert result.exit_code == 0
    starter_text = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")
    assert "### TEAM-HELLO-001: Replace this starter requirement" in starter_text


def test_RQMD_core_016_init_scaffold_copies_template_content(tmp_path: Path) -> None:
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
        ],
        input="\n",
    )

    assert result.exit_code == 0

    index_text = (repo / "docs" / "requirements" / "README.md").read_text(encoding="utf-8")
    starter_text = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")

    assert "Generated from init-docs/README.md." in index_text
    assert "## Schema Reference" in index_text
    assert "This section is intentionally included in the generated requirements index" in index_text
    assert "filter-sub-domain" in index_text
    assert "And this file content is sourced from init-docs/domain-example.md." in starter_text


def test_RQMD_core_011b_init_scaffold_is_idempotent(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    runner = CliRunner()

    first = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--bootstrap",
        ],
        input="\n",
    )
    assert first.exit_code == 0

    second = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--bootstrap",
        ],
        input="\n",
    )
    assert second.exit_code == 0
    assert "already present" in second.output


def test_RQMD_core_011c_init_scaffold_supports_custom_criteria_dir(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "custom/ac",
            "--bootstrap",
        ],
        input="\n",
    )

    assert result.exit_code == 0
    assert (repo / "custom" / "ac" / "README.md").exists()
    assert (repo / "custom" / "ac" / "starter.md").exists()


def test_RQMD_core_011d_init_cannot_be_combined_with_check(tmp_path: Path) -> None:
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
            "--verify-summaries",
        ],
        input="\n",
    )

    assert result.exit_code != 0
    assert "--bootstrap cannot be combined" in result.output


def test_RQMD_core_005b_file_priority_sort_key_uses_current_statuses() -> None:
    implemented = {
        "💡 Proposed": 0,
        "🔧 Implemented": 2,
        "✅ Verified": 0,
        "⛔ Blocked": 0,
        "🗑️ Deprecated": 0,
    }
    verified = {
        "💡 Proposed": 0,
        "🔧 Implemented": 0,
        "✅ Verified": 3,
        "⛔ Blocked": 0,
        "🗑️ Deprecated": 0,
    }

    key_impl = cli.file_sort_key_by_priority(implemented, "A")
    key_ver = cli.file_sort_key_by_priority(verified, "B")
    assert key_impl < key_ver


def test_RQMD_core_005c_file_priority_sort_key_tie_breaks_by_label() -> None:
    same_counts = {
        "💡 Proposed": 1,
        "🔧 Implemented": 1,
        "✅ Verified": 1,
        "⛔ Blocked": 0,
        "🗑️ Deprecated": 0,
    }

    key_a = cli.file_sort_key_by_priority(same_counts, "a-file")
    key_b = cli.file_sort_key_by_priority(same_counts, "b-file")
    assert key_a < key_b


# Priority parsing and normalization tests (RQMD-PRIORITY-001 & 002)
def test_RQMD_priority_001_parse_priority_field() -> None:
    from rqmd.req_parser import parse_requirements

    text = """# Demo Requirements

### AC-DEMO-001: Critical Feature
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical

### AC-DEMO-002: Nice to Have
- **Status:** 💡 Proposed
- **Priority:** 🟢 P3 - Low
"""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path = Path(td) / "demo.md"
        path.write_text(text, encoding="utf-8")
        requirements = parse_requirements(path)

        assert len(requirements) == 2
        assert requirements[0]["priority"] == "🔴 P0 - Critical"
        assert requirements[0]["priority_line"] == 4  # 0-indexed line 4
        assert requirements[1]["priority"] == "🟢 P3 - Low"
        assert requirements[1]["priority_line"] == 8  # 0-indexed line 8


def test_RQMD_priority_001_priority_is_optional() -> None:
    from rqmd.req_parser import parse_requirements

    text = """# Demo Requirements

### AC-DEMO-001: Has Priority
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical

### AC-DEMO-002: No Priority
- **Status:** 💡 Proposed
"""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path = Path(td) / "demo.md"
        path.write_text(text, encoding="utf-8")
        requirements = parse_requirements(path)

        assert requirements[0]["priority"] == "🔴 P0 - Critical"
        assert requirements[1]["priority"] is None  # Priority is optional


def test_RQMD_priority_002_coerce_priority_with_aliases() -> None:
    from rqmd.priority_model import coerce_priority_label

    # Test canonical forms
    assert coerce_priority_label("🔴 P0 - Critical") == "🔴 P0 - Critical"
    assert coerce_priority_label("🟠 P1 - High") == "🟠 P1 - High"
    assert coerce_priority_label("🟡 P2 - Medium") == "🟡 P2 - Medium"
    assert coerce_priority_label("🟢 P3 - Low") == "🟢 P3 - Low"

    # Test case-insensitive aliases
    assert coerce_priority_label("p0") == "🔴 P0 - Critical"
    assert coerce_priority_label("P0") == "🔴 P0 - Critical"
    assert coerce_priority_label("critical") == "🔴 P0 - Critical"
    assert coerce_priority_label("p1") == "🟠 P1 - High"
    assert coerce_priority_label("high") == "🟠 P1 - High"
    assert coerce_priority_label("p2") == "🟡 P2 - Medium"
    assert coerce_priority_label("medium") == "🟡 P2 - Medium"
    assert coerce_priority_label("p3") == "🟢 P3 - Low"
    assert coerce_priority_label("low") == "🟢 P3 - Low"


def test_RQMD_priority_002_coerce_priority_unknown_yields_unset() -> None:
    from rqmd.priority_model import coerce_priority_label

    # Unknown priority defaults to "unset"
    assert coerce_priority_label("unknown") == "unset"
    assert coerce_priority_label("maybe") == "unset"
    assert coerce_priority_label("") == "unset"
