"""
Health Check Routes
"""
import logging
from fastapi import APIRouter
from ..models.quiz import HealthResponse
from ..models.user import Database
from ..config import get_settings
from ..core.config import INDEX_PATH, META_PATH

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health status."""
    # Check services
    db = Database(settings.data_dir)
    
    services = {
        "api": True,
        "database": db.check_health(),
        "vectorstore": INDEX_PATH.exists() and META_PATH.exists()
    }
    
    all_healthy = all(services.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        version=settings.app_version,
        services=services
    )
