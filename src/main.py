"""
Location Intelligence API - Main Application Entry Point.

This module initializes and configures the FastAPI application with:
- Rate limiting middleware
- API versioning
- OpenAPI documentation
- Database lifecycle management
- Redis caching (when available)
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1 import api_router
from src.core.cache import set_redis_cache
from src.core.config import settings
from src.core.rate_limit import set_redis_rate_limiter
from src.db.session import close_db, init_db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if settings.log_format == "text"
    else '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database, connect to Redis
    - Shutdown: Close database connections, disconnect from Redis
    """
    # Startup
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize Redis (optional - falls back to in-memory if unavailable)
    try:
        import redis.asyncio as redis
        
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        
        # Test connection
        await redis_client.ping()
        
        # Set up Redis-based caching and rate limiting
        set_redis_cache(redis_client)
        set_redis_rate_limiter(redis_client)
        
        logger.info("Redis connected successfully")
        
        # Store client for cleanup
        app.state.redis = redis_client
    except Exception as e:
        logger.warning(f"Redis not available, using in-memory fallback: {e}")
        app.state.redis = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Close Redis connection
    if hasattr(app.state, "redis") and app.state.redis:
        await app.state.redis.close()
        logger.info("Redis connection closed")
    
    # Close database connections
    await close_db()
    logger.info("Database connections closed")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        description="""
## Location Intelligence API

A production-ready FastAPI application for geocoding and location services:

- **JWT Authentication** - Secure access and refresh tokens
- **API Versioning** - Clean versioned API structure
- **Rate Limiting** - Protection against abuse
- **Caching** - Redis-backed with in-memory fallback

### Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <access_token>
```

### Rate Limiting

API endpoints are rate limited. Check response headers for current limits:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
        """,
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle validation errors with consistent response format."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected errors."""
        logger.exception(f"Unhandled exception: {exc}")
        
        # Don't expose internal errors in production
        if settings.is_production:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": "internal_error",
                    "message": "An unexpected error occurred",
                },
            )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "internal_error",
                "message": str(exc),
            },
        )
    
    # Include API routers
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "docs": f"{settings.api_v1_prefix}/docs" if settings.debug else "disabled",
            "health": f"{settings.api_v1_prefix}/health",
        }
    
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        workers=settings.workers if settings.is_production else 1,
        log_level=settings.log_level.lower(),
    )
