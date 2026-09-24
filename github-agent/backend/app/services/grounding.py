from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import ToolMessage

logger = logging.getLogger("app.grounding")

MUTATION_STATUSES = frozenset(
    {"created", "updated", "deleted", "appended", "sent", "trashed", "merged"}
)
MUTATION_CLAIM_RE = re.compile(
    r"(?i)\b(?:"
    r"(?:i|we)\s+(?:have\s+|just\s+|successfully\s+)?"
    r"(?:created|sent|emailed|updated|deleted|trashed|scheduled|appended|booked|merged|commented)"
    r"|successfully\s+(?:created|sent|emailed|updated|deleted|trashed|scheduled|appended|booked|merged|commented)"
    r"|(?:has|have|was|were)\s+been\s+"
    r"(?:created|sent|emailed|updated|deleted|trashed|scheduled|appended|booked|merged)"
    r")"
)
QUESTION_RE = re.compile(r"\?|could you (provide|share)|what(?:'s| is) the", re.IGNORECASE)
EMPTY_LOOKUP_CLAIM_RE = re.compile(
    r"(?i)\b(?:"
    r"no (?:repositor(?:y|ies)|issues?|pull requests?|prs?|matches?|results?|items?)"
    r" (?:found|matched|were found)"
    r"|nothing matching"
    r"|no items found"
    r")\b"
)

EMPTY_NOTHING_FOUND = "Nothing matching that request was found."
UNVERIFIED_MUTATION = (
    "I could not verify that action from tool results, so I did not claim it succeeded."
)
NO_TOOL_FACTS = "I do not have verified tool results for that yet."


def _parse_tool_payload(content: str) -> dict[str, Any] | None:
    text = (content or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def parse_tool_payloads(tool_messages: list[ToolMessage] | list[Any]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for message in tool_messages:
        content = getattr(message, "content", message)
        if not isinstance(content, str):
            content = str(content)
        payload = _parse_tool_payload(content)
        if payload is not None:
            payloads.append(payload)
    return payloads


def _format_tool_payload(payload: dict[str, Any]) -> str:
    summary = str(payload.get("summary") or payload.get("message") or "").strip()
    preview = str(payload.get("preview") or "").strip()
    if preview and preview.lower() != "no items found.":
        if preview in summary:
            return summary
        if summary:
            return f"{summary.rstrip('.')}:\n{preview}"
        return preview
    return summary


def _tool_summaries(payloads: list[dict[str, Any]]) -> str:
    lines = [_format_tool_payload(payload) for payload in payloads]
    return "\n\n".join(line for line in lines if line).strip()


def _has_mutation_status(payloads: list[dict[str, Any]]) -> bool:
    return any(str(p.get("status") or "").lower() in MUTATION_STATUSES for p in payloads)


def _is_empty_lookup(payload: dict[str, Any]) -> bool:
    status = str(payload.get("status") or "").lower()
    if status == "error":
        return False
    for key in (
        "count",
        "unread_count",
        "result_count",
        "event_count",
        "file_count",
        "message_count",
    ):
        value = payload.get(key)
        if isinstance(value, int) and value == 0:
            return True
    for key in (
        "repos",
        "issues",
        "pulls",
        "commits",
        "notifications",
        "files",
        "results",
    ):
        value = payload.get(key)
        if isinstance(value, list) and len(value) == 0:
            return True
    summary = str(payload.get("summary") or "").lower()
    return any(
        marker in summary
        for marker in (
            "no items found",
            "no unread",
            "nothing found",
            "no issues",
            "no pull",
            "no repos",
            "no notifications",
        )
    )


def _looks_like_item_list(text: str) -> bool:
    bullets = len(re.findall(r"(?m)^\s*[-*]\s+", text))
    numbered = len(re.findall(r"(?m)^\s*\d+\.\s+", text))
    links = len(re.findall(r"\[[^\]]+\]\([^)]+\)", text))
    return bullets + numbered >= 2 or links >= 2


def ground_assistant_text(
    text: str,
    tool_messages: list[Any] | None,
    *,
    specialist: bool = True,
) -> str:
    original = (text or "").strip()
    payloads = parse_tool_payloads(tool_messages or [])

    if not specialist:
        return original

    if not payloads:
        if original and MUTATION_CLAIM_RE.search(original):
            return UNVERIFIED_MUTATION
        if _looks_like_item_list(original) or EMPTY_LOOKUP_CLAIM_RE.search(original):
            logger.info("Grounding blocked ungrounded lookup claim")
            return NO_TOOL_FACTS
        if original and QUESTION_RE.search(original):
            return original
        return original or NO_TOOL_FACTS

    if MUTATION_CLAIM_RE.search(original) and not _has_mutation_status(payloads):
        summary = _tool_summaries(payloads)
        logger.info("Grounding blocked unverified mutation claim")
        return summary or UNVERIFIED_MUTATION

    lookups = [p for p in payloads if _is_empty_lookup(p)]
    if lookups and len(lookups) == len(payloads) and _looks_like_item_list(original):
        summary = _tool_summaries(payloads)
        logger.info("Grounding replaced fabricated list after empty lookup")
        return summary or EMPTY_NOTHING_FOUND

    return original


def empty_specialist_fallback(tool_messages: list[Any] | None) -> str:
    payloads = parse_tool_payloads(tool_messages or [])
    summary = _tool_summaries(payloads)
    if summary:
        return summary
    if payloads:
        return EMPTY_NOTHING_FOUND
    return NO_TOOL_FACTS
