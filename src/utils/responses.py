"""Standardized API response utilities."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """
    Standard success response wrapper.
    
    Provides consistent response structure across all endpoints.
    """
    
    success: bool = Field(default=True, description="Indicates successful operation")
    message: str | None = Field(default=None, description="Optional success message")
    data: T | None = Field(default=None, description="Response data payload")


class ErrorResponse(BaseModel):
    """
    Standard error response.
    
    Provides consistent error structure across all endpoints.
    """
    
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details",
    )


def success_response(
    data: Any = None,
    message: str | None = None,
) -> dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data payload.
        message: Optional success message.
    
    Returns:
        Dictionary with success response structure.
    """
    response: dict[str, Any] = {"success": True}
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return response


def error_response(
    error: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: Error type or code.
        message: Human-readable error message.
        details: Additional error details.
    
    Returns:
        Dictionary with error response structure.
    """
    response: dict[str, Any] = {
        "success": False,
        "error": error,
        "message": message,
    }
    
    if details:
        response["details"] = details
    
    return response
