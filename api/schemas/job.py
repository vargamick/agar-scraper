"""
Job-related Pydantic schemas.

Defines request and response models for scraper jobs.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from api.database.models import JobStatus, JobType, LogLevel


# ==================== Job Configuration Schemas ====================


class RateLimitConfig(BaseModel):
    """Rate limit configuration."""
    requests: int = Field(..., ge=1, description="Number of requests")
    per: str = Field(..., description="Time period (second, minute, hour)")


class SelectorConfig(BaseModel):
    """CSS and XPath selector configuration."""
    css: Optional[List[str]] = Field(default=None, description="CSS selectors")
    xpath: Optional[List[str]] = Field(default=None, description="XPath selectors")


class AuthConfig(BaseModel):
    """Authentication configuration for scraping."""
    type: Literal["bearer", "basic", "oauth2", "apikey"] = Field(..., description="Auth type")
    credentials: Dict[str, str] = Field(..., description="Auth credentials")


class JobConfig(BaseModel):
    """Job configuration for web scraping."""
    startUrls: List[str] = Field(..., min_length=1, description="Starting URLs")
    crawlDepth: Optional[int] = Field(default=3, ge=1, le=10, description="Maximum crawl depth")
    maxPages: Optional[int] = Field(default=100, ge=1, description="Maximum pages to scrape")

    rateLimit: Optional[RateLimitConfig] = Field(default=None, description="Rate limiting")
    selectors: Optional[SelectorConfig] = Field(default=None, description="CSS/XPath selectors")
    authentication: Optional[AuthConfig] = Field(default=None, description="Authentication config")

    headers: Optional[Dict[str, str]] = Field(default=None, description="Custom HTTP headers")
    followLinks: Optional[bool] = Field(default=True, description="Whether to follow links")
    respectRobotsTxt: Optional[bool] = Field(default=True, description="Respect robots.txt")


class MementoConfig(BaseModel):
    """Memento integration configuration."""
    enabled: bool = Field(default=False, description="Enable Memento integration")
    instanceId: str = Field(default="main-knowledge", description="Memento instance ID")
    processingOptions: Optional[Dict[str, Any]] = Field(
        default={"chunking": True, "embedding": True},
        description="Processing options"
    )


class WebhookConfig(BaseModel):
    """Webhook notification configuration."""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to trigger webhook")


class S3UploadConfig(BaseModel):
    """AWS S3 upload configuration."""
    enabled: bool = Field(default=True, description="Enable S3 upload")
    bucket: Optional[str] = Field(default=None, description="Override default S3 bucket")
    prefix: Optional[str] = Field(default=None, description="Custom S3 path prefix")
    includeFiles: List[str] = Field(
        default=["all_products.json", "categories.json", "results.json"],
        description="Specific files to upload"
    )
    uploadPdfs: bool = Field(default=True, description="Upload PDF files")
    uploadScreenshots: bool = Field(default=False, description="Upload screenshots")
    uploadCategories: bool = Field(default=False, description="Upload individual category JSON files")


class OutputConfig(BaseModel):
    """Output configuration for job results."""
    saveFiles: bool = Field(default=True, description="Save files locally")
    fileFormat: Literal["json", "markdown", "html"] = Field(default="json", description="File format")
    sendToMemento: Optional[MementoConfig] = Field(default=None, description="Memento config")
    webhook: Optional[WebhookConfig] = Field(default=None, description="Webhook config")
    uploadToS3: Optional[S3UploadConfig] = Field(default=None, description="S3 upload config")


class ScheduleConfig(BaseModel):
    """Schedule configuration for recurring jobs."""
    enabled: bool = Field(default=False, description="Enable scheduling")
    cron: str = Field(..., description="Cron expression")
    timezone: str = Field(default="UTC", description="Timezone")


# ==================== Job Request/Response Schemas ====================


class JobCreate(BaseModel):
    """Schema for creating a new job."""
    name: str = Field(..., min_length=1, max_length=255, description="Job name")
    description: Optional[str] = Field(default=None, description="Job description")
    type: JobType = Field(default=JobType.WEB, description="Job type")
    config: JobConfig = Field(..., description="Job configuration")
    output: OutputConfig = Field(..., description="Output configuration")
    schedule: Optional[ScheduleConfig] = Field(default=None, description="Schedule configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "docs-scrape-001",
                "description": "Scrape product documentation",
                "type": "web",
                "config": {
                    "startUrls": ["https://docs.example.com"],
                    "crawlDepth": 3,
                    "maxPages": 100,
                    "rateLimit": {"requests": 10, "per": "second"},
                    "respectRobotsTxt": True
                },
                "output": {
                    "saveFiles": True,
                    "fileFormat": "json",
                    "sendToMemento": {
                        "enabled": True,
                        "instanceId": "main-knowledge"
                    }
                }
            }
        }


class JobProgress(BaseModel):
    """Job progress information."""
    percentage: int = Field(..., ge=0, le=100, description="Progress percentage")
    pagesScraped: int = Field(..., ge=0, description="Pages scraped")
    totalPages: int = Field(..., ge=0, description="Total pages")
    startedAt: Optional[datetime] = Field(default=None, description="Start time")
    estimatedCompletion: Optional[datetime] = Field(default=None, description="Estimated completion")


class JobStats(BaseModel):
    """Job statistics."""
    bytesDownloaded: int = Field(default=0, ge=0, description="Bytes downloaded")
    itemsExtracted: int = Field(default=0, ge=0, description="Items extracted")
    errors: int = Field(default=0, ge=0, description="Error count")
    retries: int = Field(default=0, ge=0, description="Retry count")


class JobResponse(BaseModel):
    """Schema for job response."""
    jobId: UUID = Field(..., description="Job ID")
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(default=None, description="Job description")
    type: JobType = Field(..., description="Job type")
    status: JobStatus = Field(..., description="Job status")

    config: Dict[str, Any] = Field(..., description="Job configuration")
    output: Dict[str, Any] = Field(..., description="Output configuration")
    schedule: Optional[Dict[str, Any]] = Field(default=None, description="Schedule configuration")

    progress: Dict[str, Any] = Field(..., description="Progress information")
    stats: Dict[str, Any] = Field(..., description="Statistics")

    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Update timestamp")
    startedAt: Optional[datetime] = Field(default=None, description="Start timestamp")
    completedAt: Optional[datetime] = Field(default=None, description="Completion timestamp")

    createdBy: str = Field(..., description="Creator username")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "jobId": "123e4567-e89b-12d3-a456-426614174000",
                "name": "docs-scrape-001",
                "status": "running",
                "type": "web",
                "progress": {
                    "percentage": 67,
                    "pagesScraped": 67,
                    "totalPages": 100
                },
                "createdAt": "2025-01-11T10:29:00Z"
            }
        }


class JobCreateResponse(BaseModel):
    """Response after creating a job."""
    jobId: UUID = Field(..., description="Job ID")
    name: str = Field(..., description="Job name")
    status: JobStatus = Field(..., description="Job status")
    createdAt: datetime = Field(..., description="Creation timestamp")
    estimatedDuration: Optional[int] = Field(default=None, description="Estimated duration in seconds")


class JobListResponse(BaseModel):
    """Response for job listing."""
    jobs: List[JobResponse] = Field(..., description="List of jobs")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")


class JobControl(BaseModel):
    """Job control action."""
    action: Literal["start", "pause", "resume", "stop", "cancel"] = Field(..., description="Control action")

    class Config:
        json_schema_extra = {
            "example": {"action": "pause"}
        }


class JobControlResponse(BaseModel):
    """Response after job control action."""
    jobId: UUID = Field(..., description="Job ID")
    status: JobStatus = Field(..., description="New job status")
    message: str = Field(..., description="Status message")


# ==================== Job Result Schemas ====================


class JobResultItem(BaseModel):
    """Individual job result item."""
    url: Optional[str] = Field(default=None, description="Scraped URL")
    scrapedAt: datetime = Field(..., description="Scrape timestamp")
    content: Dict[str, Any] = Field(..., description="Scraped content")
    links: List[str] = Field(default=[], description="Extracted links")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://docs.example.com/api/intro",
                "scrapedAt": "2025-01-11T10:30:15Z",
                "content": {
                    "title": "API Introduction",
                    "body": "Welcome to our API..."
                },
                "links": ["https://docs.example.com/api/auth"]
            }
        }


class JobResultsResponse(BaseModel):
    """Response for job results."""
    jobId: UUID = Field(..., description="Job ID")
    itemsCount: int = Field(..., ge=0, description="Number of items")
    results: List[JobResultItem] = Field(..., description="Result items")
    exportUrl: Optional[str] = Field(default=None, description="Export download URL")


# ==================== Job Log Schemas ====================


class JobLogEntry(BaseModel):
    """Job log entry."""
    timestamp: datetime = Field(..., description="Log timestamp")
    level: LogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "timestamp": "2025-01-11T10:33:12Z",
                "level": "info",
                "message": "Scraped page: https://docs.example.com/api/intro",
                "metadata": {
                    "url": "https://docs.example.com/api/intro",
                    "statusCode": 200
                }
            }
        }


class JobLogsResponse(BaseModel):
    """Response for job logs."""
    logs: List[JobLogEntry] = Field(..., description="Log entries")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")


# ==================== Statistics Schemas ====================


class JobStatistics(BaseModel):
    """Overall job statistics."""
    totalJobs: int = Field(..., ge=0, description="Total number of jobs")
    runningJobs: int = Field(..., ge=0, description="Running jobs")
    queuedJobs: int = Field(..., ge=0, description="Queued jobs")
    completedJobs: int = Field(..., ge=0, description="Completed jobs")
    failedJobs: int = Field(..., ge=0, description="Failed jobs")

    totalPagesScraped: int = Field(..., ge=0, description="Total pages scraped")
    totalBytesDownloaded: int = Field(..., ge=0, description="Total bytes downloaded")
    averageJobDuration: int = Field(..., ge=0, description="Average job duration in seconds")

    last24h: Dict[str, int] = Field(..., description="Last 24 hours statistics")

    class Config:
        json_schema_extra = {
            "example": {
                "totalJobs": 50,
                "runningJobs": 1,
                "queuedJobs": 3,
                "completedJobs": 47,
                "failedJobs": 2,
                "totalPagesScraped": 12487,
                "totalBytesDownloaded": 524288000,
                "averageJobDuration": 287,
                "last24h": {
                    "jobsCompleted": 5,
                    "pagesScraped": 487
                }
            }
        }
