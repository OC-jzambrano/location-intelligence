"""Authentication service for token management."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.security import (
    TokenType,
    create_token_pair,
    verify_token,
)
from src.models.user import User
from src.schemas.auth import TokenResponse
from src.services.user import UserService


class AuthService:
    """
    Service class for authentication operations.
    
    Handles login, token generation, and token refresh.
    """
    
    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize with database session.
        
        Args:
            db: Async database session.
        """
        self.db = db
        self.user_service = UserService(db)
    
    async def login(self, email: str, password: str) -> TokenResponse | None:
        """
        Authenticate user and generate tokens.
        
        Args:
            email: User's email address.
            password: User's password.
        
        Returns:
            TokenResponse with access and refresh tokens if successful,
            None if authentication fails.
        """
        user = await self.user_service.authenticate(email, password)
        
        if not user:
            return None
        
        return self._create_token_response(user)
    
    async def refresh_tokens(self, refresh_token: str) -> TokenResponse | None:
        """
        Generate new tokens using a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token.
        
        Returns:
            TokenResponse with new tokens if successful,
            None if refresh token is invalid.
        """
        # Verify refresh token
        payload = verify_token(refresh_token, TokenType.REFRESH)
        
        if payload is None:
            return None
        
        # Get user from token subject
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            user = await self.user_service.get_by_id(int(user_id))
        except ValueError:
            return None
        
        if not user or not user.is_active:
            return None
        
        return self._create_token_response(user)
    
    async def get_current_user(self, token: str) -> User | None:
        """
        Get the current user from an access token.
        
        Args:
            token: JWT access token.
        
        Returns:
            User if token is valid and user exists, None otherwise.
        """
        payload = verify_token(token, TokenType.ACCESS)
        
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        try:
            user = await self.user_service.get_by_id(int(user_id))
        except ValueError:
            return None
        
        if not user or not user.is_active:
            return None
        
        return user
    
    def _create_token_response(self, user: User) -> TokenResponse:
        """
        Create a token response for a user.
        
        Args:
            user: User to generate tokens for.
        
        Returns:
            TokenResponse with access and refresh tokens.
        """
        tokens = create_token_pair(user.id)
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )
