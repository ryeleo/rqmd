"""Persistent history backend for rqmd undo/redo operations."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HISTORY_ROOT_RELATIVE = Path(".rqmd/history")
HISTORY_REPO_RELATIVE = HISTORY_ROOT_RELATIVE / "rqmd-history"
STATE_FILE_RELATIVE = HISTORY_ROOT_RELATIVE / "state.json"
CATALOG_DIRNAME = "catalog"


class HistoryInitError(Exception):
    """Raised when the history repository cannot be initialized."""


class HistoryCommitError(Exception):
    """Raised when a snapshot cannot be committed to history."""


class HistoryRestoreError(Exception):
    """Raised when a historical snapshot cannot be restored."""


class HistoryManager:
    """Manage persistent catalog snapshots in a local hidden git repository."""

    def __init__(self, repo_root: Path | str = ".", requirements_dir: Path | str = "docs/requirements"):
        self.repo_root = Path(repo_root).resolve()
        self.requirements_dir = self._normalize_requirements_dir(requirements_dir)
        self.history_root = self.repo_root / HISTORY_ROOT_RELATIVE
        self.repo_dir = self.repo_root / HISTORY_REPO_RELATIVE
        self.state_path = self.repo_root / STATE_FILE_RELATIVE
        self.catalog_dir = self.repo_dir / CATALOG_DIRNAME

    def _normalize_requirements_dir(self, requirements_dir: Path | str) -> Path:
        path = Path(requirements_dir)
        if path.is_absolute():
            try:
                return path.resolve().relative_to(self.repo_root)
            except ValueError as exc:
                raise HistoryInitError(
                    f"Requirements dir must be inside repo root: {path}"
                ) from exc
        return path

    def _git(self, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.setdefault("GIT_AUTHOR_NAME", "rqmd")
        env.setdefault("GIT_AUTHOR_EMAIL", "rqmd@local")
        env.setdefault("GIT_COMMITTER_NAME", env["GIT_AUTHOR_NAME"])
        env.setdefault("GIT_COMMITTER_EMAIL", env["GIT_AUTHOR_EMAIL"])
        try:
            return subprocess.run(
                ["git", *args],
                cwd=self.repo_dir,
                input=input_text,
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            raise HistoryCommitError(message) from exc

    def _default_state(self) -> dict[str, Any]:
        return {
            "version": "2.0",
            "requirements_dir": self.requirements_dir.as_posix(),
            "entries": [],
            "cursor": -1,
            "branches": {"main": {"head": None, "label": "Main timeline"}},
            "current_branch": "main",
        }

    def _write_state(self, state: dict[str, Any]) -> None:
        self.history_root.mkdir(parents=True, exist_ok=True)
        with self.state_path.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return self._default_state()
        with self.state_path.open("r", encoding="utf-8") as handle:
            state = json.load(handle)
        if "entries" not in state or "cursor" not in state:
            return self._default_state()
        state.setdefault("requirements_dir", self.requirements_dir.as_posix())
        state.setdefault("version", "1.0")
        return state

    def _snapshot_source_files(self) -> list[Path]:
        requirements_root = (self.repo_root / self.requirements_dir).resolve()
        if not requirements_root.exists():
            return []
        return sorted(path for path in requirements_root.rglob("*.md") if path.is_file())

    def _replace_catalog_snapshot(self) -> list[str]:
        if self.catalog_dir.exists():
            shutil.rmtree(self.catalog_dir)
        self.catalog_dir.mkdir(parents=True, exist_ok=True)

        snapshot_files: list[str] = []
        for source_path in self._snapshot_source_files():
            relative_path = source_path.relative_to(self.repo_root)
            snapshot_files.append(relative_path.as_posix())
            target_path = self.catalog_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)
        return snapshot_files

    def _snapshot_files_from_checkout(self) -> list[str]:
        if not self.catalog_dir.exists():
            return []
        return sorted(
            path.relative_to(self.catalog_dir).as_posix()
            for path in self.catalog_dir.rglob("*.md")
            if path.is_file()
        )

    def _restore_commit(self, commit_hash: str) -> list[str]:
        try:
            self._git("checkout", "--force", commit_hash)
        except HistoryCommitError as exc:
            raise HistoryRestoreError(f"Failed to checkout history commit {commit_hash}: {exc}") from exc

        requirements_root = self.repo_root / self.requirements_dir
        current_files = []
        if requirements_root.exists():
            current_files = [
                path.relative_to(self.repo_root).as_posix()
                for path in requirements_root.rglob("*.md")
                if path.is_file()
            ]

        snapshot_files = self._snapshot_files_from_checkout()
        snapshot_set = set(snapshot_files)

        for relative_path in current_files:
            if relative_path not in snapshot_set:
                (self.repo_root / relative_path).unlink(missing_ok=True)

        for relative_path in snapshot_files:
            source_path = self.catalog_dir / relative_path
            target_path = self.repo_root / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, target_path)

        return snapshot_files

    def _build_commit_message(
        self,
        command: str,
        actor: str,
        reason: str | None,
        snapshot_files: list[str],
    ) -> str:
        metadata = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "command": command,
            "reason": reason,
            "requirements_dir": self.requirements_dir.as_posix(),
            "files": snapshot_files,
        }
        title = command
        if reason:
            title = f"{command}: {reason}"
        return title + "\n\n[rqmd-metadata]\n" + json.dumps(metadata, ensure_ascii=False, indent=2)

    def _ensure_initialized(self) -> bool:
        existed = (self.repo_dir / ".git").exists() and self.state_path.exists()
        self.history_root.mkdir(parents=True, exist_ok=True)
        if existed:
            return True

        self.repo_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                ["git", "init"],
                cwd=self.repo_dir,
                text=True,
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            raise HistoryInitError(f"Failed to initialize history repository: {message}") from exc

        gitignore_path = self.repo_dir / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text("audit.jsonl\n", encoding="utf-8")

        if not self.state_path.exists():
            self._write_state(self._default_state())

        return False

    def list_entries(self) -> list[dict[str, Any]]:
        return list(self._read_state().get("entries", []))

    def resolve_ref(self, ref: str) -> dict[str, Any] | None:
        normalized = ref.strip()
        if not normalized:
            return None

        entries = self.list_entries()
        if not entries:
            return None

        if normalized.lower() in {"head", "current"}:
            cursor = int(self._read_state().get("cursor", -1))
            if 0 <= cursor < len(entries):
                return dict(entries[cursor], entry_index=cursor)
            return None

        if normalized.isdigit():
            index = int(normalized)
            if 0 <= index < len(entries):
                return dict(entries[index], entry_index=index)
            return None

        for index, entry in enumerate(entries):
            commit = str(entry.get("commit") or "")
            if commit == normalized or commit.startswith(normalized):
                return dict(entry, entry_index=index)
        return None

    def list_snapshot_files(self, commit_hash: str) -> list[str]:
        result = self._git("ls-tree", "-r", "--name-only", commit_hash, CATALOG_DIRNAME)
        prefix = f"{CATALOG_DIRNAME}/"
        files: list[str] = []
        for line in result.stdout.splitlines():
            item = line.strip()
            if not item.startswith(prefix):
                continue
            files.append(item[len(prefix):])
        return sorted(files)

    def read_snapshot_file(self, commit_hash: str, relative_path: str) -> str:
        git_path = f"{commit_hash}:{CATALOG_DIRNAME}/{relative_path}"
        return self._git("show", git_path).stdout

    def materialize_snapshot(self, commit_hash: str, target_root: Path | str) -> list[Path]:
        target = Path(target_root)
        materialized: list[Path] = []
        for relative_path in self.list_snapshot_files(commit_hash):
            destination = target / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                self.read_snapshot_file(commit_hash, relative_path),
                encoding="utf-8",
            )
            materialized.append(destination)
        return materialized

    def materialize_snapshot_tempdir(self, commit_hash: str) -> tempfile.TemporaryDirectory[str]:
        tempdir = tempfile.TemporaryDirectory()
        self.materialize_snapshot(commit_hash, Path(tempdir.name))
        return tempdir

    def get_current_head(self) -> str | None:
        state = self._read_state()
        entries = state.get("entries", [])
        cursor = int(state.get("cursor", -1))
        if cursor < 0 or cursor >= len(entries):
            return None
        return str(entries[cursor]["commit"])

    def can_undo(self) -> bool:
        return int(self._read_state().get("cursor", -1)) > 0

    def can_redo(self) -> bool:
        state = self._read_state()
        entries = state.get("entries", [])
        cursor = int(state.get("cursor", -1))
        return 0 <= cursor < len(entries) - 1

    def capture(self, command: str, actor: str = "rqmd", reason: str | None = None) -> str:
        self._ensure_initialized()
        state = self._read_state()
        entries = list(state.get("entries", []))
        cursor = int(state.get("cursor", -1))
        
        # Detect divergence: if cursor < len(entries)-1, we're branching from an old point
        diverging = cursor < len(entries) - 1
        parent_commit: str | None = None
        branch_point_commit: str | None = None
        new_branch: str | None = None
        
        if diverging:
            # Save the old branch head before truncating
            if entries:
                branch_point_commit = str(entries[cursor]["commit"])
                parent_commit = str(entries[cursor]["commit"])
            entries = entries[: cursor + 1]
            # Generate new branch name
            timestamp_label = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            new_branch = f"recovery-{timestamp_label}"
        else:
            parent_commit = str(entries[cursor]["commit"]) if entries else None
        
        snapshot_files = self._replace_catalog_snapshot()
        entry_path = self.repo_dir / "entry.json"
        entry_payload = {
            "command": command,
            "actor": actor,
            "reason": reason,
            "files": snapshot_files,
            "requirements_dir": self.requirements_dir.as_posix(),
        }
        entry_path.write_text(json.dumps(entry_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        self._git("add", "-A")
        self._git("commit", "--allow-empty", "-m", self._build_commit_message(command, actor, reason, snapshot_files))
        commit_hash = self._git("rev-parse", "HEAD").stdout.strip()

        new_entry: dict[str, Any] = {
            "commit": commit_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "actor": actor,
            "reason": reason,
            "files": snapshot_files,
            "parent_commit": parent_commit,
            "branch": "main" if not new_branch else new_branch,
            "branch_point": branch_point_commit,
        }
        entries.append(new_entry)
        state["entries"] = entries
        state["cursor"] = len(entries) - 1
        state["requirements_dir"] = self.requirements_dir.as_posix()
        state.setdefault("branches", {})
        state.setdefault("current_branch", "main")
        
        # Track branch heads in state
        if new_branch:
            state["branches"][new_branch] = {"head": commit_hash, "label": f"Alternate timeline starting at {timestamp_label}"}
            state["current_branch"] = new_branch
        else:
            current_branch = state.get("current_branch", "main")
            state["branches"][current_branch]["head"] = commit_hash
        
        state.setdefault("version", "2.0")
        self._write_state(state)
        return commit_hash

    def undo(self) -> str | None:
        self._ensure_initialized()
        state = self._read_state()
        entries = state.get("entries", [])
        cursor = int(state.get("cursor", -1))
        if cursor <= 0 or not entries:
            return None

        cursor -= 1
        commit_hash = str(entries[cursor]["commit"])
        self._restore_commit(commit_hash)
        state["cursor"] = cursor
        self._write_state(state)
        return commit_hash

    def redo(self) -> str | None:
        self._ensure_initialized()
        state = self._read_state()
        entries = state.get("entries", [])
        cursor = int(state.get("cursor", -1))
        if cursor >= len(entries) - 1:
            return None

        cursor += 1
        commit_hash = str(entries[cursor]["commit"])
        self._restore_commit(commit_hash)
        state["cursor"] = cursor
        self._write_state(state)
        return commit_hash

    def get_timeline_graph(self) -> dict[str, Any]:
        """Reconstruct the DAG of history entries with branch information."""
        state = self._read_state()
        entries = state.get("entries", [])
        branches = state.get("branches", {})
        cursor = int(state.get("cursor", -1))
        current_branch = state.get("current_branch", "main")
        
        # Build nodes indexed by commit hash
        nodes: dict[str, dict[str, Any]] = {}
        for index, entry in enumerate(entries):
            commit = str(entry.get("commit", ""))
            nodes[commit] = {
                "entry_index": index,
                "commit": commit,
                "timestamp": entry.get("timestamp"),
                "command": entry.get("command"),
                "actor": entry.get("actor"),
                "reason": entry.get("reason"),
                "branch": entry.get("branch", "main"),
                "parent_commit": entry.get("parent_commit"),
                "branch_point": entry.get("branch_point"),
                "is_current_head": index == cursor,
            }
        
        return {
            "nodes": nodes,
            "branches": branches,
            "current_branch": current_branch,
            "cursor": cursor,
            "entries_count": len(entries),
        }

    def get_branches(self) -> dict[str, Any]:
        """Return a summary of all tracked branches."""
        state = self._read_state()
        branches = state.get("branches", {})
        current_branch = state.get("current_branch", "main")
        entries = state.get("entries", [])
        
        branches_info: dict[str, dict[str, Any]] = {}
        for branch_name, branch_data in branches.items():
            head_commit = branch_data.get("head")
            entries_on_branch = [e for e in entries if e.get("branch") == branch_name]
            branches_info[branch_name] = {
                "label": branch_data.get("label", branch_name),
                "head": head_commit,
                "entry_count": len(entries_on_branch),
                "is_current": branch_name == current_branch,
            }
        return branches_info
