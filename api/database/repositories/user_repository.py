"""
User repository for database operations.

Provides CRUD operations and queries for User model.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from api.database.models import User


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: Session):
        """
        Initialize user repository.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def create(self, user: User) -> User:
        """
        Create a new user.

        Args:
            user: User instance to create

        Returns:
            Created user with ID
        """
        self.session.add(user)
        self.session.flush()
        return user

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User instance or None if not found
        """
        return self.session.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username string

        Returns:
            User instance or None if not found
        """
        return self.session.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: Email string

        Returns:
            User instance or None if not found
        """
        return self.session.query(User).filter(User.email == email).first()

    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """
        Get user by username or email.

        Args:
            identifier: Username or email string

        Returns:
            User instance or None if not found
        """
        return self.session.query(User).filter(
            or_(User.username == identifier, User.email == identifier)
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of users
        """
        return self.session.query(User).offset(skip).limit(limit).all()

    def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get active users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active users
        """
        return (
            self.session.query(User)
            .filter(User.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, user: User) -> User:
        """
        Update user.

        Args:
            user: User instance with updated fields

        Returns:
            Updated user
        """
        self.session.flush()
        return user

    def delete(self, user_id: UUID) -> bool:
        """
        Delete user by ID.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        user = self.get_by_id(user_id)
        if user:
            self.session.delete(user)
            self.session.flush()
            return True
        return False

    def count(self) -> int:
        """
        Count total number of users.

        Returns:
            Total user count
        """
        return self.session.query(User).count()

    def exists_by_username(self, username: str) -> bool:
        """
        Check if username exists.

        Args:
            username: Username to check

        Returns:
            True if exists, False otherwise
        """
        return (
            self.session.query(User.id)
            .filter(User.username == username)
            .first()
            is not None
        )

    def exists_by_email(self, email: str) -> bool:
        """
        Check if email exists.

        Args:
            email: Email to check

        Returns:
            True if exists, False otherwise
        """
        return (
            self.session.query(User.id)
            .filter(User.email == email)
            .first()
            is not None
        )
