from __future__ import annotations

import re

from app.services.github.support import list_text, resolve_repo, tool_error, tool_result

_LANGUAGE_NAME_RE = re.compile(r"^[A-Za-z+#.]{1,20}$")
_LANGUAGE_ALIASES = {
    "react": "javascript",
    "reactjs": "javascript",
    "react.js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "node.js": "javascript",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "cpp": "c++",
    "csharp": "c#",
    "cs": "c#",
}


class ReposMixin:
    def list_my_repos(self, max_results: int = 10) -> str:
        items = self._request(
            "GET",
            "/user/repos",
            params={
                "per_page": min(max(max_results, 1), 50),
                "sort": "updated",
                "affiliation": "owner,collaborator,organization_member",
            },
        )
        repos = [_repo_item(item) for item in _as_list(items)]
        count = len(repos)
        preview = list_text(repos, "full_name")
        return tool_result(
            "ok",
            f"Found {count} repositories:\n{preview}" if count else "No repositories found.",
            next_step="Use owner and repo from repos[] for follow-up tools. Never ask the user for ids.",
            count=count,
            preview=preview,
            repos=repos,
        )

    def get_repo(self, owner: str = "", repo: str = "") -> str:
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        data = self._request("GET", f"/repos/{owner}/{repo}")
        item = _repo_item(data)
        readme = _readme_excerpt(self, owner, repo)
        files = _root_listing(self, owner, repo)
        summary = _repo_summary(item)
        if readme:
            summary = f"{summary}\n\nREADME:\n{readme}"
        elif files:
            summary = f"{summary}\n\nRoot:\n{list_text(files)}"
        extra: dict = {"repo_url": item["link"]}
        if readme:
            extra["readme"] = readme
        if files:
            extra["files"] = files
            extra["preview"] = list_text(files)
        return tool_result(
            "ok",
            summary,
            next_step="Use this owner/repo for issues, pull requests, and files.",
            **extra,
            **item,
        )

    def search_my_repos(self, query: str, max_results: int = 10) -> str:
        query = _normalize_repo_search_query(query)
        language = _language_from_query(query)
        if language:
            repos = _repos_with_language(self, language, max_results)
        else:
            login = self.login
            q = f"{query} user:{login}".strip() if login else query
            data = self._request(
                "GET",
                "/search/repositories",
                params={"q": q, "per_page": min(max(max_results, 1), 30)},
            )
            items = data.get("items", []) if isinstance(data, dict) else []
            repos = [_repo_item(item) for item in _as_list(items)]
        count = len(repos)
        preview = list_text(repos, "full_name")
        return tool_result(
            "ok",
            f"Found {count} repositories matching '{query}':\n{preview}"
            if count
            else f"No repositories matched '{query}'.",
            next_step="Use owner and repo from repos[] for follow-up tools.",
            query=query,
            count=count,
            preview=preview,
            repos=repos,
        )


    def list_branches(
        self,
        owner: str = "",
        repo: str = "",
        max_results: int = 20,
    ) -> str:
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        items = self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            params={"per_page": min(max(max_results, 1), 50)},
        )
        branches = [_branch_item(item) for item in _as_list(items)]
        count = len(branches)
        preview = list_text(branches)
        return tool_result(
            "ok",
            f"Found {count} branch(es) in {owner}/{repo}:\n{preview}"
            if count
            else f"No branches found in {owner}/{repo}.",
            owner=owner,
            repo=repo,
            count=count,
            preview=preview,
            branches=branches,
        )

    def list_releases(
        self,
        owner: str = "",
        repo: str = "",
        max_results: int = 10,
    ) -> str:
        try:
            owner, repo = resolve_repo(owner, repo, getattr(self, "_workspace_context", None))
        except ValueError as exc:
            return tool_error(str(exc))
        items = self._request(
            "GET",
            f"/repos/{owner}/{repo}/releases",
            params={"per_page": min(max(max_results, 1), 30)},
        )
        releases = [_release_item(item) for item in _as_list(items)]
        count = len(releases)
        preview = list_text(releases, "title")
        return tool_result(
            "ok",
            f"Found {count} release(s) in {owner}/{repo}:\n{preview}"
            if count
            else f"No releases found in {owner}/{repo}.",
            owner=owner,
            repo=repo,
            count=count,
            preview=preview,
            releases=releases,
        )


def _as_list(value: object) -> list:
    return value if isinstance(value, list) else []


def _canonical_language(name: str) -> str:
    text = name.strip()
    if not text:
        return text
    return _LANGUAGE_ALIASES.get(text.lower(), text)


def _normalize_repo_search_query(query: str) -> str:
    text = query.strip()
    if not text:
        return text
    if text.lower().startswith("language:"):
        language = _canonical_language(text.split(":", 1)[1])
        return f"language:{language}" if language else text
    if _LANGUAGE_NAME_RE.fullmatch(text):
        return f"language:{_canonical_language(text)}"
    return text


def _language_from_query(query: str) -> str | None:
    text = query.strip()
    if text.lower().startswith("language:"):
        language = _canonical_language(text.split(":", 1)[1])
        return language or None
    return None


def _repos_with_language(client, language: str, max_results: int) -> list[dict]:
    wanted = language.lower()
    matched: list[dict] = []
    page = 1
    while page <= 3 and len(matched) < max_results:
        items = client._request(
            "GET",
            "/user/repos",
            params={
                "per_page": 100,
                "page": page,
                "sort": "updated",
                "affiliation": "owner,collaborator,organization_member",
            },
        )
        batch = _as_list(items)
        if not batch:
            break
        for item in batch:
            row = _repo_item(item)
            if str(row.get("language") or "").lower() == wanted:
                matched.append(row)
                if len(matched) >= max_results:
                    break
        if len(batch) < 100:
            break
        page += 1
    return matched


def _root_listing(client, owner: str, repo: str) -> list[dict]:
    try:
        data = client._request("GET", f"/repos/{owner}/{repo}/contents/")
    except (FileNotFoundError, RuntimeError):
        return []
    if not isinstance(data, list):
        return []
    entries: list[dict] = []
    for item in data[:30]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        html = str(item.get("html_url") or "")
        entries.append(
            {
                "name": name,
                "title": name,
                "path": str(item.get("path") or name),
                "type": str(item.get("type") or ""),
                "link": html,
            }
        )
    return entries


def _readme_excerpt(client, owner: str, repo: str) -> str:
    from app.services.github.contents import _decode_file_content

    try:
        data = client._request("GET", f"/repos/{owner}/{repo}/readme")
    except (FileNotFoundError, RuntimeError):
        return ""
    if not isinstance(data, dict):
        return ""
    text = _decode_file_content(data)
    if not text:
        return ""
    text = text.strip()
    if len(text) > 2500:
        return text[:2500] + "\n… [truncated]"
    return text


def _repo_summary(item: dict) -> str:
    name = item.get("full_name") or "(unknown repo)"
    link = item.get("link") or ""
    heading = f"**[{name}]({link})**" if link else f"**{name}**"
    description = str(item.get("description") or "").strip()
    bits: list[str] = []
    if item.get("language"):
        bits.append(str(item["language"]))
    if item.get("private"):
        bits.append("private")
    stars = item.get("stars")
    if isinstance(stars, int) and stars:
        bits.append(f"{stars} stars")
    forks = item.get("forks")
    if isinstance(forks, int) and forks:
        bits.append(f"{forks} forks")
    updated = str(item.get("updated_at") or "")
    if updated:
        bits.append(f"updated {updated[:10]}")
    lines = [heading]
    if description:
        lines.append(description)
    if bits:
        lines.append(" · ".join(bits))
    return "\n".join(lines)


def _repo_item(item: dict) -> dict:
    owner = ""
    owner_obj = item.get("owner")
    if isinstance(owner_obj, dict):
        owner = str(owner_obj.get("login") or "")
    full_name = str(item.get("full_name") or "")
    if not owner and "/" in full_name:
        owner = full_name.split("/", 1)[0]
    name = str(item.get("name") or "")
    html = str(item.get("html_url") or "")
    return {
        "id": str(item.get("id") or ""),
        "owner": owner,
        "repo": name,
        "full_name": full_name or f"{owner}/{name}",
        "name": full_name or name,
        "description": str(item.get("description") or ""),
        "private": bool(item.get("private")),
        "default_branch": str(item.get("default_branch") or ""),
        "language": str(item.get("language") or ""),
        "stars": int(item.get("stargazers_count") or 0),
        "forks": int(item.get("forks_count") or 0),
        "open_issues": int(item.get("open_issues_count") or 0),
        "updated_at": str(item.get("updated_at") or ""),
        "link": html,
        "html_url": html,
    }


def _branch_item(item: dict) -> dict:
    commit = item.get("commit") if isinstance(item.get("commit"), dict) else {}
    name = str(item.get("name") or "")
    return {
        "name": name,
        "title": name,
        "sha": str(commit.get("sha") or "")[:12],
        "protected": bool(item.get("protected")),
    }


def _release_item(item: dict) -> dict:
    html = str(item.get("html_url") or "")
    tag = str(item.get("tag_name") or "")
    title = str(item.get("name") or tag or "(untitled release)")
    return {
        "name": title,
        "title": title,
        "tag": tag,
        "draft": bool(item.get("draft")),
        "prerelease": bool(item.get("prerelease")),
        "published_at": str(item.get("published_at") or item.get("created_at") or ""),
        "link": html,
        "html_url": html,
    }
