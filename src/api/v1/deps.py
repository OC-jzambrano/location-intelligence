"""FastAPI dependencies for API v1."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.models.user import User
from src.services.auth import AuthService

# Bearer token security scheme
bearer_scheme = HTTPBearer(
    description="JWT access token for authentication",
    auto_error=True,
)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user.
    
    Extracts and validates the JWT token from the Authorization header,
    then returns the corresponding user.
    
    Args:
        credentials: Bearer token from Authorization header.
        db: Database session.
    
    Returns:
        The authenticated User.
    
    Raises:
        HTTPException: If token is invalid or user not found.
    """
    auth_service = AuthService(db)
    user = await auth_service.get_current_user(credentials.credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency to get the current active user.
    
    Extends get_current_user to also verify the user is active.
    
    Args:
        current_user: User from get_current_user dependency.
    
    Returns:
        The authenticated and active User.
    
    Raises:
        HTTPException: If user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Dependency to get the current superuser.
    
    Extends get_current_active_user to also verify superuser status.
    
    Args:
        current_user: User from get_current_active_user dependency.
    
    Returns:
        The authenticated superuser.
    
    Raises:
        HTTPException: If user is not a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(HTTPBearer(auto_error=False)),
    ],
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Dependency to optionally get the current user.
    
    Does not raise an error if no token is provided.
    Useful for endpoints that have different behavior for
    authenticated vs anonymous users.
    
    Args:
        credentials: Optional bearer token.
        db: Database session.
    
    Returns:
        The authenticated User or None.
    """
    if not credentials:
        return None
    
    auth_service = AuthService(db)
    return await auth_service.get_current_user(credentials.credentials)
