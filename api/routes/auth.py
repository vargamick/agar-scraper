"""
Authentication routes.

Handles user registration, login, token refresh, and user management.
"""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.config import settings
from api.database.models import User
from api.database.repositories import UserRepository
from api.dependencies import (
    get_session,
    get_user_repository,
    get_current_user,
    get_current_superuser,
)
from api.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
    ApiKeyRequest,
)
from api.schemas.common import SuccessResponse
from api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from api.auth.jwt import decode_refresh_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=SuccessResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session
        user_repo: User repository

    Returns:
        Success response with tokens and user info

    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username exists
    if user_repo.exists_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    # Check if email exists
    if user_repo.exists_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        is_superuser=False,  # First user can be made superuser manually
        last_login=datetime.utcnow(),
    )

    # Save user
    user_repo.create(user)
    db.commit()

    logger.info(f"New user registered: {user.username} ({user.email})")

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Prepare response
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

    return SuccessResponse(data=token_response)


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Login with username/email and password.

    Args:
        credentials: Login credentials
        db: Database session
        user_repo: User repository

    Returns:
        Success response with tokens and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by username or email
    user = user_repo.get_by_username_or_email(credentials.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    logger.info(f"User logged in: {user.username}")

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Prepare response
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

    return SuccessResponse(data=token_response)


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh_token(
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Refresh access token using refresh token.

    Args:
        token_request: Refresh token request
        db: Database session
        user_repo: User repository

    Returns:
        Success response with new tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Decode refresh token
    payload = decode_refresh_token(token_request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Get user ID from payload
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
        )

    # Get user
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

    logger.info(f"Token refreshed for user: {user.username}")

    # Generate new tokens
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    # Prepare response
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

    return SuccessResponse(data=token_response)


@router.post("/api-key", response_model=SuccessResponse[TokenResponse])
async def authenticate_with_api_key(
    request: ApiKeyRequest,
    db: Session = Depends(get_session),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    Authenticate using an API key to receive JWT tokens.

    Creates a service account user on first use. Subsequent calls
    return tokens for the existing service account.

    Args:
        request: API key request
        db: Database session
        user_repo: User repository

    Returns:
        Success response with tokens and user info

    Raises:
        HTTPException: If API key is invalid or not configured
    """
    if not settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key authentication is not configured",
        )

    if request.api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    # Find or create the service account user
    service_username = "service-account"
    user = user_repo.get_by_username(service_username)

    if not user:
        user = User(
            username=service_username,
            email="service@scraper.internal",
            password_hash=hash_password(settings.API_KEY),
            full_name="API Service Account",
            is_active=True,
            is_superuser=True,
            last_login=datetime.utcnow(),
        )
        user_repo.create(user)
        db.commit()
        logger.info("Created service account user for API key authentication")
    else:
        user.last_login = datetime.utcnow()
        db.commit()

    logger.info("API key authentication successful")

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

    return SuccessResponse(data=token_response)


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from token

    Returns:
        Success response with user info
    """
    return SuccessResponse(data=UserResponse.model_validate(current_user))


@router.get("/users", response_model=SuccessResponse[list[UserResponse]])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_superuser),
    user_repo: UserRepository = Depends(get_user_repository),
):
    """
    List all users (superuser only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current superuser
        user_repo: User repository

    Returns:
        Success response with list of users
    """
    users = user_repo.get_all(skip=skip, limit=limit)
    return SuccessResponse(
        data=[UserResponse.model_validate(user) for user in users]
    )
