import json

from app.services.workspace_context import _parse_tool_payload, sanitize_workspace_context


def _format_resource_block(
    heading: str,
    *,
    resource_id: str,
    title: str = "",
    link: str = "",
) -> list[str]:
    lines = [heading]
    suffix = f' — "{title}"' if title else ""
    lines.append(f"- id: {resource_id}{suffix}")
    if link:
        lines.append(f"- link: {link}")
    return lines


def format_workspace_context(context: dict[str, str]) -> str:
    ctx = sanitize_workspace_context(context)
    if not ctx:
        return ""
    lines: list[str] = []

    owner = ctx.get("owner", "")
    repo = ctx.get("repo", "")
    if owner and repo:
        lines.extend(
            _format_resource_block(
                "Active repository in this conversation:",
                resource_id=f"{owner}/{repo}",
                title=ctx.get("repo_full_name", ""),
                link=ctx.get("repo_url", ""),
            )
        )

    issue_number = ctx.get("issue_number")
    if issue_number:
        lines.extend(
            _format_resource_block(
                "Active issue in this conversation:",
                resource_id=issue_number,
                title=ctx.get("issue_title", ""),
                link=ctx.get("issue_url", ""),
            )
        )

    pr_number = ctx.get("pr_number")
    if pr_number:
        lines.extend(
            _format_resource_block(
                "Active pull request in this conversation:",
                resource_id=pr_number,
                title=ctx.get("pr_title", ""),
                link=ctx.get("pr_url", ""),
            )
        )

    for key, value in sorted(ctx.items()):
        if not key.startswith("list_data_"):
            continue
        domain = key.removeprefix("list_data_")
        try:
            rows = json.loads(value)
        except json.JSONDecodeError:
            rows = []
        row_count = len(rows) if isinstance(rows, list) else 0
        query = ctx.get(f"list_query_{domain}", "")
        lines.append(
            f"Last {domain} lookup ({row_count} item(s)) — names for follow-up on those items only:"
        )
        if query:
            lines.append(f"- query: {query}")
        names: list[str] = []
        if isinstance(rows, list):
            for row in rows[:20]:
                if not isinstance(row, dict):
                    continue
                label = str(
                    row.get("full_name") or row.get("title") or row.get("name") or ""
                ).strip()
                if label:
                    names.append(label)
        if names:
            lines.append("- items: " + ", ".join(names))
        lines.append(
            "- A different query, language, or filter requires a new list/search tool call. Do not answer a new search from this list."
        )

    handled = {
        "owner",
        "repo",
        "repo_url",
        "repo_full_name",
        "issue_number",
        "issue_url",
        "issue_title",
        "pr_number",
        "pr_url",
        "pr_title",
    }
    handled.update(key for key in ctx if key.startswith(("list_data_", "list_query_")))
    for key, value in ctx.items():
        if key in handled:
            continue
        lines.append(f"- {key.replace('_', ' ')}: {value}")

    return "\n".join(lines)


def format_sheet_markdown(read_result_json: str) -> str | None:
    del read_result_json
    return None
