"""User management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_active_user, get_current_superuser
from src.core.rate_limit import rate_limit
from src.db.session import get_db
from src.models.user import User
from src.schemas.user import UserResponse, UserUpdate
from src.services.user import UserService

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user.",
    responses={
        200: {"description": "User profile"},
        401: {"description": "Not authenticated"},
    },
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Get current user's profile.

    Returns the full profile of the authenticated user.
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the profile of the currently authenticated user.",
    responses={
        200: {"description": "Profile updated"},
        401: {"description": "Not authenticated"},
    },
    dependencies=[Depends(rate_limit(limit=30))],
)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Update current user's profile.

    - **full_name**: Optional new full name
    - **password**: Optional new password (minimum 8 characters)
    """
    user_service = UserService(db)
    updated_user = await user_service.update(current_user, user_data)
    return updated_user


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete current user account",
    description="Permanently delete the current user's account.",
    responses={
        204: {"description": "Account deleted"},
        401: {"description": "Not authenticated"},
    },
)
async def delete_current_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete current user's account.

    This action is permanent and cannot be undone.
    """
    user_service = UserService(db)
    await user_service.delete(current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID (admin)",
    description="Get any user's profile by ID. Requires superuser privileges.",
    responses={
        200: {"description": "User profile"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized (superuser required)"},
        404: {"description": "User not found"},
    },
)
async def get_user_by_id(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_superuser)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get a user by ID.

    Requires superuser privileges.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate user (admin)",
    description="Activate a user account. Requires superuser privileges.",
    responses={
        200: {"description": "User activated"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized (superuser required)"},
        404: {"description": "User not found"},
    },
)
async def activate_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_superuser)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Activate a user account.

    Requires superuser privileges.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return await user_service.set_active(user, True)


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate user (admin)",
    description="Deactivate a user account. Requires superuser privileges.",
    responses={
        200: {"description": "User deactivated"},
        401: {"description": "Not authenticated"},
        403: {"description": "Not authorized (superuser required)"},
        404: {"description": "User not found"},
    },
)
async def deactivate_user(
    user_id: int,
    current_user: Annotated[User, Depends(get_current_superuser)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Deactivate a user account.

    Requires superuser privileges.
    """
    user_service = UserService(db)
    user = await user_service.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    return await user_service.set_active(user, False)
