from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

_ISO_DATETIME_RE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b"
)


def format_display_datetime(value: str, tz_name: str = "UTC") -> str:
    """Turn API datetimes into user-friendly text, e.g. Tue, Jun 16, 2026 at 6:00 PM IST."""
    raw = (value or "").strip()
    if not raw:
        return ""

    if "T" not in raw and len(raw) == 10:
        try:
            parsed = datetime.fromisoformat(raw)
            return parsed.strftime("%a, %b ") + str(parsed.day) + parsed.strftime(", %Y")
        except ValueError:
            return raw

    try:
        tz = ZoneInfo(tz_name)
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz)
        local = dt.astimezone(tz)
        tz_label = local.strftime("%Z") or tz_name
        time_part = local.strftime("%I:%M %p").lstrip("0")
        date_part = local.strftime("%a, %b ") + str(local.day) + local.strftime(", %Y")
        return f"{date_part} at {time_part} {tz_label}".strip()
    except ValueError:
        return raw


def humanize_iso_datetimes(text: str, tz_name: str = "UTC") -> str:
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        return format_display_datetime(match.group(0), tz_name)

    return _ISO_DATETIME_RE.sub(_replace, text)
