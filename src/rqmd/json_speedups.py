from __future__ import annotations

import json
from typing import Any

try:
    import orjson as _orjson
except ImportError:
    _orjson = None


def native_json_acceleration_enabled() -> bool:
    return _orjson is not None


def dumps_json(payload: Any, *, indent: int | None = None, sort_keys: bool = False) -> str:
    if _orjson is not None:
        option = 0
        if indent == 2:
            option |= _orjson.OPT_INDENT_2
        if sort_keys:
            option |= _orjson.OPT_SORT_KEYS
        return _orjson.dumps(payload, option=option).decode("utf-8")

    kwargs: dict[str, Any] = {"ensure_ascii": False}
    if indent is not None:
        kwargs["indent"] = indent
    if sort_keys:
        kwargs["sort_keys"] = True
    return json.dumps(payload, **kwargs)