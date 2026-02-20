"""Health check endpoints."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.cache import get_cache
from src.core.config import settings
from src.db.session import get_db

router = APIRouter()


@router.get(
    "",
    summary="Health Check",
    description="Basic health check endpoint.",
    response_description="Health status",
)
async def health_check() -> dict[str, Any]:
    """
    Basic health check.

    Returns application status and version info.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "version": "1.0.0",
    }


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Check if the application is ready to serve traffic.",
    response_description="Readiness status with service checks",
)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness check with dependency verification.

    Checks database connectivity and cache availability.
    """
    checks: dict[str, Any] = {}
    all_healthy = True

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check cache
    try:
        cache = get_cache()
        await cache.set("health_check", "ok", ttl=10)
        value = await cache.get("health_check")
        if value == "ok":
            checks["cache"] = {"status": "healthy"}
        else:
            checks["cache"] = {"status": "degraded", "message": "Cache write/read mismatch"}
            all_healthy = False
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
    }


@router.get(
    "/live",
    summary="Liveness Check",
    description="Check if the application process is alive.",
    response_description="Liveness status",
)
async def liveness_check() -> dict[str, str]:
    """
    Liveness check.

    Simple check to verify the application is running.
    Used by Kubernetes/container orchestrators.
    """
    return {"status": "alive"}
