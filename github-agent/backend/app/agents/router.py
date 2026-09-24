import logging
from dataclasses import dataclass, field

from app.agents.base import get_agent
from app.models.chat import ChatMessage, LLMSettings
from app.services.auth_service import StoredCredentials
from app.services.github_clients import GitHubClients
from app.types.agents import ROOM_AGENT_NAMES, AgentName, is_room_agent

logger = logging.getLogger("app.router")


@dataclass
class AgentResolution:
    agent: AgentName
    method: str
    detail: dict = field(default_factory=dict)


@dataclass
class AgentPipelineResolution:
    agents: list[AgentName]
    method: str
    detail: dict = field(default_factory=dict)

    @property
    def primary_agent(self) -> AgentName:
        if not self.agents:
            raise ValueError("No agent resolved")
        return self.agents[0]


def _resolve_if_enabled(
    agent_name: AgentName,
    settings: LLMSettings | None,
    creds: StoredCredentials,
) -> AgentName | None:
    agent = get_agent(agent_name, GitHubClients(creds))
    if agent.is_enabled(settings):
        return agent_name
    return None


async def resolve_agent(
    message: str,
    agent_filter: str | None,
    settings: LLMSettings | None,
    creds: StoredCredentials,
    history: list[ChatMessage] | None = None,
    workspace_context: dict[str, str] | None = None,
) -> AgentResolution:
    pipeline = await resolve_agent_pipeline(
        message, agent_filter, settings, creds, history, workspace_context
    )
    return AgentResolution(pipeline.primary_agent, pipeline.method, pipeline.detail)


async def resolve_agent_pipeline(
    message: str,
    agent_filter: str | None,
    settings: LLMSettings | None,
    creds: StoredCredentials,
    history: list[ChatMessage] | None = None,
    workspace_context: dict[str, str] | None = None,
) -> AgentPipelineResolution:
    del message, history, workspace_context

    if not is_room_agent(agent_filter) or agent_filter not in ROOM_AGENT_NAMES:
        return AgentPipelineResolution([], "missing_room", {"filter": agent_filter})

    locked: AgentName = agent_filter  # type: ignore[assignment]
    resolved = _resolve_if_enabled(locked, settings, creds)
    if resolved is None:
        logger.info("Locked agent %s is disabled", locked)
        return AgentPipelineResolution([], "disabled", {"filter": locked})

    return AgentPipelineResolution(
        [resolved],
        "agent_filter",
        {"filter": locked},
    )
