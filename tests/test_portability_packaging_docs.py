from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from rqmd import cli


def test_RQMD_portability_001_and_002_repo_root_and_criteria_dir_flags(tmp_path: Path) -> None:
    repo = tmp_path / "another-repo"
    criteria = repo / "custom" / "ac"
    criteria.mkdir(parents=True)
    (criteria / "x.md").write_text(
        """# X Acceptance Criteria

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
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "custom/ac",
            "--check",
            "--no-interactive",
            "--no-summary-table",
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
            """# Demo Acceptance Criteria

Scope: demo.

### AC-HELLO-001: Hello criterion
- **Status:** 🔧 Implemented
""",
            encoding="utf-8",
        )
        result = runner.invoke(cli.main, ["--check", "--no-interactive", "--no-summary-table"])
        assert result.exit_code == 1


def test_RQMD_portability_004_relative_source_display(tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    path = repo / "docs" / "requirements" / "demo.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        """# Demo Acceptance Criteria

Scope: demo.

### AC-HELLO-001: Hello criterion
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    criterion = cli.find_criterion_by_id(path, "AC-HELLO-001")
    cli.print_criterion_panel(path, criterion, repo)
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
        """# Generic Acceptance Criteria

Scope: generic.

### AC-GENERIC-001: Generic
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--repo-root", str(repo), "--criteria-dir", "docs/requirements", "--no-interactive", "--no-summary-table"],
    )
    assert result.exit_code == 0


def test_RQMD_portability_008a_auto_detects_requirements_dir_without_explicit_flag(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Demo](demo.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "demo.md").write_text(
        """# Demo Acceptance Criteria

Scope: demo.

### REQ-DEMO-001: Demo criterion
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--repo-root", str(repo), "--filter-status", "Implemented", "--tree", "--no-interactive", "--no-summary-table"],
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
        """# Root Acceptance Criteria

Scope: root.

### AC-ROOT-001: Root criterion
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    (nested_criteria_dir / "feature.md").write_text(
        """# Feature Acceptance Criteria

Scope: feature.

### AC-FEATURE-001: Feature criterion
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(nested_root)
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        ["--repo-root", str(repo), "--filter-status", "Implemented", "--tree", "--no-interactive", "--no-summary-table"],
    )

    assert result.exit_code == 0
    assert "Auto-selected requirement docs: packages/feature/requirements/README.md" in result.output
    assert "AC-FEATURE-001" in result.output
    assert "AC-ROOT-001" not in result.output


def test_RQMD_packaging_001_to_005_metadata_and_layout() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "src" / "rqmd" / "cli.py").exists()
    assert (project_root / "src" / "rqmd" / "__main__.py").exists()

    pyproject = (project_root / "pyproject.toml").read_text(encoding="utf-8")
    assert "rqmd = \"rqmd.cli:main\"" in pyproject
    assert "click>=8.1.0" in pyproject
    assert "tabulate>=0.9.0" in pyproject

    readme = (project_root / "README.md").read_text(encoding="utf-8")
    assert "rqmd --check" in readme
    assert "--repo-root" in readme
    assert "--criteria-dir" in readme
    assert "--id-prefix" in readme

    changelog_path = project_root / "CHANGELOG.md"
    assert changelog_path.exists()
    changelog = changelog_path.read_text(encoding="utf-8")
    assert "# Changelog" in changelog
    assert "## [Unreleased]" in changelog
    assert "Keep a Changelog" in changelog


def test_RQMD_portability_008_scratch_corpus_runs_from_requirements_dir_without_docs_prefix() -> None:
    project_root = Path(__file__).resolve().parents[1]
    scratch_root = project_root / "scratch"

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(scratch_root),
            "--criteria-dir",
            "requirements",
            "--filter-status",
            "Implemented",
            "--tree",
            "--no-interactive",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "REQ-PAG-002" in result.output
    assert "REQ-PAG-037" in result.output
    assert "REQ-PAG-227" in result.output
