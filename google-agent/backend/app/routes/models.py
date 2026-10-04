"""The built-in AI models: list, download, delete, unload. Local-only (the backend binds to
127.0.0.1), and used during onboarding before sign-in, so no session is required."""

from fastapi import APIRouter, HTTPException

from app.services.platform import local_llm

router = APIRouter(prefix="/models", tags=["models"])


@router.get("")
async def list_models():
    return local_llm.catalog()


@router.post("/{model_id}/download")
async def download(model_id: str):
    try:
        local_llm.start_download(model_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return local_llm.catalog()


@router.post("/download/cancel")
async def cancel_download():
    local_llm.cancel_download()
    return local_llm.catalog()


@router.delete("/{model_id}")
async def delete(model_id: str):
    try:
        await local_llm.delete_model(model_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return local_llm.catalog()

