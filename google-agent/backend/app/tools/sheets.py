import json
from typing import Any

from langchain_core.tools import BaseTool, tool

from app.services.google_clients import GoogleClients
from app.tools._errors import wrap_google_tool
from app.utils.tools import tool_error, tool_result


def _tool_result_status(result: str) -> str | None:
    try:
        data = json.loads(result)
    except json.JSONDecodeError:
        return None
    status = data.get("status")
    return status if isinstance(status, str) else None


def _matches_active_title(requested_title: str, ctx: dict[str, str]) -> bool:
    active_title = ctx.get("spreadsheet_title", "").strip().lower()
    if not active_title:
        return False
    return requested_title.strip().lower() == active_title


def build_sheets_tools(
    google: GoogleClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = google
    ctx = workspace_context if workspace_context is not None else {}

    @tool
    def read_sheet_data(
        range_a1: str = "Sheet1!A1:Z1000",
        offset: int = 0,
        limit: int = 40,
    ) -> str:
        """Read a page of rows from the active spreadsheet. Use offset to fetch the next page when has_more is true."""
        sid = ctx.get("spreadsheet_id", "")
        if not sid:
            return tool_error(
                "No active spreadsheet in this conversation.",
                next_step="Call list_spreadsheets or create_spreadsheet_with_data first.",
            )
        return wrap_google_tool(g.read_range, "read_sheet_data")(
            spreadsheet_id=sid, range_a1=range_a1, offset=offset, limit=limit
        )

    @tool
    def append_rows(rows: list[list[Any]], range_a1: str = "Sheet1!A1") -> str:
        """Append one or more rows to the active spreadsheet. Use for add-row requests."""
        sid = ctx.get("spreadsheet_id", "")
        if not sid:
            return tool_error(
                "No active spreadsheet in this conversation.",
                next_step="Call create_spreadsheet_with_data first.",
            )
        result = wrap_google_tool(g.append_range, "append_rows")(
            spreadsheet_id=sid, range_a1=range_a1, values=rows
        )
        if _tool_result_status(result) == "appended":
            ctx["spreadsheet_id"] = sid
        return result

    @tool
    def update_sheet_data(values: list[list[Any]], range_a1: str = "Sheet1!A1") -> str:
        """Replace the full table on the active spreadsheet. Use when restructuring columns or bulk edits."""
        sid = ctx.get("spreadsheet_id", "")
        if not sid:
            return tool_error(
                "No active spreadsheet in this conversation.",
                next_step="Call create_spreadsheet_with_data first.",
            )
        result = wrap_google_tool(g.write_range, "update_sheet_data")(
            spreadsheet_id=sid, range_a1=range_a1, values=values
        )
        if _tool_result_status(result) == "updated":
            ctx["spreadsheet_id"] = sid
        return result

    @tool
    def list_spreadsheets(max_results: int = 20) -> str:
        """List the user's Google Sheets files (name and id)."""
        return wrap_google_tool(g.list_spreadsheets, "list_spreadsheets")(max_results=max_results)

    @tool
    def search_spreadsheets(query: str, max_results: int = 10) -> str:
        """Search spreadsheets by name."""
        return wrap_google_tool(g.search_spreadsheets, "search_spreadsheets")(
            query=query, max_results=max_results
        )

    @tool
    def create_spreadsheet(title: str) -> str:
        """Create an empty Google Sheet."""
        known_id = ctx.get("spreadsheet_id", "")
        if known_id and _matches_active_title(title, ctx):
            return tool_result(
                "exists",
                f'Spreadsheet "{ctx.get("spreadsheet_title", title)}" is already active ({known_id}).',
                next_step=f"Use spreadsheet_id={known_id} for edits.",
                id=known_id,
                spreadsheet_id=known_id,
                title=ctx.get("spreadsheet_title", title),
            )

        result = wrap_google_tool(g.create_spreadsheet, "create_spreadsheet")(title=title)
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            return result
        if data.get("status") == "created":
            sid = (data.get("spreadsheet_id") or data.get("id") or "").strip()
            if sid:
                ctx["spreadsheet_id"] = sid
                ctx["spreadsheet_title"] = data.get("title", title.strip())
        return result

    @tool
    def create_spreadsheet_with_data(
        title: str,
        values: list[list[Any]],
        range_a1: str = "Sheet1!A1",
    ) -> str:
        """Create a Google Sheet and write headers+rows in one call."""
        known_id = ctx.get("spreadsheet_id", "")
        if known_id and _matches_active_title(title, ctx):
            return wrap_google_tool(g.write_range, "write_range")(
                spreadsheet_id=known_id,
                range_a1=range_a1,
                values=values,
            )

        result = wrap_google_tool(g.create_spreadsheet_with_data, "create_spreadsheet_with_data")(
            title=title, values=values, range_a1=range_a1
        )
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            return result
        if data.get("status") in ("created", "updated"):
            sid = (data.get("spreadsheet_id") or data.get("id") or "").strip()
            if sid:
                ctx["spreadsheet_id"] = sid
                ctx["spreadsheet_title"] = data.get("title", title.strip())
        return result

    @tool
    def get_spreadsheet_info(spreadsheet_id: str) -> str:
        """Get spreadsheet metadata and sheet tab names by ID."""
        sid = ctx.get("spreadsheet_id") or spreadsheet_id.strip()
        return wrap_google_tool(g.get_spreadsheet_info, "get_spreadsheet_info")(
            spreadsheet_id=sid
        )

    @tool
    def read_range(
        spreadsheet_id: str,
        range_a1: str,
        offset: int = 0,
        limit: int = 40,
    ) -> str:
        """Read a page of cell values by spreadsheet ID. Use offset for the next page when has_more is true."""
        sid = spreadsheet_id.strip()
        if not sid:
            return tool_error(
                "spreadsheet_id is required.",
                next_step="Call list_spreadsheets to get a real id.",
            )
        return wrap_google_tool(g.read_range, "read_range")(
            spreadsheet_id=sid, range_a1=range_a1, offset=offset, limit=limit
        )

    @tool
    def write_range(spreadsheet_id: str, range_a1: str, values: list[list[Any]]) -> str:
        """Write data by spreadsheet ID. Use when no active spreadsheet is set."""
        sid = spreadsheet_id.strip()
        if not sid:
            return tool_error(
                "spreadsheet_id is required.",
                next_step="Call list_spreadsheets or create_spreadsheet first.",
            )
        result = wrap_google_tool(g.write_range, "write_range")(
            spreadsheet_id=sid, range_a1=range_a1, values=values
        )
        if _tool_result_status(result) == "updated":
            ctx["spreadsheet_id"] = sid
        return result

    @tool
    def trash_spreadsheet(spreadsheet_id: str) -> str:
        """Move one spreadsheet file to Drive trash."""
        return wrap_google_tool(g.trash_spreadsheet, "trash_spreadsheet")(
            spreadsheet_id=spreadsheet_id
        )

    return [
        read_sheet_data,
        append_rows,
        update_sheet_data,
        create_spreadsheet_with_data,
        list_spreadsheets,
        search_spreadsheets,
        create_spreadsheet,
        get_spreadsheet_info,
        read_range,
        write_range,
        trash_spreadsheet,
    ]
