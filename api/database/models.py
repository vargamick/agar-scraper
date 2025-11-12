"""
SQLAlchemy ORM models for the Scraper API.

Defines database schema for jobs, results, logs, and users.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Integer,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    """Job type enumeration."""
    WEB = "web"
    API = "api"
    FILESYSTEM = "filesystem"
    DATABASE = "database"


class LogLevel(str, enum.Enum):
    """Log level enumeration."""
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"


class User(Base):
    """
    User model for authentication and authorization.

    Stores user credentials, API tokens, and metadata.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # API tokens stored as JSON array
    api_tokens = Column(JSONB, default=list, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    jobs = relationship("Job", back_populates="creator", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Job(Base):
    """
    Scraper job model.

    Stores job configuration, status, progress, and statistics.
    """
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Job type and status
    type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)

    # Configuration stored as JSON
    config = Column(JSONB, nullable=False)

    # Output configuration
    output = Column(JSONB, nullable=False)

    # Schedule configuration
    schedule = Column(JSONB, nullable=True)

    # Progress tracking
    progress = Column(JSONB, default={
        "percentage": 0,
        "pagesScraped": 0,
        "totalPages": 0,
        "startedAt": None,
        "estimatedCompletion": None,
    }, nullable=False)

    # Statistics
    stats = Column(JSONB, default={
        "bytesDownloaded": 0,
        "itemsExtracted": 0,
        "errors": 0,
        "retries": 0,
    }, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Foreign keys
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Relationships
    creator = relationship("User", back_populates="jobs")
    results = relationship("JobResult", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_job_status_created", "status", "created_at"),
        Index("idx_job_type_status", "type", "status"),
        Index("idx_job_created_by_status", "created_by", "status"),
    )

    def __repr__(self):
        return f"<Job(id={self.id}, name='{self.name}', type={self.type}, status={self.status})>"


class JobResult(Base):
    """
    Job result model.

    Stores individual scraped items/pages from a job.
    """
    __tablename__ = "job_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)

    # Result data
    url = Column(Text, nullable=True)
    scraped_at = Column(DateTime(timezone=True), nullable=False)

    # Content stored as JSON (flexible schema)
    content = Column(JSONB, nullable=False)

    # Links extracted from the page
    links = Column(JSONB, default=list, nullable=False)

    # Result metadata
    result_metadata = Column(JSONB, default={}, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="results")

    # Indexes
    __table_args__ = (
        Index("idx_result_job_scraped", "job_id", "scraped_at"),
    )

    def __repr__(self):
        return f"<JobResult(id={self.id}, job_id={self.job_id}, url='{self.url}')>"


class JobLog(Base):
    """
    Job log model.

    Stores log entries for job execution.
    """
    __tablename__ = "job_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)

    # Log data
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    level = Column(SQLEnum(LogLevel), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Additional context stored as JSON
    log_metadata = Column(JSONB, default={}, nullable=False)

    # Relationships
    job = relationship("Job", back_populates="logs")

    # Indexes for log queries
    __table_args__ = (
        Index("idx_log_job_timestamp", "job_id", "timestamp"),
        Index("idx_log_job_level", "job_id", "level"),
    )

    def __repr__(self):
        return f"<JobLog(id={self.id}, job_id={self.job_id}, level={self.level}, message='{self.message[:50]}...')>"


class ScheduledJob(Base):
    """
    Scheduled job model.

    Stores scheduled job configurations for cron-based execution.
    """
    __tablename__ = "scheduled_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Reference to job configuration (can be a template)
    job_template = Column(JSONB, nullable=False)

    # Schedule configuration
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Execution tracking
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    run_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Foreign keys
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<ScheduledJob(id={self.id}, name='{self.name}', cron='{self.cron_expression}', active={self.is_active})>"


class WebhookEndpoint(Base):
    """
    Webhook endpoint model.

    Stores webhook configurations for job notifications.
    """
    __tablename__ = "webhook_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)

    # Webhook configuration
    url = Column(Text, nullable=False)
    events = Column(JSONB, nullable=False)  # Array of event types
    headers = Column(JSONB, default={}, nullable=False)  # Custom headers

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Retry configuration
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay = Column(Integer, default=60, nullable=False)  # seconds

    # Statistics
    total_sent = Column(Integer, default=0, nullable=False)
    total_failed = Column(Integer, default=0, nullable=False)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<WebhookEndpoint(id={self.id}, job_id={self.job_id}, url='{self.url}')>"
