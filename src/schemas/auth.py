"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login requests."""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="User's password",
        examples=["securepassword123"],
    )


class TokenResponse(BaseModel):
    """Schema for token responses."""
    
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
    )


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh requests."""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
    )
