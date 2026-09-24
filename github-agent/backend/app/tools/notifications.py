from langchain_core.tools import BaseTool, tool

from app.services.github_clients import GitHubClients
from app.tools._errors import wrap_github_tool


def build_notifications_tools(
    github: GitHubClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    del workspace_context
    g = github

    @tool
    def list_notifications(all_notifications: bool = False, max_results: int = 10) -> str:
        """List GitHub notifications. Default is unread only."""
        return wrap_github_tool(g.list_notifications, "list_notifications")(
            all_notifications=all_notifications,
            max_results=max_results,
        )

    @tool
    def mark_notification_read(thread_id: str) -> str:
        """Mark a notification thread as read using thread_id from list_notifications."""
        return wrap_github_tool(g.mark_notification_read, "mark_notification_read")(
            thread_id=thread_id
        )

    return [list_notifications, mark_notification_read]
