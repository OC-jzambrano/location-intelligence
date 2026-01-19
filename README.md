# FastAPI REST API Starter

A production-grade FastAPI REST API starter kit with JWT authentication, API versioning, rate limiting, and caching. Designed for building scalable, maintainable backend services.

## Overview

This starter kit provides a solid foundation for building production REST APIs with FastAPI. It implements common patterns and best practices out of the box, allowing you to focus on your business logic instead of boilerplate.

**Key Characteristics:**
- Production-ready architecture with clear separation of concerns
- Async-first design using SQLAlchemy 2.0 and asyncpg
- Type-safe with full type hints and Pydantic validation
- Containerized deployment with Docker and docker-compose
- Comprehensive security with JWT tokens and rate limiting

## Who This Is For

- Backend engineers starting new API projects
- Teams wanting a standardized FastAPI structure
- Developers who need auth, caching, and rate limiting out of the box
- Organizations requiring production-ready API foundations

**Prerequisites:**
- Python 3.11+
- Docker and docker-compose
- Basic understanding of FastAPI and async Python

## What's Included

| Feature | Implementation |
|---------|---------------|
| JWT Authentication | Access + refresh tokens with secure password hashing |
| API Versioning | Prefixed routes (`/api/v1`) with clean separation |
| Rate Limiting | Sliding window algorithm with Redis/in-memory support |
| Caching | Abstraction layer with Redis backend and in-memory fallback |
| Database | PostgreSQL with async SQLAlchemy 2.0 |
| Validation | Pydantic v2 schemas with automatic OpenAPI generation |
| Health Checks | Liveness, readiness, and dependency checks |
| Error Handling | Consistent error responses with proper HTTP status codes |

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | FastAPI 0.109+ |
| Server | Uvicorn (ASGI) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Cache | Redis 7 |
| Auth | python-jose (JWT), passlib (bcrypt) |
| Validation | Pydantic v2 |
| Container | Docker, docker-compose |

## Project Structure

```
fastapi-api-starter/
├── src/
│   ├── main.py              # Application entry point
│   ├── api/
│   │   ├── v1/
│   │   │   ├── routes/      # API endpoints
│   │   │   │   ├── auth.py
│   │   │   │   ├── health.py
│   │   │   │   └── users.py
│   │   │   └── deps.py      # Route dependencies
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py        # Pydantic settings
│   │   ├── security.py      # JWT and password utils
│   │   ├── rate_limit.py    # Rate limiting
│   │   └── cache.py         # Caching abstraction
│   ├── db/
│   │   ├── session.py       # Database connection
│   │   └── base.py          # SQLAlchemy base model
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   └── utils/               # Helpers
├── docs/
│   ├── architecture.md
│   ├── decisions.md
│   └── deployment.md
├── scripts/
│   └── setup.sh
├── tests/
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Quick Start

Get the API running in under 10 minutes.

### 1. Clone and Configure

```bash
git clone https://github.com/Open-Starter-Kits/fastapi-api-starter.git
cd fastapi-api-starter

# Copy environment template
cp .env.example .env

# Generate a secure JWT secret (recommended)
# Linux/Mac:
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
# Windows (PowerShell):
# Add-Content .env "JWT_SECRET_KEY=$([System.Guid]::NewGuid().ToString('N') + [System.Guid]::NewGuid().ToString('N'))"
```

### 2. Start with Docker

```bash
docker-compose up -d
```

### 3. Verify Installation

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Open API docs
open http://localhost:8000/docs
```

### 4. Create Your First User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

### 5. Login and Get Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL and Redis (or use Docker for just these)
docker-compose up -d db redis

# Run the application
python -m uvicorn src.main:app --reload
```

## Environment Variables

All configuration is via environment variables. See `.env.example` for the complete list.

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/staging/production) | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | Secret for signing tokens | **Must be set** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `RATE_LIMIT_PER_MINUTE` | Default rate limit | `60` |

**Security Note:** Never commit `.env` files. Always set `JWT_SECRET_KEY` to a secure random value in production.

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Authentication Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Register                                                     │
│     POST /api/v1/auth/register                                  │
│     Body: { email, password, full_name? }                       │
│     Returns: User object                                         │
│                                                                  │
│  2. Login                                                        │
│     POST /api/v1/auth/login                                     │
│     Body: { email, password }                                   │
│     Returns: { access_token, refresh_token, expires_in }        │
│                                                                  │
│  3. Access Protected Resources                                   │
│     GET /api/v1/users/me                                        │
│     Header: Authorization: Bearer <access_token>                │
│                                                                  │
│  4. Refresh Tokens (when access token expires)                  │
│     POST /api/v1/auth/refresh                                   │
│     Body: { refresh_token }                                     │
│     Returns: New access_token and refresh_token                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Token Lifetimes:**
- Access token: 30 minutes (configurable)
- Refresh token: 7 days (configurable)

**Security Features:**
- Passwords hashed with bcrypt (12 rounds)
- Tokens signed with HS256 algorithm
- Refresh tokens for seamless session extension
- Rate limiting on auth endpoints (10 req/min)

## API Versioning Strategy

This starter uses URL-based versioning with the pattern `/api/v{version}/`.

**Current Version:** `v1`

**Adding a New Version:**

1. Create new version module:
   ```
   src/api/v2/
   ├── __init__.py
   └── routes/
   ```

2. Register in `main.py`:
   ```python
   app.include_router(v2_router, prefix="/api/v2")
   ```

3. Maintain backward compatibility - don't remove v1 immediately

**Versioning Philosophy:**
- Breaking changes require a new version
- Non-breaking additions can go in the current version
- Deprecate old versions with headers before removal

## Rate Limiting & Caching

### Rate Limiting

Default limits:
- General endpoints: 60 requests/minute
- Auth endpoints: 10 requests/minute

Response headers indicate current limits:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 60
```

**Custom Limits:**
```python
from src.core.rate_limit import rate_limit

@router.get("/sensitive", dependencies=[Depends(rate_limit(limit=10))])
async def sensitive_endpoint():
    ...
```

### Caching

Use the `@cached` decorator for automatic caching:

```python
from src.core.cache import cached

@cached(ttl=300, key_prefix="users")
async def get_user_stats(user_id: int) -> dict:
    # Expensive operation cached for 5 minutes
    ...
```

**Cache Backends:**
- **Redis** (production): Distributed, persistent
- **In-Memory** (fallback): Single process, volatile

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

**Test Categories:**
- `tests/test_auth.py` - Authentication flow
- `tests/test_users.py` - User management
- `tests/test_health.py` - Health endpoints

**Testing Protected Endpoints:**
```python
async def test_protected_route(client, auth_headers):
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
```

## Deployment

### Docker (Recommended)

```bash
# Production build
docker build --target production -t fastapi-api:latest .

# Run with production settings
docker run -d \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  -e JWT_SECRET_KEY=your-secure-key \
  fastapi-api:latest
```

### Production Checklist

- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=false`
- [ ] Generate secure `JWT_SECRET_KEY`
- [ ] Configure production `DATABASE_URL`
- [ ] Set up Redis for caching/rate limiting
- [ ] Enable HTTPS (via reverse proxy)
- [ ] Configure CORS origins
- [ ] Set appropriate rate limits
- [ ] Enable log aggregation

See [docs/deployment.md](docs/deployment.md) for detailed deployment guides.

## Customization Guide

### Adding a New Model

1. Create model in `src/models/`:
   ```python
   # src/models/item.py
   from src.db.base import Base
   
   class Item(Base):
       name: Mapped[str] = mapped_column(String(255))
       # ...
   ```

2. Create schemas in `src/schemas/`
3. Create service in `src/services/`
4. Create routes in `src/api/v1/routes/`
5. Register routes in `src/api/v1/__init__.py`

### Adding Custom Middleware

```python
# src/middleware/custom.py
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Pre-processing
        response = await call_next(request)
        # Post-processing
        return response

# In main.py
app.add_middleware(CustomMiddleware)
```

### Extending Authentication

For OAuth2/social login, extend `AuthService`:

```python
class AuthService:
    async def login_with_google(self, token: str) -> TokenResponse:
        # Verify Google token, create/get user, return tokens
        ...
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

Part of the [Open Starter Kits](https://github.com/Open-Starter-Kits) ecosystem.
