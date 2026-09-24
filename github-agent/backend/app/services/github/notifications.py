from __future__ import annotations

from app.services.github.support import list_text, tool_error, tool_result


class NotificationsMixin:
    def list_notifications(
        self,
        all_notifications: bool = False,
        max_results: int = 10,
    ) -> str:
        items = self._request(
            "GET",
            "/notifications",
            params={
                "all": "true" if all_notifications else "false",
                "per_page": min(max(max_results, 1), 50),
            },
        )
        notes = [_notification_item(item) for item in items if isinstance(item, dict)]
        count = len(notes)
        preview = list_text(notes, "title")
        return tool_result(
            "ok",
            f"Found {count} notification(s):\n{preview}" if count else "No unread notifications.",
            next_step="Use notifications[].thread_id to mark a notification read.",
            count=count,
            preview=preview,
            notifications=notes,
        )

    def mark_notification_read(self, thread_id: str) -> str:
        if not thread_id.strip():
            return tool_error("thread_id is required.")
        self._request("PATCH", f"/notifications/threads/{thread_id.strip()}")
        return tool_result(
            "updated",
            f"Marked notification {thread_id} as read.",
            thread_id=thread_id.strip(),
        )


def _notification_item(item: dict) -> dict:
    repo = item.get("repository") if isinstance(item.get("repository"), dict) else {}
    subject = item.get("subject") if isinstance(item.get("subject"), dict) else {}
    full_name = str(repo.get("full_name") or "")
    owner, name = ("", "")
    if "/" in full_name:
        owner, name = full_name.split("/", 1)
    return {
        "thread_id": str(item.get("id") or ""),
        "title": str(subject.get("title") or ""),
        "name": str(subject.get("title") or ""),
        "reason": str(item.get("reason") or ""),
        "unread": bool(item.get("unread")),
        "type": str(subject.get("type") or ""),
        "owner": owner,
        "repo": name,
        "updated_at": str(item.get("updated_at") or ""),
        "link": str(repo.get("html_url") or ""),
    }
