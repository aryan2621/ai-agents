import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.router import resolve_agent_pipeline
from app.graph.runner import stream_agent
from app.db.database import get_db
from app.models.chat import ChatMessage, ChatRequest, LLMSettings, PreflightRequest, PreflightResponse
from app.services.auth_service import get_user_by_access_token
from app.graph.llm import NO_LLM_CONFIGURED
from app.services.llm_keys import apply_keys_to_llm_settings, llm_provider_configured
from app.services.tavily_search import resolve_tavily_api_key
from app.services.conversation_service import (
    add_message,
    get_conversation,
    get_conversation_history,
    get_or_create_settings,
    merge_workspace_context,
    get_workspace_context,
)
from app.services.datetime_display import humanize_iso_datetimes
from app.services.github_clients import GitHubClients
from app.services.github_oauth import get_valid_credentials
from app.services.scope_registry import (
    AGENT_LABELS,
    InsufficientScopeError,
    agent_scope,
    detect_agent_from_error,
    effective_granted_scopes,
    is_agent_scope_granted,
    validate_oauth_scope,
)
from app.types.agents import (
    AGENT_DISABLED,
    AGENT_ROOM_REQUIRED,
    SPECIALIST_AGENT_NAMES,
    AgentName,
    is_room_agent,
)
from app.types.api import PermissionErrorPayload

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger("app.chat")

EMPTY_SPECIALIST_RESPONSE = (
    "The specialist could not retrieve verified data for that task."
)
WEB_SEARCH_NOT_CONFIGURED = (
    "Tavily API key is not configured. Add it in Settings → Web Search."
)


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization[7:]


def _permission_error_payload(agent: str, scope: str) -> PermissionErrorPayload:
    label = AGENT_LABELS.get(agent, agent)
    return {
        "error": f"{label} permission was not granted on GitHub. Re-authenticate to grant access.",
        "code": "INSUFFICIENT_SCOPE",
        "agent": agent,
        "scope": scope,
        "label": label,
    }


def _locked_room_agent(agent_filter: str | None) -> AgentName | None:
    if is_room_agent(agent_filter):
        return agent_filter  # type: ignore[return-value]
    return None


async def _resolve_history(
    session: AsyncSession,
    user_id: str,
    conversation_id: str,
    client_history: list[ChatMessage],
) -> list[ChatMessage]:
    db_history = await get_conversation_history(session, user_id, conversation_id)
    if db_history:
        return db_history
    return client_history


def _llm_settings_with_keys(
    body_settings: LLMSettings | None, user_settings
) -> LLMSettings:
    return apply_keys_to_llm_settings(body_settings, user_settings)


async def _stream_chat(
    body: ChatRequest, access_token: str, session: AsyncSession
) -> AsyncGenerator[str, None]:
    try:
        creds = await get_valid_credentials(session, access_token)
    except ValueError as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        return

    user_row = await get_user_by_access_token(session, access_token)
    user_id = user_row[0].id if user_row else creds.user_id

    conv = await get_conversation(session, user_id, body.conversation_id)
    if conv is None:
        yield f"data: {json.dumps({'error': 'Conversation not found'})}\n\n"
        return

    locked_agent = _locked_room_agent(conv.agent_filter)
    if locked_agent is None:
        yield f"data: {json.dumps({'error': AGENT_ROOM_REQUIRED})}\n\n"
        return

    granted = effective_granted_scopes(creds.granted_scopes)
    user_settings = await get_or_create_settings(session, user_id)
    settings = _llm_settings_with_keys(body.settings, user_settings)
    if not llm_provider_configured(settings.ollama_base_url):
        yield f"data: {json.dumps({'error': NO_LLM_CONFIGURED})}\n\n"
        return
    tavily_api_key = resolve_tavily_api_key(
        getattr(user_settings, "tavily_search_api_key", None)
    )
    history = await _resolve_history(session, user_id, body.conversation_id, body.history)
    workspace_ctx = await get_workspace_context(session, user_id, body.conversation_id)

    yield ": connected\n\n"

    try:
        pipeline = await resolve_agent_pipeline(
            body.message,
            locked_agent,
            settings,
            creds,
            history,
            workspace_ctx,
        )
    except Exception as e:
        logger.exception("Agent routing failed")
        yield f"data: {json.dumps({'error': str(e) or 'Routing failed'})}\n\n"
        return

    if not pipeline.agents:
        error = AGENT_DISABLED if pipeline.method == "disabled" else AGENT_ROOM_REQUIRED
        yield f"data: {json.dumps({'error': error})}\n\n"
        return

    agent_name = pipeline.agents[0]

    logger.info(
        "Chat stream agent=%s message=%r history_len=%d",
        agent_name,
        body.message[:200],
        len(history),
    )

    missing_scope = validate_oauth_scope(agent_name, granted)
    if missing_scope:
        yield f"data: {json.dumps(_permission_error_payload(agent_name, missing_scope))}\n\n"
        return
    if agent_name == "web" and not tavily_api_key:
        yield f"data: {json.dumps({'error': WEB_SEARCH_NOT_CONFIGURED})}\n\n"
        return

    yield f"data: {json.dumps({'agent': agent_name, 'agents': [agent_name]})}\n\n"

    github = GitHubClients(creds, workspace_ctx)
    display_tz = "UTC"
    full_response: list[str] = []
    workspace_updates: dict[str, str] = {}
    running_workspace = dict(workspace_ctx or {})
    if running_workspace:
        logger.info("Workspace context loaded: %s", running_workspace)

    try:
        async for chunk in stream_agent(
            agent_name,
            body.message,
            history,
            github,
            settings,
            running_workspace,
            workspace_updates,
            tavily_api_key=tavily_api_key,
        ):
            humanized = humanize_iso_datetimes(chunk, display_tz)
            full_response.append(humanized)
            yield f"data: {json.dumps({'chunk': humanized})}\n\n"
        running_workspace.update(workspace_updates)
    except InsufficientScopeError as e:
        yield f"data: {json.dumps(_permission_error_payload(e.agent, e.scope))}\n\n"
        return
    except Exception as e:
        err = str(e)
        detected = detect_agent_from_error(err)
        if detected and not is_agent_scope_granted(detected, granted):
            scope = agent_scope(detected) or ""
            yield f"data: {json.dumps(_permission_error_payload(detected, scope))}\n\n"
            return
        if "403" in err or "insufficient" in err.lower():
            detected = detected or agent_name
            scope = agent_scope(detected) or ""
            if scope and not is_agent_scope_granted(detected, granted):
                yield f"data: {json.dumps(_permission_error_payload(detected, scope))}\n\n"
                return
        yield f"data: {json.dumps({'error': err})}\n\n"
        return

    content = "".join(full_response)
    if not content and agent_name in SPECIALIST_AGENT_NAMES:
        yield f"data: {json.dumps({'error': EMPTY_SPECIALIST_RESPONSE})}\n\n"
        return

    if workspace_updates:
        await merge_workspace_context(
            session, user_id, body.conversation_id, workspace_updates
        )
    if body.assistant_message_id and content:
        await add_message(
            session,
            user_id,
            body.conversation_id,
            body.assistant_message_id,
            "assistant",
            content,
            agent_name,
        )

    yield "data: [DONE]\n\n"


@router.post("/preflight", response_model=PreflightResponse)
async def chat_preflight(
    body: PreflightRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> PreflightResponse:
    access_token = _extract_bearer(authorization)
    creds = await get_valid_credentials(session, access_token)
    granted = effective_granted_scopes(creds.granted_scopes)

    user_row = await get_user_by_access_token(session, access_token)
    user_id = user_row[0].id if user_row else creds.user_id
    user_settings = await get_or_create_settings(session, user_id)
    settings = _llm_settings_with_keys(body.settings, user_settings)
    if not llm_provider_configured(settings.ollama_base_url):
        raise HTTPException(status_code=400, detail=NO_LLM_CONFIGURED)
    tavily_api_key = resolve_tavily_api_key(
        getattr(user_settings, "tavily_search_api_key", None)
    )

    if not body.conversation_id:
        raise HTTPException(status_code=400, detail=AGENT_ROOM_REQUIRED)

    conv = await get_conversation(session, user_id, body.conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    locked_agent = _locked_room_agent(conv.agent_filter)
    if locked_agent is None:
        raise HTTPException(status_code=400, detail=AGENT_ROOM_REQUIRED)

    history = await get_conversation_history(session, user_id, body.conversation_id)
    workspace_ctx = await get_workspace_context(session, user_id, body.conversation_id)
    pipeline = await resolve_agent_pipeline(
        body.message,
        locked_agent,
        settings,
        creds,
        history,
        workspace_ctx,
    )
    if not pipeline.agents:
        detail = AGENT_DISABLED if pipeline.method == "disabled" else AGENT_ROOM_REQUIRED
        raise HTTPException(status_code=400, detail=detail)

    primary_agent = pipeline.primary_agent
    label = AGENT_LABELS.get(primary_agent, primary_agent)
    missing_scope = validate_oauth_scope(primary_agent, granted)
    web_search_configured = not (primary_agent == "web" and not tavily_api_key)
    return PreflightResponse(
        agent=primary_agent,
        label=label,
        agents=list(pipeline.agents),
        oauth_granted=missing_scope is None,
        scope=missing_scope,
        web_search_configured=web_search_configured,
    )


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    access_token = _extract_bearer(authorization)
    return StreamingResponse(
        _stream_chat(body, access_token, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
