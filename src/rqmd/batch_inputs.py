"""Parse and validate batch input files for requirement status/priority updates.

This module handles parsing of various batch input formats (JSONL, CSV, TSV)
for non-interactive bulk requirement updates. It provides functions to parse
individual --update entries as well as batch files, with comprehensive validation
of input structure and allowed values.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: 'click' package is required.", file=sys.stderr)
    print("Install with: pip3 install click", file=sys.stderr)
    sys.exit(1)


def parse_set_entry(entry: str) -> tuple[str, str]:
    """Parse a single --update command-line entry into criterion ID and status.

    Args:
        entry: A string in format 'ID=STATUS' (e.g., 'AC-001=verified').

    Returns:
        A tuple of (requirement_id, status).

    Raises:
        click.ClickException: If entry is malformed or missing required parts.
    """
    raw = entry.strip()
    if "=" not in raw:
        raise click.ClickException(
            f"Invalid --update value '{entry}'. Expected format ID=STATUS."
        )

    requirement_id, status = raw.split("=", 1)
    requirement_id = requirement_id.strip()
    status = status.strip()
    if not requirement_id or not status:
        raise click.ClickException(
            f"Invalid --update value '{entry}'. Expected format ID=STATUS."
        )

    return requirement_id, status


def parse_set_priority_entry(entry: str) -> tuple[str, str]:
    """Parse a single --update-priority command-line entry into criterion ID and priority.

    Args:
        entry: A string in format 'ID=PRIORITY' (e.g., 'AC-001=p0').

    Returns:
        A tuple of (requirement_id, priority).

    Raises:
        click.ClickException: If entry is malformed or missing required parts.
    """
    raw = entry.strip()
    if "=" not in raw:
        raise click.ClickException(
            f"Invalid --update-priority value '{entry}'. Expected format ID=PRIORITY."
        )

    requirement_id, priority = raw.split("=", 1)
    requirement_id = requirement_id.strip()
    priority = priority.strip()
    if not requirement_id or not priority:
        raise click.ClickException(
            f"Invalid --update-priority value '{entry}'. Expected format ID=PRIORITY."
        )

    return requirement_id, priority


def parse_set_flagged_entry(entry: str) -> tuple[str, bool]:
    """Parse a single --update-flagged command-line entry into criterion ID and boolean.

    Args:
        entry: A string in format 'ID=true|false' (e.g., 'AC-001=true').

    Returns:
        A tuple of (requirement_id, flagged_bool).

    Raises:
        click.ClickException: If entry is malformed or flagged value is not 'true'/'false'.
    """
    raw = entry.strip()
    if "=" not in raw:
        raise click.ClickException(
            f"Invalid --update-flagged value '{entry}'. Expected format ID=true|false."
        )

    requirement_id, flagged_raw = raw.split("=", 1)
    requirement_id = requirement_id.strip()
    flagged_value = flagged_raw.strip().lower()
    if not requirement_id or flagged_value not in {"true", "false"}:
        raise click.ClickException(
            f"Invalid --update-flagged value '{entry}'. Expected format ID=true|false."
        )

    return requirement_id, flagged_value == "true"


def parse_batch_update_file(repo_root: Path, file_path_input: str) -> list[dict[str, str | None]]:
    """Load and parse a batch update file (JSONL, CSV, or TSV).

    Automatically detects file format based on file extension and delegates to the
    appropriate parser (parse_batch_update_jsonl or parse_batch_update_csv).

    Args:
        repo_root: Root path of the project (for resolving relative paths).
        file_path_input: Path to the batch file (absolute or repo-relative).

    Returns:
        A list of update dictionaries, each containing requirement_id and optional
        status, priority, flagged, file, blocked_reason, and deprecated_reason.

    Raises:
        click.ClickException: If file not found, unsupported format, or invalid content.
    """
    path = Path(file_path_input)
    if not path.is_absolute():
        path = (repo_root / file_path_input).resolve()

    if not path.exists() or not path.is_file():
        raise click.ClickException(f"--update-file path not found: {file_path_input}")

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return parse_batch_update_jsonl(path)
    if suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        return parse_batch_update_csv(path, delimiter=delimiter)

    raise click.ClickException("--update-file must end with .jsonl, .csv, or .tsv")


def parse_batch_update_jsonl(path: Path) -> list[dict[str, str | None]]:
    """Parse JSONL (JSON Lines) batch update file.

    Each line should be a JSON object with keys like:
    - requirement_id/requirement_id/id/req_id/r_id: The requirement identifier (required)
    - status: New status value (optional)
    - priority: New priority value (optional)
    - flagged: Boolean flag value 'true' or 'false' (optional)
    - file: Filter criterion to this file only (optional)
    - blocked_reason, deprecated_reason: Additional metadata (optional)

    Args:
        path: Path to the JSONL file.

    Returns:
        A list of update dictionaries.

    Raises:
        click.ClickException: If JSON is invalid, rows malformed, or no valid updates found.
    """
    updates: list[dict[str, str | None]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue

            try:
                record = json.loads(text)
            except json.JSONDecodeError as exc:
                raise click.ClickException(
                    f"Invalid JSONL at {path}:{line_number}: {exc.msg}"
                ) from exc

            if not isinstance(record, dict):
                raise click.ClickException(
                    f"Invalid JSONL object at {path}:{line_number}: expected object"
                )

            requirement_id = str(
                record.get("requirement_id")
                or record.get("requirement_id")
                or record.get("id")
                or record.get("req_id")
                or record.get("r_id")
                or ""
            ).strip()
            status = str(record.get("status") or "").strip() or None
            priority = str(record.get("priority") or "").strip() or None
            flagged_value = str(record.get("flagged") or "").strip().lower() or None
            if flagged_value is not None and flagged_value not in {"true", "false"}:
                raise click.ClickException(
                    f"Invalid JSONL row at {path}:{line_number}: flagged must be true or false"
                )
            flagged = (flagged_value == "true") if flagged_value is not None else None

            if not requirement_id or (status is None and priority is None and flagged is None):
                raise click.ClickException(
                    f"Invalid JSONL row at {path}:{line_number}: requires requirement_id/requirement_id/id/req_id/r_id and at least one of status, priority, or flagged"
                )

            file_filter = str(record.get("file") or "").strip() or None
            blocked_reason = str(record.get("blocked_reason") or "").strip() or None
            deprecated_reason = str(record.get("deprecated_reason") or "").strip() or None

            updates.append(
                {
                    "requirement_id": requirement_id,
                    "status": status,
                    "priority": priority,
                    "flagged": flagged,
                    "file": file_filter,
                    "blocked_reason": blocked_reason,
                    "deprecated_reason": deprecated_reason,
                }
            )

    if not updates:
        raise click.ClickException(f"--update-file contains no update rows: {path}")

    return updates


def parse_batch_update_csv(path: Path, delimiter: str = ",") -> list[dict[str, str | None]]:
    """Parse CSV or TSV batch update file using DictReader.

    Expected header columns (case-insensitive, flexible):
    - requirement_id/requirement_id/id/req_id/r_id: The requirement identifier (required)
    - status: New status value (optional)
    - priority: New priority value (optional)
    - flagged: Boolean 'true' or 'false' (optional)
    - file: Filter criterion to this file only (optional)
    - blocked_reason, deprecated_reason: Additional metadata (optional)

    Args:
        path: Path to the CSV or TSV file.
        delimiter: Field delimiter (default: ',' for CSV; '\\t' for TSV).

    Returns:
        A list of update dictionaries.

    Raises:
        click.ClickException: If file is malformed, header missing, or no valid updates found.
    """
    updates: list[dict[str, str | None]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise click.ClickException(f"Invalid CSV/TSV at {path}: missing header row")

        for line_number, row in enumerate(reader, start=2):
            requirement_id = str(
                row.get("requirement_id")
                or row.get("requirement_id")
                or row.get("id")
                or row.get("req_id")
                or row.get("r_id")
                or ""
            ).strip()
            status = str(row.get("status") or "").strip() or None
            priority = str(row.get("priority") or "").strip() or None
            flagged_value = str(row.get("flagged") or "").strip().lower() or None
            if flagged_value is not None and flagged_value not in {"true", "false"}:
                raise click.ClickException(
                    f"Invalid CSV/TSV row at {path}:{line_number}: flagged must be true or false"
                )
            flagged = (flagged_value == "true") if flagged_value is not None else None

            if not requirement_id or (status is None and priority is None and flagged is None):
                raise click.ClickException(
                    f"Invalid CSV/TSV row at {path}:{line_number}: requires requirement_id/requirement_id/id/req_id/r_id and at least one of status, priority, or flagged columns"
                )

            file_filter = str(row.get("file") or "").strip() or None
            blocked_reason = str(row.get("blocked_reason") or "").strip() or None
            deprecated_reason = str(row.get("deprecated_reason") or "").strip() or None

            updates.append(
                {
                    "requirement_id": requirement_id,
                    "status": status,
                    "priority": priority,
                    "flagged": flagged,
                    "file": file_filter,
                    "blocked_reason": blocked_reason,
                    "deprecated_reason": deprecated_reason,
                }
            )

    if not updates:
        raise click.ClickException(f"--update-file contains no update rows: {path}")

    return updates
