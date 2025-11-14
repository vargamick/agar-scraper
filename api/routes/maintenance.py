"""
Maintenance API routes for run management.

Provides endpoints for archival, cleanup, and storage management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.database.models import User
from api.dependencies import get_session, get_current_user
from api.schemas.common import SuccessResponse
from api.jobs.maintenance_tasks import (
    archive_old_runs,
    cleanup_old_runs,
    restore_archived_run,
    get_storage_stats,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/maintenance/archive", response_model=SuccessResponse[dict])
async def trigger_archival(
    days: int = Query(7, ge=1, le=365, description="Archive runs older than this many days"),
    dry_run: bool = Query(False, description="Preview changes without executing"),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger archival of old runs.

    Only superusers can trigger archival.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can trigger archival",
        )

    try:
        logger.info(f"User {current_user.username} triggered archival (days={days}, dry_run={dry_run})")

        # Run archival task synchronously
        result = archive_old_runs(days=days, dry_run=dry_run)

        return SuccessResponse(data=result)

    except Exception as e:
        logger.error(f"Archival failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Archival failed: {str(e)}",
        )


@router.post("/maintenance/cleanup", response_model=SuccessResponse[dict])
async def trigger_cleanup(
    days: int = Query(30, ge=1, le=365, description="Delete runs older than this many days"),
    dry_run: bool = Query(False, description="Preview changes without executing"),
    strategy: str = Query("soft", regex="^(soft|hard)$", description="Deletion strategy"),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger cleanup of old runs.

    Only superusers can trigger cleanup.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can trigger cleanup",
        )

    try:
        logger.info(f"User {current_user.username} triggered cleanup (days={days}, dry_run={dry_run}, strategy={strategy})")

        # Run cleanup task synchronously
        result = cleanup_old_runs(days=days, dry_run=dry_run, strategy=strategy)

        return SuccessResponse(data=result)

    except Exception as e:
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}",
        )


@router.post("/maintenance/restore/{job_id}", response_model=SuccessResponse[dict])
async def restore_run(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    """
    Restore an archived run back to active storage.

    Only the job owner or superusers can restore runs.
    """
    try:
        from api.database.repositories import JobRepository

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
                detail="Not authorized to restore this job",
            )

        logger.info(f"User {current_user.username} restoring job {job_id}")

        # Run restore task synchronously
        result = restore_archived_run(str(job_id))

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Restoration failed"),
            )

        return SuccessResponse(data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}",
        )


@router.get("/maintenance/storage-stats", response_model=SuccessResponse[dict])
async def storage_statistics(
    current_user: User = Depends(get_current_user),
):
    """
    Get storage statistics for runs.

    Shows active and archived storage usage.
    """
    try:
        logger.info(f"User {current_user.username} requested storage stats")

        # Get storage stats synchronously
        result = get_storage_stats()

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return SuccessResponse(data=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}",
        )


@router.get("/maintenance/health", response_model=SuccessResponse[dict])
async def maintenance_health(
    current_user: User = Depends(get_current_user),
):
    """
    Get health status of maintenance system.

    Shows when archival and cleanup tasks last ran.
    """
    try:
        from celery.result import AsyncResult
        from api.jobs.celery_app import celery_app

        # Get task states
        # Note: This is a simplified version - you'd want to track task runs in database
        health = {
            "celery_available": celery_app.control.inspect().active() is not None,
            "scheduled_tasks": {
                "archival": {
                    "name": "archive-old-runs",
                    "schedule": "Daily at 2:00 AM UTC",
                    "enabled": True,
                },
                "cleanup": {
                    "name": "cleanup-old-runs",
                    "schedule": "Daily at 3:00 AM UTC",
                    "enabled": True,
                },
                "storage_stats": {
                    "name": "storage-stats",
                    "schedule": "Every 6 hours",
                    "enabled": True,
                },
            },
        }

        return SuccessResponse(data=health)

    except Exception as e:
        logger.error(f"Failed to get maintenance health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get maintenance health: {str(e)}",
        )
