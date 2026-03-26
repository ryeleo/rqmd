from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from reqmd import cli


def test_REQMD_portability_001_and_002_repo_root_and_criteria_dir_flags(tmp_path: Path) -> None:
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


def test_REQMD_portability_003_default_conventions(monkeypatch, repo_with_domain_docs: Path) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Build default docs/requirements under isolated CWD.
        cwd = Path.cwd()
        domain = cwd / "docs" / "requirements"
        domain.mkdir(parents=True)
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


def test_REQMD_portability_004_relative_source_display(tmp_path: Path, capsys) -> None:
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


def test_REQMD_portability_005_generic_project_assumptions(tmp_path: Path) -> None:
    repo = tmp_path / "generic"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
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


def test_REQMD_packaging_001_to_005_metadata_and_layout() -> None:
    project_root = Path(__file__).resolve().parents[1]

    assert (project_root / "src" / "reqmd" / "cli.py").exists()
    assert (project_root / "src" / "reqmd" / "__main__.py").exists()

    pyproject = (project_root / "pyproject.toml").read_text(encoding="utf-8")
    assert "reqmd = \"reqmd.cli:main\"" in pyproject
    assert "click>=8.1.0" in pyproject
    assert "tabulate>=0.9.0" in pyproject

    readme = (project_root / "README.md").read_text(encoding="utf-8")
    assert "reqmd --check" in readme
    assert "--repo-root" in readme
    assert "--criteria-dir" in readme
    assert "--id-prefix" in readme


def test_REQMD_portability_008_scratch_corpus_runs_from_requirements_dir_without_docs_prefix() -> None:
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
