from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List


def _load_yaml_any(path: Path) -> Any:
    """Like _load_yaml but accepts a YAML list or dict at the top level."""
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ValueError(
            f"YAML config requires PyYAML. Install with: uv add pyyaml (while loading {path})"
        ) from exc

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        return []
    return data


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise ValueError(
            f"YAML config requires PyYAML. Install with: uv add pyyaml (while loading {path})"
        ) from exc

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc
    except Exception as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML in {path}: expected top-level object")
    return data


def _load_json_any(path: Path) -> Any:
    """Like _load_json but accepts a JSON list or dict at the top level."""
    try:
        content = path.read_text(encoding="utf-8")
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e
    except OSError as e:
        raise ValueError(f"Cannot read {path}: {e}") from e


def _load_json(path: Path) -> dict[str, Any]:
    data = _load_json_any(path)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid JSON in {path}: expected top-level object")
    return data


def load_config(repo_root: Path) -> dict[str, Any]:
    """
    Load project configuration from a unified .rqmd.* file at repo root.
    
    Precedence:
    1. CLI flags (handled by Click, not this function)
    2. .rqmd.yml / .rqmd.yaml / .rqmd.json values (this function)
    3. Built-in defaults (handled by Click)
    
    Args:
        repo_root: Path to project root
        
    Returns:
        Dictionary of config values; empty dict if no config file exists
    """
    candidate_paths = [
        repo_root / ".rqmd.yml",
        repo_root / ".rqmd.yaml",
        repo_root / ".rqmd.json",
    ]

    config_path = next((p for p in candidate_paths if p.exists()), None)
    if config_path is None:
        return {}

    if not config_path.is_file():
        raise ValueError(f"Config file exists but is not a file: {config_path}")

    suffix = config_path.suffix.lower()
    if suffix == ".json":
        return _load_json(config_path)
    if suffix in {".yml", ".yaml"}:
        return _load_yaml(config_path)

    raise ValueError(f"Unsupported config extension for {config_path}. Use .json, .yml, or .yaml")


def _parse_statuses_from_path(path: Path) -> List[Any]:
    """Load and extract a statuses list from a catalog file.

    The file may be:
    - A YAML/JSON list (statuses directly).
    - A YAML/JSON dict with a top-level 'statuses' key.
    """
    suffix = path.suffix.lower()
    if suffix in {".yml", ".yaml"}:
        data: Any = _load_yaml_any(path)
    elif suffix == ".json":
        data = _load_json_any(path)
    else:
        # Content-based sniff: try YAML then JSON.
        try:
            data = _load_yaml_any(path)
        except ValueError:
            try:
                data = _load_json_any(path)
            except ValueError as exc:
                raise ValueError(
                    f"Cannot parse {path}: not valid JSON or YAML"
                ) from exc

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "statuses" in data:
        statuses = data["statuses"]
        if not isinstance(statuses, list):
            raise ValueError(f"'statuses' in {path} must be a list")
        return statuses
    raise ValueError(
        f"Status config file {path} must be a JSON/YAML list or a dict with a 'statuses' key"
    )


def load_statuses_file(
    repo_root: Path,
    override_path: str | None = None,
) -> List[Any] | None:
    """Load a standalone statuses catalog file.

    Precedence:
    1. ``override_path`` (from ``--status-config``): resolved relative to
       *repo_root* when not absolute; raises ValueError if not found.
    2. Auto-detect: ``.rqmd/statuses.yml``, ``.rqmd/statuses.yaml``,
       ``.rqmd/statuses.json`` under *repo_root*.
    3. Return ``None`` if neither applies (caller falls back to unified config).
    """
    if override_path is not None:
        path = Path(override_path)
        if not path.is_absolute():
            path = (repo_root / override_path).resolve()
        if not path.exists():
            raise ValueError(f"--status-config file not found: {override_path}")
        return _parse_statuses_from_path(path)

    candidates = [
        repo_root / ".rqmd" / "statuses.yml",
        repo_root / ".rqmd" / "statuses.yaml",
        repo_root / ".rqmd" / "statuses.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return _parse_statuses_from_path(candidate)

    return None


def validate_config(config: dict[str, Any]) -> None:
    """
    Validate that config keys are known and values are reasonable.
    
    Args:
        config: Configuration dictionary
        
    Raises:
        ValueError: If config is invalid
    """
    allowed_keys = {
        "repo_root",
        "requirements_dir",
        "id_prefix",
        "sort_strategy",
        "state_dir",
        # Unified config can also carry rollup definitions consumed elsewhere.
        "rollup_map",
        "rollup_equations",
        "statuses",
    }
    
    for key in config:
        if key not in allowed_keys:
            raise ValueError(f"Unknown config key: {key}. Allowed keys: {', '.join(sorted(allowed_keys))}")
    
    # Validate types
    if "repo_root" in config and not isinstance(config["repo_root"], str):
        raise ValueError("Config key 'repo_root' must be a string")
    if "requirements_dir" in config and not isinstance(config["requirements_dir"], str):
        raise ValueError("Config key 'requirements_dir' must be a string")
    if "id_prefix" in config and not isinstance(config["id_prefix"], str):
        raise ValueError("Config key 'id_prefix' must be a string")
    if "sort_strategy" in config and not isinstance(config["sort_strategy"], str):
        raise ValueError("Config key 'sort_strategy' must be a string")
    if "state_dir" in config and not isinstance(config["state_dir"], str):
        raise ValueError("Config key 'state_dir' must be a string")
