"""Tests for authentication endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient

from src.models.user import User


@pytest.mark.asyncio
async def test_register_user(
    client: AsyncClient,
    sample_user_data: dict[str, Any],
) -> None:
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json=sample_user_data,
    )

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == sample_user_data["email"]
    assert data["full_name"] == sample_user_data["full_name"]
    assert "id" in data
    assert "hashed_password" not in data  # Password should not be exposed


@pytest.mark.asyncio
async def test_register_duplicate_email(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Test registration with existing email fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "somepassword123",
        },
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    """Test registration with invalid email fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "securepassword123",
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    """Test registration with short password fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    test_user: User,
    sample_login_data: dict[str, str],
) -> None:
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/login",
        json=sample_login_data,
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


@pytest.mark.asyncio
async def test_login_wrong_password(
    client: AsyncClient,
    test_user: User,
) -> None:
    """Test login with wrong password fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Test login with non-existent user fails."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "somepassword123",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """Test getting current user profile."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient) -> None:
    """Test getting current user without token fails."""
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 403  # HTTPBearer returns 403 when no token


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient) -> None:
    """Test getting current user with invalid token fails."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(
    client: AsyncClient,
    test_user: User,
    sample_login_data: dict[str, str],
) -> None:
    """Test token refresh."""
    # First, login to get tokens
    login_response = await client.post(
        "/api/v1/auth/login",
        json=sample_login_data,
    )

    tokens = login_response.json()

    # Then refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    # New tokens should be different
    assert data["access_token"] != tokens["access_token"]


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """Test refresh with invalid token fails."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-refresh-token"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test logout endpoint."""
    response = await client.post(
        "/api/v1/auth/logout",
        headers=auth_headers,
    )

    assert response.status_code == 204
