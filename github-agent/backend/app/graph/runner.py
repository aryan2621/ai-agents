from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import RunnableConfig

from app.agents.base import build_system_prompt
from app.graph.llm import build_chat_model
from app.models.chat import ChatMessage, LLMSettings
from app.services.grounding import empty_specialist_fallback, ground_assistant_text
from app.services.github_clients import GitHubClients
from app.services.workspace_context import extract_workspace_updates
from app.tools.registry import get_agent_prompt, get_tools_for_agent
from app.types.agents import AgentName, SPECIALIST_AGENT_NAMES

MAX_RECURSION = 15
EMPTY_SPECIALIST_RESPONSE = (
    "The specialist could not retrieve verified data for that task."
)


def _history_to_messages(
    history: list[ChatMessage],
    user_message: str,
) -> list[HumanMessage | AIMessage]:
    messages: list[HumanMessage | AIMessage] = []
    for msg in history[-20:]:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
    if (
        messages
        and isinstance(messages[-1], HumanMessage)
        and messages[-1].content.strip() == user_message.strip()
    ):
        return messages
    messages.append(HumanMessage(content=user_message))
    return messages


def build_react_graph(
    agent_name: AgentName,
    github: GitHubClients,
    settings: LLMSettings | None,
    workspace_context: dict[str, str] | None = None,
    tavily_api_key: str | None = None,
) -> CompiledStateGraph | None:
    tools = get_tools_for_agent(
        agent_name, github, workspace_context, tavily_api_key=tavily_api_key
    )
    if not tools:
        return None

    model = build_chat_model(
        settings,
        agent_name=agent_name,
    )
    prompt = build_system_prompt(get_agent_prompt(agent_name, github), workspace_context)
    return create_react_agent(model, tools, prompt=prompt, name=agent_name)


def _is_agent_response(msg: AIMessage | AIMessageChunk, metadata: dict) -> bool:
    if metadata.get("langgraph_node") != "agent":
        return False
    if msg.tool_calls or getattr(msg, "tool_call_chunks", None):
        return False
    content = msg.content
    return isinstance(content, str) and bool(content)


def _extract_final_response(messages: list) -> str | None:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            content = msg.content
            if isinstance(content, str) and content.strip():
                return content
    return None


def _messages_after_stream(baseline_messages: list, stream_messages: list) -> list:
    if stream_messages:
        return [*baseline_messages, *stream_messages]
    return baseline_messages


async def _stream_simple(
    agent_name: AgentName,
    message: str,
    history: list[ChatMessage],
    github: GitHubClients,
    settings: LLMSettings | None,
    workspace_context: dict[str, str] | None = None,
) -> AsyncGenerator[str, None]:
    model = build_chat_model(
        settings,
        agent_name=agent_name,
    )
    prompt = build_system_prompt(get_agent_prompt(agent_name, github), workspace_context)
    messages: list[dict[str, str]] = [{"role": "system", "content": prompt}]
    for msg in history[-20:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": message})

    async for chunk in model.astream(messages):
        content = chunk.content
        if isinstance(content, str) and content:
            yield content


async def stream_agent(
    agent_name: AgentName,
    message: str,
    history: list[ChatMessage],
    github: GitHubClients,
    settings: LLMSettings | None = None,
    workspace_context: dict[str, str] | None = None,
    workspace_updates: dict[str, str] | None = None,
    tavily_api_key: str | None = None,
) -> AsyncGenerator[str, None]:
    ctx = dict(workspace_context or {})
    graph = build_react_graph(
        agent_name, github, settings, ctx, tavily_api_key=tavily_api_key
    )

    if graph is None:
        async for chunk in _stream_simple(
            agent_name, message, history, github, settings, ctx
        ):
            yield chunk
        return

    config: RunnableConfig = {"recursion_limit": MAX_RECURSION}
    state: dict = {"messages": _history_to_messages(history, message)}
    stream_messages: list[AIMessage | ToolMessage] = []
    parts: list[str] = []

    async for msg, metadata in graph.astream(
        state,
        stream_mode="messages",
        config=config,
    ):
        if isinstance(msg, ToolMessage):
            stream_messages.append(msg)
            continue
        if not isinstance(msg, (AIMessageChunk, AIMessage)):
            continue
        if isinstance(msg, AIMessage):
            stream_messages.append(msg)
        if msg.tool_calls or getattr(msg, "tool_call_chunks", None):
            continue
        if not _is_agent_response(msg, metadata):
            continue
        content = msg.content  # type: ignore[misc]
        if isinstance(content, str) and content:
            parts.append(content)

    final_messages = _messages_after_stream(state["messages"], stream_messages)

    tool_messages = [m for m in final_messages if isinstance(m, ToolMessage)]
    if workspace_updates is not None and tool_messages:
        workspace_updates.update(extract_workspace_updates(tool_messages))
        ctx.update(workspace_updates)

    raw = "".join(parts).strip()
    if not raw:
        raw = (_extract_final_response(final_messages) or "").strip()

    if agent_name in SPECIALIST_AGENT_NAMES:
        grounded = ground_assistant_text(raw, tool_messages)
        if not grounded.strip():
            grounded = empty_specialist_fallback(tool_messages)
        yield grounded
        return

    if raw:
        yield raw
        return


async def collect_agent_response(
    agent_name: AgentName,
    message: str,
    history: list[ChatMessage],
    github: GitHubClients,
    settings: LLMSettings | None = None,
    workspace_context: dict[str, str] | None = None,
    workspace_updates: dict[str, str] | None = None,
    tavily_api_key: str | None = None,
) -> str:
    parts: list[str] = []
    async for chunk in stream_agent(
        agent_name,
        message,
        history,
        github,
        settings,
        workspace_context,
        workspace_updates,
        tavily_api_key=tavily_api_key,
    ):
        parts.append(chunk)
    return "".join(parts) or EMPTY_SPECIALIST_RESPONSE
