"""
JWT token creation and validation.

Handles access and refresh token generation and decoding.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from jose import JWTError, jwt

from api.config import settings


def create_access_token(
    user_id: UUID,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create JWT access token for a user.

    Args:
        user_id: User UUID
        additional_claims: Optional additional claims to include in token

    Returns:
        Encoded JWT token string
    """
    # Calculate expiration time
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Build token payload
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow(),  # Issued at
        "type": "access",  # Token type
    }

    # Add additional claims if provided
    if additional_claims:
        payload.update(additional_claims)

    # Encode and return token
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(
    user_id: UUID,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create JWT refresh token for a user.

    Args:
        user_id: User UUID
        additional_claims: Optional additional claims to include in token

    Returns:
        Encoded JWT token string
    """
    # Calculate expiration time
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Build token payload
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow(),  # Issued at
        "type": "refresh",  # Token type
    }

    # Add additional claims if provided
    if additional_claims:
        payload.update(additional_claims)

    # Encode and return token
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT access token.

    Args:
        token: JWT token string

    Returns:
        Token payload dict if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        # Verify token type
        if payload.get("type") != "access":
            return None

        return payload

    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT refresh token.

    Args:
        token: JWT token string

    Returns:
        Token payload dict if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        # Verify token type
        if payload.get("type") != "refresh":
            return None

        return payload

    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token (any type).

    Args:
        token: JWT token string

    Returns:
        Token payload dict if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload

    except JWTError:
        return None
