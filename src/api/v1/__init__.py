"""API v1 routes."""

from fastapi import APIRouter

from src.api.v1.routes import auth, health, users

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

__all__ = ["api_router"]
