"""
Common Pydantic schemas used across the API.
"""

from typing import Any, Optional, Generic, TypeVar
from pydantic import BaseModel, Field

# Generic type for data payloads
T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """
    Standard success response wrapper.

    Used to wrap successful API responses with consistent structure.
    """

    success: bool = Field(default=True, description="Success indicator")
    data: T = Field(..., description="Response data")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"message": "Operation completed successfully"},
            }
        }


class ErrorDetail(BaseModel):
    """Error detail information."""

    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Any] = Field(default=None, description="Additional error details")


class ErrorResponse(BaseModel):
    """
    Standard error response wrapper.

    Used to wrap error responses with consistent structure.
    """

    success: bool = Field(default=False, description="Success indicator (always false)")
    error: ErrorDetail = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": 400,
                    "message": "Bad request",
                    "details": None,
                },
            }
        }


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.
    """

    skip: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of records to return",
    )


class PaginationInfo(BaseModel):
    """
    Pagination information in responses.
    """

    total: int = Field(..., description="Total number of records")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Number of records requested")
    has_more: bool = Field(..., description="Whether there are more records")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 100,
                "skip": 0,
                "limit": 20,
                "has_more": True,
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    database: str = Field(..., description="Database connection status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "database": "connected",
            }
        }
