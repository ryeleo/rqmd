from __future__ import annotations

import json

from rqmd import json_speedups


def test_json_speedups_falls_back_to_stdlib_when_orjson_missing(monkeypatch) -> None:
    monkeypatch.setattr(json_speedups, "_orjson", None)

    payload = {"emoji": "💡", "nested": {"value": 1}}
    encoded = json_speedups.dumps_json(payload, indent=2, sort_keys=True)

    assert json.loads(encoded) == payload
    assert '  "emoji": "💡"' in encoded


def test_json_speedups_uses_orjson_when_available(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeOrjson:
        OPT_INDENT_2 = 1
        OPT_SORT_KEYS = 2

        @staticmethod
        def dumps(payload, option=0):
            captured["payload"] = payload
            captured["option"] = option
            return b'{"ok":true}'

    monkeypatch.setattr(json_speedups, "_orjson", FakeOrjson)

    encoded = json_speedups.dumps_json({"ok": True}, indent=2, sort_keys=True)

    assert encoded == '{"ok":true}'
    assert captured["option"] == FakeOrjson.OPT_INDENT_2 | FakeOrjson.OPT_SORT_KEYS