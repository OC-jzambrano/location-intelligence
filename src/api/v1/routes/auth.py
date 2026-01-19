"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.deps import get_current_user
from src.core.rate_limit import auth_rate_limit
from src.db.session import get_db
from src.models.user import User
from src.schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse
from src.schemas.user import UserCreate, UserResponse
from src.services.auth import AuthService
from src.services.user import UserService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password.",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Email already registered"},
        429: {"description": "Rate limit exceeded"},
    },
    dependencies=[Depends(auth_rate_limit())],
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register a new user.
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    - **full_name**: Optional full name
    """
    user_service = UserService(db)
    
    try:
        user = await user_service.create(user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate with email and password to obtain access tokens.",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        429: {"description": "Rate limit exceeded"},
    },
    dependencies=[Depends(auth_rate_limit())],
)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Login to obtain access and refresh tokens.
    
    - **email**: Registered email address
    - **password**: Account password
    
    Returns JWT access token (short-lived) and refresh token (long-lived).
    """
    auth_service = AuthService(db)
    tokens = await auth_service.login(credentials.email, credentials.password)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return tokens


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description="Get new access and refresh tokens using a valid refresh token.",
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_tokens(
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Refresh access and refresh tokens.
    
    Use this endpoint when the access token expires.
    Requires a valid refresh token.
    """
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_tokens(token_request.refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return tokens


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile.",
    responses={
        200: {"description": "User profile"},
        401: {"description": "Not authenticated"},
    },
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Get current authenticated user's profile.
    
    Requires valid access token in Authorization header.
    """
    return current_user


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Logout the current user (client should discard tokens).",
    responses={
        204: {"description": "Logout successful"},
        401: {"description": "Not authenticated"},
    },
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Logout current user.
    
    Note: With JWT, true server-side logout requires token blacklisting.
    This endpoint serves as a signal for clients to discard tokens.
    For production, implement token blacklisting in Redis.
    """
    # In a full implementation, you would blacklist the token here
    # For now, this is a signal for clients to discard their tokens
    return None
