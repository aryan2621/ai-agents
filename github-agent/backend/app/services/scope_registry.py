from dataclasses import dataclass

PROFILE_SCOPES = ("read:user", "user:email")

GITHUB_AGENT_SCOPES: dict[str, str] = {
    "repos": "repo",
    "issues": "repo",
    "pulls": "repo",
    "code": "repo",
    "notifications": "notifications",
}

SCOPE_LABELS: dict[str, str] = {
    "read:user": "GitHub profile",
    "user:email": "Email address",
    "repo": "Repositories, issues, and pull requests",
    "notifications": "Notifications",
}

AGENT_LABELS: dict[str, str] = {
    "repos": "Repos",
    "issues": "Issues",
    "pulls": "Pull requests",
    "code": "Code",
    "notifications": "Notifications",
    "web": "Web Search",
}


@dataclass
class PermissionStatus:
    id: str
    label: str
    scope: str
    granted: bool


class InsufficientScopeError(Exception):
    def __init__(self, agent: str, scope: str, label: str):
        self.agent = agent
        self.scope = scope
        self.label = label
        super().__init__(f"{label} permission was not granted")


def parse_granted_scopes(scope_string: str) -> list[str]:
    if not scope_string:
        return []
    normalized = scope_string.replace(",", " ")
    return [s for s in normalized.split() if s]


def effective_granted_scopes(scope_string: str) -> list[str]:
    if scope_string.strip():
        return parse_granted_scopes(scope_string)
    return list(PROFILE_SCOPES)


def scopes_to_string(scopes: list[str]) -> str:
    return " ".join(scopes)


def build_permission_statuses(granted_scopes: list[str]) -> list[PermissionStatus]:
    granted_set = set(granted_scopes)
    statuses: list[PermissionStatus] = []

    for scope in (*PROFILE_SCOPES, "repo", "notifications"):
        statuses.append(
            PermissionStatus(
                id=scope,
                label=SCOPE_LABELS.get(scope, scope),
                scope=scope,
                granted=scope in granted_set,
            )
        )

    return statuses


def missing_permissions(granted_scopes: list[str]) -> list[PermissionStatus]:
    return [p for p in build_permission_statuses(granted_scopes) if not p.granted]


def agent_scope(agent: str) -> str | None:
    return GITHUB_AGENT_SCOPES.get(agent)


def is_agent_scope_granted(agent: str, granted_scopes: list[str]) -> bool:
    required = agent_scope(agent)
    if required is None:
        return True
    return required in granted_scopes


GITHUB_AGENTS = frozenset(GITHUB_AGENT_SCOPES.keys())


def validate_oauth_scope(agent: str, granted_scopes: list[str]) -> str | None:
    if agent not in GITHUB_AGENTS:
        return None
    if is_agent_scope_granted(agent, granted_scopes):
        return None
    return agent_scope(agent) or ""


def detect_agent_from_error(error: str) -> str | None:
    lowered = error.lower()
    if "notification" in lowered:
        return "notifications"
    if "pull request" in lowered or "/pulls" in lowered:
        return "pulls"
    if "issue" in lowered:
        return "issues"
    if "/contents" in lowered or "/commits" in lowered or "search/code" in lowered:
        return "code"
    if "github" in lowered or "api.github.com" in lowered:
        return "repos"
    return None
