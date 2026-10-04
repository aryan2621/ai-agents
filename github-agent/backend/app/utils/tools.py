from __future__ import annotations

import json
from typing import cast

from app.types.json_types import JSONValue

TOOL_JSON_MAX_LEN = 8000
_LIST_KEYS = (
    "repos",
    "issues",
    "pulls",
    "commits",
    "notifications",
    "files",
    "comments",
    "branches",
    "releases",
)


def _dumps(data: JSONValue) -> str:
    return json.dumps(data, default=str, ensure_ascii=False, separators=(",", ":"))


def _encoded_size(data: JSONValue) -> int:
    return len(_dumps(data))


def _compact_item(item: dict) -> dict:
    out = {k: v for k, v in item.items() if v not in ("", None)}
    if out.get("html_url") == out.get("link"):
        out.pop("html_url", None)
    if out.get("name") == out.get("full_name"):
        out.pop("name", None)
    return out


def _compact(payload: dict[str, JSONValue]) -> dict[str, JSONValue]:
    """The model reads every token of a tool result (about 2 ms each on a Mac), so drop copies:
    the preview list already in the summary, and duplicate or empty fields on list items."""
    preview, summary = payload.get("preview"), payload.get("summary")
    if isinstance(preview, str) and isinstance(summary, str) and preview in summary:
        del payload["preview"]
    for key in _LIST_KEYS:
        items = payload.get(key)
        if isinstance(items, list):
            payload[key] = [_compact_item(i) if isinstance(i, dict) else i for i in items]
    return payload


def _drop_trailing_rows(values: list) -> list:
    if len(values) <= 1:
        return values
    return values[:-1]


def _drop_trailing_item(items: list) -> list:
    if len(items) <= 1:
        return items
    return items[:-1]


def fit_tool_payload(
    payload: dict[str, JSONValue], max_len: int = TOOL_JSON_MAX_LEN
) -> dict[str, JSONValue]:
    if _encoded_size(payload) <= max_len:
        return payload

    fitted: dict[str, JSONValue] = json.loads(_dumps(payload))
    trimmed = False

    values = fitted.get("values")
    if isinstance(values, list) and values:
        while len(values) > 1 and _encoded_size(fitted) > max_len:
            values = _drop_trailing_rows(values)
            fitted["values"] = values
            trimmed = True

    for key in _LIST_KEYS:
        items = fitted.get(key)
        if not isinstance(items, list) or not items:
            continue
        while len(items) > 1 and _encoded_size(fitted) > max_len:
            items = _drop_trailing_item(items)
            fitted[key] = items
            trimmed = True

    if _encoded_size(fitted) > max_len:
        for redundant in ("preview", "list_text"):
            if redundant in fitted:
                del fitted[redundant]
                trimmed = True
                if _encoded_size(fitted) <= max_len:
                    break

    if trimmed:
        fitted["has_more"] = True
    return fitted


def truncate_json(data: JSONValue, max_len: int = TOOL_JSON_MAX_LEN) -> str:
    if isinstance(data, dict):
        fitted = fit_tool_payload(cast(dict[str, JSONValue], data), max_len)
        return _dumps(fitted)
    text = _dumps(data)
    if len(text) <= max_len:
        return text
    return json.dumps(
        {
            "status": "ok",
            "summary": "Result omitted because it exceeded the size budget.",
            "has_more": True,
        }
    )


def tool_result(
    status: str,
    summary: str,
    *,
    next_step: str = "",
    **data: JSONValue,
) -> str:
    del next_step
    payload: dict[str, JSONValue] = {"status": status, "summary": summary}
    payload.update(data)
    payload.pop("next_step", None)
    return truncate_json(_compact(payload))


def tool_error(message: str, *, next_step: str = "", **data: JSONValue) -> str:
    return tool_result("error", message, message=message, next_step=next_step, **data)
