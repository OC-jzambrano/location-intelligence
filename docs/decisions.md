# Architectural Decisions

This document records the key architectural decisions made in this project and the reasoning behind them.

## ADR-001: FastAPI as the Web Framework

### Context
We needed to choose a Python web framework for building a production-grade REST API.

### Options Considered
1. **Django REST Framework** - Mature, batteries-included
2. **Flask + Extensions** - Lightweight, flexible
3. **FastAPI** - Modern, async-first, type-safe

### Decision
**FastAPI**

### Rationale
- **Performance**: Built on Starlette with async/await support; benchmarks show 2-3x better throughput than Flask
- **Type Safety**: Native Pydantic integration provides runtime validation and IDE support
- **Documentation**: Automatic OpenAPI/Swagger generation from type hints
- **Modern Python**: Leverages Python 3.10+ features (type hints, async/await)
- **Developer Experience**: Excellent error messages, dependency injection system

### Trade-offs
- Smaller ecosystem than Django
- Less "batteries included" - need to make more decisions upfront
- Async requires understanding of asyncio patterns

---

## ADR-002: JWT for Authentication

### Context
The API needs stateless authentication suitable for distributed deployment.

### Options Considered
1. **Session-based auth** - Server stores session state
2. **JWT (JSON Web Tokens)** - Stateless, self-contained tokens
3. **OAuth2 + external provider** - Delegated auth

### Decision
**JWT with access and refresh tokens**

### Rationale
- **Stateless**: No server-side session storage required; scales horizontally
- **Self-contained**: Token includes user claims; reduces database lookups
- **Standard**: Well-documented RFC 7519; libraries available in all languages
- **Flexible**: Refresh tokens allow long sessions without long-lived access tokens

### Implementation Details
- Access tokens: 30-minute expiry, used for API requests
- Refresh tokens: 7-day expiry, used only to obtain new access tokens
- HS256 algorithm (symmetric) for simplicity; can upgrade to RS256 for microservices
- Token type claim prevents token misuse

### Trade-offs
- Cannot invalidate individual tokens without blacklisting (requires Redis)
- Token size larger than session ID
- Must handle token refresh on client side

### Security Considerations
- Tokens signed with secret key (never exposed)
- Short access token lifetime limits damage from theft
- Refresh token rotation possible for enhanced security

---

## ADR-003: Project Structure (Layered Architecture)

### Context
Need a code structure that scales with team size and feature count.

### Options Considered
1. **Flat structure** - All files in one directory
2. **Feature-based** - Group by feature (users/, auth/, items/)
3. **Layer-based** - Group by technical concern (models/, services/, routes/)
4. **Hybrid** - Combine approaches

### Decision
**Layer-based with clear separation of concerns**

```
src/
├── api/v1/routes/    # HTTP layer
├── services/         # Business logic
├── models/           # Database entities
├── schemas/          # Request/response validation
├── core/             # Cross-cutting concerns
└── db/               # Database configuration
```

### Rationale
- **Clear Dependencies**: Each layer has defined responsibilities
- **Testability**: Services can be tested without HTTP; models without services
- **Onboarding**: New developers understand where code belongs
- **Refactoring**: Changes isolated to affected layers

### Trade-offs
- Feature code spread across directories
- More files than feature-based approach
- Requires discipline to maintain boundaries

---

## ADR-004: URL-Based API Versioning

### Context
APIs evolve; we need a strategy for breaking changes.

### Options Considered
1. **URL versioning** - `/api/v1/users`
2. **Header versioning** - `Accept: application/vnd.api.v1+json`
3. **Query parameter** - `/users?version=1`
4. **No versioning** - Evolve in place

### Decision
**URL-based versioning with /api/v{n}/ prefix**

### Rationale
- **Visibility**: Version is obvious in URL; easy to debug and document
- **Caching**: Different URLs = different cache entries
- **Routing**: Simple to implement with FastAPI routers
- **Client Compatibility**: Works with all HTTP clients without special headers

### Implementation
```python
app.include_router(v1_router, prefix="/api/v1")
# Future: app.include_router(v2_router, prefix="/api/v2")
```

### Trade-offs
- URL pollution (version in every endpoint)
- Harder to support many versions simultaneously
- Breaking change definition requires team agreement

---

## ADR-005: Pydantic Settings for Configuration

### Context
Application needs configuration from environment variables with validation.

### Options Considered
1. **python-dotenv only** - Simple but no validation
2. **environ-config** - Dataclass-based
3. **Pydantic Settings** - Pydantic-based with validation

### Decision
**Pydantic Settings**

### Rationale
- **Validation**: Type coercion and validation at startup
- **Consistency**: Same Pydantic patterns used throughout codebase
- **IDE Support**: Full autocomplete and type checking
- **Documentation**: Settings are self-documenting with field descriptions

### Implementation
```python
class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    debug: bool = False
    
    model_config = SettingsConfigDict(env_file=".env")
```

### Trade-offs
- Slightly more setup than raw environment access
- Application fails fast if required variables missing (actually a benefit)

---

## ADR-006: SQLAlchemy 2.0 with Async

### Context
Need an ORM that supports async operations for FastAPI.

### Options Considered
1. **SQLAlchemy 1.4** - Mature, sync-first
2. **SQLAlchemy 2.0** - Modern, native async support
3. **Tortoise ORM** - Async-first, Django-like
4. **Raw SQL** - Maximum control

### Decision
**SQLAlchemy 2.0 with asyncpg**

### Rationale
- **Industry Standard**: Most widely used Python ORM; extensive documentation
- **Native Async**: 2.0 has first-class async support
- **Migration Path**: Easy to upgrade from 1.4; familiar to most Python developers
- **Flexibility**: Can drop to raw SQL when needed
- **Ecosystem**: Alembic migrations, extensive plugin ecosystem

### Implementation
```python
engine = create_async_engine(settings.database_url)
async_session_maker = async_sessionmaker(engine)
```

### Trade-offs
- Learning curve for 2.0 syntax changes
- Async patterns require care (no lazy loading)
- More complex than simpler ORMs

---

## ADR-007: Redis for Caching and Rate Limiting

### Context
Need distributed caching and rate limiting for multi-instance deployment.

### Options Considered
1. **In-memory only** - Simple, no infrastructure
2. **Redis** - Distributed, persistent
3. **Memcached** - Distributed, ephemeral
4. **Database-backed** - Consistent but slow

### Decision
**Redis with in-memory fallback**

### Rationale
- **Distributed**: State shared across all application instances
- **Performance**: Sub-millisecond operations
- **Features**: Sorted sets for rate limiting, pub/sub for future features
- **Persistence**: Optional AOF/RDB for cache warming after restart
- **Fallback**: In-memory cache ensures app works without Redis

### Implementation
- Cache abstraction layer (`CacheBackend` interface)
- Automatic fallback to `InMemoryCache` if Redis unavailable
- Rate limiting uses Redis sorted sets for sliding window

### Trade-offs
- Additional infrastructure to manage
- Network latency (though minimal)
- Fallback mode loses distributed consistency

---

## ADR-008: Bcrypt for Password Hashing

### Context
User passwords must be stored securely.

### Options Considered
1. **bcrypt** - Battle-tested, adaptive
2. **Argon2** - Memory-hard, newer
3. **scrypt** - Memory-hard
4. **PBKDF2** - Standard but dated

### Decision
**Bcrypt via passlib**

### Rationale
- **Battle-tested**: Decades of production use
- **Library Support**: passlib provides excellent interface
- **Adjustable Cost**: Can increase rounds as hardware improves
- **Sufficient Security**: For most applications, bcrypt is more than adequate

### Implementation
```python
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12)
```

### Trade-offs
- Not memory-hard (Argon2 is theoretically more secure against GPU attacks)
- Fixed work factor (can't adapt to available memory)

---

## ADR-009: Dependency Injection Pattern

### Context
Need clean way to provide database sessions, auth, and other dependencies to routes.

### Decision
**FastAPI's built-in Depends() system**

### Rationale
- **Native**: Built into FastAPI; no additional libraries
- **Composable**: Dependencies can depend on other dependencies
- **Testable**: Easy to override in tests
- **Automatic**: Lifecycle managed by framework

### Implementation
```python
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    ...

@router.get("/me")
async def get_me(user: Annotated[User, Depends(get_current_user)]):
    return user
```

### Trade-offs
- Learning curve for Depends() patterns
- Complex dependency chains can be hard to debug
- All dependencies evaluated per-request (use caching carefully)

---

## ADR-010: Service Layer for Business Logic

### Context
Need to decide where business logic lives.

### Options Considered
1. **In route handlers** - Simple, direct
2. **In models** - Active Record pattern
3. **In services** - Separate business logic layer

### Decision
**Service layer with dependency injection**

### Rationale
- **Testability**: Services can be tested without HTTP
- **Reusability**: Same service used by multiple routes
- **Clarity**: Routes handle HTTP; services handle business rules
- **Transaction Management**: Services can coordinate multiple operations

### Implementation
```python
class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user_data: UserCreate) -> User:
        # Business logic here
        ...

# In route:
user_service = UserService(db)
user = await user_service.create(user_data)
```

### Trade-offs
- More files and indirection
- Must pass db session to each service
- Overhead for simple CRUD operations

---

## Summary of Key Principles

1. **Async-First**: Everything uses async/await for maximum concurrency
2. **Type-Safe**: Pydantic and type hints throughout
3. **Stateless**: JWT tokens enable horizontal scaling
4. **Layered**: Clear separation between HTTP, business logic, and data
5. **Configurable**: All settings from environment variables
6. **Observable**: Structured logging, health checks, metrics-ready
7. **Graceful Degradation**: In-memory fallbacks when Redis unavailable
