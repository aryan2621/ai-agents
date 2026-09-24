from __future__ import annotations

from app.services.github.support import (
    linked_action_summary,
    list_text,
    pull_url,
    resolve_repo,
    tool_error,
    tool_result,
)


class PullsMixin:
    def list_pull_requests(
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
            f"/repos/{owner}/{repo}/pulls",
            params={
                "state": state or "open",
                "per_page": min(max(max_results, 1), 50),
            },
        )
        pulls = [_pr_item(owner, repo, item) for item in _as_list(items)]
        count = len(pulls)
        preview = list_text(pulls, "title")
        return tool_result(
            "ok",
            f"Found {count} pull request(s) in {owner}/{repo}:\n{preview}"
            if count
            else f"No pull requests found in {owner}/{repo}.",
            next_step="Use pulls[].pr_number for get_pull_request, comments, files, or merge.",
            owner=owner,
            repo=repo,
            count=count,
            preview=preview,
            pulls=pulls,
        )

    def get_pull_request(self, owner: str = "", repo: str = "", pr_number: int = 0) -> str:
        try:
            owner, repo, number = _resolve_pr(
                owner, repo, pr_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        data = self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}")
        item = _pr_item(owner, repo, data)
        return tool_result(
            "ok",
            f"Loaded pull request #{item['pr_number']}: [{item['title']}]({item['link']}).",
            owner=owner,
            repo=repo,
            pr_url=item["link"],
            pr_title=item["title"],
            **item,
        )

    def create_pull_request(
        self,
        title: str,
        head: str,
        base: str,
        body: str = "",
        owner: str = "",
        repo: str = "",
    ) -> str:
        if not title.strip() or not head.strip() or not base.strip():
            return tool_error("title, head, and base are required to create a pull request.")
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json={
                "title": title.strip(),
                "head": head.strip(),
                "base": base.strip(),
                "body": body,
            },
        )
        item = _pr_item(owner, repo, data)
        return tool_result(
            "created",
            linked_action_summary(
                "Created pull request",
                item["title"],
                item["link"],
                fallback=f"Created pull request #{item['pr_number']}.",
            ),
            owner=owner,
            repo=repo,
            pr_number=item["pr_number"],
            pr_url=item["link"],
            pr_title=item["title"],
            link=item["link"],
        )

    def add_pr_comment(
        self,
        body: str,
        owner: str = "",
        repo: str = "",
        pr_number: int = 0,
    ) -> str:
        if not body.strip():
            return tool_error("Comment body is required.")
        try:
            owner, repo, number = _resolve_pr(
                owner, repo, pr_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        data = self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{number}/comments",
            json={"body": body},
        )
        link = str(data.get("html_url") or pull_url(owner, repo, number))
        return tool_result(
            "created",
            f"Added a comment on {owner}/{repo}#{number}.",
            owner=owner,
            repo=repo,
            pr_number=number,
            pr_url=pull_url(owner, repo, number),
            link=link,
        )

    def list_pr_files(
        self,
        owner: str = "",
        repo: str = "",
        pr_number: int = 0,
        max_results: int = 20,
    ) -> str:
        try:
            owner, repo, number = _resolve_pr(
                owner, repo, pr_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        items = self._request("GET", f"/repos/{owner}/{repo}/pulls/{number}/files")
        files = [_file_change(item) for item in _as_list(items)[: max(max_results, 1)]]
        count = len(files)
        preview = list_text(files, "filename")
        return tool_result(
            "ok",
            f"Pull request #{number} changes {count} file(s):\n{preview}"
            if count
            else f"Pull request #{number} has no file changes.",
            owner=owner,
            repo=repo,
            pr_number=number,
            pr_url=pull_url(owner, repo, number),
            count=count,
            preview=preview,
            files=files,
        )

    def merge_pull_request(
        self,
        owner: str = "",
        repo: str = "",
        pr_number: int = 0,
        merge_method: str = "merge",
    ) -> str:
        try:
            owner, repo, number = _resolve_pr(
                owner, repo, pr_number, getattr(self, "_workspace_context", None)
            )
        except ValueError as exc:
            return tool_error(str(exc))
        method = merge_method.strip() or "merge"
        if method not in {"merge", "squash", "rebase"}:
            return tool_error("merge_method must be merge, squash, or rebase.")
        data = self._request(
            "PUT",
            f"/repos/{owner}/{repo}/pulls/{number}/merge",
            json={"merge_method": method},
        )
        merged = bool(data.get("merged"))
        status = "updated" if merged else "error"
        summary = str(data.get("message") or ("Merged." if merged else "Merge did not complete."))
        return tool_result(
            status,
            summary,
            owner=owner,
            repo=repo,
            pr_number=number,
            pr_url=pull_url(owner, repo, number),
            merged=merged,
            sha=str(data.get("sha") or ""),
        )


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _resolve_pr(
    owner: str,
    repo: str,
    pr_number: int,
    workspace_context: dict[str, str] | None,
) -> tuple[str, str, int]:
    owner, repo = resolve_repo(owner, repo, workspace_context)
    ctx = workspace_context or {}
    number = int(pr_number or ctx.get("pr_number") or 0)
    if number <= 0:
        raise ValueError("pr_number is required. List pull requests first.")
    return owner, repo, number


def _pr_item(owner: str, repo: str, item: dict) -> dict:
    number = int(item.get("number") or 0)
    html = str(item.get("html_url") or pull_url(owner, repo, number))
    head = item.get("head") if isinstance(item.get("head"), dict) else {}
    base = item.get("base") if isinstance(item.get("base"), dict) else {}
    return {
        "id": str(item.get("id") or ""),
        "pr_number": number,
        "number": number,
        "title": str(item.get("title") or ""),
        "state": str(item.get("state") or ""),
        "draft": bool(item.get("draft")),
        "merged": bool(item.get("merged")),
        "user": str((item.get("user") or {}).get("login") or "")
        if isinstance(item.get("user"), dict)
        else "",
        "head": str(head.get("ref") or ""),
        "base": str(base.get("ref") or ""),
        "body": str(item.get("body") or "")[:4000],
        "updated_at": str(item.get("updated_at") or ""),
        "link": html,
        "html_url": html,
    }


def _file_change(item: dict) -> dict:
    name = str(item.get("filename") or "")
    return {
        "name": name,
        "filename": name,
        "title": name,
        "status": str(item.get("status") or ""),
        "additions": item.get("additions") or 0,
        "deletions": item.get("deletions") or 0,
        "changes": item.get("changes") or 0,
    }
