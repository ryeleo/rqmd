from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

from click.testing import CliRunner

from rqmd import cli
from rqmd.markdown_io import scope_and_body_from_file
from rqmd.req_parser import collect_sub_sections


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


def test_RQMD_core_020_collect_sub_sections_includes_optional_subsection_body() -> None:
    text = """# Demo Requirements

Scope: demo.

## Query API
This subsection body explains the query flow.

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
        sections = collect_sub_sections(path)

    assert sections[0]["name"] == "Query API"
    assert sections[0]["count"] == 1
    assert sections[0]["body"] == "This subsection body explains the query flow."
    assert sections[1] == {"name": "Mutation API", "count": 1}


def test_RQMD_core_020a_version_option_reports_installed_version(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(cli.importlib_metadata, "version", lambda _name: "9.8.7")
    monkeypatch.setattr(cli, "_editable_source_path_from_distribution", lambda: None)

    result = runner.invoke(cli.main, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "rqmd 9.8.7"


def test_RQMD_core_020b_version_option_reports_editable_source_path(tmp_path: Path, monkeypatch) -> None:
    runner = CliRunner()
    editable_root = tmp_path / "editable-repo"
    editable_root.mkdir()

    monkeypatch.setattr(cli.importlib_metadata, "version", lambda _name: "1.2.3")
    monkeypatch.setattr(cli, "_editable_source_path_from_distribution", lambda: editable_root)

    result = runner.invoke(cli.main, ["--version"])

    assert result.exit_code == 0
    assert "rqmd 1.2.3" in result.output
    assert f"editable source: {editable_root}" in result.output
    assert "package path:" in result.output


def test_RQMD_core_020c_cli_import_succeeds_without_readline(monkeypatch) -> None:
    module_name = "rqmd.cli"
    original_import_module = importlib.import_module
    original_module = sys.modules.get(module_name)

    def fake_import_module(name: str, package: str | None = None):
        if name == "readline":
            raise ModuleNotFoundError("No module named 'readline'")
        return original_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    sys.modules.pop(module_name, None)

    try:
        reimported_cli = original_import_module(module_name)
        assert hasattr(reimported_cli, "main")
    finally:
        if original_module is not None:
            sys.modules[module_name] = original_module


def test_RQMD_core_026_duplicate_ids_fail_fast(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "one.md").write_text(
        """# One

Scope: demo.

### REQ-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    (criteria_dir / "two.md").write_text(
        """# Two

Scope: demo.

### REQ-001: Second
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
            "--id-namespace",
            "REQ",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code != 0
    assert "Duplicate requirement IDs found" in result.output
    assert "REQ-001" in result.output


def test_RQMD_core_027_next_id_uses_custom_prefix_and_three_digit_padding(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        """# Demo

Scope: demo.

### TEAM-001: First
- **Status:** 💡 Proposed

### TEAM-002: Second
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
            "--id-namespace",
            "TEAM",
            "--next-id",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "next-id"
    assert payload["prefix"] == "TEAM"
    assert payload["requirement_id"] == "TEAM-003"
    assert payload["next_number"] == 3
    assert payload["min_width"] == 3


def test_RQMD_core_028_next_id_overflows_past_999(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        """# Demo

Scope: demo.

### REQ-999: Large catalog
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
            "REQ",
            "--next-id",
        ],
    )

    assert result.exit_code == 0
    assert result.output.strip().endswith("REQ-1000")


def test_RQMD_core_027_next_id_requires_single_namespace(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        """# Demo

Scope: demo.

### AC-001: First
- **Status:** 💡 Proposed

### R-001: Second
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
            "--next-id",
        ],
    )

    assert result.exit_code != 0
    assert "requires a single active ID namespace" in result.output


def test_RQMD_core_019_domain_body_excludes_h2_subsection_content() -> None:
    text = """# Demo Requirements

Scope: demo.

Global domain note before subsections.

## Query API
Subsection narrative that should not be in domain_body.

### AC-DEMO-001: Read model
- **Status:** ✅ Verified
"""

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path = Path(td) / "demo.md"
        path.write_text(text, encoding="utf-8")
        scope, body = scope_and_body_from_file(path)
        sections = collect_sub_sections(path)

    assert scope == "demo"
    assert body == "Global domain note before subsections."
    assert sections[0]["name"] == "Query API"
    assert sections[0]["body"] == "Subsection narrative that should not be in domain_body."


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
            "- **Status:** ⚠️ Janky",
            "- **Status:** ⛔ Blocked",
            "- **Status:** 🗑️ Deprecated",
        ]
    )
    counts = cli.count_statuses(text)
    assert counts["💡 Proposed"] == 1
    assert counts["🔧 Implemented"] == 1
    assert counts["✅ Verified"] == 1
    assert counts["⚠️ Janky"] == 1
    assert counts["⛔ Blocked"] == 1
    assert counts["🗑️ Deprecated"] == 1


def test_RQMD_core_006b_build_summary_block_uses_builtin_status_order() -> None:
    counts = {label: 0 for label, _ in cli.STATUS_ORDER}
    counts["💡 Proposed"] = 2
    counts["🔧 Implemented"] = 3
    counts["✅ Verified"] = 4
    counts["⚠️ Janky"] = 6
    counts["⛔ Blocked"] = 1
    counts["🗑️ Deprecated"] = 5

    summary = cli.build_summary_block(counts)
    assert "Summary: 2💡 3🔧 4✅ 6⚠️ 1⛔ 5🗑️" in summary


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
    assert "default chat-first setup flow" in result.output
    assert "rqmd init" in result.output


def test_RQMD_core_009_missing_requirements_index_shows_first_time_setup_guidance(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    assert "No requirement docs found. Expected to find docs/requirements/README.md or requirements/README.md." in result.output
    assert "First time setup?" in result.output
    assert "rqmd init" in result.output
    assert "rqmd init --scaffold" in result.output


def test_RQMD_core_013_verify_index_missing_index_uses_shared_startup_guidance(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        "# Demo Requirement\n\n"
        "Scope: demo.\n\n"
        "### AC-DEMO-001: Example\n"
        "- **Status:** 💡 Proposed\n",
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
            "--verify-index",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    assert "No requirements index found at: docs/requirements/README.md" in result.output
    assert "guided setup flow" in result.output
    assert "rqmd init --scaffold" in result.output


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
    assert "Initialized requirement scaffold:" in result.output
    assert (repo / "docs" / "requirements" / "README.md").exists()
    starter = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")
    assert "### REQ-HELLO-001: Replace this starter requirement" in starter


def test_RQMD_core_009b_missing_domain_docs_prompt_template_matches_cli_confirmation_copy() -> None:
    assert cli.render_startup_message("scaffold-empty-confirm.md").rstrip() == (
        "No requirement files found. Initialize a starter scaffold now?"
    )


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
            "init",
            "--scaffold",
            "--force-yes",
        ],
    )

    assert result.exit_code == 0
    starter = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")
    assert "### REQ-HELLO-001: Replace this starter requirement" in starter


def test_RQMD_core_009g_positional_init_emits_chat_handoff_payload(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    runner = CliRunner()

    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--json",
            "init",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "init-chat"
    assert payload["workflow_mode"] == "init"
    assert payload["strategy"]["selected"] == "starter-scaffold"
    assert payload["handoff_prompt"]


def test_RQMD_core_017_bootstrap_readme_includes_tagline_and_links(tmp_path: Path) -> None:
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
            "init",
            "--scaffold",
            "--force-yes",
        ],
    )

    assert result.exit_code == 0
    readme_text = (repo / "docs" / "requirements" / "README.md").read_text(encoding="utf-8")
    assert "This document is the source-of-truth index for rqmd requirements." in readme_text
    assert "Generated from resources/init/README.md." in readme_text
    assert "## Project Tooling Metadata" in readme_text
    assert "- `rqmd_version`: `" in readme_text
    assert "- `json_schema_version`: `1.0.0`" in readme_text
    assert "- `⚠️ Janky`" in readme_text


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
            "init",
            "--scaffold",
            "--force-yes",
            "--as-json",
        ],
    )
    assert first.exit_code == 0
    first_payload = json.loads(first.output)
    assert first_payload["mode"] == "init"
    assert first_payload["starter_prefix"] == "REQ"
    assert first_payload["created_count"] == 3
    assert sorted(first_payload["created_files"]) == [
        ".rqmd.yml",
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
            "init",
            "--scaffold",
            "--force-yes",
            "--as-json",
        ],
    )
    assert second.exit_code == 0
    second_payload = json.loads(second.output)
    assert second_payload["mode"] == "init"
    assert second_payload["created_count"] == 0
    assert second_payload["created_files"] == []


def test_RQMD_core_011f_init_yes_json_alias_emits_json_payload(tmp_path: Path) -> None:
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
            "init",
            "--scaffold",
            "--force-yes",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "init"
    assert payload["starter_prefix"] == "REQ"
    assert payload["created_count"] == 3


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
            "init",
            "--scaffold",
        ],
        input="\n",
    )

    assert result.exit_code == 0
    assert "Initialize scaffold: choose a requirement ID key prefix" in result.output
    assert "Tip: customize this for your project to avoid generic IDs." in result.output
    assert "Initialized requirement scaffold:" in result.output
    config_path = repo / ".rqmd.yml"
    index_path = repo / "docs" / "requirements" / "README.md"
    starter_path = repo / "docs" / "requirements" / "starter.md"
    assert config_path.exists()
    assert index_path.exists()
    assert starter_path.exists()

    config_text = config_path.read_text(encoding="utf-8")
    starter_text = starter_path.read_text(encoding="utf-8")
    assert "requirements_dir: docs/requirements" in config_text
    assert "id_prefix: REQ" in config_text
    assert "statuses:" in config_text
    assert "priorities:" in config_text
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
            "init",
            "--scaffold",
        ],
        input="TEAM\n",
    )

    assert result.exit_code == 0
    config_text = (repo / ".rqmd.yml").read_text(encoding="utf-8")
    starter_text = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")
    assert "id_prefix: TEAM" in config_text
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
            "init",
            "--scaffold",
        ],
        input="\n",
    )

    assert result.exit_code == 0

    index_text = (repo / "docs" / "requirements" / "README.md").read_text(encoding="utf-8")
    starter_text = (repo / "docs" / "requirements" / "starter.md").read_text(encoding="utf-8")

    assert "Generated from resources/init/README.md." in index_text
    assert "## Project Tooling Metadata" in index_text
    assert "rqmd --sync-index-metadata --force-yes" in index_text
    assert "## Schema Reference" in index_text
    assert "This section is intentionally included in the generated requirements index" in index_text
    assert "filter-sub-domain" in index_text
    assert "Prefer pairing a short user story" in index_text
    assert "And this file content is sourced from resources/init/domain-example.md." in starter_text
    assert "I want a starter requirement that demonstrates both intent and acceptance detail" in starter_text


def test_RQMD_core_033a_sync_index_metadata_adds_project_tooling_block(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    index_path = criteria_dir / "README.md"
    index_path.write_text(
        """# Requirements\n\nThis document is the source-of-truth index for rqmd requirements.\n\n## Requirement Documents\n\n- [Demo](demo.md)\n""",
        encoding="utf-8",
    )
    (criteria_dir / "demo.md").write_text(
        """# Demo\n\nScope: demo.\n\n### RQMD-DEMO-001: First\n- **Status:** 💡 Proposed\n""",
        encoding="utf-8",
    )
    runner = CliRunner()
    monkeypatch.setattr(cli.importlib_metadata, "version", lambda _name: "9.9.9")
    monkeypatch.setattr("rqmd.markdown_io.importlib_metadata.version", lambda _name: "9.9.9")

    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--sync-index-metadata",
            "--force-yes",
        ],
    )

    assert result.exit_code == 0
    updated_text = index_path.read_text(encoding="utf-8")
    assert "## Project Tooling Metadata" in updated_text
    assert "- `rqmd_version`: `9.9.9`" in updated_text
    assert "- `json_schema_version`: `1.0.0`" in updated_text


def test_RQMD_core_033b_warns_when_requirements_index_metadata_mismatches(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        """# Requirements\n\nThis document is the source-of-truth index for rqmd requirements.\n\n## Project Tooling Metadata\n\nThis section records the rqmd tooling versions currently expected by this repository.\nRefresh it after upgrading rqmd by running `rqmd --sync-index-metadata --force-yes`.\n\n<!-- rqmd-project-metadata:start -->\n- `rqmd_version`: `0.0.1`\n- `json_schema_version`: `0.0.1`\n<!-- rqmd-project-metadata:end -->\n\n## Requirement Documents\n\n- [Demo](demo.md)\n""",
        encoding="utf-8",
    )
    (criteria_dir / "demo.md").write_text(
        """# Demo\n\nScope: demo.\n\n### RQMD-DEMO-001: First\n- **Status:** 💡 Proposed\n""",
        encoding="utf-8",
    )
    runner = CliRunner()
    monkeypatch.setattr(cli.importlib_metadata, "version", lambda _name: "9.9.9")
    monkeypatch.setattr("rqmd.markdown_io.importlib_metadata.version", lambda _name: "9.9.9")

    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--verify-index",
        ],
    )

    assert result.exit_code == 0
    assert "Warning: requirements index metadata mismatch" in result.output
    assert "run `rqmd --sync-index-metadata --force-yes`".lower() in result.output.lower()


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
            "init",
            "--scaffold",
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
            "init",
            "--scaffold",
        ],
        input="\n",
    )
    assert second.exit_code == 0


def test_RQMD_core_037_history_flags_removed_in_simplification_mode(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    runner = CliRunner()

    history_result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--history",
        ],
    )
    assert history_result.exit_code != 0
    assert "No such option: --history" in history_result.output

    undo_result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--undo",
        ],
    )
    assert undo_result.exit_code != 0
    assert "No such option: --undo" in undo_result.output


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
            "init",
            "--scaffold",
        ],
        input="\n",
    )

    assert result.exit_code == 0
    config_text = (repo / ".rqmd.yml").read_text(encoding="utf-8")
    assert (repo / "custom" / "ac" / "README.md").exists()
    assert (repo / "custom" / "ac" / "starter.md").exists()
    assert "requirements_dir: custom/ac" in config_text


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
            "init",
            "--scaffold",
            "--verify-summaries",
        ],
        input="\n",
    )

    assert result.exit_code != 0
    assert "rqmd init is an onboarding surface" in result.output


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


def test_RQMD_core_021_parse_requirement_links_plain_and_markdown() -> None:
    text = """# Demo Requirements

Scope: demo.

### AC-DEMO-001: With links
- **Status:** 💡 Proposed
- **Links:**
  - https://github.com/issue/123
  - [GitHub Issues](https://github.com/issues)
  - [Jira](https://jira.example.com/browse/PROJ-456)

### AC-DEMO-002: No links
- **Status:** ✅ Verified
"""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        path = Path(td) / "demo.md"
        path.write_text(text, encoding="utf-8")
        requirements = cli.parse_requirements(path)

    assert len(requirements) == 2
    
    req_001 = requirements[0]
    assert req_001["id"] == "AC-DEMO-001"
    assert req_001["links"] is not None
    assert len(req_001["links"]) == 3
    assert req_001["links"][0] == {"url": "https://github.com/issue/123", "label": None}
    assert req_001["links"][1] == {"url": "https://github.com/issues", "label": "GitHub Issues"}
    assert req_001["links"][2] == {"url": "https://jira.example.com/browse/PROJ-456", "label": "Jira"}

    req_002 = requirements[1]
    assert req_002["id"] == "AC-DEMO-002"
    assert req_002["links"] is None


def test_RQMD_core_021_links_included_in_json_payload(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: With links
- **Status:** 💡 Proposed
- **Links:**
  - https://github.com/issue/123
  - [Docs](https://docs.example.com)

### AC-DEMO-002: No links
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
            "proposed",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["files"][0]["requirements"][0]["id"] == "AC-DEMO-001"
    assert "links" in payload["files"][0]["requirements"][0]
    links = payload["files"][0]["requirements"][0]["links"]
    assert len(links) == 2
    assert links[0] == {"url": "https://github.com/issue/123", "label": None}
    assert links[1] == {"url": "https://docs.example.com", "label": "Docs"}


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


def test_RQMD_core_023_rename_id_prefix_updates_headers_and_citations(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "alpha.md").write_text(
        "# Alpha\n\n"
        "### AC-ALPHA-001: First\n"
        "- **Status:** 💡 Proposed\n"
        "- Depends on AC-ALPHA-002\n\n"
        "### AC-ALPHA-002: Second\n"
        "- **Status:** ✅ Verified\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root", str(repo),
            "--docs-dir", "docs/requirements",
            "--rename-id-prefix", "AC=RQMD",
            "--no-table",
        ],
    )
    assert result.exit_code == 0, result.output
    updated = (domain / "alpha.md").read_text(encoding="utf-8")
    assert "### RQMD-ALPHA-001: First" in updated
    assert "### RQMD-ALPHA-002: Second" in updated
    assert "Depends on RQMD-ALPHA-002" in updated


def test_RQMD_core_023_rename_id_prefix_detects_conflicts(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "alpha.md").write_text(
        "# Alpha\n\n"
        "### AC-ALPHA-001: First\n"
        "- **Status:** 💡 Proposed\n\n"
        "### RQMD-ALPHA-001: Existing\n"
        "- **Status:** ✅ Verified\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root", str(repo),
            "--docs-dir", "docs/requirements",
            "--rename-id-prefix", "AC=RQMD",
            "--no-table",
        ],
    )
    assert result.exit_code != 0
    assert "conflict" in result.output.lower()


def test_RQMD_core_023_rename_id_prefix_json_dry_run(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    file_path = domain / "alpha.md"
    original = (
        "# Alpha\n\n"
        "### AC-ALPHA-001: First\n"
        "- **Status:** 💡 Proposed\n"
    )
    file_path.write_text(original, encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root", str(repo),
            "--docs-dir", "docs/requirements",
            "--rename-id-prefix", "AC=RQMD",
            "--dry-run",
            "--as-json",
            "--no-table",
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "rename-id-prefix"
    assert payload["dry_run"] is True
    assert payload["replacement_count"] == 1
    assert file_path.read_text(encoding="utf-8") == original
