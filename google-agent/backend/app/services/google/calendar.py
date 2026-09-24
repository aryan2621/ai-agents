from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.platform.datetime_display import format_display_datetime
from app.services.google.support import (
    _created_response,
    _event_preview,
    _invalid_id_response,
    _tool_error,
    _tool_result,
    _linked_action_summary,
)
import logging

logger = logging.getLogger("app.google")


class CalendarMixin:
    def _get_calendar_timezone(self) -> str:
        if self._calendar_tz:
            return self._calendar_tz
        try:
            cal = self._calendar.calendars().get(calendarId="primary").execute()
            self._calendar_tz = cal.get("timeZone") or "UTC"
        except Exception:
            logger.warning("Could not fetch calendar timezone; defaulting to UTC")
            self._calendar_tz = "UTC"
        return self._calendar_tz

    def _parse_calendar_datetime(self, value: str) -> datetime:
        """Parse ISO 8601; naive values use the user's primary calendar timezone."""
        tz_name = self._get_calendar_timezone()
        tz = ZoneInfo(tz_name)
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        return dt.astimezone(timezone.utc)

    def _calendar_api_time(self, dt_utc: datetime) -> dict[str, str]:
        tz_name = self._get_calendar_timezone()
        local = dt_utc.astimezone(ZoneInfo(tz_name))
        return {
            "dateTime": local.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": tz_name,
        }

    def calendar_datetime_context(self) -> str:
        tz_name = self._get_calendar_timezone()
        now = datetime.now(ZoneInfo(tz_name))
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        return (
            f"Current calendar time ({tz_name}): {now.strftime('%Y-%m-%d %H:%M %Z')} "
            f"({now.strftime('%A')}). Tomorrow's date: {tomorrow}. "
            "For create_event/update_event, pass start_time and end_time as ISO 8601 without a "
            f"timezone offset (interpreted as {tz_name}), e.g. {tomorrow}T15:00:00 for 3pm tomorrow."
        )

    def _format_calendar_event(self, item: dict, *, compact: bool = True) -> dict:
        start = item.get("start", {})
        end = item.get("end", {})
        tz_name = self._get_calendar_timezone()
        start_raw = start.get("dateTime", start.get("date", ""))
        end_raw = end.get("dateTime", end.get("date", ""))
        event = {
            "id": item.get("id"),
            "event_id": item.get("id"),
            "summary": item.get("summary", "(no title)"),
            "start_display": format_display_datetime(start_raw, tz_name),
            "end_display": format_display_datetime(end_raw, tz_name),
            "location": item.get("location", ""),
            "htmlLink": item.get("htmlLink", ""),
        }
        if not compact:
            event["start"] = start_raw
            event["end"] = end_raw
            event["status"] = item.get("status", "")
        return event

    def get_calendar_timezone(self) -> str:
        return self._get_calendar_timezone()

    def list_upcoming_events(self, max_results: int = 10) -> str:
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        result = (
            self._calendar.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = [self._format_calendar_event(item) for item in result.get("items", [])]
        count = len(events)
        return _tool_result(
            "ok",
            f"Found {count} upcoming event(s)." if count else "No upcoming events scheduled.",
            next_step="If the user refers to an event, call get_event_by_id yourself with events[].event_id. Never ask the user for an id.",
            count=count,
            preview=_event_preview(events),
            events=events,
        )

    def get_events_for_date(self, date: str) -> str:
        tz = ZoneInfo(self._get_calendar_timezone())
        start_dt = datetime.fromisoformat(date).replace(tzinfo=tz)
        end_dt = start_dt + timedelta(days=1)
        result = (
            self._calendar.events()
            .list(
                calendarId="primary",
                timeMin=start_dt.isoformat(),
                timeMax=end_dt.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = [self._format_calendar_event(item) for item in result.get("items", [])]
        count = len(events)
        return _tool_result(
            "ok",
            f"Found {count} event(s) on {date}." if count else f"No events on {date}.",
            next_step="If the user refers to an event, call get_event_by_id yourself with events[].event_id. Never ask the user for an id.",
            date=date,
            count=count,
            preview=_event_preview(events),
            events=events,
        )

    def get_event_by_id(self, event_id: str) -> str:
        invalid = _invalid_id_response(event_id, "event_id")
        if invalid:
            return invalid
        try:
            item = (
                self._calendar.events()
                .get(calendarId="primary", eventId=event_id)
                .execute()
            )
            event = self._format_calendar_event(item, compact=False)
            title = event.get("summary", "(no title)")
            event_link = event.get("htmlLink", "")
            return _tool_result(
                "ok",
                _linked_action_summary(
                    "Retrieved event",
                    title,
                    event_link,
                    fallback=f'Retrieved event "{title}".',
                ),
                next_step="If the user wants to update or delete this event, call the tool yourself with this event_id. Never ask the user for an id.",
                event=event,
                event_id=event.get("id"),
                htmlLink=event_link,
            )
        except Exception as e:
            return _tool_error(str(e), event_id=event_id)

    def create_event(
        self, summary: str, start_time: str, end_time: str, description: str = ""
    ) -> str:
        try:
            start_dt = self._parse_calendar_datetime(start_time)
            end_dt = self._parse_calendar_datetime(end_time)
        except ValueError:
            return _tool_error("start_time and end_time must be ISO 8601 datetimes.")

        now = datetime.now(timezone.utc)
        if start_dt <= now:
            tz_name = self._get_calendar_timezone()
            return _tool_error(
                "start_time must be in the future.",
                parsed_start_utc=start_dt.isoformat(),
                now_utc=now.isoformat(),
                calendar_timezone=tz_name,
            )
        if end_dt <= start_dt:
            return _tool_error("end_time must be after start_time.")

        event = {
            "summary": summary,
            "description": description,
            "start": self._calendar_api_time(start_dt),
            "end": self._calendar_api_time(end_dt),
        }
        created = (
            self._calendar.events()
            .insert(calendarId="primary", body=event)
            .execute()
        )
        formatted = self._format_calendar_event(created, compact=False)
        return _created_response(
            created.get("id", ""),
            id_key="event_id",
            title=formatted.get("summary", summary),
            event=formatted,
            htmlLink=formatted.get("htmlLink", ""),
        )

    def search_events(self, query: str, max_results: int = 10) -> str:
        now = datetime.now(timezone.utc)
        result = (
            self._calendar.events()
            .list(
                calendarId="primary",
                q=query,
                timeMin=now.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = [self._format_calendar_event(item) for item in result.get("items", [])]
        count = len(events)
        return _tool_result(
            "ok",
            f"Found {count} event(s) matching '{query}'." if count else f"No events matched '{query}'.",
            next_step="If the user refers to an event, call get_event_by_id yourself with events[].event_id. Never ask the user for an id.",
            query=query,
            count=count,
            preview=_event_preview(events),
            events=events,
        )

    def update_event(
        self,
        event_id: str,
        summary: str = "",
        start_time: str = "",
        end_time: str = "",
        description: str = "",
    ) -> str:
        body: dict = {}
        if summary:
            body["summary"] = summary
        if description:
            body["description"] = description
        if start_time:
            start_dt = self._parse_calendar_datetime(start_time)
            body["start"] = self._calendar_api_time(start_dt)
        if end_time:
            end_dt = self._parse_calendar_datetime(end_time)
            body["end"] = self._calendar_api_time(end_dt)
        if not body:
            return _tool_error("Provide at least one field to update.")
        updated = (
            self._calendar.events()
            .patch(calendarId="primary", eventId=event_id, body=body)
            .execute()
        )
        event = self._format_calendar_event(updated, compact=False)
        title = event.get("summary", "(no title)")
        event_link = event.get("htmlLink", "")
        return _tool_result(
            "updated",
            _linked_action_summary(
                "Updated event",
                title,
                event_link,
                fallback=f'Updated event "{title}".',
            ),
            event=event,
            event_id=event.get("id"),
            htmlLink=event_link,
        )

    def delete_event(self, event_id: str) -> str:
        invalid = _invalid_id_response(event_id, "event_id")
        if invalid:
            return invalid
        self._calendar.events().delete(calendarId="primary", eventId=event_id).execute()
        return _tool_result("deleted", f"Deleted event {event_id}.", event_id=event_id)

    def find_free_busy(self, start_time: str, end_time: str) -> str:
        try:
            start_dt = self._parse_calendar_datetime(start_time)
            end_dt = self._parse_calendar_datetime(end_time)
        except ValueError:
            return _tool_error("start_time and end_time must be ISO 8601 datetimes.")
        if end_dt <= start_dt:
            return _tool_error("end_time must be after start_time.")

        result = (
            self._calendar.freebusy()
            .query(
                body={
                    "timeMin": start_dt.isoformat(),
                    "timeMax": end_dt.isoformat(),
                    "items": [{"id": "primary"}],
                }
            )
            .execute()
        )
        primary = result.get("calendars", {}).get("primary", {})
        busy = primary.get("busy", [])
        return _tool_result(
            "ok",
            f"Found {len(busy)} busy block(s) between {start_time} and {end_time}.",
            start_time=start_time,
            end_time=end_time,
            busy=busy,
        )

    # --- Drive ---
