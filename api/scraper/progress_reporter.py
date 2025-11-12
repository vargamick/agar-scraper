"""
Progress reporter for scraper jobs.

Reports scraper progress back to the job system in real-time.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from api.database.connection import get_db_session
from api.database.repositories import JobRepository
from api.database.models import JobStatus, JobLog, LogLevel

logger = logging.getLogger(__name__)


class ProgressReporter:
    """
    Reports scraper progress to the database.

    Updates job progress, status, and logs in real-time.
    """

    def __init__(self, job_id: UUID):
        """
        Initialize progress reporter.

        Args:
            job_id: Job UUID
        """
        self.job_id = job_id
        self._db: Optional[Session] = None
        self._repo: Optional[JobRepository] = None

    def _get_repository(self) -> JobRepository:
        """Get job repository with database session."""
        if self._repo is None:
            self._db = get_db_session()
            self._repo = JobRepository(self._db)
        return self._repo

    def close(self):
        """Close database session."""
        if self._db:
            self._db.close()
            self._db = None
            self._repo = None

    def update_status(self, status: JobStatus):
        """
        Update job status.

        Args:
            status: New job status
        """
        try:
            repo = self._get_repository()
            repo.update_status(self.job_id, status)
            self._db.commit()
            logger.info(f"Job {self.job_id} status updated to {status.value}")
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
            if self._db:
                self._db.rollback()

    def update_progress(
        self,
        pages_scraped: int,
        total_pages: int,
        started_at: Optional[datetime] = None,
    ):
        """
        Update job progress.

        Args:
            pages_scraped: Number of pages scraped
            total_pages: Total number of pages
            started_at: Job start time
        """
        try:
            percentage = int((pages_scraped / total_pages) * 100) if total_pages > 0 else 0

            # Estimate completion time
            estimated_completion = None
            if started_at and pages_scraped > 0:
                elapsed = datetime.utcnow() - started_at
                rate = pages_scraped / elapsed.total_seconds()
                remaining_pages = total_pages - pages_scraped
                if rate > 0:
                    remaining_seconds = remaining_pages / rate
                    estimated_completion = datetime.utcnow() + timedelta(seconds=remaining_seconds)

            progress = {
                "percentage": percentage,
                "pagesScraped": pages_scraped,
                "totalPages": total_pages,
                "startedAt": started_at.isoformat() if started_at else None,
                "estimatedCompletion": estimated_completion.isoformat() if estimated_completion else None,
            }

            repo = self._get_repository()
            repo.update_progress(self.job_id, progress)
            self._db.commit()

            logger.debug(f"Job {self.job_id} progress: {percentage}% ({pages_scraped}/{total_pages})")
        except Exception as e:
            logger.error(f"Failed to update job progress: {e}")
            if self._db:
                self._db.rollback()

    def update_stats(
        self,
        bytes_downloaded: int = 0,
        items_extracted: int = 0,
        errors: int = 0,
        retries: int = 0,
    ):
        """
        Update job statistics.

        Args:
            bytes_downloaded: Bytes downloaded
            items_extracted: Items extracted
            errors: Error count
            retries: Retry count
        """
        try:
            stats = {
                "bytesDownloaded": bytes_downloaded,
                "itemsExtracted": items_extracted,
                "errors": errors,
                "retries": retries,
            }

            repo = self._get_repository()
            repo.update_stats(self.job_id, stats)
            self._db.commit()

            logger.debug(f"Job {self.job_id} stats updated: {items_extracted} items, {errors} errors")
        except Exception as e:
            logger.error(f"Failed to update job stats: {e}")
            if self._db:
                self._db.rollback()

    def add_log(
        self,
        level: LogLevel,
        message: str,
        metadata: Optional[dict] = None,
    ):
        """
        Add a log entry.

        Args:
            level: Log level
            message: Log message
            metadata: Optional metadata
        """
        try:
            log = JobLog(
                job_id=self.job_id,
                timestamp=datetime.utcnow(),
                level=level,
                message=message,
                log_metadata=metadata or {},
            )

            repo = self._get_repository()
            repo.add_log(log)
            self._db.commit()

            logger.debug(f"Job {self.job_id} log added: [{level.value}] {message}")
        except Exception as e:
            logger.error(f"Failed to add job log: {e}")
            if self._db:
                self._db.rollback()

    def log_info(self, message: str, metadata: Optional[dict] = None):
        """Log info message."""
        self.add_log(LogLevel.INFO, message, metadata)

    def log_warning(self, message: str, metadata: Optional[dict] = None):
        """Log warning message."""
        self.add_log(LogLevel.WARN, message, metadata)

    def log_error(self, message: str, metadata: Optional[dict] = None):
        """Log error message."""
        self.add_log(LogLevel.ERROR, message, metadata)

    def log_debug(self, message: str, metadata: Optional[dict] = None):
        """Log debug message."""
        self.add_log(LogLevel.DEBUG, message, metadata)
