from fastapi import APIRouter
from datetime import datetime

from .files import router as files_router
from models.file import HealthCheckResponse

router = APIRouter()

# Include sub-routers
router.include_router(files_router)


@router.get("/", response_model=HealthCheckResponse)
async def root():
    """Health check endpoint"""
    return HealthCheckResponse(
        message="File Service is running",
        timestamp=datetime.now().isoformat()
    )
