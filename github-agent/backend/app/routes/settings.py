from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.models import normalize_llm_model
from app.db.database import get_db
from app.services.app_config import save_ollama_config
from app.services.auth_service import get_user_by_access_token
from app.services.conversation_service import DEFAULT_AGENT_OVERRIDES, get_or_create_settings

router = APIRouter(prefix="/settings", tags=["settings"])


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization[7:]


class AgentOverrideOut(BaseModel):
    enabled: bool = True


class SettingsOut(BaseModel):
    defaultModel: str
    temperature: float
    maxTokens: int
    sendOnEnter: bool
    autoScroll: bool
    fontSize: str
    theme: str = "system"
    onboardingCompleted: bool = False
    tavilySearchApiKey: str = ""
    ollamaBaseUrl: str = ""
    agentOverrides: dict[str, AgentOverrideOut] = Field(default_factory=dict)


class SettingsUpdate(BaseModel):
    defaultModel: str | None = None
    temperature: float | None = None
    maxTokens: int | None = None
    sendOnEnter: bool | None = None
    autoScroll: bool | None = None
    fontSize: str | None = None
    theme: str | None = None
    onboardingCompleted: bool | None = None
    tavilySearchApiKey: str | None = None
    ollamaBaseUrl: str | None = None
    agentOverrides: dict[str, AgentOverrideOut] | None = None


def _to_out(s) -> SettingsOut:
    overrides = s.agent_overrides or DEFAULT_AGENT_OVERRIDES
    return SettingsOut(
        defaultModel=s.default_model,
        temperature=s.temperature,
        maxTokens=s.max_tokens,
        sendOnEnter=s.send_on_enter,
        autoScroll=s.auto_scroll,
        fontSize=s.font_size,
        theme=getattr(s, "theme", None) or "system",
        onboardingCompleted=bool(getattr(s, "onboarding_completed", False)),
        tavilySearchApiKey=getattr(s, "tavily_search_api_key", "") or "",
        ollamaBaseUrl=getattr(s, "ollama_base_url", "") or "",
        agentOverrides={
            k: AgentOverrideOut(**v) if isinstance(v, dict) else AgentOverrideOut(enabled=True)
            for k, v in overrides.items()
        },
    )


@router.get("", response_model=SettingsOut)
async def get_settings(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    row = await get_user_by_access_token(session, token)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    user, _ = row
    settings = await get_or_create_settings(session, user.id)
    return _to_out(settings)


@router.put("", response_model=SettingsOut)
async def put_settings(
    body: SettingsUpdate,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    row = await get_user_by_access_token(session, token)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    user, _ = row
    settings = await get_or_create_settings(session, user.id)

    if body.defaultModel is not None:
        settings.default_model = normalize_llm_model(body.defaultModel)
    if body.temperature is not None:
        settings.temperature = max(0.0, min(2.0, body.temperature))
    if body.maxTokens is not None:
        settings.max_tokens = max(256, min(8192, body.maxTokens))
    if body.sendOnEnter is not None:
        settings.send_on_enter = body.sendOnEnter
    if body.autoScroll is not None:
        settings.auto_scroll = body.autoScroll
    if body.fontSize is not None:
        settings.font_size = body.fontSize
    if body.theme is not None:
        settings.theme = body.theme
    if body.onboardingCompleted is not None:
        settings.onboarding_completed = body.onboardingCompleted
    if body.tavilySearchApiKey is not None:
        settings.tavily_search_api_key = body.tavilySearchApiKey.strip()
    if body.ollamaBaseUrl is not None:
        settings.ollama_base_url = body.ollamaBaseUrl.strip()
    if body.defaultModel is not None or body.ollamaBaseUrl is not None:
        save_ollama_config(
            base_url=body.ollamaBaseUrl.strip() if body.ollamaBaseUrl is not None else None,
            model=settings.default_model if body.defaultModel is not None else None,
        )
    if body.agentOverrides is not None:
        from app.types.agents import ROOM_AGENT_NAMES, is_room_agent

        merged: dict[str, dict] = {name: {"enabled": True} for name in ROOM_AGENT_NAMES}
        for key, value in body.agentOverrides.items():
            if is_room_agent(key):
                merged[key] = {"enabled": value.enabled}
        settings.agent_overrides = merged

    await session.commit()
    await session.refresh(settings)
    return _to_out(settings)
