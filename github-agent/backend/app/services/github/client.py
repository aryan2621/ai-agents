from __future__ import annotations

import types

import httpx

from app.services.auth_service import StoredCredentials
from app.services.github.contents import ContentsMixin
from app.services.github.issues import IssuesMixin
from app.services.github.notifications import NotificationsMixin
from app.services.github.pulls import PullsMixin
from app.services.github.repos import ReposMixin
from app.services.github.support import (
    GITHUB_API_VERSION,
    GITHUB_HTTP_TIMEOUT_SEC,
    InsufficientScopeError,
    github_error_message,
    logged_public_method,
    tool_error,
    tool_result,
)


class GitHubClients(ReposMixin, IssuesMixin, PullsMixin, ContentsMixin, NotificationsMixin):
    def __init__(
        self,
        creds: StoredCredentials,
        workspace_context: dict[str, str] | None = None,
    ) -> None:
        self._token = creds.github_access_token
        self._workspace_context = dict(workspace_context or {})
        self._login = ""
        self._http = httpx.Client(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
                "User-Agent": "github-agent",
            },
            timeout=GITHUB_HTTP_TIMEOUT_SEC,
        )

    @property
    def login(self) -> str:
        if self._login:
            return self._login
        data = self._request("GET", "/user")
        if isinstance(data, dict):
            self._login = str(data.get("login") or "")
        return self._login

    def get_me(self) -> str:
        data = self._request("GET", "/user")
        if not isinstance(data, dict):
            return tool_error("Could not load the signed-in GitHub user.")
        login = str(data.get("login") or "")
        self._login = login or self._login
        html = str(data.get("html_url") or "")
        name = str(data.get("name") or login)
        lines = [f"**[{login}]({html})**" if html else f"**{login}**"]
        if data.get("name"):
            lines.append(str(data["name"]))
        if data.get("bio"):
            lines.append(str(data["bio"]).strip())
        return tool_result(
            "ok",
            "\n".join(line for line in lines if line),
            login=login,
            name=name,
            link=html,
            html_url=html,
            public_repos=int(data.get("public_repos") or 0),
            followers=int(data.get("followers") or 0),
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict | list:
        response = self._http.request(method, path, params=params, json=json)
        if response.status_code in (401, 403):
            if "/notifications" in path:
                raise InsufficientScopeError("notifications", "notifications", "Notifications")
            raise InsufficientScopeError("repos", "repo", "Repos")
        if response.status_code == 404:
            raise FileNotFoundError(f"GitHub resource not found: {path}")
        if response.status_code >= 400:
            raise RuntimeError(
                f"GitHub API error ({response.status_code}): {github_error_message(response)}"
            )
        if response.status_code == 204 or not response.content:
            return {}
        payload = response.json()
        if isinstance(payload, (dict, list)):
            return payload
        return {}


for cls in GitHubClients.__mro__:
    if cls is object:
        continue
    for _method_name, _method in list(cls.__dict__.items()):
        if isinstance(_method, types.FunctionType) and not _method_name.startswith("_"):
            setattr(GitHubClients, _method_name, logged_public_method(_method))
