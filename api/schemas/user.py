"""
User-related Pydantic schemas.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from api.config import settings


class UserCreate(BaseModel):
    """
    Schema for creating a new user.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username",
    )
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=settings.PASSWORD_MIN_LENGTH,
        description="User password",
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="User full name",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v.isalnum() and "_" not in v and "-" not in v:
            raise ValueError(
                "Username must contain only alphanumeric characters, underscores, or hyphens"
            )
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
            )
        # Add more password strength checks if needed
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "securepassword123",
                "full_name": "John Doe",
            }
        }


class UserLogin(BaseModel):
    """
    Schema for user login.
    """

    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "johndoe",
                "password": "securepassword123",
            }
        }


class UserResponse(BaseModel):
    """
    Schema for user response (without sensitive data).
    """

    id: UUID = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: Optional[str] = Field(default=None, description="Full name")
    is_active: bool = Field(..., description="Whether user is active")
    is_superuser: bool = Field(..., description="Whether user is superuser")
    created_at: datetime = Field(..., description="Account creation timestamp")
    last_login: Optional[datetime] = Field(
        default=None, description="Last login timestamp"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "john@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_superuser": False,
                "created_at": "2025-01-11T10:00:00Z",
                "last_login": "2025-01-11T10:30:00Z",
            }
        }


class TokenResponse(BaseModel):
    """
    Schema for authentication token response.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "is_superuser": False,
                    "created_at": "2025-01-11T10:00:00Z",
                    "last_login": "2025-01-11T10:30:00Z",
                },
            }
        }


class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token request.
    """

    refresh_token: str = Field(..., description="JWT refresh token")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class UserUpdate(BaseModel):
    """
    Schema for updating user information.
    """

    email: Optional[EmailStr] = Field(default=None, description="New email address")
    full_name: Optional[str] = Field(
        default=None, max_length=255, description="New full name"
    )
    password: Optional[str] = Field(
        default=None,
        min_length=settings.PASSWORD_MIN_LENGTH,
        description="New password",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "newemail@example.com",
                "full_name": "John Updated Doe",
                "password": "newsecurepassword123",
            }
        }
