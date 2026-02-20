# Location Intelligence API (FastAPI)

Production-grade Location Intelligence API built on FastAPI with JWT auth, versioned routing, rate limiting, caching, and a clean service/adapters architecture. The first release focuses on address normalization and geocoding + place enrichment using Google APIs.

## What This Project Does

This API exposes two core endpoints under `/api/v1`:

- **POST `/api/v1/normalize`** — Takes a raw address string and returns a normalized version.
- **POST `/api/v1/geocode` (protected)** — Takes an address (plus optional language and region), normalizes it, geocodes it, and enriches it with place details.

Authentication uses JWT (access + refresh tokens). Protected endpoints require:

```
Authorization: Bearer <access_token>
```

## Postman Collection

A Postman collection is included to make testing repeatable across machines and environments.

**Import collection from:**
```
docs/postman/location_intelligence.postman_collection.json
```

**Use these variables inside Postman:**

- `{{base_url}}` → default: `http://localhost:8000/api/v1`
- `{{jwt_token}}` → auto-filled by the login request

### Provider Error Handling

The API is designed to map provider failures into predictable API responses:

- **"No results" from provider** → return 422 with code `NO_RESULTS`
- **Provider timeout** → return 422 with code `TIMEOUT`
- **Other provider errors** → return 422 with code `PROVIDER_ERROR`

## Project Structure

- `src/api/v1/routes/` — routers (endpoints)
- `src/schemas/` — Pydantic request/response models
- `src/services/` — business logic and orchestration (e.g., LISService)
- `src/core/` — config, security, rate limiting, caching
- `src/db/` — database session/lifecycle

### Prerequisites

- Python 3.11+
- Docker and docker-compose
- Basic understanding of FastAPI and async Python

## Quick Start

Get the API running in under 10 minutes.

### 1. Clone and Configure

```bash
git clone https://github.com/OC-jzambrano/location-intelligence.git
cd location-intelligence

# Copy environment template
cp .env.example .env
```

Make sure `.env` contains:

- `JWT_SECRET_KEY` (required)
- `GOOGLE_MAPS_API_KEY` (required for `/geocode`)
- `DATABASE_URL` and `REDIS_URL` (defaults exist in docker-compose)

```bash
JWT_SECRET_KEY=dev-secret-key-change-me
GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_KEY_HERE

# Generate a secure JWT secret (recommended)
# Linux/Mac:
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Windows (PowerShell):
# Add-Content .env "JWT_SECRET_KEY=$([System.Guid]::NewGuid().ToString('N') + [System.Guid]::NewGuid().ToString('N'))"
```

**Important:** Ensure your `docker-compose.yml` passes `GOOGLE_MAPS_API_KEY` to the api container.

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
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | `YOUR-API-KEY` |

**Security Note:** Never commit `.env` files. Always set `JWT_SECRET_KEY` to a secure random value in production.

## Authentication Flow

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

### 2. Login to Obtain Tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

Response includes:
- `access_token`
- `refresh_token`

### 3. Use Access Token for Protected Endpoints

```
Authorization: Bearer <access_token>
```

### 4. Refresh Token (When Access Expires)

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### Authentication Flow Diagram

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

### Token Lifetimes

- **Access token:** 30 minutes (configurable)
- **Refresh token:** 7 days (configurable)

### Security Features

- Passwords hashed with bcrypt (12 rounds)
- Tokens signed with HS256 algorithm
- Refresh tokens for seamless session extension
- Rate limiting on auth endpoints (10 req/min)

## Testing Endpoints

### POST `/api/v1/normalize`

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/normalize \
  -H "Content-Type: application/json" \
  -d '{"address": " 1600 Amphitheatre Parkway, Mountain View, CA "}'
```

**Expected response:**

```json
{
  "input_address": " 1600 Amphitheatre Parkway, Mountain View, CA ",
  "normalized_address": "1600 Amphitheatre Parkway, Mountain View, CA"
}
```

### POST `/api/v1/geocode` (Protected)

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/geocode \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"address": "1600 Amphitheatre Parkway, Mountain View, CA", "language": "en", "region": "us"}'
```

**Parameters:**

- `language` (optional) — Language code (defaults to `en`)
- `region` (optional) — Country code for bias (ISO 3166-1 alpha-2: `us`, `co`, `mx`, `es`, `de`, `fr`, `gb`, etc.)

## API Versioning Strategy

This starter uses URL-based versioning with the pattern `/api/v{version}/`.

**Current Version:** `v1`

### Adding a New Version

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