from fastapi import APIRouter
from api.schemas.common import UnifiedResponse

router = APIRouter(prefix="/api/v1/health", tags=["System"])

@router.get("", response_model=UnifiedResponse)
async def health_check():
    return UnifiedResponse(status="success", message="RagnaRok API is running and healthy")
