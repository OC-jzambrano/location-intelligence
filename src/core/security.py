"""
Security utilities for JWT token handling and password hashing.

This module provides:
- JWT access and refresh token generation/validation
- Secure password hashing using bcrypt
- Token payload extraction and validation
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.bcrypt_rounds,
)


class TokenType:
    """Token type constants."""

    ACCESS = "access"
    REFRESH = "refresh"


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The subject of the token (typically user ID).
        expires_delta: Optional custom expiration time.
        additional_claims: Optional additional claims to include in the token.

    Returns:
        Encoded JWT access token string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TokenType.ACCESS,
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Refresh tokens have a longer expiration and are used to obtain new access tokens.

    Args:
        subject: The subject of the token (typically user ID).
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT refresh token string.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TokenType.REFRESH,
    }

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        Decoded token payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str) -> dict[str, Any] | None:
    """
    Verify a token is valid and of the expected type.

    Args:
        token: The JWT token string to verify.
        token_type: Expected token type (access or refresh).

    Returns:
        Decoded token payload if valid and correct type, None otherwise.
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != token_type:
        return None

    return payload


def get_token_subject(token: str) -> str | None:
    """
    Extract the subject (user ID) from a token.

    Args:
        token: The JWT token string.

    Returns:
        The subject string if token is valid, None otherwise.
    """
    payload = decode_token(token)

    if payload is None:
        return None

    return payload.get("sub")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Hashed password to compare against.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_token_pair(subject: str | int) -> dict[str, str]:
    """
    Create both access and refresh tokens for a user.

    Args:
        subject: The subject of the tokens (typically user ID).

    Returns:
        Dictionary with 'access_token' and 'refresh_token' keys.
    """
    return {
        "access_token": create_access_token(subject),
        "refresh_token": create_refresh_token(subject),
    }
