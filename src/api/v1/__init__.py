"""API v1 routes."""

from fastapi import APIRouter

from src.api.v1.routes import auth, health, users, geocode, normalize

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(geocode.router, prefix="/geocode", tags=["Geocode"])
api_router.include_router(normalize.router, prefix="/normalize", tags=["Normalize"])

__all__ = ["api_router"]
