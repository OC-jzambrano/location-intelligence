"""Tests for user management endpoints."""

import pytest
from httpx import AsyncClient

from src.models.user import User


@pytest.mark.asyncio
async def test_get_user_profile(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """Test getting user profile."""
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_user_profile_unauthenticated(client: AsyncClient) -> None:
    """Test getting profile without authentication fails."""
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_user_profile(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """Test updating user profile."""
    response = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"full_name": "Updated Name"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["full_name"] == "Updated Name"
    assert data["email"] == test_user.email  # Email unchanged


@pytest.mark.asyncio
async def test_update_user_password(
    client: AsyncClient,
    test_user: User,
    auth_headers: dict[str, str],
) -> None:
    """Test updating user password."""
    new_password = "newpassword456"

    response = await client.patch(
        "/api/v1/users/me",
        headers=auth_headers,
        json={"password": new_password},
    )

    assert response.status_code == 200

    # Verify new password works
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.email,
            "password": new_password,
        },
    )

    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_delete_user_account(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test deleting user account."""
    response = await client.delete(
        "/api/v1/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify user is deleted (token should no longer work)
    profile_response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers,
    )

    assert profile_response.status_code == 401


@pytest.mark.asyncio
async def test_admin_get_user_by_id(
    client: AsyncClient,
    test_user: User,
    admin_auth_headers: dict[str, str],
) -> None:
    """Test admin getting user by ID."""
    response = await client.get(
        f"/api/v1/users/{test_user.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_non_admin_cannot_get_user_by_id(
    client: AsyncClient,
    test_user: User,
    test_superuser: User,
    auth_headers: dict[str, str],
) -> None:
    """Test non-admin cannot get other user by ID."""
    response = await client.get(
        f"/api/v1/users/{test_superuser.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_get_nonexistent_user(
    client: AsyncClient,
    admin_auth_headers: dict[str, str],
) -> None:
    """Test admin getting non-existent user returns 404."""
    response = await client.get(
        "/api/v1/users/99999",
        headers=admin_auth_headers,
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_deactivate_user(
    client: AsyncClient,
    test_user: User,
    admin_auth_headers: dict[str, str],
) -> None:
    """Test admin deactivating a user."""
    response = await client.patch(
        f"/api/v1/users/{test_user.id}/deactivate",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["is_active"] is False


@pytest.mark.asyncio
async def test_admin_activate_user(
    client: AsyncClient,
    test_user: User,
    admin_auth_headers: dict[str, str],
) -> None:
    """Test admin activating a user."""
    # First deactivate
    await client.patch(
        f"/api/v1/users/{test_user.id}/deactivate",
        headers=admin_auth_headers,
    )

    # Then activate
    response = await client.patch(
        f"/api/v1/users/{test_user.id}/activate",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_self(
    client: AsyncClient,
    test_superuser: User,
    admin_auth_headers: dict[str, str],
) -> None:
    """Test admin cannot deactivate their own account."""
    response = await client.patch(
        f"/api/v1/users/{test_superuser.id}/deactivate",
        headers=admin_auth_headers,
    )

    assert response.status_code == 400
    assert "own account" in response.json()["detail"].lower()
