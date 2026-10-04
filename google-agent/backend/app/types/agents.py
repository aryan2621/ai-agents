from typing import Literal, TypeAlias

AgentName: TypeAlias = Literal[
    "gmail",
    "calendar",
    "drive",
    "docs",
    "sheets",
    "web",
]

ROOM_AGENT_NAMES: tuple[AgentName, ...] = (
    "gmail",
    "calendar",
    "drive",
    "docs",
    "sheets",
    "web",
)

GOOGLE_ROOM_AGENT_NAMES: tuple[AgentName, ...] = (
    "gmail",
    "calendar",
    "drive",
    "docs",
    "sheets",
)

AGENT_ROOM_REQUIRED = (
    "This chat is not tied to an agent. Start a new chat from the home screen."
)
INVALID_AGENT_ROOM = (
    "Select an agent room: gmail, calendar, drive, docs, sheets, or web."
)
AGENT_DISABLED = "This agent is disabled in Settings."


def is_room_agent(name: str | None) -> bool:
    return name in ROOM_AGENT_NAMES
