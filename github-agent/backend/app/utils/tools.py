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


def _encoded_size(data: JSONValue) -> int:
    return len(json.dumps(data, default=str))


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

    fitted: dict[str, JSONValue] = json.loads(json.dumps(payload, default=str))
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
        return json.dumps(fitted, default=str)
    text = json.dumps(data, default=str)
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
    return truncate_json(payload)


def tool_error(message: str, *, next_step: str = "", **data: JSONValue) -> str:
    return tool_result("error", message, message=message, next_step=next_step, **data)
