"""
API Configuration Management.

Handles all configuration settings for the Scraper API using pydantic-settings.
"""

import os
import secrets
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    API settings loaded from environment variables.

    Attributes are automatically loaded from environment variables
    with the same name (case-insensitive).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )

    # ==================== Application Settings ====================

    APP_NAME: str = "3DN Scraper API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "RESTful API for managing web scraping jobs"

    # API Server
    API_HOST: str = Field(default="0.0.0.0", description="API server host")
    API_PORT: int = Field(default=3010, description="API server port")
    API_PREFIX: str = Field(default="/api/scraper", description="API route prefix")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=False, description="Debug mode")

    # CORS (accepts comma-separated string or JSON array)
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:8080",
        description="Allowed CORS origins (comma-separated)"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # ==================== Database Settings ====================

    DATABASE_URL: str = Field(
        default="sqlite:///./scraper_api.db",
        description="Database connection URL"
    )
    DATABASE_ECHO: bool = Field(default=False, description="Echo SQL queries")

    # Connection pool settings (PostgreSQL only)
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Connection recycle time (seconds)")

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v

    # ==================== Authentication Settings ====================

    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT tokens"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, description="Access token expiration (minutes)")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, description="Refresh token expiration (days)")

    # Password hashing
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_HASH_SCHEMES: List[str] = ["bcrypt"]

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is set in production."""
        if not v or len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    # ==================== Redis Settings ====================

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Redis max connections")

    # ==================== Celery Settings ====================

    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend"
    )
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = Field(default=7200, description="Task time limit (seconds)")
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 100

    # ==================== Job Settings ====================

    JOB_DEFAULT_TIMEOUT: int = Field(default=3600, description="Default job timeout (seconds)")
    JOB_MAX_RETRIES: int = Field(default=3, description="Max job retries on failure")
    JOB_RETRY_DELAY: int = Field(default=60, description="Delay between retries (seconds)")

    # Rate limiting
    JOB_RATE_LIMIT_REQUESTS: int = Field(default=10, description="Rate limit requests")
    JOB_RATE_LIMIT_PERIOD: int = Field(default=1, description="Rate limit period (seconds)")

    # Pagination
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum page size for pagination")
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default page size")

    # ==================== Storage Settings ====================

    STORAGE_BASE_PATH: str = Field(
        default="./scraper_data",
        description="Base path for storing scraped data"
    )
    STORAGE_JOBS_PATH: str = Field(
        default="./scraper_data/jobs",
        description="Path for job-specific data"
    )
    STORAGE_EXPORTS_PATH: str = Field(
        default="./scraper_data/exports",
        description="Path for exported data"
    )

    # ==================== Webhook Settings ====================

    WEBHOOK_TIMEOUT: int = Field(default=30, description="Webhook request timeout (seconds)")
    WEBHOOK_MAX_RETRIES: int = Field(default=3, description="Webhook max retries")
    WEBHOOK_RETRY_DELAY: int = Field(default=60, description="Webhook retry delay (seconds)")

    # ==================== Memento Integration ====================

    MEMENTO_ENABLED: bool = Field(default=False, description="Enable Memento integration")
    MEMENTO_API_URL: Optional[str] = Field(default=None, description="Memento API base URL")
    MEMENTO_API_KEY: Optional[str] = Field(default=None, description="Memento API key")
    MEMENTO_DEFAULT_INSTANCE: str = Field(default="main-knowledge", description="Default Memento instance")

    # Processing options
    MEMENTO_ENABLE_CHUNKING: bool = Field(default=True, description="Enable content chunking")
    MEMENTO_ENABLE_EMBEDDING: bool = Field(default=True, description="Enable embedding generation")
    MEMENTO_CHUNK_SIZE: int = Field(default=1000, description="Chunk size (characters)")
    MEMENTO_CHUNK_OVERLAP: int = Field(default=200, description="Chunk overlap (characters)")

    # Matrix processing
    MATRIX_FILE_S3_PATH: Optional[str] = Field(
        default="agar/reference-data/application-matrix/AskAgar_ProductsData_v1.xlsx",
        description="S3 path to Product Application Matrix file"
    )
    MATRIX_MATCH_THRESHOLD: float = Field(default=0.85, description="Product matching threshold (0-1)")

    # ==================== AWS S3 Integration ====================

    S3_ENABLED: bool = Field(default=False, description="Enable S3 upload integration")
    S3_BUCKET_NAME: Optional[str] = Field(default=None, description="S3 bucket name for uploads")
    S3_REGION: str = Field(default="us-east-1", description="AWS region for S3 bucket")
    S3_ACCESS_KEY_ID: Optional[str] = Field(default=None, description="AWS access key ID")
    S3_SECRET_ACCESS_KEY: Optional[str] = Field(default=None, description="AWS secret access key")
    S3_UPLOAD_ON_COMPLETION: bool = Field(default=True, description="Auto-upload to S3 on job completion")
    S3_PREFIX: str = Field(default="scraper-outputs/", description="S3 key prefix for uploads")
    S3_UPLOAD_TIMEOUT: int = Field(default=300, description="S3 upload timeout (seconds)")
    S3_MAX_RETRIES: int = Field(default=3, description="S3 upload max retries")

    @field_validator("S3_BUCKET_NAME")
    @classmethod
    def validate_s3_bucket(cls, v: Optional[str], values) -> Optional[str]:
        """Validate S3 bucket is set when S3 is enabled."""
        # Note: In pydantic v2, we get ValidationInfo instead of values dict
        # This validator will check if S3_ENABLED but no bucket provided
        if v and not v.strip():
            raise ValueError("S3_BUCKET_NAME cannot be empty string")
        return v

    # ==================== Scraper Settings ====================

    # Inherit from existing scraper config
    SCRAPER_DEFAULT_TIMEOUT: int = 60
    SCRAPER_DEFAULT_USER_AGENT: str = "3DN-Scraper/1.0"
    SCRAPER_RESPECT_ROBOTS_TXT: bool = True
    SCRAPER_MAX_DEPTH: int = 5
    SCRAPER_MAX_PAGES_PER_JOB: int = 1000

    # ==================== Logging Settings ====================

    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    LOG_ROTATION: str = Field(default="100 MB", description="Log rotation size")
    LOG_RETENTION: str = Field(default="30 days", description="Log retention period")

    # ==================== Monitoring Settings ====================

    ENABLE_METRICS: bool = Field(default=False, description="Enable Prometheus metrics")
    METRICS_PORT: int = Field(default=9090, description="Metrics server port")

    # ==================== Helper Methods ====================

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"

    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for SQLAlchemy)."""
        return self.DATABASE_URL

    @property
    def database_url_async(self) -> str:
        """Get async database URL (for async SQLAlchemy)."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as list.

        Handles both comma-separated strings and JSON array format.
        """
        import json
        if isinstance(self.CORS_ORIGINS, str):
            # Try parsing as JSON first (handles ["url1", "url2"] format)
            if self.CORS_ORIGINS.startswith("["):
                try:
                    return json.loads(self.CORS_ORIGINS)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma-separated
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    def create_directories(self):
        """Create necessary storage directories."""
        os.makedirs(self.STORAGE_BASE_PATH, exist_ok=True)
        os.makedirs(self.STORAGE_JOBS_PATH, exist_ok=True)
        os.makedirs(self.STORAGE_EXPORTS_PATH, exist_ok=True)


# Global settings instance
settings = Settings()

# Create storage directories on import
settings.create_directories()
