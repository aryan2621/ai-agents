from __future__ import annotations


def list_text(items: list[dict], name_key: str = "name") -> str:
    if not items:
        return "No items found."
    lines = []
    for index, item in enumerate(items, start=1):
        name = item.get(name_key, "(unnamed)")
        link = (
            item.get("webViewLink")
            or item.get("htmlLink")
            or item.get("link")
            or item.get("spreadsheetUrl")
            or ""
        )
        extras: list[str] = []
        language = item.get("language")
        if isinstance(language, str) and language.strip():
            extras.append(language.strip())
        extra = (
            item.get("modifiedTime")
            or item.get("date")
            or item.get("updated_at")
            or item.get("mimeType")
            or ""
        )
        if isinstance(extra, str) and extra:
            if len(extra) >= 10 and extra[4:5] == "-":
                extra = extra[:10]
            extras.append(extra)
        if link:
            line = f"{index}. [{name}]({link})"
        else:
            line = f"{index}. {name}"
        if extras:
            line += f" — {' · '.join(extras)}"
        lines.append(line)
    return "\n".join(lines)


def table_preview(values: list[list], max_rows: int = 4) -> str:
    if not values:
        return "(empty range)"
    lines = [" | ".join(str(cell) for cell in row) for row in values[:max_rows]]
    if len(values) > max_rows:
        lines.append(f"... +{len(values) - max_rows} more row(s)")
    return "\n".join(lines)


def linked_action_summary(action: str, title: str, link: str, *, fallback: str) -> str:
    if link and title:
        return f"{action} **[{title}]({link})**."
    if link:
        return f"{action} [open on GitHub]({link})."
    return fallback
