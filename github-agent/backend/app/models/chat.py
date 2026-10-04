from typing import Literal

from pydantic import BaseModel, Field

from app.constants.models import DEFAULT_LLM_MODEL


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    agent_name: str | None = None


class AgentOverride(BaseModel):
    enabled: bool = True


class LLMSettings(BaseModel):
    default_model: str = DEFAULT_LLM_MODEL
    temperature: float = 0.4
    max_tokens: int = 2048
    agent_overrides: dict[str, AgentOverride] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str
    agent_filter: str | None = None
    history: list[ChatMessage] = Field(default_factory=list)
    settings: LLMSettings | None = None
    assistant_message_id: str | None = None

