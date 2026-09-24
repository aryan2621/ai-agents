from langchain_core.tools import BaseTool, tool

from app.services.google_clients import GoogleClients
from app.tools._errors import wrap_google_tool


def build_gmail_tools(
    google: GoogleClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = google

    @tool
    def list_emails(max_results: int = 10, query: str = "in:inbox") -> str:
        """List emails matching a Gmail query."""
        return wrap_google_tool(g.list_emails, "list_emails")(
            max_results=max_results, query=query
        )

    @tool
    def list_unread(max_results: int = 10) -> str:
        """List unread emails."""
        return wrap_google_tool(g.list_unread, "list_unread")(max_results=max_results)

    @tool
    def search_emails(query: str, max_results: int = 10) -> str:
        """Search emails with Gmail query syntax."""
        return wrap_google_tool(g.search_emails, "search_emails")(
            query=query, max_results=max_results
        )

    @tool
    def get_email(message_id: str) -> str:
        """Get full email by message ID from list/search results."""
        return wrap_google_tool(g.get_email, "get_email")(message_id=message_id)

    @tool
    def send_email(to: str, subject: str, body: str) -> str:
        """Send a new email."""
        return wrap_google_tool(g.send_email, "send_email")(
            to=to, subject=subject, body=body
        )

    @tool
    def reply_to_email(message_id: str, body: str) -> str:
        """Reply to an email by message ID."""
        return wrap_google_tool(g.reply_to_email, "reply_to_email")(
            message_id=message_id, body=body
        )

    @tool
    def create_draft(to: str, subject: str, body: str) -> str:
        """Create an email draft. Returns JSON with id and draft_id."""
        return wrap_google_tool(g.create_draft, "create_draft")(
            to=to, subject=subject, body=body
        )

    @tool
    def mark_email_read(message_id: str) -> str:
        """Mark an email as read."""
        return wrap_google_tool(g.mark_email_read, "mark_email_read")(message_id=message_id)

    @tool
    def mark_email_unread(message_id: str) -> str:
        """Mark an email as unread."""
        return wrap_google_tool(g.mark_email_unread, "mark_email_unread")(
            message_id=message_id
        )

    @tool
    def archive_email(message_id: str) -> str:
        """Archive an email (remove from inbox)."""
        return wrap_google_tool(g.archive_email, "archive_email")(message_id=message_id)

    @tool
    def trash_email(message_id: str) -> str:
        """Move an email to trash."""
        return wrap_google_tool(g.trash_email, "trash_email")(message_id=message_id)

    @tool
    def list_labels() -> str:
        """List Gmail labels."""
        return wrap_google_tool(g.list_labels, "list_labels")()

    return [
        list_emails,
        list_unread,
        search_emails,
        get_email,
        send_email,
        reply_to_email,
        create_draft,
        mark_email_read,
        mark_email_unread,
        archive_email,
        trash_email,
        list_labels,
    ]
