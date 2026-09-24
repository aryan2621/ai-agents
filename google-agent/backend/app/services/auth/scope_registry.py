from dataclasses import dataclass

PROFILE_SCOPES = ("openid", "email", "profile")

GOOGLE_AGENT_SCOPES: dict[str, str] = {
    "gmail": "https://www.googleapis.com/auth/gmail.modify",
    "calendar": "https://www.googleapis.com/auth/calendar",
    "drive": "https://www.googleapis.com/auth/drive",
    "docs": "https://www.googleapis.com/auth/documents",
    "sheets": "https://www.googleapis.com/auth/spreadsheets",
}

SCOPE_LABELS: dict[str, str] = {
    "openid": "OpenID Connect",
    "email": "Email address",
    "profile": "Profile",
    "https://www.googleapis.com/auth/gmail.modify": "Gmail",
    "https://www.googleapis.com/auth/calendar": "Google Calendar",
    "https://www.googleapis.com/auth/drive": "Google Drive",
    "https://www.googleapis.com/auth/documents": "Google Docs",
    "https://www.googleapis.com/auth/spreadsheets": "Google Sheets",
}

AGENT_LABELS: dict[str, str] = {
    "gmail": "Gmail",
    "calendar": "Google Calendar",
    "drive": "Google Drive",
    "docs": "Google Docs",
    "sheets": "Google Sheets",
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
    return [s for s in scope_string.split() if s]


def effective_granted_scopes(scope_string: str) -> list[str]:
    """Return stored scopes; empty means profile-only (re-auth required for agents)."""
    if scope_string.strip():
        return parse_granted_scopes(scope_string)
    return list(PROFILE_SCOPES)


def scopes_to_string(scopes: list[str]) -> str:
    return " ".join(scopes)


def build_permission_statuses(granted_scopes: list[str]) -> list[PermissionStatus]:
    granted_set = set(granted_scopes)
    statuses: list[PermissionStatus] = []

    for scope in PROFILE_SCOPES:
        statuses.append(
            PermissionStatus(
                id=scope,
                label=SCOPE_LABELS.get(scope, scope),
                scope=scope,
                granted=scope in granted_set,
            )
        )

    for agent, scope in GOOGLE_AGENT_SCOPES.items():
        statuses.append(
            PermissionStatus(
                id=agent,
                label=AGENT_LABELS.get(agent, agent),
                scope=scope,
                granted=scope in granted_set,
            )
        )

    return statuses


def missing_permissions(granted_scopes: list[str]) -> list[PermissionStatus]:
    return [p for p in build_permission_statuses(granted_scopes) if not p.granted]


def agent_scope(agent: str) -> str | None:
    return GOOGLE_AGENT_SCOPES.get(agent)


def is_agent_scope_granted(agent: str, granted_scopes: list[str]) -> bool:
    required = agent_scope(agent)
    if required is None:
        return True
    return required in granted_scopes


GOOGLE_AGENTS = frozenset(GOOGLE_AGENT_SCOPES.keys())


def validate_oauth_scope(agent: str, granted_scopes: list[str]) -> str | None:
    if agent not in GOOGLE_AGENTS:
        return None
    if is_agent_scope_granted(agent, granted_scopes):
        return None
    return agent_scope(agent) or ""


def detect_agent_from_error(error: str) -> str | None:
    lowered = error.lower()
    if "gmail" in lowered:
        return "gmail"
    if "calendar" in lowered:
        return "calendar"
    if "drive" in lowered:
        return "drive"
    if "document" in lowered or "docs" in lowered:
        return "docs"
    if "spreadsheet" in lowered or "sheets" in lowered:
        return "sheets"
    return None
