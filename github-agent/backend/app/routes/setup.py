from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.app_config import (
    oauth_is_configured,
    resolve_github_credentials,
    save_oauth_credentials,
)
from app.services import local_llm
from app.services.llm_keys import llm_provider_configured

router = APIRouter(prefix="/setup", tags=["setup"])


class OAuthSetupRequest(BaseModel):
    clientId: str = Field(min_length=1)
    clientSecret: str = Field(min_length=1)


class OAuthStatusResponse(BaseModel):
    configured: bool
    clientIdPreview: str = ""


class LlmStatusResponse(BaseModel):
    configured: bool
    recommended: str = ""
    installed: list[str] = Field(default_factory=list)


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
    return LlmStatusResponse(
        configured=llm_provider_configured(),
        recommended=local_llm.recommended(),
        installed=local_llm.installed(),
    )
