"""
Dependency injection for FastAPI routes.

Provides reusable dependencies for authentication, database sessions, and more.
"""

from typing import Generator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from api.database.connection import get_db
from api.database.models import User
from api.database.repositories import UserRepository
from api.auth.jwt import decode_access_token

# Security scheme for Bearer token authentication
security = HTTPBearer()


# ==================== Database Dependencies ====================


def get_session() -> Generator[Session, None, None]:
    """
    Get database session dependency.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_session)):
            ...

    Yields:
        Database session
    """
    yield from get_db()


def get_user_repository(db: Session = Depends(get_session)) -> UserRepository:
    """
    Get user repository dependency.

    Args:
        db: Database session

    Returns:
        UserRepository instance
    """
    return UserRepository(db)


# ==================== Authentication Dependencies ====================


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Get current user ID from JWT token.

    Args:
        credentials: Bearer token credentials

    Returns:
        User UUID

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    # Decode JWT token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from payload
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    """
    Get current authenticated user.

    Args:
        user_id: Current user ID from token
        user_repo: User repository

    Returns:
        User instance

    Raises:
        HTTPException: If user not found or inactive
    """
    user = user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current active user (alias for get_current_user).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Active user instance
    """
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current superuser (admin only).

    Args:
        current_user: Current user from get_current_user

    Returns:
        Superuser instance

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions (superuser required)",
        )

    return current_user


# ==================== Optional Authentication Dependencies ====================


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    user_repo: UserRepository = Depends(get_user_repository),
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.

    Useful for endpoints that optionally require authentication.

    Args:
        credentials: Optional bearer token credentials
        user_repo: User repository

    Returns:
        User instance if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        user_id = await get_current_user_id(credentials)
        return user_repo.get_by_id(user_id)
    except HTTPException:
        return None
