import json
import logging

from langchain_core.messages import BaseMessage, ToolMessage

logger = logging.getLogger("app.workspace")

_WORKSPACE_KEYS = frozenset({
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
})

_LIST_DATA_TOOLS: dict[str, tuple[str, str]] = {
    "list_my_repos": ("repos", "repos"),
    "search_my_repos": ("repos", "repos"),
    "list_issues": ("issues", "issues"),
    "search_issues": ("issues", "search"),
    "list_pull_requests": ("pulls", "pulls"),
    "list_notifications": ("notifications", "notifications"),
    "list_commits": ("commits", "commits"),
    "search_code": ("files", "code"),
    "list_pr_files": ("files", "pr_files"),
    "list_branches": ("branches", "branches"),
    "list_releases": ("releases", "releases"),
    "list_issue_comments": ("comments", "comments"),
}


def _parse_tool_payload(content: str | list) -> dict | None:
    if isinstance(content, list):
        return None
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _store_id(updates: dict[str, str], key: str, value: object) -> None:
    if value is None:
        return
    text = str(value).strip()
    if text:
        updates[key] = text


def _is_workspace_key(key: str) -> bool:
    return key in _WORKSPACE_KEYS or key.startswith(("list_data_", "list_query_"))


def _compact_list_item(item: dict) -> dict[str, str]:
    compact: dict[str, str] = {}
    for field in (
        "id",
        "owner",
        "repo",
        "full_name",
        "name",
        "title",
        "path",
        "issue_number",
        "pr_number",
        "number",
        "state",
        "link",
        "html_url",
        "thread_id",
        "sha",
        "language",
        "description",
        "updated_at",
    ):
        value = item.get(field)
        if value is not None and str(value).strip():
            compact[field] = str(value)[:500]
    return compact


def _store_list_data(updates: dict[str, str], tool_name: str, data: dict) -> None:
    spec = _LIST_DATA_TOOLS.get(tool_name)
    if not spec:
        return
    list_key, domain = spec
    items = data.get(list_key)
    if not isinstance(items, list) or not items:
        return
    rows = [_compact_list_item(item) for item in items if isinstance(item, dict)]
    rows = [row for row in rows if row]
    if rows:
        updates[f"list_data_{domain}"] = json.dumps(rows, ensure_ascii=False)
    query = data.get("query")
    if isinstance(query, str) and query.strip():
        updates[f"list_query_{domain}"] = query.strip()


def sanitize_workspace_context(context: dict[str, str] | None) -> dict[str, str]:
    if not context:
        return {}
    return {
        str(k): str(v)
        for k, v in context.items()
        if _is_workspace_key(k) and v
    }


def extract_workspace_updates(messages: list[BaseMessage]) -> dict[str, str]:
    updates: dict[str, str] = {}
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        data = _parse_tool_payload(msg.content)
        if not data:
            continue

        tool_name = msg.name or ""
        status = str(data.get("status") or "")

        if status in ("ok", "created", "updated", "error"):
            _store_id(updates, "owner", data.get("owner"))
            _store_id(updates, "repo", data.get("repo"))
            _store_id(updates, "repo_url", data.get("repo_url") or data.get("html_url"))
            if data.get("owner") and data.get("repo"):
                updates["repo_full_name"] = f"{data['owner']}/{data['repo']}"
            if data.get("issue_number"):
                _store_id(updates, "issue_number", data.get("issue_number"))
                _store_id(updates, "issue_url", data.get("issue_url") or data.get("link"))
                _store_id(updates, "issue_title", data.get("issue_title") or data.get("title"))
            if data.get("pr_number"):
                _store_id(updates, "pr_number", data.get("pr_number"))
                _store_id(updates, "pr_url", data.get("pr_url") or data.get("link"))
                _store_id(updates, "pr_title", data.get("pr_title") or data.get("title"))

        if tool_name in ("list_my_repos", "search_my_repos") and status == "ok":
            items = data.get("repos")
            if isinstance(items, list) and len(items) == 1 and isinstance(items[0], dict):
                item = items[0]
                _store_id(updates, "owner", item.get("owner"))
                _store_id(updates, "repo", item.get("repo"))
                _store_id(updates, "repo_url", item.get("link") or item.get("html_url"))
                if item.get("owner") and item.get("repo"):
                    updates["repo_full_name"] = f"{item['owner']}/{item['repo']}"

        if tool_name in _LIST_DATA_TOOLS and status == "ok":
            _store_list_data(updates, tool_name, data)

    updates = sanitize_workspace_context(updates)
    if updates:
        logger.info("Workspace context updates: %s", updates)
    return updates


def merge_workspace_context(
    existing: dict[str, str] | None, updates: dict[str, str]
) -> dict[str, str]:
    merged = sanitize_workspace_context(existing)
    incoming = sanitize_workspace_context(updates)
    prev_owner = merged.get("owner", "")
    prev_repo = merged.get("repo", "")
    next_owner = incoming.get("owner", prev_owner)
    next_repo = incoming.get("repo", prev_repo)
    if prev_owner and prev_repo and (next_owner != prev_owner or next_repo != prev_repo):
        for key in (
            "issue_number",
            "issue_url",
            "issue_title",
            "pr_number",
            "pr_url",
            "pr_title",
        ):
            merged.pop(key, None)
        for key in list(merged):
            if key.startswith(("list_data_", "list_query_")) and not key.endswith(
                "_repos"
            ):
                merged.pop(key, None)
    merged.update(incoming)
    return merged
