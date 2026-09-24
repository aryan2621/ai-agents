from __future__ import annotations

import base64

from app.services.github.support import (
    list_text,
    resolve_repo,
    tool_error,
    tool_result,
)


class ContentsMixin:
    def get_file_contents(
        self,
        path: str,
        owner: str = "",
        repo: str = "",
        ref: str = "",
    ) -> str:
        if not path.strip():
            return tool_error("path is required.")
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        params = {"ref": ref.strip()} if ref.strip() else None
        data = self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path.strip().lstrip('/')}",
            params=params,
        )
        if isinstance(data, list):
            entries = [
                {
                    "name": str(item.get("name") or ""),
                    "path": str(item.get("path") or ""),
                    "type": str(item.get("type") or ""),
                    "link": str(item.get("html_url") or ""),
                }
                for item in data
                if isinstance(item, dict)
            ]
            return tool_result(
                "ok",
                f"Listed {len(entries)} item(s) in {path}.",
                owner=owner,
                repo=repo,
                path=path,
                files=entries,
                preview=list_text(entries),
            )
        if not isinstance(data, dict):
            return tool_error("Unexpected GitHub contents response.")
        if data.get("type") != "file":
            return tool_error("That path is not a file.")
        content = _decode_file_content(data)
        if content is None:
            return tool_error("File is binary and cannot be shown as text.")
        html = str(data.get("html_url") or "")
        return tool_result(
            "ok",
            f"Loaded {data.get('path') or path}.",
            owner=owner,
            repo=repo,
            path=str(data.get("path") or path),
            sha=str(data.get("sha") or ""),
            size=data.get("size") or 0,
            link=html,
            body=content,
        )

    def search_code(
        self,
        query: str,
        owner: str = "",
        repo: str = "",
        max_results: int = 10,
    ) -> str:
        if not query.strip():
            return tool_error("query is required.")
        ctx = getattr(self, "_workspace_context", None) or {}
        try:
            scoped_owner, scoped_repo = resolve_repo(owner, repo, ctx)
            q = f"{query} repo:{scoped_owner}/{scoped_repo}"
        except ValueError:
            scoped_owner, scoped_repo = "", ""
            login = self.login
            q = f"{query} user:{login}" if login else query
        data = self._request(
            "GET",
            "/search/code",
            params={"q": q, "per_page": min(max(max_results, 1), 30)},
        )
        items = data.get("items", []) if isinstance(data, dict) else []
        files = [_code_hit(item) for item in items if isinstance(item, dict)]
        count = len(files)
        return tool_result(
            "ok",
            f"Found {count} code result(s)." if count else f"No code matched '{query}'.",
            query=query,
            owner=scoped_owner,
            repo=scoped_repo,
            count=count,
            preview=list_text(files, "path"),
            files=files,
        )

    def list_commits(
        self,
        owner: str = "",
        repo: str = "",
        sha: str = "",
        max_results: int = 10,
    ) -> str:
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        params: dict[str, str | int] = {"per_page": min(max(max_results, 1), 50)}
        if sha.strip():
            params["sha"] = sha.strip()
        items = self._request("GET", f"/repos/{owner}/{repo}/commits", params=params)
        commits = [_commit_item(item) for item in items if isinstance(item, dict)]
        count = len(commits)
        preview = list_text(commits, "title")
        return tool_result(
            "ok",
            f"Found {count} commit(s) in {owner}/{repo}:\n{preview}"
            if count
            else f"No commits found in {owner}/{repo}.",
            owner=owner,
            repo=repo,
            count=count,
            preview=preview,
            commits=commits,
        )


def _decode_file_content(data: dict) -> str | None:
    raw = data.get("content") or ""
    if data.get("encoding") == "base64":
        try:
            decoded = base64.b64decode(raw)
        except (ValueError, TypeError):
            return None
        try:
            text = decoded.decode("utf-8")
        except UnicodeDecodeError:
            return None
    else:
        text = str(raw)
    if len(text) > 6000:
        return text[:6000] + "\n… [truncated]"
    return text


def _code_hit(item: dict) -> dict:
    repo = item.get("repository") if isinstance(item.get("repository"), dict) else {}
    html = str(item.get("html_url") or "")
    return {
        "name": str(item.get("name") or ""),
        "path": str(item.get("path") or ""),
        "sha": str(item.get("sha") or ""),
        "owner": str((repo.get("owner") or {}).get("login") or "")
        if isinstance(repo.get("owner"), dict)
        else "",
        "repo": str(repo.get("name") or ""),
        "link": html,
        "html_url": html,
    }


def _commit_item(item: dict) -> dict:
    sha = str(item.get("sha") or "")
    commit = item.get("commit") if isinstance(item.get("commit"), dict) else {}
    message = str(commit.get("message") or "").split("\n", 1)[0]
    if len(message) > 80:
        message = message[:77] + "…"
    html = str(item.get("html_url") or "")
    author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
    return {
        "sha": sha[:12],
        "title": message or sha[:12],
        "name": message or sha[:12],
        "author": str(author.get("name") or ""),
        "date": str(author.get("date") or ""),
        "link": html,
    }
