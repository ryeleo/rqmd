from __future__ import annotations

import re

SUMMARY_START = "<!-- acceptance-status-summary:start -->"
SUMMARY_END = "<!-- acceptance-status-summary:end -->"
DEFAULT_ID_PREFIXES = ("AC", "R", "RQMD")
DEFAULT_CRITERIA_DIR = "docs/requirements"
REQUIREMENTS_INDEX_NAME = "README.md"

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

MENU_UP = "u"
MENU_QUIT = "q"
MENU_NEXT = "n"
MENU_PREV = "p"
MENU_TOGGLE_SORT = "s"
MENU_PAGE_SIZE = 9

STATUS_PATTERN = re.compile(r"^- \*\*Status:\*\* (?P<status>.+?)\s*$", re.MULTILINE)
BLOCKED_REASON_PATTERN = re.compile(r"^\*\*Blocked:\*\*\s*(.+?)\s*$", re.MULTILINE)
DEPRECATED_REASON_PATTERN = re.compile(r"^\*\*Deprecated:\*\*\s*(.+?)\s*$", re.MULTILINE)
ID_PREFIX_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*$")
GENERIC_CRITERION_HEADER_PATTERN = re.compile(
    r"^###\s+(?P<id>(?P<prefix>[A-Z][A-Z0-9]*)-[A-Z0-9-]+):\s*(?P<title>.+?)\s*$"
)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\((?P<target>[^)#?]+\.md)(?:#[^)]+)?\)")
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
NON_ALNUM_PREFIX_PATTERN = re.compile(r"^[^a-zA-Z0-9]+")
NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")

ANSI_RESET = "\x1b[0m"
ZEBRA_BG = "\x1b[48;5;236m"
# Fixed 256-color purple for Proposed status; avoids theme-dependent drift.
PROPOSED_FG = "\x1b[38;5;135m"
