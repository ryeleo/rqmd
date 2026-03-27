from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rqmd import cli


def test_RQMD_portability_001_and_002_repo_root_and_criteria_dir_flags(tmp_path: Path) -> None:
    repo = tmp_path / "another-repo"
    requirements = repo / "custom" / "ac"
    requirements.mkdir(parents=True)
    (requirements / "x.md").write_text(
        """# X Requirement

Scope: x.

### AC-X-001: X
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
            "custom/ac",
            "--verify-summaries",
            "--no-walk",
            "--no-table",
        ],
    )
    assert result.exit_code == 1


def test_RQMD_portability_003_default_conventions(monkeypatch, repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Build default docs/requirements under isolated CWD.
        cwd = Path.cwd()
        domain = cwd / "docs" / "requirements"
        domain.mkdir(parents=True)
        (domain / "README.md").write_text(
            "# Requirements\n\n## Domain Documents\n\n- [Demo](demo.md)\n",
            encoding="utf-8",
        )
        (domain / "demo.md").write_text(
            """# Demo Requirement

Scope: demo.

### AC-HELLO-001: Hello requirement
- **Status:** 🔧 Implemented
""",
            encoding="utf-8",
        )
        result = runner.invoke(cli.main, ["--verify-summaries", "--no-walk", "--no-table"])
        assert result.exit_code == 1


def test_RQMD_portability_004_relative_source_display(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    path = repo / "docs" / "requirements" / "demo.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        """# Demo Requirement

Scope: demo.

### AC-HELLO-001: Hello requirement
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    requirement = cli.find_requirement_by_id(path, "AC-HELLO-001")
    cli.print_criterion_panel(path, requirement, repo)
    output = capsys.readouterr().out
    assert "Source: docs/requirements/demo.md" in output


def test_RQMD_portability_005_generic_project_assumptions(tmp_path: Path) -> None:
    repo = tmp_path / "generic"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Generic](generic.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "generic.md").write_text(
        """# Generic Requirement

Scope: generic.

### AC-GENERIC-001: Generic
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--project-root", str(repo), "--docs-dir", "docs/requirements", "--no-walk", "--no-table"],
    )
    assert result.exit_code == 0


def test_RQMD_portability_017_unknown_status_reports_actionable_guidance(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        """# Demo Requirement

Scope: demo.

### AC-DEMO-001: Demo requirement
- **Status:** 💻 Desktop-Verified
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
            "--verify-summaries",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    assert "Unknown status compatibility issue" in result.output
    assert "Desktop-Verified" in result.output
    assert "docs/requirements/demo.md" in result.output
    assert "Remediation:" in result.output


def test_RQMD_portability_017_unknown_status_json_error_payload(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        """# Demo Requirement

Scope: demo.

### AC-DEMO-001: Demo requirement
- **Status:** 💻 Desktop-Verified
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
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["mode"] == "summary"
    assert payload["ok"] is False
    assert payload["error"]["type"] == "unknown-status"
    assert payload["error"]["input"] == "💻 Desktop-Verified"
    assert payload["error"]["source_file"] == "docs/requirements/demo.md"
    assert isinstance(payload["error"]["line"], int)
    assert payload["error"]["candidates"]


def test_RQMD_portability_008a_auto_detects_requirements_dir_without_explicit_flag(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Demo](demo.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "demo.md").write_text(
        """# Demo Requirement

Scope: demo.

### REQ-DEMO-001: Demo requirement
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--project-root", str(repo), "--status", "Implemented", "--as-tree", "--no-walk", "--no-table"],
    )

    assert result.exit_code == 0
    assert "Auto-selected requirement docs: requirements/README.md" in result.output
    assert "REQ-DEMO-001" in result.output


def test_RQMD_portability_008b_auto_detection_prefers_nearest_requirements_dir_from_cwd(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    root_criteria_dir = repo / "requirements"
    nested_root = repo / "packages" / "feature"
    nested_criteria_dir = nested_root / "requirements"
    root_criteria_dir.mkdir(parents=True)
    nested_criteria_dir.mkdir(parents=True)
    (root_criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Root](root.md)\n",
        encoding="utf-8",
    )
    (nested_criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Feature](feature.md)\n",
        encoding="utf-8",
    )
    (root_criteria_dir / "root.md").write_text(
        """# Root Requirement

Scope: root.

### AC-ROOT-001: Root requirement
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    (nested_criteria_dir / "feature.md").write_text(
        """# Feature Requirement

Scope: feature.

### AC-FEATURE-001: Feature requirement
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested_root)
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--project-root", str(repo), "--status", "Implemented", "--as-tree", "--no-walk", "--no-table"],
    )

    assert result.exit_code == 0
    assert "Auto-selected requirement docs: packages/feature/requirements/README.md" in result.output
    assert "AC-FEATURE-001" in result.output
    assert "AC-ROOT-001" not in result.output


def test_RQMD_portability_014_state_dir_option_forwards_to_filtered_walk(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        """# Demo Requirement

Scope: demo.

### AC-DEMO-001: Demo
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_filtered_loop(repo_root, domain_files, target_status, emoji_columns, id_prefixes, resume_filter, state_dir, include_status_emojis, priority_mode, include_priority_summary):
        captured["state_dir"] = state_dir
        captured["target_status"] = target_status
        return 0

    monkeypatch.setattr(cli, "filtered_interactive_loop", fake_filtered_loop)

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
            "--session-state-dir",
            "project-local",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert captured["state_dir"] == "project-local"
    assert captured["target_status"] == "🔧 Implemented"


def test_RQMD_portability_010_strip_and_restore_status_emojis(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    target = criteria_dir / "demo.md"
    target.write_text(
        """# Demo Requirement

Scope: demo.

### AC-DEMO-001: Demo
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()

    strip_result = runner.invoke(
        cli.main,
        [
            "--project-root", str(repo),
            "--docs-dir", "docs/requirements",
            "--strip-status-icons",
            "--no-table",
        ],
    )
    assert strip_result.exit_code == 0

    stripped_text = target.read_text(encoding="utf-8")
    assert "- **Status:** Implemented" in stripped_text
    assert "🔧" not in stripped_text

    no_reintroduce_result = runner.invoke(
        cli.main,
        [
            "--project-root", str(repo),
            "--docs-dir", "docs/requirements",
            "--no-walk",
            "--no-table",
        ],
    )
    assert no_reintroduce_result.exit_code == 0
    assert "🔧" not in target.read_text(encoding="utf-8")

    restore_result = runner.invoke(
        cli.main,
        [
            "--project-root", str(repo),
            "--docs-dir", "docs/requirements",
            "--restore-status-icons",
            "--no-table",
        ],
    )
    assert restore_result.exit_code == 0

    restored_text = target.read_text(encoding="utf-8")
    assert "- **Status:** 🔧 Implemented" in restored_text
    assert "Summary:" in restored_text
    assert "🔧" in restored_text


def test_RQMD_packaging_001_to_005_metadata_and_layout() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "src" / "rqmd" / "cli.py").exists()
    assert (project_root / "src" / "rqmd" / "__main__.py").exists()

    pyproject = (project_root / "pyproject.toml").read_text(encoding="utf-8")
    assert "rqmd = \"rqmd.cli:main\"" in pyproject
    assert "click>=8.1.0" in pyproject
    assert "tabulate>=0.9.0" in pyproject

    readme = (project_root / "README.md").read_text(encoding="utf-8")
    assert "rqmd --verify-summaries" in readme
    assert "--project-root" in readme
    assert "--docs-dir" in readme
    assert "--id-namespace" in readme


def test_RQMD_automation_012_readme_documents_json_schema_contract() -> None:
    project_root = Path(__file__).resolve().parents[1]
    readme = (project_root / "README.md").read_text(encoding="utf-8")

    assert "JSON contract (stable keys)" in readme
    assert "summary" in readme
    assert "check" in readme
    assert "set" in readme
    assert "filter-status" in readme
    assert "filter-priority" in readme
    assert "filter-flagged" in readme
    assert "rollup" in readme


def test_RQMD_automation_016_readme_documents_exit_code_matrix() -> None:
    project_root = Path(__file__).resolve().parents[1]
    readme = (project_root / "README.md").read_text(encoding="utf-8")

    assert "Exit codes" in readme
    assert "- `0`:" in readme
    assert "- `1`:" in readme
    assert "130" in readme

    changelog_path = project_root / "CHANGELOG.md"
    assert changelog_path.exists()
    changelog = changelog_path.read_text(encoding="utf-8")
    assert "# Changelog" in changelog
    assert "## [Unreleased]" in changelog
    assert "Keep a Changelog" in changelog


def test_RQMD_packaging_006_metadata_hardening_fields_present() -> None:
    project_root = Path(__file__).resolve().parents[1]
    pyproject = (project_root / "pyproject.toml").read_text(encoding="utf-8")

    assert "license = \"MIT\"" in pyproject
    assert "[project.urls]" in pyproject
    assert "Homepage = \"https://github.com/example/rqmd\"" in pyproject
    assert "Repository = \"https://github.com/example/rqmd\"" in pyproject
    assert "Issues = \"https://github.com/example/rqmd/issues\"" in pyproject
    assert "classifiers = [" in pyproject
    assert "Programming Language :: Python :: 3.10" in pyproject


def test_RQMD_packaging_007_semver_policy_documented() -> None:
    project_root = Path(__file__).resolve().parents[1]
    semver_path = project_root / "docs" / "SEMVER.md"

    assert semver_path.exists()
    semver_text = semver_path.read_text(encoding="utf-8")
    assert "Semantic Versioning" in semver_text
    assert "MAJOR.MINOR.PATCH" in semver_text
    assert "PATCH" in semver_text
    assert "MINOR" in semver_text
    assert "MAJOR" in semver_text


def test_RQMD_packaging_010_readme_documents_shell_completion_activation() -> None:
    project_root = Path(__file__).resolve().parents[1]
    readme = (project_root / "README.md").read_text(encoding="utf-8")

    assert "## Shell completion" in readme
    assert "_RQMD_COMPLETE=zsh_source rqmd" in readme
    assert "_RQMD_COMPLETE=bash_source rqmd" in readme
    assert "_RQMD_COMPLETE=fish_source rqmd | source" in readme
    assert "zcompdump" in readme
    assert "Completion candidates stay in sync with live requirement docs" in readme


def test_RQMD_packaging_008_release_publish_workflow_present() -> None:
    project_root = Path(__file__).resolve().parents[1]
    workflow_path = project_root / ".github" / "workflows" / "publish-pypi.yml"

    assert workflow_path.exists()
    workflow_text = workflow_path.read_text(encoding="utf-8")
    assert "release:" in workflow_text
    assert "types: [published]" in workflow_text
    assert "uv build" in workflow_text
    assert "uv publish" in workflow_text
    assert "PYPI_API_TOKEN" in workflow_text


def test_RQMD_portability_008_scratch_corpus_runs_from_requirements_dir_without_docs_prefix() -> None:
    project_root = Path(__file__).resolve().parents[1]
    scratch_root = project_root / "test-corpus" / "scratch"

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(scratch_root),
            "--docs-dir",
            "requirements",
            "--status",
            "Implemented",
            "--as-tree",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "REQ-PAG-002" in result.output
    assert "REQ-PAG-037" in result.output
    assert "REQ-PAG-227" in result.output


# ---------------------------------------------------------------------------
# RQMD-PORTABILITY-009: Graceful startup errors
# ---------------------------------------------------------------------------


def test_RQMD_portability_009_nonexistent_criteria_dir_gives_not_found_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root", str(repo),
            "--docs-dir", "no/such/dir",
            "--verify-summaries",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code != 0
    assert "not found" in result.output.lower()
    assert "rqmd --bootstrap" in result.output or "requirements-dir" in result.output.lower()


def test_RQMD_portability_009_unreadable_domain_file_gives_permission_error(tmp_path: Path) -> None:
    import os
    import stat

    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "locked.md"
    domain_file.write_text(
        "# Locked\n\n### AC-LOCK-001: Locked\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )
    domain_file.chmod(0o000)

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--project-root", str(repo),
                "--docs-dir", "docs/requirements",
                "--verify-summaries",
                "--no-walk",
                "--no-table",
            ],
        )
        assert result.exit_code != 0
        combined = (result.output or "") + (str(result.exception) if result.exception else "")
        assert "permission" in combined.lower() or "inaccessible" in combined.lower()
    finally:
        domain_file.chmod(stat.S_IRUSR | stat.S_IWUSR)


# ---------------------------------------------------------------------------
# RQMD-CORE-013: Domain-sync maintenance (--verify-index)
# ---------------------------------------------------------------------------

_SAMPLE_DOMAIN = """# Demo Domain

### AC-DEMO-001: Demo
- **Status:** 🔧 Implemented
"""


def _make_index_repo(repo: Path, index_body: str, domain_files: dict[str, str]) -> None:
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(index_body, encoding="utf-8")
    for name, content in domain_files.items():
        (criteria_dir / name).write_text(content, encoding="utf-8")


def test_RQMD_core_013_check_index_clean_exits_zero(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_index_repo(
        repo,
        "# Requirements\n\n- [Demo](demo.md)\n",
        {"demo.md": _SAMPLE_DOMAIN},
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--project-root", str(repo), "--verify-index", "--no-walk", "--no-table"],
    )
    assert result.exit_code == 0
    assert "in sync" in result.output.lower()


def test_RQMD_core_013_check_index_stale_link_exits_nonzero(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_index_repo(
        repo,
        "# Requirements\n\n- [Demo](demo.md)\n- [Gone](gone.md)\n",
        {"demo.md": _SAMPLE_DOMAIN},  # gone.md does NOT exist
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--project-root", str(repo), "--verify-index", "--no-walk", "--no-table"],
    )
    assert result.exit_code != 0
    assert "stale" in result.output.lower()
    assert "gone.md" in result.output


def test_RQMD_core_013_check_index_orphan_file_exits_nonzero(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_index_repo(
        repo,
        "# Requirements\n\n- [Demo](demo.md)\n",
        {"demo.md": _SAMPLE_DOMAIN, "unlisted.md": _SAMPLE_DOMAIN},  # unlisted.md not in index
    )
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--project-root", str(repo), "--verify-index", "--no-walk", "--no-table"],
    )
    assert result.exit_code != 0
    assert "orphan" in result.output.lower()
    assert "unlisted.md" in result.output


def test_RQMD_core_013_parse_index_links_extracts_md_filenames(tmp_path: Path) -> None:
    index = tmp_path / "README.md"
    index.write_text(
        "# Index\n\n- [Core](core.md)\n- [UX](ux.md)\n- [External](../other/doc.md)\n- [Web](https://example.com/doc.md)\n",
        encoding="utf-8",
    )
    links = cli.parse_index_links(index)
    # Only simple relative filenames without path separators
    assert "core.md" in links
    assert "ux.md" in links
    # Links with path separators or external domains should be excluded
    assert not any("/" in lnk for lnk in links)


def test_RQMD_portability_015_upward_root_discovery_prefers_nearest_ancestor(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    root_criteria = repo / "docs" / "requirements"
    nested_root = repo / "packages" / "feature"
    nested_criteria = nested_root / "requirements"

    root_criteria.mkdir(parents=True)
    nested_criteria.mkdir(parents=True)

    (root_criteria / "README.md").write_text("# Requirements\n\n- [Root](root.md)\n", encoding="utf-8")
    (root_criteria / "root.md").write_text(
        """# Root Requirement

### AC-ROOT-001: Root
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    (nested_criteria / "README.md").write_text("# Requirements\n\n- [Nested](nested.md)\n", encoding="utf-8")
    (nested_criteria / "nested.md").write_text(
        """# Nested Requirement

### AC-NEST-001: Nested
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    (nested_root / "src").mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(nested_root / "src")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--status", "Implemented", "--as-tree", "--no-walk", "--no-table"],
    )

    assert result.exit_code == 0
    assert "AC-NEST-001" in result.output
    assert "AC-ROOT-001" not in result.output


def test_RQMD_portability_015_marker_priority_prefers_rqmd_config(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    (repo / ".rqmd.yml").write_text("requirements_dir: docs/requirements\n", encoding="utf-8")
    (repo / "requirements").mkdir(parents=True)
    requirements = repo / "docs" / "requirements"
    requirements.mkdir(parents=True)
    (requirements / "README.md").write_text("# Requirements\n\n- [Demo](demo.md)\n", encoding="utf-8")
    (requirements / "demo.md").write_text(
        """# Demo Requirement

### AC-DEMO-001: Demo
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(repo)
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--status", "Implemented", "--as-tree", "--no-walk", "--no-table"],
    )

    assert result.exit_code == 0
    assert "marker:.rqmd.yml" in result.output


def test_RQMD_portability_015_explicit_repo_root_bypasses_discovery(tmp_path: Path, monkeypatch) -> None:
    repo = tmp_path / "repo"
    nested = repo / "nested"
    nested.mkdir(parents=True)
    (nested / ".rqmd.yml").write_text("requirements_dir: requirements\n", encoding="utf-8")
    (nested / "requirements").mkdir(parents=True)

    root_criteria = repo / "docs" / "requirements"
    root_criteria.mkdir(parents=True)
    (root_criteria / "root.md").write_text(
        """# Root Requirement

### AC-ROOT-001: Root
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested)
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
    assert "Auto-discovered project root:" not in result.output
    assert "AC-ROOT-001" in result.output
