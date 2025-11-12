"""
Database connection management.

Handles SQLAlchemy engine creation, session management, and database initialization.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from api.database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions.

    Provides connection pooling, session management, and database initialization.
    """

    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL
            echo: Whether to echo SQL statements (for debugging)
        """
        self.database_url = database_url
        self.echo = echo
        self._engine = None
        self._session_factory = None

    @property
    def engine(self) -> Engine:
        """Get or create database engine."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._session_factory

    def _create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine with appropriate configuration.

        Returns:
            Configured SQLAlchemy engine
        """
        # Determine if using PostgreSQL or SQLite
        is_postgres = self.database_url.startswith("postgresql")

        if is_postgres:
            # PostgreSQL configuration with connection pooling
            engine = create_engine(
                self.database_url,
                echo=self.echo,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,  # Recycle connections after 1 hour
                connect_args={
                    "connect_timeout": 10,
                },
            )
        else:
            # SQLite configuration
            engine = create_engine(
                self.database_url,
                echo=self.echo,
                connect_args={
                    "check_same_thread": False,  # Allow SQLite in multi-threaded context
                    "timeout": 30,
                },
            )

            # Enable foreign key constraints for SQLite
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        logger.info(f"Database engine created: {self.database_url.split('@')[-1] if '@' in self.database_url else 'sqlite'}")
        return engine

    def create_all_tables(self):
        """
        Create all database tables.

        This should only be used for development/testing.
        In production, use Alembic migrations.
        """
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def drop_all_tables(self):
        """
        Drop all database tables.

        WARNING: This will delete all data!
        Should only be used for development/testing.
        """
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise

    def get_session(self) -> Session:
        """
        Create a new database session.

        Returns:
            SQLAlchemy session
        """
        return self.session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db_manager.session_scope() as session:
                session.add(user)
                # Commit happens automatically
                # Rollback on exception

        Yields:
            SQLAlchemy session
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """Close database engine and all connections."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance (will be initialized by the application)
db_manager: DatabaseManager = None


def init_database(database_url: str, echo: bool = False) -> DatabaseManager:
    """
    Initialize global database manager.

    Args:
        database_url: SQLAlchemy database URL
        echo: Whether to echo SQL statements

    Returns:
        Initialized DatabaseManager instance
    """
    global db_manager
    db_manager = DatabaseManager(database_url, echo)
    logger.info("Database manager initialized")
    return db_manager


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.

    Usage in FastAPI:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Yields:
        Database session
    """
    if db_manager is None:
        raise RuntimeError("Database manager not initialized. Call init_database() first.")

    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def get_db_session() -> Session:
    """
    Get a database session directly (not for FastAPI dependencies).

    Auto-initializes the database manager if needed (for Celery worker processes).

    Returns:
        Database session (caller is responsible for closing it)
    """
    global db_manager
    if db_manager is None:
        # Auto-initialize for Celery worker processes
        from api.config import settings
        logger.info("Auto-initializing database manager in worker process")
        db_manager = DatabaseManager(settings.DATABASE_URL, echo=False)

    return db_manager.get_session()
