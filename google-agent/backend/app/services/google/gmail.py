from __future__ import annotations

from email.mime.text import MIMEText
import base64

from app.services.google.support import (
    _created_response,
    _email_preview,
    _gmail_body_text,
    _gmail_draft_url,
    _gmail_headers,
    _gmail_message_url,
    _invalid_id_response,
    _tool_error,
    _tool_result,
    _linked_action_summary,
)
import logging

logger = logging.getLogger("app.google")

_EMAIL_BODY_MAX = 8000


class GmailMixin:
    def _gmail_message_summary(self, msg_ref: dict, include_snippet: bool = True) -> dict:
        msg = (
            self._gmail.users()
            .messages()
            .get(
                userId="me",
                id=msg_ref["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date", "To"],
            )
            .execute()
        )
        return self._format_gmail_message_summary(msg, include_snippet=include_snippet)

    def _format_gmail_message_summary(self, msg: dict, include_snippet: bool = True) -> dict:
        headers = _gmail_headers(msg.get("payload", {}))
        summary = {
            "id": msg["id"],
            "message_id": msg["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
        }
        if include_snippet:
            snippet = (msg.get("snippet") or "").strip()
            if snippet:
                summary["snippet"] = snippet[:80]
        summary["link"] = _gmail_message_url(msg["id"])
        return summary

    def _gmail_message_summaries(self, msg_refs: list[dict], max_results: int) -> list[dict]:
        refs = msg_refs[:max_results]
        if not refs:
            return []
        if len(refs) == 1:
            return [self._gmail_message_summary(refs[0])]

        results: dict[str, dict] = {}
        batch = self._gmail.new_batch_http_request()

        def _callback(request_id: str, response: dict | None, exception: Exception | None) -> None:
            if exception is not None:
                logger.warning("Gmail batch get %s failed: %s", request_id, exception)
                return
            if response is None:
                return
            results[request_id] = self._format_gmail_message_summary(response)

        for ref in refs:
            batch.add(
                self._gmail.users()
                .messages()
                .get(
                    userId="me",
                    id=ref["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date", "To"],
                ),
                callback=_callback,
                request_id=ref["id"],
            )

        batch.execute()
        return [results[ref["id"]] for ref in refs if ref["id"] in results]

    def list_unread(self, max_results: int = 10) -> str:
        result = (
            self._gmail.users()
            .messages()
            .list(userId="me", q="is:unread", maxResults=max_results)
            .execute()
        )
        messages = result.get("messages", [])
        summaries = self._gmail_message_summaries(messages, max_results)
        count = len(summaries)
        return _tool_result(
            "ok",
            f"Found {count} unread email(s)." if count else "No unread emails.",
            next_step="If the user refers to an email, call get_email or reply_to_email yourself with messages[].message_id. Never ask the user for an id.",
            unread_count=count,
            preview=_email_preview(summaries),
            messages=summaries,
        )

    def list_emails(self, max_results: int = 20, query: str = "in:inbox") -> str:
        return self.search_emails(query=query, max_results=max_results)

    def search_emails(self, query: str, max_results: int = 10) -> str:
        result = (
            self._gmail.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = result.get("messages", [])
        summaries = self._gmail_message_summaries(messages, max_results)
        count = len(summaries)
        return _tool_result(
            "ok",
            f"Found {count} email(s) matching query." if count else f"No emails matched query '{query}'.",
            next_step="If the user refers to an email, call get_email or reply_to_email yourself with messages[].message_id. Never ask the user for an id.",
            query=query,
            count=count,
            preview=_email_preview(summaries),
            messages=summaries,
        )

    def get_email(self, message_id: str) -> str:
        invalid = _invalid_id_response(message_id, "message_id")
        if invalid:
            return invalid
        msg = (
            self._gmail.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        payload = msg.get("payload", {})
        headers = _gmail_headers(payload)
        body = _gmail_body_text(payload) or ""
        body_truncated = len(body) > _EMAIL_BODY_MAX
        if body_truncated:
            body = body[:_EMAIL_BODY_MAX]
        subject = headers.get("Subject", "") or "(no subject)"
        mail_link = _gmail_message_url(message_id)
        email_fields: dict = {
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": subject,
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
            "body": body,
        }
        if body_truncated:
            email_fields["body_truncated"] = True
        return _tool_result(
            "ok",
            _linked_action_summary(
                "Retrieved email",
                subject,
                mail_link,
                fallback=f'Retrieved email "{subject}".',
            ),
            next_step="If the user wants to reply or change labels, call the tool yourself with this message_id. Never ask the user for an id.",
            id=message_id,
            message_id=message_id,
            thread_id=msg.get("threadId", ""),
            link=mail_link,
            **email_fields,
        )

    def send_email(self, to: str, subject: str, body: str) -> str:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = (
            self._gmail.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )
        message_id = sent.get("id", "")
        mail_link = _gmail_message_url(message_id)
        return _tool_result(
            "sent",
            _linked_action_summary(
                f'Email sent to {to}',
                subject,
                mail_link,
                fallback=f'Email sent to {to} with subject "{subject}".',
            ),
            message_id=message_id,
            link=mail_link,
            subject=subject,
        )

    def reply_to_email(self, message_id: str, body: str) -> str:
        invalid = _invalid_id_response(message_id, "message_id")
        if invalid:
            return invalid
        original = (
            self._gmail.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=["From", "Subject", "Message-ID", "References"],
            )
            .execute()
        )
        headers = _gmail_headers(original.get("payload", {}))
        thread_id = original.get("threadId", "")
        to_addr = headers.get("From", "")
        subject = headers.get("Subject", "")
        if subject and not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        message = MIMEText(body)
        message["to"] = to_addr
        message["subject"] = subject
        if headers.get("Message-ID"):
            message["In-Reply-To"] = headers["Message-ID"]
            message["References"] = headers.get("References", headers["Message-ID"])

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent = (
            self._gmail.users()
            .messages()
            .send(userId="me", body={"raw": raw, "threadId": thread_id})
            .execute()
        )
        sent_id = sent.get("id", "")
        mail_link = _gmail_message_url(sent_id)
        return _tool_result(
            "sent",
            _linked_action_summary(
                "Reply sent",
                subject,
                mail_link,
                fallback=f"Reply sent in thread {thread_id}.",
            ),
            message_id=sent_id,
            link=mail_link,
            subject=subject,
            thread_id=thread_id,
            in_reply_to=message_id,
        )

    def create_draft(self, to: str, subject: str, body: str) -> str:
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft = (
            self._gmail.users()
            .drafts()
            .create(userId="me", body={"message": {"raw": raw}})
            .execute()
        )
        draft_id = draft.get("id", "")
        return _created_response(
            draft_id,
            id_key="draft_id",
            title=subject,
            link=_gmail_draft_url(draft_id),
            message_id=draft.get("message", {}).get("id"),
        )

    def _modify_message_labels(
        self,
        message_id: str,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> str:
        body: dict[str, list[str]] = {}
        if add:
            body["addLabelIds"] = add
        if remove:
            body["removeLabelIds"] = remove
        if not body:
            return _tool_error("No label changes specified.")
        result = (
            self._gmail.users()
            .messages()
            .modify(userId="me", id=message_id, body=body)
            .execute()
        )
        return _tool_result(
            "updated",
            f"Updated labels on message {message_id}.",
            message_id=message_id,
            label_ids=result.get("labelIds", []),
        )

    def mark_email_read(self, message_id: str) -> str:
        return self._modify_message_labels(message_id, remove=["UNREAD"])

    def mark_email_unread(self, message_id: str) -> str:
        return self._modify_message_labels(message_id, add=["UNREAD"])

    def archive_email(self, message_id: str) -> str:
        return self._modify_message_labels(message_id, remove=["INBOX"])

    def trash_email(self, message_id: str) -> str:
        self._gmail.users().messages().trash(userId="me", id=message_id).execute()
        return _tool_result("trashed", f"Moved message {message_id} to trash.", message_id=message_id)

    def list_labels(self) -> str:
        result = self._gmail.users().labels().list(userId="me").execute()
        labels = [
            {"id": label["id"], "name": label["name"], "type": label.get("type", "")}
            for label in result.get("labels", [])
        ]
        return _tool_result(
            "ok",
            f"Found {len(labels)} Gmail label(s).",
            count=len(labels),
            labels=labels,
        )

    # --- Calendar ---
