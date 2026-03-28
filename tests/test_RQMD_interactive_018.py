"""Tests for RQMD-INTERACTIVE-018: Domain-level notes discoverability."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from rqmd.status_update import print_criterion_panel

_TERM_SIZE = MagicMock(columns=120)


def _capture_panel(domain_file, requirement, repo_root):
    output_lines: list[str] = []

    def fake_echo(msg="", **kwargs):
        output_lines.append(str(msg))

    with patch("rqmd.status_update.click.echo", side_effect=fake_echo):
        with patch("rqmd.status_update.shutil.get_terminal_size",
                   return_value=_TERM_SIZE):
            print_criterion_panel(domain_file, requirement, repo_root)

    return "\n".join(output_lines)


class TestPrintCriterionPanelDomainNotes:
    def test_domain_notes_shown_in_panel(self, tmp_path: Path):
        domain_file = tmp_path / "domain.md"
        domain_file.write_text(
            "# Domain\n\n"
            "This is domain context for the implementer.\n\n"
            "### RQMD-DOM-001: Test requirement\n"
            "- **Status:** 💡 Proposed\n"
        )
        requirement = {
            "id": "RQMD-DOM-001",
            "title": "Test requirement",
            "status": "💡 Proposed",
        }

        output = _capture_panel(domain_file, requirement, tmp_path)
        assert "Domain notes:" in output
        assert "This is domain context" in output

    def test_no_domain_notes_when_body_empty(self, tmp_path: Path):
        domain_file = tmp_path / "domain.md"
        domain_file.write_text(
            "# Domain\n\n"
            "### RQMD-DOM-001: Test requirement\n"
            "- **Status:** 💡 Proposed\n"
        )
        requirement = {
            "id": "RQMD-DOM-001",
            "title": "Test requirement",
            "status": "💡 Proposed",
        }

        output = _capture_panel(domain_file, requirement, tmp_path)
        assert "Domain notes:" not in output

    def test_domain_notes_truncated_at_3_lines(self, tmp_path: Path):
        domain_file = tmp_path / "domain.md"
        domain_file.write_text(
            "# Domain\n\n"
            "Line one of domain notes.\n"
            "Line two of domain notes.\n"
            "Line three of domain notes.\n"
            "Line four should be truncated.\n"
            "Line five also.\n\n"
            "### RQMD-DOM-001: Test requirement\n"
            "- **Status:** 💡 Proposed\n"
        )
        requirement = {
            "id": "RQMD-DOM-001",
            "title": "Test requirement",
            "status": "💡 Proposed",
        }

        output = _capture_panel(domain_file, requirement, tmp_path)
        assert "Line one" in output
        assert "Line four" not in output
        assert "…" in output

