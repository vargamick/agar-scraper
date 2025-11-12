"""
Job repository for database operations.

Provides CRUD operations and queries for Job, JobResult, and JobLog models.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

from api.database.models import (
    Job,
    JobResult,
    JobLog,
    JobStatus,
    JobType,
    LogLevel,
)


class JobRepository:
    """Repository for Job model operations."""

    def __init__(self, session: Session):
        """
        Initialize job repository.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    # ==================== Job CRUD Operations ====================

    def create(self, job: Job) -> Job:
        """
        Create a new job.

        Args:
            job: Job instance to create

        Returns:
            Created job with ID
        """
        self.session.add(job)
        self.session.flush()
        return job

    def get_by_id(self, job_id: UUID) -> Optional[Job]:
        """
        Get job by ID.

        Args:
            job_id: Job UUID

        Returns:
            Job instance or None if not found
        """
        return self.session.query(Job).filter(Job.id == job_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        created_by: Optional[UUID] = None,
    ) -> List[Job]:
        """
        Get all jobs with filtering and pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by job status
            job_type: Filter by job type
            created_by: Filter by creator user ID

        Returns:
            List of jobs
        """
        query = self.session.query(Job)

        # Apply filters
        if status:
            query = query.filter(Job.status == status)
        if job_type:
            query = query.filter(Job.type == job_type)
        if created_by:
            query = query.filter(Job.created_by == created_by)

        # Order by created_at descending (newest first)
        query = query.order_by(desc(Job.created_at))

        # Pagination
        return query.offset(skip).limit(limit).all()

    def update(self, job: Job) -> Job:
        """
        Update job.

        Args:
            job: Job instance with updated fields

        Returns:
            Updated job
        """
        self.session.flush()
        return job

    def update_status(self, job_id: UUID, status: JobStatus) -> Optional[Job]:
        """
        Update job status.

        Args:
            job_id: Job UUID
            status: New job status

        Returns:
            Updated job or None if not found
        """
        job = self.get_by_id(job_id)
        if job:
            job.status = status

            # Update timestamps based on status
            if status == JobStatus.RUNNING and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job.completed_at = datetime.utcnow()

            self.session.flush()
        return job

    def update_progress(
        self, job_id: UUID, progress: Dict[str, Any]
    ) -> Optional[Job]:
        """
        Update job progress.

        Args:
            job_id: Job UUID
            progress: Progress dictionary

        Returns:
            Updated job or None if not found
        """
        job = self.get_by_id(job_id)
        if job:
            job.progress = progress
            self.session.flush()
        return job

    def update_stats(self, job_id: UUID, stats: Dict[str, Any]) -> Optional[Job]:
        """
        Update job statistics.

        Args:
            job_id: Job UUID
            stats: Stats dictionary

        Returns:
            Updated job or None if not found
        """
        job = self.get_by_id(job_id)
        if job:
            job.stats = stats
            self.session.flush()
        return job

    def delete(self, job_id: UUID) -> bool:
        """
        Delete job by ID.

        Args:
            job_id: Job UUID

        Returns:
            True if deleted, False if not found
        """
        job = self.get_by_id(job_id)
        if job:
            self.session.delete(job)
            self.session.flush()
            return True
        return False

    def count(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        created_by: Optional[UUID] = None,
    ) -> int:
        """
        Count jobs with optional filtering.

        Args:
            status: Filter by job status
            job_type: Filter by job type
            created_by: Filter by creator user ID

        Returns:
            Job count
        """
        query = self.session.query(func.count(Job.id))

        if status:
            query = query.filter(Job.status == status)
        if job_type:
            query = query.filter(Job.type == job_type)
        if created_by:
            query = query.filter(Job.created_by == created_by)

        return query.scalar()

    # ==================== Job Statistics ====================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall job statistics.

        Returns:
            Dictionary with job statistics
        """
        total_jobs = self.session.query(func.count(Job.id)).scalar()

        # Count by status
        status_counts = (
            self.session.query(Job.status, func.count(Job.id))
            .group_by(Job.status)
            .all()
        )
        status_dict = {status.value: count for status, count in status_counts}

        # Total pages scraped and bytes downloaded
        # Note: This requires PostgreSQL's JSON operators
        # For SQLite, we'll return 0 for now
        total_stats = (0, 0)
        try:
            from sqlalchemy.dialects.postgresql import INTEGER
            total_stats = self.session.query(
                func.sum(Job.stats["itemsExtracted"].astext.cast(INTEGER)),
                func.sum(Job.stats["bytesDownloaded"].astext.cast(INTEGER)),
            ).first()
        except Exception:
            pass

        # Average job duration (for completed jobs)
        avg_duration_query = (
            self.session.query(
                func.avg(
                    func.extract("epoch", Job.completed_at - Job.started_at)
                )
            )
            .filter(
                and_(
                    Job.status == JobStatus.COMPLETED,
                    Job.started_at.isnot(None),
                    Job.completed_at.isnot(None),
                )
            )
            .scalar()
        )

        # Last 24 hours stats
        yesterday = datetime.utcnow() - timedelta(hours=24)
        last_24h = (0, 0)
        try:
            from sqlalchemy.dialects.postgresql import INTEGER
            last_24h = (
                self.session.query(
                    func.count(Job.id),
                    func.sum(Job.stats["itemsExtracted"].astext.cast(INTEGER)),
                )
                .filter(
                    and_(
                        Job.completed_at >= yesterday,
                        Job.status == JobStatus.COMPLETED,
                    )
                )
                .first()
            )
        except Exception:
            pass

        return {
            "totalJobs": total_jobs or 0,
            "runningJobs": status_dict.get("running", 0),
            "queuedJobs": status_dict.get("pending", 0),
            "completedJobs": status_dict.get("completed", 0),
            "failedJobs": status_dict.get("failed", 0),
            "totalPagesScraped": total_stats[0] or 0,
            "totalBytesDownloaded": total_stats[1] or 0,
            "averageJobDuration": int(avg_duration_query or 0),
            "last24h": {
                "jobsCompleted": last_24h[0] or 0,
                "pagesScraped": last_24h[1] or 0,
            },
        }

    # ==================== JobResult Operations ====================

    def add_result(self, result: JobResult) -> JobResult:
        """
        Add a job result.

        Args:
            result: JobResult instance

        Returns:
            Created result with ID
        """
        self.session.add(result)
        self.session.flush()
        return result

    def get_results(
        self, job_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[JobResult]:
        """
        Get job results with pagination.

        Args:
            job_id: Job UUID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of job results
        """
        return (
            self.session.query(JobResult)
            .filter(JobResult.job_id == job_id)
            .order_by(JobResult.scraped_at)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_results(self, job_id: UUID) -> int:
        """
        Count job results.

        Args:
            job_id: Job UUID

        Returns:
            Result count
        """
        return (
            self.session.query(func.count(JobResult.id))
            .filter(JobResult.job_id == job_id)
            .scalar()
        )

    # ==================== JobLog Operations ====================

    def add_log(self, log: JobLog) -> JobLog:
        """
        Add a job log entry.

        Args:
            log: JobLog instance

        Returns:
            Created log with ID
        """
        self.session.add(log)
        self.session.flush()
        return log

    def get_logs(
        self,
        job_id: UUID,
        level: Optional[LogLevel] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[JobLog]:
        """
        Get job logs with filtering and pagination.

        Args:
            job_id: Job UUID
            level: Filter by log level
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of job logs
        """
        query = self.session.query(JobLog).filter(JobLog.job_id == job_id)

        if level:
            query = query.filter(JobLog.level == level)

        return (
            query.order_by(desc(JobLog.timestamp))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_logs(
        self, job_id: UUID, level: Optional[LogLevel] = None
    ) -> int:
        """
        Count job logs.

        Args:
            job_id: Job UUID
            level: Filter by log level

        Returns:
            Log count
        """
        query = self.session.query(func.count(JobLog.id)).filter(
            JobLog.job_id == job_id
        )

        if level:
            query = query.filter(JobLog.level == level)

        return query.scalar()
