"""User-related Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for user data."""
    
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="User's full name",
        examples=["John Doe"],
    )


class UserCreate(UserBase):
    """Schema for user registration."""
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password (min 8 characters)",
        examples=["securepassword123"],
    )


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="User's full name",
    )
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="New password (optional)",
    )


class UserResponse(UserBase):
    """Schema for user responses (excludes sensitive data)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(
        ...,
        description="User's unique identifier",
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active",
    )
    is_verified: bool = Field(
        ...,
        description="Whether the user's email is verified",
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp",
    )


class UserInDB(UserResponse):
    """Schema for user data including hashed password (internal use only)."""
    
    hashed_password: str
    is_superuser: bool
