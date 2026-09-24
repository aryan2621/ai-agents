from langchain_core.tools import BaseTool, tool

from app.services.google_clients import GoogleClients
from app.tools._errors import wrap_google_tool


def build_calendar_tools(
    google: GoogleClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = google

    @tool
    def list_upcoming_events(max_results: int = 10) -> str:
        """List upcoming calendar events from now onward."""
        return wrap_google_tool(g.list_upcoming_events, "list_upcoming_events")(
            max_results=max_results
        )

    @tool
    def get_events_for_date(date: str) -> str:
        """Get events for a specific date (YYYY-MM-DD)."""
        return wrap_google_tool(g.get_events_for_date, "get_events_for_date")(date=date)

    @tool
    def search_events(query: str, max_results: int = 10) -> str:
        """Search upcoming events by title or text."""
        return wrap_google_tool(g.search_events, "search_events")(
            query=query, max_results=max_results
        )

    @tool
    def get_event_by_id(event_id: str) -> str:
        """Get a calendar event by Google event id from tool results."""
        return wrap_google_tool(g.get_event_by_id, "get_event_by_id")(event_id=event_id)

    @tool
    def find_free_busy(start_time: str, end_time: str) -> str:
        """Get busy time blocks in a date range (ISO 8601 datetimes)."""
        return wrap_google_tool(g.find_free_busy, "find_free_busy")(
            start_time=start_time, end_time=end_time
        )

    @tool
    def create_event(
        summary: str,
        start_time: str,
        end_time: str,
        description: str = "",
    ) -> str:
        """Create a calendar event. Use ISO 8601 start_time and end_time in the user's calendar timezone (no offset)."""
        return wrap_google_tool(g.create_event, "create_event")(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
        )

    @tool
    def update_event(
        event_id: str,
        summary: str = "",
        start_time: str = "",
        end_time: str = "",
        description: str = "",
    ) -> str:
        """Update an existing event by ID."""
        return wrap_google_tool(g.update_event, "update_event")(
            event_id=event_id,
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
        )

    @tool
    def delete_event(event_id: str) -> str:
        """Delete an event by ID."""
        return wrap_google_tool(g.delete_event, "delete_event")(event_id=event_id)

    return [
        list_upcoming_events,
        get_events_for_date,
        search_events,
        get_event_by_id,
        find_free_busy,
        create_event,
        update_event,
        delete_event,
    ]
