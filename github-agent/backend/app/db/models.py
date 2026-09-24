from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.json_type import json_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    oauth_token: Mapped[OAuthToken | None] = relationship(back_populates="user", uselist=False)
    conversations: Mapped[list[Conversation]] = relationship(back_populates="user")
    settings: Mapped[UserSettings | None] = relationship(back_populates="user", uselist=False)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    access_token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    github_access_token: Mapped[str] = mapped_column(Text, default="")
    refresh_token: Mapped[str] = mapped_column(Text, default="")
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)
    granted_scopes: Mapped[str] = mapped_column(Text, default="")

    user: Mapped[User] = relationship(back_populates="oauth_token")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    agent_filter: Mapped[str] = mapped_column(String(32), default="")
    workspace_context: Mapped[dict] = mapped_column(json_column, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.timestamp",
        lazy="selectin",
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    agent_name: Mapped[str | None] = mapped_column(String(32), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    ollama_base_url: Mapped[str] = mapped_column(String(255), default="http://127.0.0.1:11434")
    default_model: Mapped[str] = mapped_column(String(128), default="ministral-3:8b")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    send_on_enter: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_scroll: Mapped[bool] = mapped_column(Boolean, default=True)
    font_size: Mapped[str] = mapped_column(String(8), default="md")
    theme: Mapped[str] = mapped_column(String(8), default="system")
    debug_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    agent_overrides: Mapped[dict] = mapped_column(json_column, default=dict)
    tavily_search_api_key: Mapped[str] = mapped_column(String(255), default="")
    gemini_api_key: Mapped[str] = mapped_column(String(255), default="")
    groq_api_key: Mapped[str] = mapped_column(String(255), default="")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="settings")


class TurnTrace(Base):
    __tablename__ = "turn_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    assistant_message_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    user_input: Mapped[str] = mapped_column(Text, default="")
    ai_input: Mapped[dict] = mapped_column(json_column, default=dict)
    ai_output: Mapped[str] = mapped_column(Text, default="")
    agent_name: Mapped[str] = mapped_column(String(32), default="orchestrator")
    model: Mapped[str] = mapped_column(String(128), default="")
    routing_method: Mapped[str] = mapped_column(String(32), default="")
    routing_detail: Mapped[dict] = mapped_column(json_column, default=dict)
    tool_calls: Mapped[list] = mapped_column(json_column, default=list)
    ai_messages: Mapped[list] = mapped_column(json_column, default=list)
    turn_timeline: Mapped[list] = mapped_column(json_column, default=list)
    workspace_context_before: Mapped[dict] = mapped_column(json_column, default=dict)
    workspace_context_after: Mapped[dict] = mapped_column(json_column, default=dict)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
