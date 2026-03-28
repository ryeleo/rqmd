"""Tests for RQMD-INTERACTIVE-022: Interactive link entry flow."""

from pathlib import Path
from unittest.mock import patch

import pytest

from rqmd.req_parser import parse_requirements
from rqmd.status_update import (
    _add_link_to_file,
    _remove_link_from_file,
    prompt_for_links_flow,
)
from rqmd.workflows import _build_requirement_field_menu, ENTRY_FIELDS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_req_file(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "domain.md"
    p.write_text(body, encoding="utf-8")
    return p


def _parse_first_req(path: Path) -> dict:
    reqs = parse_requirements(path)
    assert reqs, f"No requirements found in {path}"
    return reqs[0]


# ---------------------------------------------------------------------------
# ENTRY_FIELDS
# ---------------------------------------------------------------------------

class TestEntryFields:
    def test_links_in_entry_fields(self):
        assert "links" in ENTRY_FIELDS

    def test_entry_fields_order(self):
        # links must come after flagged so the cycle is: status → priority → flagged → links
        idx_flagged = ENTRY_FIELDS.index("flagged")
        idx_links = ENTRY_FIELDS.index("links")
        assert idx_links == idx_flagged + 1


# ---------------------------------------------------------------------------
# _build_requirement_field_menu
# ---------------------------------------------------------------------------

class TestBuildRequirementFieldMenuLinks:
    def _req(self, links=None) -> dict:
        return {"id": "RQMD-LINK-001", "links": links or []}

    def test_returns_links_title(self):
        title, labels, options, current_index, bg = _build_requirement_field_menu(
            self._req(), active_field="links"
        )
        assert "links" in title.lower()
        assert "RQMD-LINK-001" in title

    def test_returns_manage_label(self):
        _, labels, options, _, _ = _build_requirement_field_menu(
            self._req(), active_field="links"
        )
        assert labels == ["manage"]

    def test_no_links_shows_no_links(self):
        _, _, options, _, _ = _build_requirement_field_menu(
            self._req(links=[]), active_field="links"
        )
        assert "no links" in options[0]

    def test_single_link_singular(self):
        links = [{"url": "https://example.com", "label": None}]
        _, _, options, _, _ = _build_requirement_field_menu(
            self._req(links=links), active_field="links"
        )
        assert "1 link" in options[0]
        assert "1 links" not in options[0]

    def test_multiple_links_plural(self):
        links = [
            {"url": "https://a.com", "label": None},
            {"url": "https://b.com", "label": None},
        ]
        _, _, options, _, _ = _build_requirement_field_menu(
            self._req(links=links), active_field="links"
        )
        assert "2 links" in options[0]

    def test_current_index_is_none(self):
        _, _, _, current_index, _ = _build_requirement_field_menu(
            self._req(), active_field="links"
        )
        assert current_index is None


# ---------------------------------------------------------------------------
# _add_link_to_file
# ---------------------------------------------------------------------------

class TestAddLinkToFile:
    def test_creates_links_section_when_absent(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n- **Status:** 💡 Proposed\n",
        )
        req = _parse_first_req(path)
        _add_link_to_file(path, req, "https://example.com")
        content = path.read_text(encoding="utf-8")
        assert "- **Links:**" in content
        assert "  - https://example.com" in content

    def test_appends_to_existing_links_section(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n"
            "- **Status:** 💡 Proposed\n"
            "- **Links:**\n"
            "  - https://first.com\n",
        )
        req = _parse_first_req(path)
        _add_link_to_file(path, req, "https://second.com")
        content = path.read_text(encoding="utf-8")
        assert "  - https://first.com" in content
        assert "  - https://second.com" in content

    def test_markdown_link_stored_verbatim(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n- **Status:** 💡 Proposed\n",
        )
        req = _parse_first_req(path)
        _add_link_to_file(path, req, "[My Label](https://example.com)")
        content = path.read_text(encoding="utf-8")
        assert "  - [My Label](https://example.com)" in content

    def test_does_nothing_when_no_metadata_anchor(self, tmp_path: Path):
        """If there's no status_line or other anchor, _add_link_to_file is a no-op."""
        path = _make_req_file(tmp_path, "# Domain\n\n### RQMD-LINK-001: Item\n")
        req = {"id": "RQMD-LINK-001"}  # no status_line
        _add_link_to_file(path, req, "https://example.com")
        content = path.read_text(encoding="utf-8")
        assert "https://example.com" not in content


# ---------------------------------------------------------------------------
# _remove_link_from_file
# ---------------------------------------------------------------------------

class TestRemoveLinkFromFile:
    def test_removes_link_by_index(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n"
            "- **Status:** 💡 Proposed\n"
            "- **Links:**\n"
            "  - https://first.com\n"
            "  - https://second.com\n",
        )
        req = _parse_first_req(path)
        _remove_link_from_file(path, req, 0)
        content = path.read_text(encoding="utf-8")
        assert "https://first.com" not in content
        assert "https://second.com" in content
        assert "- **Links:**" in content  # header stays when items remain

    def test_removes_header_when_last_link_removed(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n"
            "- **Status:** 💡 Proposed\n"
            "- **Links:**\n"
            "  - https://only.com\n",
        )
        req = _parse_first_req(path)
        _remove_link_from_file(path, req, 0)
        content = path.read_text(encoding="utf-8")
        assert "https://only.com" not in content
        assert "- **Links:**" not in content

    def test_noop_when_no_links_section(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n- **Status:** 💡 Proposed\n",
        )
        req = _parse_first_req(path)
        original = path.read_text(encoding="utf-8")
        _remove_link_from_file(path, req, 0)
        assert path.read_text(encoding="utf-8") == original

    def test_noop_on_out_of_range_index(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n"
            "- **Status:** 💡 Proposed\n"
            "- **Links:**\n"
            "  - https://only.com\n",
        )
        req = _parse_first_req(path)
        original = path.read_text(encoding="utf-8")
        _remove_link_from_file(path, req, 5)
        assert path.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# prompt_for_links_flow
# ---------------------------------------------------------------------------

class TestPromptForLinksFlow:
    def test_empty_input_returns_false(self, tmp_path: Path):
        """Pressing Enter immediately (empty input) → no changes, returns False."""
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n- **Status:** 💡 Proposed\n",
        )
        req = _parse_first_req(path)
        with patch("rqmd.status_update.click.prompt", return_value=""):
            result = prompt_for_links_flow(path, req)
        assert result is False

    def test_adding_plain_url_without_label(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n- **Status:** 💡 Proposed\n",
        )
        req = _parse_first_req(path)
        # Prompt side_effect: URL → then label (skip) → then empty (exit)
        with patch("rqmd.status_update.click.prompt", side_effect=["https://example.com", "", ""]):
            result = prompt_for_links_flow(path, req)
        assert result is True
        content = path.read_text(encoding="utf-8")
        assert "https://example.com" in content

    def test_adding_plain_url_with_label(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n- **Status:** 💡 Proposed\n",
        )
        req = _parse_first_req(path)
        with patch("rqmd.status_update.click.prompt", side_effect=["https://example.com", "My Label", ""]):
            result = prompt_for_links_flow(path, req)
        assert result is True
        content = path.read_text(encoding="utf-8")
        assert "[My Label](https://example.com)" in content

    def test_adding_markdown_link_skips_label_prompt(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n- **Status:** 💡 Proposed\n",
        )
        req = _parse_first_req(path)
        # markdown link → no label prompt should fire → then empty exit
        with patch("rqmd.status_update.click.prompt", side_effect=["[Spec](https://spec.example.com)", ""]) as mock_prompt:
            result = prompt_for_links_flow(path, req)
        assert result is True
        # Only 2 prompt calls: the link entry and the exit
        assert mock_prompt.call_count == 2
        content = path.read_text(encoding="utf-8")
        assert "[Spec](https://spec.example.com)" in content

    def test_removing_link_by_number(self, tmp_path: Path):
        path = _make_req_file(
            tmp_path,
            "# Domain\n\n### RQMD-LINK-001: Item\n"
            "- **Status:** 💡 Proposed\n"
            "- **Links:**\n"
            "  - https://remove-me.com\n",
        )
        req = _parse_first_req(path)
        with patch("rqmd.status_update.click.prompt", side_effect=["1", ""]):
            result = prompt_for_links_flow(path, req)
        assert result is True
        content = path.read_text(encoding="utf-8")
        assert "https://remove-me.com" not in content
