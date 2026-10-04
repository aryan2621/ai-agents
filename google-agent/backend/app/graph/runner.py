from collections.abc import AsyncGenerator

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from app.agents.base import build_system_prompt
from app.graph.llm import build_chat_model, ensure_model_running
from app.models.chat import ChatMessage, LLMSettings
from app.services.workspace.grounding import empty_specialist_fallback, ground_assistant_text
from app.services.google_clients import GoogleClients
from app.services.workspace.workspace_context import extract_workspace_updates
from app.tools.registry import get_agent_prompt, get_tools_for_agent
from app.types.agents import AgentName

MAX_RECURSION = 15


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


async def stream_agent(
    agent_name: AgentName,
    message: str,
    history: list[ChatMessage],
    google: GoogleClients,
    settings: LLMSettings | None = None,
    workspace_context: dict[str, str] | None = None,
    workspace_updates: dict[str, str] | None = None,
    tavily_api_key: str | None = None,
) -> AsyncGenerator[tuple[str, str], None]:
    """Yields ("delta", text) as the model writes, then ("final", text): the checked answer.

    Deltas go straight to the screen so the reply appears while it is generated. Text a model
    writes before deciding to call a tool is not the answer, so a ("reset", "") clears it; the
    final text replaces whatever was shown if grounding changed it.
    """
    ctx = dict(workspace_context or {})
    await ensure_model_running(settings)
    tools = get_tools_for_agent(agent_name, google, ctx, tavily_api_key=tavily_api_key)
    model = build_chat_model(settings)
    prompt = build_system_prompt(get_agent_prompt(agent_name, google), ctx)
    graph = create_react_agent(model, tools, prompt=prompt, name=agent_name)

    tool_messages: list[ToolMessage] = []
    current: list[str] = []  # text of the agent message being written

    async for msg, metadata in graph.astream(
        {"messages": _history_to_messages(history, message)},
        stream_mode="messages",
        config={"recursion_limit": MAX_RECURSION},
    ):
        if isinstance(msg, ToolMessage):
            tool_messages.append(msg)
            continue
        if not isinstance(msg, (AIMessageChunk, AIMessage)):
            continue
        if metadata.get("langgraph_node") != "agent":
            continue
        if msg.tool_calls or getattr(msg, "tool_call_chunks", None):
            if current:
                current = []
                yield "reset", ""
            continue
        content = msg.content
        if isinstance(content, str) and content:
            current.append(content)
            yield "delta", content

    if workspace_updates is not None and tool_messages:
        workspace_updates.update(extract_workspace_updates(tool_messages))

    final = ground_assistant_text("".join(current).strip(), tool_messages)
    if not final.strip():
        final = empty_specialist_fallback(tool_messages)
    yield "final", final
