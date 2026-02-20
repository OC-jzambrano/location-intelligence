# Design Decisions & Trade-offs

This document explains the key architectural and technical decisions behind the Location Intelligence API, including the reasoning, trade-offs, and alternatives considered.

## 1. Architectural Style

**Decision:** Layered / Clean Architecture (Hexagonal-inspired)

The project follows a separation of concerns structure:

API (routes)
    ↓
Application Services (LISService)
    ↓
Adapters (Google Geocoding / Places)
    ↓
External APIs
**Why**

- Keeps HTTP logic separated from business logic
- Allows external providers to be swapped
- Improves testability
- Reduces coupling between layers

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Cleaner structure | Slightly more boilerplate |
| Easier testing | Requires clear interface boundaries |
| Replaceable providers | More abstractions to maintain |

**Alternative Considered**

- Direct API calls inside routes (rejected due to tight coupling)
- Monolithic service without adapters (rejected due to poor extensibility)

## 2. Use of Adapters for External Providers

**Decision:** Wrap Google APIs behind adapters

Instead of calling Google APIs directly inside services, we created adapter classes such as:

- `GoogleGeocodingAdapter`
- `GooglePlacesAdapter`

**Why**

- Encapsulates provider-specific logic
- Allows future addition of providers (e.g., Mapbox, HERE)
- Keeps service logic provider-agnostic

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Easy provider replacement | More files/classes |
| Clear external boundary | Slightly higher complexity |
## 3. JWT Authentication (Access + Refresh)

**Decision:** Use stateless JWT with refresh tokens

Authentication uses:

- Short-lived access tokens
- Long-lived refresh tokens

**Why**

- Stateless architecture
- Horizontal scalability
- No server-side session storage

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Scales easily | No built-in logout unless blacklisting |
| Simple for APIs | Token revocation requires Redis or DB |

**Alternative Considered**

- Server-side sessions (rejected for scalability concerns)
- OAuth-only flow (not needed at current stage)

## 4. Google Places API (New) + FieldMask

**Decision:** Use FieldMask in Places API (New)

When calling Places API (New), the request specifies:

```
X-Goog-FieldMask
```

**Why**

- Reduces payload size
- Reduces cost (Google charges per field returned)
- Improves performance

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Lower API costs | Must explicitly manage fields |
| Faster responses | Requires maintenance when fields change |
## 5. Explicit Provider Error Mapping

**Decision:** Map provider errors to structured API errors

Examples:

- `ZERO_RESULTS` → 422 `NO_RESULTS`
- Timeout → 422 `TIMEOUT`
- Other errors → 422 `PROVIDER_ERROR`

**Why**

- Keeps API contract stable
- Avoids leaking raw provider errors
- Makes frontend error handling predictable

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Cleaner API contract | Additional error-mapping logic |
| Predictable responses | Must maintain mapping logic |
## 6. Environment-Based Configuration

**Decision:** Use Pydantic Settings for configuration

All configuration is environment-driven:

- JWT secret
- Google API key
- Database URL
- Redis URL

**Why**

- Twelve-factor app compliant
- Easy container deployment
- Secure secrets management

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Production-ready config | Startup fails if required vars missing |
| Clear config model | Slightly stricter setup |
## 7. Rate Limiting

**Decision:** Sliding window rate limiting (Redis-backed)

Auth endpoints and API endpoints are rate limited.

**Why**

- Protect against brute force
- Prevent abuse
- Maintain system stability

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Security improvement | Requires Redis in production |
| Abuse prevention | Slight added infrastructure |
## 8. Commit Strategy (Atomic Commits)

**Decision:** Use atomic commits

Each commit should represent a single logical change.

**Example of good commit:**

```
feat(geocode): implement Google geocoding adapter
```

**Example of bad commit:**

```
fix stuff and add new endpoint and update docker
```

**Why**

- Easier code review
- Clear project history
- Safer rollbacks

## 9. Why Google as Initial Provider

**Decision:** Start with Google Maps APIs

**Why**

- Industry-standard accuracy
- Comprehensive documentation
- Strong global coverage

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| High reliability | Vendor lock-in risk |
| Global coverage | Paid API usage |
| Rich data | Cost per request |

**Mitigation**

Architecture allows future addition of:

- Mapbox
- HERE
- OpenStreetMap-based providers

## 10. Why Async (FastAPI + SQLAlchemy 2.0 Async)

**Decision:** Async-first design

**Why**

- High concurrency
- Efficient I/O handling
- Modern Python best practice

**Trade-offs**

| Advantage | Cost |
|-----------|------|
| Better scalability | More complexity in debugging |
| Efficient API calls | Requires async-compatible libraries |

## Future Improvements

- Formal Strategy pattern for multi-provider support
- Provider selection via configuration
- Centralized domain interfaces (true hexagonal port layer)
- Token blacklisting for logout
- Observability (metrics + tracing)
- Circuit breaker for external APIs

## Summary

This project prioritizes:

- Clean separation of concerns
- Extensibility
- Scalability
- Predictable API contracts
- Production readiness

The architecture balances pragmatic implementation with long-term flexibility.

