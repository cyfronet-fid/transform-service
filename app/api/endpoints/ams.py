"""AMS Health Check API Endpoints"""

from typing import Any, Dict

from fastapi import APIRouter

from app.services.ams.health import ams_health_tracker
from app.settings import settings

router = APIRouter()


@router.get("/ams/health", tags=["ams"])
@router.get("/health/ams", tags=["ams"], include_in_schema=False)
async def ams_health() -> Dict[str, Any]:
    """Get health status of AMS subscriptions and consumers"""
    return ams_health_tracker.get_health_status(ams_enabled=settings.AMS_SUBSCRIPTION)
