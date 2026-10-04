"""Records the app keeps on disk. Plain dataclasses, saved as JSON by app.db.database."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.constants.models import DEFAULT_LLM_MODEL


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    id: str
    email: str
    name: str
    picture: str = ""
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class OAuthToken:
    user_id: str
    access_token: str
    expires_at: int
    github_access_token: str = ""
    refresh_token: str = ""
    granted_scopes: str = ""


@dataclass
class Message:
    id: str
    conversation_id: str
    role: str
    content: str = ""
    agent_name: str | None = None
    timestamp: datetime = field(default_factory=utcnow)


@dataclass
class Conversation:
    id: str
    user_id: str
    title: str = "New Chat"
    agent_filter: str = ""
    workspace_context: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    messages: list[Message] = field(default_factory=list)


@dataclass
class UserSettings:
    user_id: str
    default_model: str = DEFAULT_LLM_MODEL
    temperature: float = 0.7
    max_tokens: int = 2048
    send_on_enter: bool = True
    auto_scroll: bool = True
    font_size: str = "md"
    theme: str = "system"
    debug_mode: bool = False
    agent_overrides: dict = field(default_factory=dict)
    tavily_search_api_key: str = ""
    onboarding_completed: bool = False
