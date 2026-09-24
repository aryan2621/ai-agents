from fastapi import APIRouter, Header

from app.db.database import async_session
from app.services.auth.auth_service import get_user_by_access_token
from app.services.workspace.conversation_service import get_or_create_settings
from app.services.platform.health_service import health_status

router = APIRouter()


@router.get("/health")
async def health(authorization: str | None = Header(default=None)):
    user_ollama: str | None = None
    if authorization and authorization.startswith("Bearer "):
        try:
            async with async_session() as session:
                row = await get_user_by_access_token(session, authorization[7:])
                if row is not None:
                    settings = await get_or_create_settings(session, row[0].id)
                    user_ollama = getattr(settings, "ollama_base_url", None)
        except Exception:
            pass
    return await health_status(user_ollama)
