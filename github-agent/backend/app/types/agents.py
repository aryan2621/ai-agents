from typing import Literal, TypeAlias

AgentName: TypeAlias = Literal[
    "repos",
    "issues",
    "pulls",
    "code",
    "notifications",
    "web",
]

ROOM_AGENT_NAMES: tuple[AgentName, ...] = (
    "repos",
    "issues",
    "pulls",
    "code",
    "notifications",
    "web",
)

GITHUB_ROOM_AGENT_NAMES: tuple[AgentName, ...] = (
    "repos",
    "issues",
    "pulls",
    "code",
    "notifications",
)

AGENT_ROOM_REQUIRED = (
    "This chat is not tied to an agent. Start a new chat from the home screen."
)
INVALID_AGENT_ROOM = (
    "Select an agent room: repos, issues, pulls, code, notifications, or web."
)
AGENT_DISABLED = "This agent is disabled in Settings."


def is_room_agent(name: str | None) -> bool:
    return name in ROOM_AGENT_NAMES

