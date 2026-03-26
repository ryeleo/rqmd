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
    raw = entry.strip()
    if "=" not in raw:
        raise click.ClickException(
            f"Invalid --set value '{entry}'. Expected format ID=STATUS."
        )

    criterion_id, status = raw.split("=", 1)
    criterion_id = criterion_id.strip()
    status = status.strip()
    if not criterion_id or not status:
        raise click.ClickException(
            f"Invalid --set value '{entry}'. Expected format ID=STATUS."
        )

    return criterion_id, status


def parse_batch_update_file(repo_root: Path, file_path_input: str) -> list[dict[str, str | None]]:
    path = Path(file_path_input)
    if not path.is_absolute():
        path = (repo_root / file_path_input).resolve()

    if not path.exists() or not path.is_file():
        raise click.ClickException(f"--set-file path not found: {file_path_input}")

    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return parse_batch_update_jsonl(path)
    if suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        return parse_batch_update_csv(path, delimiter=delimiter)

    raise click.ClickException("--set-file must end with .jsonl, .csv, or .tsv")


def parse_batch_update_jsonl(path: Path) -> list[dict[str, str | None]]:
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

            criterion_id = str(
                record.get("criterion_id")
                or record.get("requirement_id")
                or record.get("id")
                or record.get("ac_id")
                or record.get("r_id")
                or ""
            ).strip()
            status = str(record.get("status") or "").strip()
            if not criterion_id or not status:
                raise click.ClickException(
                    f"Invalid JSONL row at {path}:{line_number}: requires criterion_id/requirement_id/id/ac_id/r_id and status"
                )

            file_filter = str(record.get("file") or "").strip() or None
            blocked_reason = str(record.get("blocked_reason") or "").strip() or None
            deprecated_reason = str(record.get("deprecated_reason") or "").strip() or None

            updates.append(
                {
                    "criterion_id": criterion_id,
                    "status": status,
                    "file": file_filter,
                    "blocked_reason": blocked_reason,
                    "deprecated_reason": deprecated_reason,
                }
            )

    if not updates:
        raise click.ClickException(f"--set-file contains no update rows: {path}")

    return updates


def parse_batch_update_csv(path: Path, delimiter: str = ",") -> list[dict[str, str | None]]:
    updates: list[dict[str, str | None]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if reader.fieldnames is None:
            raise click.ClickException(f"Invalid CSV/TSV at {path}: missing header row")

        for line_number, row in enumerate(reader, start=2):
            criterion_id = str(
                row.get("criterion_id")
                or row.get("requirement_id")
                or row.get("id")
                or row.get("ac_id")
                or row.get("r_id")
                or ""
            ).strip()
            status = str(row.get("status") or "").strip()
            if not criterion_id or not status:
                raise click.ClickException(
                    f"Invalid CSV/TSV row at {path}:{line_number}: requires criterion_id/requirement_id/id/ac_id/r_id and status columns"
                )

            file_filter = str(row.get("file") or "").strip() or None
            blocked_reason = str(row.get("blocked_reason") or "").strip() or None
            deprecated_reason = str(row.get("deprecated_reason") or "").strip() or None

            updates.append(
                {
                    "criterion_id": criterion_id,
                    "status": status,
                    "file": file_filter,
                    "blocked_reason": blocked_reason,
                    "deprecated_reason": deprecated_reason,
                }
            )

    if not updates:
        raise click.ClickException(f"--set-file contains no update rows: {path}")

    return updates
