import logging
import re
import types
from functools import wraps

import base64

import httplib2
from google.oauth2.credentials import Credentials
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.auth.auth_service import StoredCredentials
from app.types.json_types import JSONValue
from app.utils.format import (
    linked_action_summary as _linked_action_summary,
    list_text as _list_text,
    table_preview as _table_preview,
)
from app.utils.tools import tool_error as _tool_error, tool_result as _tool_result

logger = logging.getLogger("app.google")

MAX_LOG_CHARS = 2000
GOOGLE_HTTP_TIMEOUT_SEC = 30


def _truncate_log(text: str, max_len: int = MAX_LOG_CHARS) -> str:
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}... [truncated {len(text) - max_len} chars]"


def _logged_public_method(fn: types.FunctionType) -> types.FunctionType:
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        logger.info("Google API %s input args=%r kwargs=%r", fn.__name__, args, kwargs)
        try:
            result = fn(self, *args, **kwargs)
            logger.info("Google API %s output=%s", fn.__name__, _truncate_log(result))
            return result
        except HttpError as exc:
            logger.warning("Google API %s HttpError %s: %s", fn.__name__, exc.resp.status, exc)
            raise
        except Exception as exc:
            logger.exception("Google API %s error=%s", fn.__name__, exc)
            raise

    return wrapper  # type: ignore[return-value]


def _credentials(creds: StoredCredentials) -> Credentials:
    return Credentials(token=creds.google_access_token)


def _authorized_http(creds: Credentials) -> AuthorizedHttp:
    return AuthorizedHttp(creds, http=httplib2.Http(timeout=GOOGLE_HTTP_TIMEOUT_SEC))


def _google_service(service_name: str, version: str, creds: Credentials):
    return build(
        service_name,
        version,
        http=_authorized_http(creds),
        cache_discovery=False,
    )


SHEETS_MIME = "application/vnd.google-apps.spreadsheet"
DOCS_MIME = "application/vnd.google-apps.document"
SHEET_PAGE_DEFAULT = 40
SHEET_PAGE_MAX = 100


def _gmail_message_url(message_id: str) -> str:
    cleaned = (message_id or "").strip()
    if not cleaned:
        return ""
    return f"https://mail.google.com/mail/u/0/#all/{cleaned}"


def _gmail_draft_url(draft_id: str) -> str:
    cleaned = (draft_id or "").strip()
    if not cleaned:
        return ""
    return f"https://mail.google.com/mail/u/0/#drafts/{cleaned}"


def _pick_resource_link(data: dict) -> str:
    for key in ("htmlLink", "webViewLink", "spreadsheetUrl", "link"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for nested_key in ("event", "folder", "file"):
        nested = data.get(nested_key)
        if isinstance(nested, dict):
            link = _pick_resource_link(nested)
            if link:
                return link
    message_id = data.get("message_id")
    if isinstance(message_id, str) and message_id.strip():
        return _gmail_message_url(message_id)
    draft_id = data.get("draft_id")
    if isinstance(draft_id, str) and draft_id.strip():
        return _gmail_draft_url(draft_id)
    event_link = data.get("htmlLink")
    if isinstance(event_link, str) and event_link.strip():
        return event_link.strip()
    spreadsheet_id = data.get("spreadsheet_id")
    if isinstance(spreadsheet_id, str) and spreadsheet_id.strip():
        return _spreadsheet_url(spreadsheet_id)
    document_id = data.get("document_id")
    if isinstance(document_id, str) and document_id.strip():
        return _document_url(document_id)
    for key in ("file_id", "folder_id"):
        file_id = data.get(key)
        if isinstance(file_id, str) and file_id.strip():
            mime = data.get("mimeType", "")
            if mime == SHEETS_MIME:
                return _spreadsheet_url(file_id)
            if mime == DOCS_MIME:
                return _document_url(file_id)
            return f"https://drive.google.com/file/d/{file_id.strip()}/view"
    return ""


def _pick_resource_title(data: dict) -> str:
    for key in ("title", "name", "subject", "summary"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for nested_key in ("event", "folder", "file"):
        nested = data.get(nested_key)
        if isinstance(nested, dict):
            title = _pick_resource_title(nested)
            if title:
                return title
    return ""


def _spreadsheet_url(spreadsheet_id: str) -> str:
    cleaned = (spreadsheet_id or "").strip()
    if not cleaned:
        return ""
    return f"https://docs.google.com/spreadsheets/d/{cleaned}/edit"


def _document_url(document_id: str) -> str:
    cleaned = (document_id or "").strip()
    if not cleaned:
        return ""
    return f"https://docs.google.com/document/d/{cleaned}/edit"


def _file_open_url(file: dict) -> str:
    link = file.get("webViewLink") or file.get("htmlLink") or ""
    if link:
        return link
    file_id = file.get("id", "")
    mime = file.get("mimeType", "")
    if mime == SHEETS_MIME:
        return _spreadsheet_url(file_id)
    if mime == DOCS_MIME:
        return _document_url(file_id)
    if file_id:
        return f"https://drive.google.com/file/d/{file_id}/view"
    return ""


def _email_preview(messages: list[dict], max_items: int = 5) -> str:
    if not messages:
        return "No emails found."
    lines = []
    for index, msg in enumerate(messages[:max_items], start=1):
        subject = msg.get("subject") or "(no subject)"
        sender = msg.get("from") or "unknown sender"
        date = msg.get("date") or ""
        link = msg.get("link") or _gmail_message_url(
            str(msg.get("message_id") or msg.get("id", ""))
        )
        snippet = (msg.get("snippet") or "").strip()
        line = f"{index}. [{subject}]({link}) — {sender}"
        if date:
            line += f", {date}"
        if snippet:
            line += f' — "{snippet[:80]}"'
        lines.append(line)
    if len(messages) > max_items:
        lines.append(f"... +{len(messages) - max_items} more email(s)")
    return "\n".join(lines)


def _event_preview(events: list[dict], max_items: int = 5) -> str:
    if not events:
        return "No events found."
    lines = []
    for index, event in enumerate(events[:max_items], start=1):
        title = event.get("summary") or "(no title)"
        start = event.get("start_display") or event.get("start") or "unknown time"
        location = (event.get("location") or "").strip()
        link = event.get("htmlLink") or ""
        if link:
            line = f"{index}. [{title}]({link}) — {start}"
        else:
            line = f"{index}. {title} @ {start}"
        if location:
            line += f", {location}"
        lines.append(line)
    if len(events) > max_items:
        lines.append(f"... +{len(events) - max_items} more event(s)")
    return "\n".join(lines)


_GOOGLE_FILE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{15,100}$")
_INVENTED_ID_PATTERNS = (
    re.compile(r"^1234567890abcdefghijklmnopqrstuvwxyz$", re.IGNORECASE),
    re.compile(r"^[0-9]+$"),
    re.compile(r"^[a-z]+$", re.IGNORECASE),
    re.compile(r"example|placeholder|test123|abcdefgh", re.IGNORECASE),
    re.compile(r"response\.json|\(\)|<KEY>|<ID>|spreadsheet_id\s*$", re.IGNORECASE),
)


def _col_letter(index: int) -> str:
    result = ""
    n = index
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def _pad_values(values: list[list]) -> list[list]:
    if not values:
        return values
    width = max(len(row) for row in values)
    return [list(row) + [""] * (width - len(row)) for row in values]


def _normalize_range_a1(range_a1: str, num_rows: int, num_cols: int) -> str:
    sheet_prefix = ""
    if "!" in range_a1:
        sheet_prefix = range_a1.split("!", 1)[0] + "!"
    end_col = _col_letter(max(num_cols, 1))
    return f"{sheet_prefix}A1:{end_col}{max(num_rows, 1)}"


def _validate_google_file_id(file_id: str, label: str = "spreadsheet_id") -> str | None:
    cleaned = file_id.strip()
    if not cleaned:
        return f"{label} is empty."
    if not _GOOGLE_FILE_ID_RE.match(cleaned):
        return (
            f"{label} '{cleaned}' is not a valid Google ID. "
            "Call a list or search tool first and use an id from that tool result."
        )
    for pattern in _INVENTED_ID_PATTERNS:
        if pattern.search(cleaned):
            return (
                f"{label} '{cleaned}' looks invented, not from a tool result. "
                "Call a list or search tool first."
            )
    return None


def _invalid_id_response(file_id: str, label: str = "spreadsheet_id") -> str | None:
    error = _validate_google_file_id(file_id, label)
    if error is None:
        return None
    return _tool_error(
        error,
        next_step=f"Call a list or create tool first, then pass the real {label} from that result. Never ask the user for an id.",
        **{label: file_id.strip()},
    )


def _google_http_error_message(exc: HttpError, label: str = "file_id") -> str:
    status = exc.resp.status if exc.resp else 0
    if status == 404:
        return (
            f"Google could not find that file ({label}). "
            "The ID may be wrong or already deleted. Call list_spreadsheets to get current IDs."
        )
    if status in (400, 500):
        return (
            f"Google rejected that {label}. It may be invalid or inaccessible. "
            "Call list_spreadsheets and use an id from the tool result."
        )
    return str(exc)


def _escape_drive_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _build_drive_name_search_query(query: str, *, mime_type: str | None = None) -> str:
    name_filter = _escape_drive_query(query.strip())
    parts = ["trashed=false", f"name contains '{name_filter}'"]
    if mime_type:
        parts.insert(0, f"mimeType='{mime_type}'")
    return " and ".join(parts)


def _file_item(file: dict, *, id_alias: str | None = None) -> dict[str, str]:
    file_id = file.get("id", "")
    item: dict[str, str] = {
        "id": file_id,
        "file_id": file_id,
        "name": file.get("name", ""),
    }
    mime = file.get("mimeType", "")
    if id_alias:
        item[id_alias] = file_id
    elif mime == DOCS_MIME:
        item["document_id"] = file_id
    elif mime == SHEETS_MIME:
        item["spreadsheet_id"] = file_id
    link = _file_open_url(file)
    if link:
        item["webViewLink"] = link
    if mime:
        item["mimeType"] = mime
    return item


def _created_response(
    resource_id: str,
    *,
    id_key: str,
    summary: str = "",
    **extra: JSONValue,
) -> str:
    cleaned = resource_id.strip()
    if not cleaned:
        return _tool_error("Create succeeded but no ID was returned from Google.")
    resource = id_key.replace("_id", "").replace("_", " ")
    payload = {id_key: cleaned, **extra}
    title = _pick_resource_title(payload)
    link = _pick_resource_link(payload)
    if not summary:
        summary = _linked_action_summary(
            f"Created {resource}",
            title,
            link,
            fallback=(
                f'Created {resource} "{title}".'
                if title
                else f"Created {resource} successfully."
            ),
        )
    return _tool_result(
        "created",
        summary,
        next_step=f"Call follow-up tools yourself with {id_key}={cleaned}. Never ask the user for an id.",
        id=cleaned,
        **{id_key: cleaned},
        **extra,
    )


def _gmail_headers(payload: dict) -> dict[str, str]:
    return {h["name"]: h["value"] for h in payload.get("headers", [])}


def _gmail_body_text(payload: dict) -> str:
    body = payload.get("body", {})
    if body.get("data"):
        return base64.urlsafe_b64decode(body["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        nested = _gmail_body_text(part)
        if nested:
            return nested
    return ""

