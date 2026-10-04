from fastapi import APIRouter

from app.services.health_service import health_status

router = APIRouter()


@router.get("/health")
async def health():
    return await health_status()
