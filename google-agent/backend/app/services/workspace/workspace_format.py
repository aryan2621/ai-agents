import json

from app.services.workspace.workspace_context import _parse_tool_payload, sanitize_workspace_context


def _format_resource_block(
    heading: str,
    *,
    resource_id: str,
    title: str = "",
    link: str = "",
) -> list[str]:
    lines = [heading]
    suffix = f' — "{title}"' if title else ""
    lines.append(f"- id: {resource_id}{suffix}")
    if link:
        lines.append(f"- link: {link}")
    return lines


def format_workspace_context(context: dict[str, str]) -> str:
    ctx = sanitize_workspace_context(context)
    if not ctx:
        return ""
    lines: list[str] = []

    sheet_id = ctx.get("spreadsheet_id")
    if sheet_id:
        lines.extend(
            _format_resource_block(
                "Active spreadsheet in this conversation:",
                resource_id=sheet_id,
                title=ctx.get("spreadsheet_title", ""),
                link=ctx.get("spreadsheet_url", ""),
            )
        )

    doc_id = ctx.get("document_id")
    if doc_id:
        lines.extend(
            _format_resource_block(
                "Active Google Doc in this conversation:",
                resource_id=doc_id,
                title=ctx.get("document_title", ""),
                link=ctx.get("document_html_link", ""),
            )
        )

    event_id = ctx.get("event_id")
    if event_id:
        lines.extend(
            _format_resource_block(
                "Active calendar event in this conversation:",
                resource_id=event_id,
                title=ctx.get("event_title", ""),
                link=ctx.get("event_html_link", ""),
            )
        )

    folder_id = ctx.get("folder_id")
    if folder_id:
        lines.extend(
            _format_resource_block(
                "Active Drive folder in this conversation:",
                resource_id=folder_id,
                title=ctx.get("folder_title", ""),
                link=ctx.get("folder_html_link", ""),
            )
        )

    file_id = ctx.get("file_id")
    if file_id:
        lines.extend(
            _format_resource_block(
                "Active Drive file in this conversation:",
                resource_id=file_id,
                title=ctx.get("file_title", ""),
                link=ctx.get("file_html_link", ""),
            )
        )

    message_id = ctx.get("message_id")
    if message_id:
        lines.extend(
            _format_resource_block(
                "Active Gmail message in this conversation:",
                resource_id=message_id,
                title=ctx.get("message_subject", ""),
                link=ctx.get("message_link", ""),
            )
        )

    draft_id = ctx.get("draft_id")
    if draft_id:
        lines.extend(
            _format_resource_block(
                "Active Gmail draft in this conversation:",
                resource_id=draft_id,
                title=ctx.get("draft_title", ""),
                link=ctx.get("draft_link", ""),
            )
        )

    gmail_messages_json = ctx.get("gmail_messages_json")
    if gmail_messages_json:
        ctx = {**ctx, "list_data_gmail": gmail_messages_json}

    for key, value in sorted(ctx.items()):
        if not key.startswith("list_data_"):
            continue
        domain = key.removeprefix("list_data_")
        try:
            rows = json.loads(value)
            row_count = len(rows) if isinstance(rows, list) else 0
        except json.JSONDecodeError:
            row_count = 0
        query = ctx.get(f"list_query_{domain}", "")
        lines.append(f"List data from {domain} available in ACTIVE WORKSPACE ({row_count} item(s)):")
        if query:
            lines.append(f"- query: {query}")
        lines.append(f"- {key}: {value}")

    handled = {
        "spreadsheet_id",
        "spreadsheet_title",
        "spreadsheet_url",
        "document_id",
        "document_title",
        "document_html_link",
        "event_id",
        "event_title",
        "event_html_link",
        "folder_id",
        "folder_title",
        "folder_html_link",
        "file_id",
        "file_title",
        "file_html_link",
        "message_id",
        "message_subject",
        "message_link",
        "draft_id",
        "draft_title",
        "draft_link",
        "gmail_messages_json",
        "gmail_search_query",
    }
    handled.update(key for key in ctx if key.startswith(("list_data_", "list_query_")))
    for key, value in ctx.items():
        if key in handled:
            continue
        lines.append(f"- {key.replace('_', ' ')}: {value}")

    return "\n".join(lines)


def format_sheet_markdown(read_result_json: str) -> str | None:
    data = _parse_tool_payload(read_result_json)
    if not data or data.get("status") != "ok":
        return None
    values = data.get("values")
    if not isinstance(values, list) or not values:
        return None

    title = data.get("title", "Spreadsheet")
    row_count = data.get("row_count", len(values))
    data_rows = max(row_count - 1, len(values) - 1)
    header = values[0]
    col_count = len(header)
    lines = [
        f"**{title}** — {data_rows} data row(s) ({row_count} total including header)",
        "",
        _markdown_row(header),
        _markdown_row(["---"] * col_count),
    ]
    for row in values[1:]:
        cells = list(row) + [""] * max(0, col_count - len(row))
        lines.append(_markdown_row(cells[:col_count]))
    return "\n".join(lines)


def _markdown_row(cells: list) -> str:
    return "| " + " | ".join(str(cell) for cell in cells) + " |"
