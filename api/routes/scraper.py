"""
Scraper API routes.

Implements the complete scraper job management API.
"""

import logging
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.database.models import User, Job, JobStatus, JobType, LogLevel
from api.database.repositories import JobRepository
from api.dependencies import get_session, get_current_user
from api.schemas.common import SuccessResponse
from api.schemas.job import (
    JobCreate,
    JobCreateResponse,
    JobResponse,
    JobListResponse,
    JobControl,
    JobControlResponse,
    JobLogsResponse,
    JobLogEntry,
    JobResultsResponse,
    JobResultItem,
    JobStatistics,
)
from api.jobs.tasks import execute_scraper_job
from api.jobs.celery_app import revoke_task

logger = logging.getLogger(__name__)

router = APIRouter()


def _job_to_response(job: Job) -> JobResponse:
    """Convert Job model to JobResponse schema."""
    return JobResponse(
        jobId=job.id,
        name=job.name,
        description=job.description,
        type=job.type,
        status=job.status,
        config=job.config,
        output=job.output,
        schedule=job.schedule,
        progress=job.progress,
        stats=job.stats,
        createdAt=job.created_at,
        updatedAt=job.updated_at,
        startedAt=job.started_at,
        completedAt=job.completed_at,
        createdBy=job.creator.username if job.creator else "unknown",
    )


@router.post("/jobs", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse[JobCreateResponse])
async def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new scraper job.

    Creates a job in the database and queues it for execution.
    """
    try:
        # Generate folder name with timestamp
        folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create job in database
        job = Job(
            name=job_data.name,
            description=job_data.description,
            type=job_data.type,
            status=JobStatus.PENDING,
            folder_name=folder_name,
            config=job_data.config.model_dump(),
            output=job_data.output.model_dump(),
            schedule=job_data.schedule.model_dump() if job_data.schedule else None,
            progress={
                "percentage": 0,
                "pagesScraped": 0,
                "totalPages": job_data.config.maxPages or 100,
                "startedAt": None,
                "estimatedCompletion": None,
            },
            stats={
                "bytesDownloaded": 0,
                "itemsExtracted": 0,
                "errors": 0,
                "retries": 0,
            },
            created_by=current_user.id,
        )

        repo = JobRepository(db)
        job = repo.create(job)
        db.commit()

        logger.info(f"Job created: {job.id} by user {current_user.username}")

        # Queue job for execution
        task = execute_scraper_job.delay(
            job_id=str(job.id),
            job_config=job.config,
            output_config=job.output,
            folder_name=folder_name,
        )

        logger.info(f"Job {job.id} queued with task ID: {task.id}")

        # Estimate duration based on max pages
        max_pages = job_data.config.maxPages or 100
        estimated_duration = max_pages * 3  # Rough estimate: 3 seconds per page

        response = JobCreateResponse(
            jobId=job.id,
            name=job.name,
            status=job.status,
            createdAt=job.created_at,
            estimatedDuration=estimated_duration,
        )

        return SuccessResponse(data=response)

    except Exception as e:
        logger.error(f"Failed to create job: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}",
        )


@router.get("/jobs", response_model=SuccessResponse[JobListResponse])
async def list_jobs(
    job_status: Optional[JobStatus] = Query(None, alias="status", description="Filter by job status"),
    job_type: Optional[JobType] = Query(None, alias="type", description="Filter by job type"),
    limit: int = Query(20, ge=1, le=100, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    List scraper jobs with filtering and pagination.
    """
    try:
        repo = JobRepository(db)

        # Get jobs
        jobs = repo.get_all(
            skip=offset,
            limit=limit,
            status=job_status,
            job_type=job_type,
            created_by=current_user.id if not current_user.is_superuser else None,
        )

        # Get total count
        total = repo.count(
            status=job_status,
            job_type=job_type,
            created_by=current_user.id if not current_user.is_superuser else None,
        )

        # Convert to response models
        job_responses = [_job_to_response(job) for job in jobs]

        response = JobListResponse(
            jobs=job_responses,
            pagination={
                "total": total,
                "limit": limit,
                "offset": offset,
                "hasMore": offset + limit < total,
            },
        )

        return SuccessResponse(data=response)

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=SuccessResponse[JobResponse])
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get job details by ID.
    """
    try:
        repo = JobRepository(db)
        job = repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        # Check permissions
        if not current_user.is_superuser and job.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this job",
            )

        response = _job_to_response(job)
        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {str(e)}",
        )


@router.post("/jobs/{job_id}/control", response_model=SuccessResponse[JobControlResponse])
async def control_job(
    job_id: UUID,
    control_data: JobControl,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Control job execution (start, pause, resume, stop, cancel).
    """
    try:
        repo = JobRepository(db)
        job = repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        # Check permissions
        if not current_user.is_superuser and job.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to control this job",
            )

        action = control_data.action
        new_status = job.status
        message = ""

        # Handle different control actions
        if action == "start":
            if job.status == JobStatus.PENDING:
                # Job will start automatically when queued
                message = "Job is already queued for execution"
            else:
                message = "Job cannot be started from current status"

        elif action == "pause":
            if job.status == JobStatus.RUNNING:
                new_status = JobStatus.PAUSED
                # Note: Actual pausing of execution would require more complex implementation
                message = "Job paused (note: currently running task will complete)"
            else:
                message = "Job can only be paused when running"

        elif action == "resume":
            if job.status == JobStatus.PAUSED:
                new_status = JobStatus.RUNNING
                message = "Job resumed"
            else:
                message = "Job can only be resumed when paused"

        elif action in ["stop", "cancel"]:
            if job.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.PAUSED]:
                new_status = JobStatus.CANCELLED
                # Revoke Celery task if it exists
                # Note: Task ID would need to be stored with job
                message = f"Job {action}led"
            else:
                message = f"Job cannot be {action}led from current status"

        # Update job status if changed
        if new_status != job.status:
            repo.update_status(job_id, new_status)
            db.commit()

        response = JobControlResponse(
            jobId=job_id,
            status=new_status,
            message=message,
        )

        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to control job: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to control job: {str(e)}",
        )


@router.get("/jobs/{job_id}/logs", response_model=SuccessResponse[JobLogsResponse])
async def get_job_logs(
    job_id: UUID,
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get job logs with filtering and pagination.
    """
    try:
        repo = JobRepository(db)
        job = repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        # Check permissions
        if not current_user.is_superuser and job.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access job logs",
            )

        # Get logs
        logs = repo.get_logs(job_id, level=level, skip=offset, limit=limit)
        total = repo.count_logs(job_id, level=level)

        # Convert to response models
        log_entries = [
            JobLogEntry(
                timestamp=log.timestamp,
                level=log.level,
                message=log.message,
                metadata=log.log_metadata,
            )
            for log in logs
        ]

        response = JobLogsResponse(
            logs=log_entries,
            pagination={
                "total": total,
                "limit": limit,
                "hasMore": offset + limit < total,
            },
        )

        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job logs: {str(e)}",
        )


@router.get("/jobs/{job_id}/results", response_model=SuccessResponse[JobResultsResponse])
async def get_job_results(
    job_id: UUID,
    result_format: str = Query("json", alias="format", description="Result format"),
    download: bool = Query(False, description="Download as file"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get job results with pagination.
    """
    try:
        repo = JobRepository(db)
        job = repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        # Check permissions
        if not current_user.is_superuser and job.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access job results",
            )

        # Get results
        results = repo.get_results(job_id, skip=offset, limit=limit)
        total = repo.count_results(job_id)

        # Convert to response models
        result_items = [
            JobResultItem(
                url=result.url,
                scrapedAt=result.scraped_at,
                content=result.content,
                links=result.links,
            )
            for result in results
        ]

        response = JobResultsResponse(
            jobId=job_id,
            itemsCount=total,
            results=result_items,
            exportUrl=f"/api/scraper/jobs/{job_id}/results/download" if total > 0 else None,
        )

        return SuccessResponse(data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job results: {str(e)}",
        )


@router.delete("/jobs/{job_id}", response_model=SuccessResponse[dict])
async def delete_job(
    job_id: UUID,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a job and all its associated data.
    """
    try:
        repo = JobRepository(db)
        job = repo.get_by_id(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found",
            )

        # Check permissions
        if not current_user.is_superuser and job.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this job",
            )

        # Cannot delete running jobs
        if job.status == JobStatus.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a running job. Stop it first.",
            )

        # Delete job
        repo.delete(job_id)
        db.commit()

        logger.info(f"Job {job_id} deleted by user {current_user.username}")

        return SuccessResponse(data={"message": "Job deleted successfully"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job: {str(e)}",
        )


@router.get("/stats", response_model=SuccessResponse[JobStatistics])
async def get_statistics(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get overall scraper statistics.
    """
    try:
        repo = JobRepository(db)
        stats = repo.get_statistics()

        response = JobStatistics(**stats)
        return SuccessResponse(data=response)

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )
