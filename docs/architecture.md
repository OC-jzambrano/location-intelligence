# Architecture

This document describes the high-level architecture of the FastAPI REST API Starter.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Applications                             │
│                    (Web Apps, Mobile Apps, Other Services)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       │ HTTPS
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Load Balancer / Reverse Proxy                      │
│                              (nginx, Traefik, etc.)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Application                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Middleware Stack                             │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │   CORS   │→ │  Logging │→ │Exception │→ │  Rate Limiting   │   │   │
│  │  └──────────┘  └──────────┘  │ Handling │  └──────────────────┘   │   │
│  │                              └──────────┘                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                           API Router                                 │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │  /api/v1/    │  │  /api/v1/    │  │  /api/v1/users           │  │   │
│  │  │  auth        │  │  health      │  │                          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Dependencies                                  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │  Auth Guard  │  │  DB Session  │  │  Rate Limit Check        │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Service Layer                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │ AuthService  │  │ UserService  │  │  Other Services          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                       │                                     │
└───────────────────────────────────────│─────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          │                             │                             │
          ▼                             ▼                             ▼
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│    PostgreSQL    │        │      Redis       │        │  External APIs   │
│    (Database)    │        │  (Cache/Queue)   │        │   (if needed)    │
└──────────────────┘        └──────────────────┘        └──────────────────┘
```

## Component Architecture

### Layer Responsibilities

| Layer | Responsibility | Location |
|-------|----------------|----------|
| Routes | HTTP handling, request/response | `src/api/v1/routes/` |
| Dependencies | Auth, DB sessions, validation | `src/api/v1/deps.py` |
| Services | Business logic | `src/services/` |
| Models | Database entities | `src/models/` |
| Schemas | Request/response validation | `src/schemas/` |
| Core | Cross-cutting concerns | `src/core/` |

### Request Lifecycle

```
1. Request Received
   │
   ▼
2. Middleware Processing
   │ ├─ CORS validation
   │ ├─ Request logging
   │ └─ Rate limit check
   │
   ▼
3. Route Matching
   │ └─ FastAPI router finds endpoint
   │
   ▼
4. Dependency Injection
   │ ├─ Database session created
   │ ├─ Auth token validated (if protected)
   │ └─ Other dependencies resolved
   │
   ▼
5. Request Validation
   │ └─ Pydantic validates request body/params
   │
   ▼
6. Route Handler Execution
   │ ├─ Service layer called
   │ ├─ Business logic executed
   │ └─ Database operations performed
   │
   ▼
7. Response Validation
   │ └─ Pydantic validates response
   │
   ▼
8. Response Returned
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Authentication Architecture                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────┐                              ┌────────────────┐        │
│   │     Client     │                              │    Database    │        │
│   └───────┬────────┘                              └───────┬────────┘        │
│           │                                               │                  │
│           │ 1. POST /auth/login                          │                  │
│           │    {email, password}                          │                  │
│           ▼                                               │                  │
│   ┌───────────────────────────────────────────────────────┐                 │
│   │                    AuthService                         │                 │
│   │  ┌─────────────────────────────────────────────────┐  │                 │
│   │  │ 1. Fetch user by email                          │──┼───▶ SELECT     │
│   │  │ 2. Verify password (bcrypt)                     │  │                 │
│   │  │ 3. Generate access token (JWT, 30min)           │  │                 │
│   │  │ 4. Generate refresh token (JWT, 7days)          │  │                 │
│   │  └─────────────────────────────────────────────────┘  │                 │
│   └───────────────────────────────────────────────────────┘                 │
│           │                                                                  │
│           │ 2. Return tokens                                                │
│           ▼                                                                  │
│   ┌────────────────┐                                                        │
│   │     Client     │ Stores tokens (memory/storage)                         │
│   └───────┬────────┘                                                        │
│           │                                                                  │
│           │ 3. GET /users/me                                                │
│           │    Authorization: Bearer <access_token>                         │
│           ▼                                                                  │
│   ┌───────────────────────────────────────────────────────┐                 │
│   │              get_current_user Dependency               │                 │
│   │  ┌─────────────────────────────────────────────────┐  │                 │
│   │  │ 1. Extract token from header                    │  │                 │
│   │  │ 2. Decode and validate JWT                      │  │                 │
│   │  │ 3. Check token type (access)                    │  │                 │
│   │  │ 4. Fetch user from database                     │──┼───▶ SELECT     │
│   │  │ 5. Verify user is active                        │  │                 │
│   │  └─────────────────────────────────────────────────┘  │                 │
│   └───────────────────────────────────────────────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Token Structure

**Access Token Payload:**
```json
{
  "sub": "123",           // User ID
  "exp": 1706234567,      // Expiration timestamp
  "iat": 1706232767,      // Issued at timestamp
  "type": "access"        // Token type
}
```

**Refresh Token Payload:**
```json
{
  "sub": "123",
  "exp": 1706839567,      // Longer expiration
  "iat": 1706234567,
  "type": "refresh"
}
```

## Database Access Pattern

### Session Management

```python
# Dependency injection provides scoped session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  # Auto-commit on success
        except Exception:
            await session.rollback()  # Rollback on error
            raise
```

### Repository Pattern (via Services)

```python
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

### Connection Pooling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Connection Pool (asyncpg)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    Pool Configuration:                                                       │
│    ├─ pool_size: 5 (minimum connections)                                    │
│    ├─ max_overflow: 10 (additional connections when needed)                 │
│    ├─ pool_timeout: 30s (wait time for available connection)                │
│    └─ pool_pre_ping: true (verify connection before use)                    │
│                                                                              │
│    Request 1 ─────┐                                                         │
│    Request 2 ─────┼───▶ [Conn 1] [Conn 2] [Conn 3] [Conn 4] [Conn 5]       │
│    Request 3 ─────┤           │                                             │
│    Request 4 ─────┤           │                                             │
│    Request 5 ─────┘           ▼                                             │
│                          PostgreSQL                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Caching Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Caching Strategy                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    Application                                                               │
│        │                                                                     │
│        ▼                                                                     │
│    ┌───────────────────────────────────┐                                    │
│    │        Cache Abstraction          │                                    │
│    │   get() / set() / delete()        │                                    │
│    └─────────────┬─────────────────────┘                                    │
│                  │                                                           │
│         ┌───────┴───────┐                                                   │
│         ▼               ▼                                                   │
│    ┌──────────┐   ┌──────────┐                                             │
│    │  Redis   │   │ In-Memory│  (fallback)                                 │
│    │  Cache   │   │  Cache   │                                             │
│    └──────────┘   └──────────┘                                             │
│                                                                              │
│    Usage Example:                                                            │
│    ┌─────────────────────────────────────────────────────────┐             │
│    │  @cached(ttl=300, key_prefix="users")                   │             │
│    │  async def get_user_profile(user_id: int):              │             │
│    │      # Cache key: "users:get_user_profile:123"          │             │
│    │      return await fetch_from_db(user_id)                │             │
│    └─────────────────────────────────────────────────────────┘             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Rate Limiting Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Rate Limiting (Sliding Window)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    Request arrives                                                           │
│         │                                                                    │
│         ▼                                                                    │
│    ┌───────────────────────────────────┐                                    │
│    │    Generate Rate Limit Key        │                                    │
│    │    key = f"{client_ip}:{path}"    │                                    │
│    └─────────────┬─────────────────────┘                                    │
│                  │                                                           │
│                  ▼                                                           │
│    ┌───────────────────────────────────┐                                    │
│    │   Check Window (last 60 seconds)  │                                    │
│    │   ┌───────────────────────────┐   │                                    │
│    │   │  [t-60s]──────────[now]   │   │                                    │
│    │   │   │ │ │   │   │ │ │ │ │   │   │                                    │
│    │   │   ▼ ▼ ▼   ▼   ▼ ▼ ▼ ▼ ▼   │   │                                    │
│    │   │   Requests in window: 45   │   │                                    │
│    │   └───────────────────────────┘   │                                    │
│    └─────────────┬─────────────────────┘                                    │
│                  │                                                           │
│         ┌───────┴───────┐                                                   │
│         ▼               ▼                                                   │
│    count < limit    count >= limit                                          │
│         │               │                                                    │
│         ▼               ▼                                                   │
│    ┌─────────┐    ┌──────────────────┐                                     │
│    │ ALLOW   │    │ REJECT (429)     │                                     │
│    │ Request │    │ Too Many Requests│                                     │
│    └─────────┘    └──────────────────┘                                     │
│                                                                              │
│    Storage:                                                                  │
│    ├─ Redis (production): Sorted sets with timestamp scores                 │
│    └─ In-Memory (fallback): Dict with timestamp lists                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Error Handling

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Error Handling Flow                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    Exception Raised                                                          │
│         │                                                                    │
│         ▼                                                                    │
│    ┌───────────────────────────────────┐                                    │
│    │      Exception Type Check          │                                    │
│    └─────────────┬─────────────────────┘                                    │
│                  │                                                           │
│    ┌─────────────┼─────────────┬───────────────┬───────────────┐           │
│    ▼             ▼             ▼               ▼               ▼           │
│ HTTPException  Validation   Database       Auth Error     Unexpected      │
│    │           Error         Error            │               │           │
│    │             │             │               │               │           │
│    ▼             ▼             ▼               ▼               ▼           │
│ ┌────────┐  ┌────────┐   ┌────────┐     ┌────────┐     ┌────────┐        │
│ │ 4xx/5xx│  │  422   │   │  500   │     │  401   │     │  500   │        │
│ │ as-is  │  │ Details│   │ Logged │     │ Bearer │     │ Logged │        │
│ └────────┘  └────────┘   └────────┘     └────────┘     └────────┘        │
│                                                                              │
│    Response Format (consistent):                                             │
│    {                                                                         │
│      "success": false,                                                       │
│      "error": "error_code",                                                  │
│      "message": "Human readable message",                                    │
│      "details": { ... }  // optional                                         │
│    }                                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Scaling Considerations

### Horizontal Scaling

```
                    Load Balancer
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │ API Pod │    │ API Pod │    │ API Pod │
    │    1    │    │    2    │    │    3    │
    └────┬────┘    └────┬────┘    └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
         ┌─────────┐          ┌─────────┐
         │  Redis  │          │PostgreSQL│
         │ Cluster │          │ Primary │
         └─────────┘          └────┬────┘
                                   │
                              ┌────┴────┐
                              ▼         ▼
                         [Replica] [Replica]
```

### Key Design Decisions for Scale

1. **Stateless Application**: No server-side sessions; JWT tokens are self-contained
2. **Centralized Cache**: Redis for distributed caching across instances
3. **Connection Pooling**: Efficient database connection management
4. **Async I/O**: Non-blocking operations throughout
5. **Rate Limiting in Redis**: Consistent limits across all instances
