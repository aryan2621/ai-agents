from __future__ import annotations

from app.services.github.support import (
    issue_url,
    linked_action_summary,
    list_text,
    resolve_repo,
    tool_error,
    tool_result,
)


class IssuesMixin:
    def list_issues(
        self,
        owner: str = "",
        repo: str = "",
        state: str = "open",
        max_results: int = 10,
    ) -> str:
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        items = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={
                "state": state or "open",
                "per_page": min(max(max_results, 1), 50),
            },
        )
        issues = [
            _issue_item(owner, repo, item)
            for item in _as_list(items)
            if not item.get("pull_request")
        ]
        count = len(issues)
        preview = list_text(issues, "title")
        return tool_result(
            "ok",
            f"Found {count} issue(s) in {owner}/{repo}:\n{preview}"
            if count
            else f"No issues found in {owner}/{repo}.",
            next_step="Use issues[].issue_number for get_issue, comments, or updates.",
            owner=owner,
            repo=repo,
            count=count,
            preview=preview,
            issues=issues,
        )

    def get_issue(self, owner: str = "", repo: str = "", issue_number: int = 0) -> str:
        try:
            owner, repo, number = _resolve_issue(
                owner, repo, issue_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        data = self._request("GET", f"/repos/{owner}/{repo}/issues/{number}")
        item = _issue_item(owner, repo, data)
        return tool_result(
            "ok",
            f"Loaded issue #{item['issue_number']}: [{item['title']}]({item['link']}).",
            owner=owner,
            repo=repo,
            issue_url=item["link"],
            issue_title=item["title"],
            **item,
        )

    def create_issue(
        self,
        title: str,
        body: str = "",
        owner: str = "",
        repo: str = "",
    ) -> str:
        if not title.strip():
            return tool_error("Issue title is required.")
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json={"title": title.strip(), "body": body},
        )
        item = _issue_item(owner, repo, data)
        return tool_result(
            "created",
            linked_action_summary(
                "Created issue",
                item["title"],
                item["link"],
                fallback=f"Created issue #{item['issue_number']}.",
            ),
            owner=owner,
            repo=repo,
            issue_number=item["issue_number"],
            issue_url=item["link"],
            issue_title=item["title"],
            link=item["link"],
        )

    def add_issue_comment(
        self,
        body: str,
        owner: str = "",
        repo: str = "",
        issue_number: int = 0,
    ) -> str:
        if not body.strip():
            return tool_error("Comment body is required.")
        try:
            owner, repo, number = _resolve_issue(
                owner, repo, issue_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{number}/comments",
            json={"body": body},
        )
        link = str(data.get("html_url") or issue_url(owner, repo, number))
        return tool_result(
            "created",
            f"Added a comment on {owner}/{repo}#{number}.",
            owner=owner,
            repo=repo,
            issue_number=number,
            issue_url=issue_url(owner, repo, number),
            link=link,
        )

    def update_issue(
        self,
        owner: str = "",
        repo: str = "",
        issue_number: int = 0,
        state: str = "",
        title: str = "",
        body: str = "",
    ) -> str:
        try:
            owner, repo, number = _resolve_issue(
                owner, repo, issue_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        payload: dict[str, str] = {}
        if state.strip():
            payload["state"] = state.strip()
        if title.strip():
            payload["title"] = title.strip()
        if body:
            payload["body"] = body
        if not payload:
            return tool_error("Provide state, title, or body to update.")
        data = self._request(
            "PATCH",
            f"/repos/{owner}/{repo}/issues/{number}",
            json=payload,
        )
        item = _issue_item(owner, repo, data)
        return tool_result(
            "updated",
            linked_action_summary(
                "Updated issue",
                item["title"],
                item["link"],
                fallback=f"Updated issue #{item['issue_number']}.",
            ),
            owner=owner,
            repo=repo,
            issue_number=item["issue_number"],
            issue_url=item["link"],
            issue_title=item["title"],
            state=item["state"],
            link=item["link"],
        )

    def list_issue_comments(
        self,
        owner: str = "",
        repo: str = "",
        issue_number: int = 0,
        max_results: int = 20,
    ) -> str:
        try:
            owner, repo, number = _resolve_issue(
                owner, repo, issue_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        items = self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues/{number}/comments",
            params={"per_page": min(max(max_results, 1), 50)},
        )
        comments = [_comment_item(item) for item in _as_list(items)]
        count = len(comments)
        preview = list_text(comments, "title")
        return tool_result(
            "ok",
            f"Found {count} comment(s) on {owner}/{repo}#{number}:\n{preview}"
            if count
            else f"No comments on {owner}/{repo}#{number}.",
            owner=owner,
            repo=repo,
            issue_number=number,
            issue_url=issue_url(owner, repo, number),
            count=count,
            preview=preview,
            comments=comments,
        )

    def search_issues(self, query: str, max_results: int = 10) -> str:
        if not query.strip():
            return tool_error("query is required. Example: is:issue assignee:@me")
        q = query.strip()
        login = self.login
        if login:
            q = q.replace("@me", login)
        data = self._request(
            "GET",
            "/search/issues",
            params={"q": q, "per_page": min(max(max_results, 1), 30)},
        )
        items = data.get("items", []) if isinstance(data, dict) else []
        issues = [_search_issue_item(item) for item in _as_list(items)]
        count = len(issues)
        preview = list_text(issues, "title")
        return tool_result(
            "ok",
            f"Found {count} issue/PR result(s) for '{query}':\n{preview}"
            if count
            else f"No issues or pull requests matched '{query}'.",
            query=query,
            count=count,
            preview=preview,
            issues=issues,
        )


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _resolve_issue(
    owner: str,
    repo: str,
    issue_number: int,
    workspace_context: dict[str, str] | None,
) -> tuple[str, str, int]:
    owner, repo = resolve_repo(owner, repo, workspace_context)
    ctx = workspace_context or {}
    number = int(issue_number or ctx.get("issue_number") or 0)
    if number <= 0:
        raise ValueError("issue_number is required. List issues first.")
    return owner, repo, number


def _issue_item(owner: str, repo: str, item: dict) -> dict:
    number = int(item.get("number") or 0)
    html = str(item.get("html_url") or issue_url(owner, repo, number))
    return {
        "id": str(item.get("id") or ""),
        "issue_number": number,
        "number": number,
        "title": str(item.get("title") or ""),
        "state": str(item.get("state") or ""),
        "body": str(item.get("body") or "")[:4000],
        "user": str((item.get("user") or {}).get("login") or "")
        if isinstance(item.get("user"), dict)
        else "",
        "comments": item.get("comments") or 0,
        "updated_at": str(item.get("updated_at") or ""),
        "link": html,
        "html_url": html,
    }


def _comment_item(item: dict) -> dict:
    html = str(item.get("html_url") or "")
    user = (
        str((item.get("user") or {}).get("login") or "")
        if isinstance(item.get("user"), dict)
        else ""
    )
    body = str(item.get("body") or "").strip()
    title = f"{user}: {body[:80]}" if user else body[:80]
    return {
        "name": title or "(comment)",
        "title": title or "(comment)",
        "user": user,
        "body": body[:2000],
        "created_at": str(item.get("created_at") or ""),
        "link": html,
        "html_url": html,
    }


def _search_issue_item(item: dict) -> dict:
    owner, name, full_name = _owner_repo_from_search(item)
    html = str(item.get("html_url") or "")
    is_pr = bool(item.get("pull_request"))
    number = int(item.get("number") or 0)
    title = str(item.get("title") or "")
    label = f"{full_name}#{number}: {title}" if full_name else title
    return {
        "id": str(item.get("id") or ""),
        "owner": owner,
        "repo": name,
        "full_name": full_name,
        "issue_number": 0 if is_pr else number,
        "pr_number": number if is_pr else 0,
        "number": number,
        "title": label,
        "name": label,
        "state": str(item.get("state") or ""),
        "type": "pull_request" if is_pr else "issue",
        "user": str((item.get("user") or {}).get("login") or "")
        if isinstance(item.get("user"), dict)
        else "",
        "updated_at": str(item.get("updated_at") or ""),
        "link": html,
        "html_url": html,
    }


def _owner_repo_from_search(item: dict) -> tuple[str, str, str]:
    repo = item.get("repository") if isinstance(item.get("repository"), dict) else {}
    full_name = str(repo.get("full_name") or "")
    if "/" in full_name:
        owner, name = full_name.split("/", 1)
        return owner, name, full_name
    repo_url = str(item.get("repository_url") or "")
    if "/repos/" in repo_url:
        full_name = repo_url.split("/repos/", 1)[1].strip("/")
        if "/" in full_name:
            owner, name = full_name.split("/", 1)
            return owner, name, full_name
    html = str(item.get("html_url") or "")
    if "github.com/" in html:
        parts = html.split("github.com/", 1)[1].split("/")
        if len(parts) >= 2:
            owner, name = parts[0], parts[1]
            return owner, name, f"{owner}/{name}"
    return "", "", ""
