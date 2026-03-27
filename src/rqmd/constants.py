from __future__ import annotations

import re

SUMMARY_START = "<!-- acceptance-status-summary:start -->"
SUMMARY_END = "<!-- acceptance-status-summary:end -->"
DEFAULT_ID_PREFIXES = ("AC", "R", "RQMD")
DEFAULT_REQUIREMENTS_DIR = "docs/requirements"
REQUIREMENTS_INDEX_NAME = "README.md"
JSON_SCHEMA_VERSION = "1.0.0"

STATUS_ORDER = [
    ("💡 Proposed", "proposed"),
    ("🔧 Implemented", "implemented"),
    ("✅ Verified", "verified"),
    ("⛔ Blocked", "blocked"),
    ("🗑️ Deprecated", "deprecated"),
]
STATUS_TERSE_HEADERS_ASCII = ["P", "I", "Ver", "Blk", "Dep"]
STATUS_ALIASES = {
    "✅ Done": "✅ Verified",
}
STATUS_PARSE_ALIASES = {
    "proposal": "💡 Proposed",
    "propose": "💡 Proposed",
}

PRIORITY_ORDER = [
    ("🔴 P0 - Critical", "p0"),
    ("🟠 P1 - High", "p1"),
    ("🟡 P2 - Medium", "p2"),
    ("🟢 P3 - Low", "p3"),
]
PRIORITY_ALIASES = {}
PRIORITY_PARSE_ALIASES = {
    "critical": "🔴 P0 - Critical",
    "p0": "🔴 P0 - Critical",
    "high": "🟠 P1 - High",
    "p1": "🟠 P1 - High",
    "medium": "🟡 P2 - Medium",
    "p2": "🟡 P2 - Medium",
    "low": "🟢 P3 - Low",
    "p3": "🟢 P3 - Low",
}

MENU_UP = "u"
MENU_QUIT = "q"
MENU_NEXT = "n"
MENU_PREV = "p"
MENU_TOGGLE_SORT = "s"
MENU_TOGGLE_DIRECTION = "d"
MENU_REFRESH = "r"
MENU_PAGE_SIZE = 9

# H2 subsection header pattern — optional organizational structure within domain files
# Matches: ## Some Subsection Title
H2_SUBSECTION_PATTERN = re.compile(r"^##\s+(?P<section_title>.+?)\s*$", re.MULTILINE)

STATUS_PATTERN = re.compile(r"^- \*\*Status:\*\* (?P<status>.+?)\s*$", re.MULTILINE)
PRIORITY_PATTERN = re.compile(r"^- \*\*Priority:\*\* (?P<priority>.+?)\s*$", re.MULTILINE)
BLOCKED_REASON_PATTERN = re.compile(r"^\*\*Blocked:\*\*\s*(.+?)\s*$", re.MULTILINE)
DEPRECATED_REASON_PATTERN = re.compile(r"^\*\*Deprecated:\*\*\s*(.+?)\s*$", re.MULTILINE)
FLAGGED_PATTERN = re.compile(r"^- \*\*Flagged:\*\* (?P<flagged>true|false)\s*$", re.MULTILINE)
LINKS_HEADER_PATTERN = re.compile(r"^- \*\*Links:\*\*\s*$", re.MULTILINE)
LINK_ITEM_PATTERN = re.compile(r"^  - (?P<link_text>.+)$", re.MULTILINE)
ID_PREFIX_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*$")
GENERIC_REQUIREMENT_HEADER_PATTERN = re.compile(
    r"^###\s+(?P<id>(?P<prefix>[A-Z][A-Z0-9]*)-[A-Z0-9-]+):\s*(?P<title>.+?)\s*$"
)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)#?]+\.md)(?:#[^)]+)?\)")
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
NON_ALNUM_PREFIX_PATTERN = re.compile(r"^[^a-zA-Z0-9]+")
NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")

ANSI_RESET = "\x1b[0m"
ZEBRA_BG = "\x1b[48;5;254m"
# Fixed 256-color purple for Proposed status; avoids theme-dependent drift.
PROPOSED_FG = "\x1b[38;5;135m"
