import json
import logging

from langchain_core.messages import BaseMessage, ToolMessage

logger = logging.getLogger("app.workspace")

_TOOL_PRIMARY_ID: dict[str, str] = {
    "create_spreadsheet": "spreadsheet_id",
    "create_spreadsheet_with_data": "spreadsheet_id",
    "read_sheet_data": "spreadsheet_id",
    "append_rows": "spreadsheet_id",
    "update_sheet_data": "spreadsheet_id",
    "write_range": "spreadsheet_id",
    "read_range": "spreadsheet_id",
    "get_spreadsheet_info": "spreadsheet_id",
    "trash_spreadsheet": "spreadsheet_id",
    "create_document": "document_id",
    "append_to_document": "document_id",
    "get_document_text": "document_id",
    "create_folder": "folder_id",
    "get_file_metadata": "file_id",
    "create_event": "event_id",
    "update_event": "event_id",
    "get_event_by_id": "event_id",
    "create_draft": "draft_id",
    "send_email": "message_id",
    "reply_to_email": "message_id",
    "get_email": "message_id",
}

_WORKSPACE_KEYS = frozenset({
    "spreadsheet_id",
    "spreadsheet_title",
    "spreadsheet_url",
    "document_id",
    "document_title",
    "document_html_link",
    "folder_id",
    "folder_title",
    "folder_html_link",
    "file_id",
    "file_title",
    "file_html_link",
    "event_id",
    "event_title",
    "event_html_link",
    "draft_id",
    "draft_link",
    "draft_title",
    "message_id",
    "message_subject",
    "message_link",
})

_LIST_DATA_TOOLS: dict[str, tuple[str, str]] = {
    "search_emails": ("messages", "gmail"),
    "list_emails": ("messages", "gmail"),
    "list_unread": ("messages", "gmail"),
    "list_upcoming_events": ("events", "calendar"),
    "search_events": ("events", "calendar"),
    "search_files": ("files", "drive"),
    "list_my_files": ("files", "drive"),
    "list_folder": ("files", "drive"),
    "list_recent_shared": ("files", "drive"),
    "list_documents": ("documents", "docs"),
    "search_documents": ("documents", "docs"),
    "list_spreadsheets": ("spreadsheets", "sheets"),
    "search_spreadsheets": ("spreadsheets", "sheets"),
}

_SINGLE_ITEM_LIST_TOOLS: dict[str, tuple[str, str, str | None]] = {
    "list_spreadsheets": ("spreadsheets", "spreadsheet_id", "spreadsheet_url"),
    "search_spreadsheets": ("spreadsheets", "spreadsheet_id", "spreadsheet_url"),
    "list_documents": ("documents", "document_id", "document_html_link"),
    "search_documents": ("documents", "document_id", "document_html_link"),
    "search_files": ("files", "file_id", "file_html_link"),
    "list_my_files": ("files", "file_id", "file_html_link"),
    "list_folder": ("files", "file_id", "file_html_link"),
    "list_recent_shared": ("files", "file_id", "file_html_link"),
}


def _parse_tool_payload(content: str | list) -> dict | None:
    if isinstance(content, list):
        return None
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _pick_link(data: dict) -> str:
    for key in ("htmlLink", "webViewLink", "spreadsheetUrl", "link"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for nested_key in ("event", "folder", "file"):
        nested = data.get(nested_key)
        if isinstance(nested, dict):
            link = _pick_link(nested)
            if link:
                return link
    return ""


def _pick_title(data: dict) -> str:
    for key in ("title", "name", "subject", "summary"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for nested_key in ("event", "folder", "file"):
        nested = data.get(nested_key)
        if isinstance(nested, dict):
            title = _pick_title(nested)
            if title:
                return title
    return ""


def _store_id(updates: dict[str, str], key: str, value: object) -> None:
    if isinstance(value, str) and value.strip():
        updates[key] = value.strip()


def _store_link_for_id(
    updates: dict[str, str],
    *,
    id_key: str,
    link_key: str,
    data: dict,
) -> None:
    link = _pick_link(data)
    if link:
        updates[link_key] = link
    elif id_key in updates:
        resource_id = updates[id_key]
        if id_key == "spreadsheet_id":
            updates[link_key] = f"https://docs.google.com/spreadsheets/d/{resource_id}/edit"
        elif id_key == "document_id":
            updates[link_key] = f"https://docs.google.com/document/d/{resource_id}/edit"
        elif id_key in ("file_id", "folder_id"):
            updates[link_key] = f"https://drive.google.com/file/d/{resource_id}/view"
        elif id_key == "event_id" and data.get("htmlLink"):
            updates[link_key] = str(data["htmlLink"])
        elif id_key == "message_id":
            updates[link_key] = f"https://mail.google.com/mail/u/0/#all/{resource_id}"
        elif id_key == "draft_id":
            updates[link_key] = f"https://mail.google.com/mail/u/0/#drafts/{resource_id}"


def _store_title_for_id(
    updates: dict[str, str],
    *,
    id_key: str,
    title_key: str,
    data: dict,
) -> None:
    title = _pick_title(data)
    if title:
        updates[title_key] = title


def _is_workspace_key(key: str) -> bool:
    return key in _WORKSPACE_KEYS or key.startswith(("list_data_", "list_query_"))


def _compact_list_item(item: dict) -> dict[str, str]:
    compact: dict[str, str] = {}
    for field in (
        "id",
        "message_id",
        "event_id",
        "file_id",
        "document_id",
        "spreadsheet_id",
        "subject",
        "from",
        "to",
        "date",
        "link",
        "snippet",
        "summary",
        "start",
        "start_display",
        "end",
        "end_display",
        "location",
        "htmlLink",
        "name",
        "title",
        "mimeType",
        "webViewLink",
        "spreadsheetUrl",
        "modifiedTime",
    ):
        value = item.get(field)
        if value is not None and str(value).strip():
            compact[field] = str(value)[:500]
    return compact


def _store_list_data(updates: dict[str, str], tool_name: str, data: dict) -> None:
    spec = _LIST_DATA_TOOLS.get(tool_name)
    if not spec:
        return
    list_key, domain = spec
    items = data.get(list_key)
    if not isinstance(items, list) or not items:
        return
    rows = [_compact_list_item(item) for item in items if isinstance(item, dict)]
    rows = [row for row in rows if row]
    if rows:
        updates[f"list_data_{domain}"] = json.dumps(rows, ensure_ascii=False)
    query = data.get("query")
    if isinstance(query, str) and query.strip():
        updates[f"list_query_{domain}"] = query.strip()


def _apply_single_item_list(
    updates: dict[str, str],
    tool_name: str,
    data: dict,
) -> None:
    spec = _SINGLE_ITEM_LIST_TOOLS.get(tool_name)
    if not spec:
        return
    list_key, id_key, link_key = spec
    items = data.get(list_key)
    if not isinstance(items, list) or len(items) != 1:
        return
    item = items[0]
    if not isinstance(item, dict):
        return
    _store_id(updates, id_key, item.get(id_key) or item.get("id"))
    if link_key:
        link = item.get("webViewLink") or item.get("htmlLink") or item.get("spreadsheetUrl")
        if isinstance(link, str) and link.strip():
            updates[link_key] = link.strip()
    title = item.get("name") or item.get("title") or item.get("summary")
    if isinstance(title, str) and title.strip():
        title_key = id_key.replace("_id", "_title")
        updates[title_key] = title.strip()


def sanitize_workspace_context(context: dict[str, str] | None) -> dict[str, str]:
    if not context:
        return {}
    return {
        str(k): str(v)
        for k, v in context.items()
        if _is_workspace_key(k) and v
    }


def extract_workspace_updates(messages: list[BaseMessage]) -> dict[str, str]:
    updates: dict[str, str] = {}
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        data = _parse_tool_payload(msg.content)
        if not data:
            continue

        tool_name = msg.name or ""
        status = data.get("status")
        primary_key = _TOOL_PRIMARY_ID.get(tool_name)

        if status in ("created", "updated", "appended", "exists", "trashed", "shared", "sent", "deleted", "ok"):
            if primary_key:
                value = data.get(primary_key) or data.get("id")
                _store_id(updates, primary_key, value)

        _apply_single_item_list(updates, tool_name, data)

        if tool_name in ("create_spreadsheet", "create_spreadsheet_with_data"):
            _store_title_for_id(
                updates,
                id_key="spreadsheet_id",
                title_key="spreadsheet_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="spreadsheet_id",
                link_key="spreadsheet_url",
                data=data,
            )

        if tool_name == "create_document":
            _store_title_for_id(
                updates,
                id_key="document_id",
                title_key="document_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="document_id",
                link_key="document_html_link",
                data=data,
            )

        if tool_name == "create_folder":
            _store_title_for_id(
                updates,
                id_key="folder_id",
                title_key="folder_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="folder_id",
                link_key="folder_html_link",
                data=data,
            )

        if tool_name in ("create_event", "update_event", "get_event_by_id"):
            _store_title_for_id(
                updates,
                id_key="event_id",
                title_key="event_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="event_id",
                link_key="event_html_link",
                data=data,
            )

        if tool_name in ("send_email", "reply_to_email", "get_email"):
            subject = data.get("subject")
            if isinstance(subject, str) and subject.strip():
                updates["message_subject"] = subject.strip()
            _store_link_for_id(
                updates,
                id_key="message_id",
                link_key="message_link",
                data=data,
            )

        if tool_name == "create_draft":
            _store_title_for_id(
                updates,
                id_key="draft_id",
                title_key="draft_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="draft_id",
                link_key="draft_link",
                data=data,
            )

        if tool_name == "get_file_metadata":
            _store_title_for_id(
                updates,
                id_key="file_id",
                title_key="file_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="file_id",
                link_key="file_html_link",
                data=data,
            )

        if tool_name == "get_document_text":
            _store_title_for_id(
                updates,
                id_key="document_id",
                title_key="document_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="document_id",
                link_key="document_html_link",
                data=data,
            )

        if tool_name == "get_spreadsheet_info":
            _store_title_for_id(
                updates,
                id_key="spreadsheet_id",
                title_key="spreadsheet_title",
                data=data,
            )
            _store_link_for_id(
                updates,
                id_key="spreadsheet_id",
                link_key="spreadsheet_url",
                data=data,
            )

        if tool_name in _LIST_DATA_TOOLS and status == "ok":
            _store_list_data(updates, tool_name, data)

    updates = sanitize_workspace_context(updates)
    if updates:
        logger.info("Workspace context updates: %s", updates)
    return updates


def merge_workspace_context(
    existing: dict[str, str] | None, updates: dict[str, str]
) -> dict[str, str]:
    merged = sanitize_workspace_context(existing)
    merged.update(sanitize_workspace_context(updates))
    return merged
