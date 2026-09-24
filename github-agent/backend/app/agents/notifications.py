from app.agents.base import BaseAgent

NOTIFICATIONS_PROMPT = """Notifications specialist. Tool map:

- Unread → list_notifications
- Include already-read → list_notifications with all_notifications true
- Mark read → mark_notification_read using thread_id from list_notifications

List items as numbered **[title](link)** — repo, date.
You may use web_search for public research. You do not have Repos, Issues, Pulls, or Code tools."""


class NotificationsAgent(BaseAgent):
    name = "notifications"
    system_prompt = NOTIFICATIONS_PROMPT
