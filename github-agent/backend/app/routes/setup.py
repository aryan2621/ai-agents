from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.app_config import (
    oauth_is_configured,
    resolve_github_credentials,
    save_oauth_credentials,
    save_ollama_config,
)
from app.services.llm_keys import (
    llm_provider_configured,
    ollama_is_reachable,
    resolve_ollama_base_url,
)

router = APIRouter(prefix="/setup", tags=["setup"])


class OAuthSetupRequest(BaseModel):
    clientId: str = Field(min_length=1)
    clientSecret: str = Field(min_length=1)


class OAuthStatusResponse(BaseModel):
    configured: bool
    clientIdPreview: str = ""


class LlmSetupRequest(BaseModel):
    ollamaBaseUrl: str = ""
    defaultModel: str = ""


class LlmStatusResponse(BaseModel):
    configured: bool
    ollamaConfigured: bool
    ollamaBaseUrl: str = ""


@router.get("/oauth/status", response_model=OAuthStatusResponse)
async def oauth_status():
    client_id, _ = resolve_github_credentials()
    preview = ""
    if client_id:
        preview = client_id[:12] + "…" if len(client_id) > 12 else client_id
    return OAuthStatusResponse(configured=oauth_is_configured(), clientIdPreview=preview)


@router.post("/oauth")
async def save_oauth(body: OAuthSetupRequest):
    if not body.clientId.strip() or not body.clientSecret.strip():
        raise HTTPException(status_code=400, detail="Client ID and secret are required")
    path = save_oauth_credentials(body.clientId.strip(), body.clientSecret.strip())
    return {
        "ok": True,
        "message": "OAuth credentials saved. You can sign in with GitHub now.",
        "path": str(path),
    }


@router.get("/llm/status", response_model=LlmStatusResponse)
async def llm_status():
    ollama_url = resolve_ollama_base_url()
    ollama = ollama_is_reachable(ollama_url)
    return LlmStatusResponse(
        configured=llm_provider_configured(ollama_url),
        ollamaConfigured=ollama,
        ollamaBaseUrl=ollama_url,
    )


@router.post("/llm")
async def save_llm(body: LlmSetupRequest):
    ollama_url = body.ollamaBaseUrl.strip()
    model = body.defaultModel.strip()
    if ollama_url or model:
        save_ollama_config(base_url=ollama_url or None, model=model or None)
    ollama_url = resolve_ollama_base_url(ollama_url or None)
    if not llm_provider_configured(ollama_url):
        raise HTTPException(
            status_code=400,
            detail="Start Ollama locally and pull a model.",
        )
    return {
        "ok": True,
        "message": "LLM settings saved.",
        "configured": True,
        "ollamaConfigured": ollama_is_reachable(ollama_url),
    }
