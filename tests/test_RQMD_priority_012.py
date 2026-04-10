"""Tests for RQMD-PRIORITY-012: Domain and sub-domain priority metadata."""

import json
from pathlib import Path

from click.testing import CliRunner

from rqmd.req_parser import parse_domain_priority_metadata


class TestParseDomainPriorityMetadata:
    def test_no_priority_in_empty_file(self, tmp_path: Path):
        f = tmp_path / "domain.md"
        f.write_text("# Domain\n\n### RQMD-DOM-001: First\n- **Status:** 💡 Proposed\n")
        result = parse_domain_priority_metadata(f)
        assert result["domain_priority"] is None
        assert result["sub_section_priorities"] == {}

    def test_domain_priority_in_preamble(self, tmp_path: Path):
        f = tmp_path / "domain.md"
        f.write_text(
            "# Domain\n"
            "- **Priority:** 🟠 P1 - High\n\n"
            "### RQMD-DOM-001: First\n"
            "- **Status:** 💡 Proposed\n"
        )
        result = parse_domain_priority_metadata(f)
        assert result["domain_priority"] == "🟠 P1 - High"

    def test_subsection_priority(self, tmp_path: Path):
        f = tmp_path / "domain.md"
        f.write_text(
            "# Domain\n\n"
            "## API Subsection\n"
            "- **Priority:** 🟡 P2 - Medium\n\n"
            "### RQMD-DOM-001: First\n"
            "- **Status:** 💡 Proposed\n"
        )
        result = parse_domain_priority_metadata(f)
        assert result["domain_priority"] is None
        assert (
            result["sub_section_priorities"].get("API Subsection") == "🟡 P2 - Medium"
        )

    def test_domain_and_subsection_priorities(self, tmp_path: Path):
        f = tmp_path / "domain.md"
        f.write_text(
            "# Domain\n"
            "- **Priority:** 🔴 P0 - Critical\n\n"
            "## Front End\n"
            "- **Priority:** 🟠 P1 - High\n\n"
            "### RQMD-DOM-001: First\n"
            "- **Status:** 💡 Proposed\n\n"
            "## Backend\n"
            "### RQMD-DOM-002: Second\n"
            "- **Status:** 💡 Proposed\n"
        )
        result = parse_domain_priority_metadata(f)
        assert result["domain_priority"] == "🔴 P0 - Critical"
        assert result["sub_section_priorities"]["Front End"] == "🟠 P1 - High"
        assert result["sub_section_priorities"]["Backend"] is None

    def test_missing_file_returns_empty(self, tmp_path: Path):
        result = parse_domain_priority_metadata(tmp_path / "nonexistent.md")
        assert result["domain_priority"] is None
        assert result["sub_section_priorities"] == {}

    def test_no_priority_in_subsection(self, tmp_path: Path):
        f = tmp_path / "domain.md"
        f.write_text(
            "# Domain\n\n"
            "## Subsection\n\n"
            "### RQMD-DOM-001: First\n"
            "- **Status:** 💡 Proposed\n"
        )
        result = parse_domain_priority_metadata(f)
        assert result["sub_section_priorities"].get("Subsection") is None

    def test_multiple_subsections_each_tracked(self, tmp_path: Path):
        f = tmp_path / "domain.md"
        f.write_text(
            "# Domain\n\n"
            "## Alpha\n"
            "- **Priority:** 🟢 P3 - Low\n\n"
            "### RQMD-DOM-001: Req\n- **Status:** 💡 Proposed\n\n"
            "## Beta\n"
            "- **Priority:** 🔴 P0 - Critical\n\n"
            "### RQMD-DOM-002: Req\n- **Status:** 💡 Proposed\n"
        )
        result = parse_domain_priority_metadata(f)
        assert result["sub_section_priorities"]["Alpha"] == "🟢 P3 - Low"
        assert result["sub_section_priorities"]["Beta"] == "🔴 P0 - Critical"


class TestDomainPriorityInExport:
    def test_domain_priority_in_ai_export(self, tmp_path: Path):
        from rqmd.cli import main as rqmd_main

        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "README.md").write_text("# Index\n")
        (req_dir / "domain.md").write_text(
            "# Domain\n"
            "- **Priority:** 🟠 P1 - High\n\n"
            "### RQMD-DOM-001: First\n"
            "- **Status:** 💡 Proposed\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            rqmd_main,
            [
                "--project-root",
                str(tmp_path),
                "--docs-dir",
                "docs/requirements",
                "--dump-status",
                "proposed",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        file_entry = payload["files"][0]
        assert file_entry["domain_priority"] == "🟠 P1 - High"

    def test_no_domain_priority_absent_from_export(self, tmp_path: Path):
        from rqmd.cli import main as rqmd_main

        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "README.md").write_text("# Index\n")
        (req_dir / "domain.md").write_text(
            "# Domain\n\n" "### RQMD-DOM-001: First\n" "- **Status:** 💡 Proposed\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            rqmd_main,
            [
                "--project-root",
                str(tmp_path),
                "--docs-dir",
                "docs/requirements",
                "--dump-status",
                "proposed",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        file_entry = payload["files"][0]
        assert "domain_priority" not in file_entry

    def test_sub_section_priorities_in_export(self, tmp_path: Path):
        from rqmd.cli import main as rqmd_main

        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True)
        (req_dir / "README.md").write_text("# Index\n")
        (req_dir / "domain.md").write_text(
            "# Domain\n\n"
            "## API\n"
            "- **Priority:** 🟡 P2 - Medium\n\n"
            "### RQMD-DOM-001: First\n"
            "- **Status:** 💡 Proposed\n"
        )
        runner = CliRunner()
        result = runner.invoke(
            rqmd_main,
            [
                "--project-root",
                str(tmp_path),
                "--docs-dir",
                "docs/requirements",
                "--dump-status",
                "proposed",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        file_entry = payload["files"][0]
        assert (
            file_entry.get("sub_section_priorities", {}).get("API") == "🟡 P2 - Medium"
        )
