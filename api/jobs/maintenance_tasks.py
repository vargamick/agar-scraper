"""
Maintenance tasks for run management.

Handles archival, deletion, and cleanup of old scraper runs.
"""

import logging
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from uuid import UUID

from api.jobs.celery_app import celery_app
from api.database.connection import get_db_session
from api.database.repositories import JobRepository
from api.database.models import JobStatus
from api.config import settings

logger = logging.getLogger(__name__)


def _get_archive_path(folder_name: str, job_id: UUID) -> Path:
    """
    Get archive path for a job.

    Args:
        folder_name: Folder name (YYYYMMDD_HHMMSS)
        job_id: Job UUID

    Returns:
        Path object for archive location
    """
    # Extract year and month from folder_name
    year = folder_name[:4]
    month = folder_name[4:6]

    archive_base = Path(settings.STORAGE_BASE_PATH) / "archive"
    archive_dir = archive_base / year / month
    archive_dir.mkdir(parents=True, exist_ok=True)

    return archive_dir / f"{folder_name}_{job_id}.tar.gz"


def _compress_folder(source_dir: Path, archive_path: Path) -> bool:
    """
    Compress a folder to tar.gz format.

    Args:
        source_dir: Source directory to compress
        archive_path: Destination archive file

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Compressing {source_dir} to {archive_path}")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source_dir, arcname=source_dir.name)

        # Verify archive was created
        if not archive_path.exists():
            logger.error(f"Archive file not created: {archive_path}")
            return False

        # Verify archive is valid
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.getmembers()

        logger.info(f"Successfully compressed {source_dir}")
        return True

    except Exception as e:
        logger.error(f"Failed to compress {source_dir}: {e}", exc_info=True)
        return False


def _decompress_folder(archive_path: Path, dest_dir: Path) -> bool:
    """
    Decompress a tar.gz archive.

    Args:
        archive_path: Archive file to decompress
        dest_dir: Destination directory

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Decompressing {archive_path} to {dest_dir}")

        dest_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=dest_dir.parent)

        logger.info(f"Successfully decompressed {archive_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to decompress {archive_path}: {e}", exc_info=True)
        return False


@celery_app.task(name="api.jobs.maintenance_tasks.archive_old_runs")
def archive_old_runs(days: int = 7, dry_run: bool = False) -> Dict[str, Any]:
    """
    Archive runs older than specified days.

    Archives completed jobs by:
    1. Compressing the output folder
    2. Moving to archive location
    3. Updating database with archive info
    4. Removing original folder

    Args:
        days: Archive runs older than this many days (default: 7)
        dry_run: If True, only report what would be archived without doing it

    Returns:
        Dictionary with archival statistics
    """
    logger.info(f"Starting archival task for runs older than {days} days (dry_run={dry_run})")

    stats = {
        "processed": 0,
        "archived": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
    }

    try:
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get jobs to archive
        db = get_db_session()
        repo = JobRepository(db)

        # Find completed jobs without archive timestamp
        jobs = repo.get_all(
            status=JobStatus.COMPLETED,
            limit=1000,  # Process in batches
        )

        # Filter by completion date and not already archived
        jobs_to_archive = [
            job for job in jobs
            if job.completed_at and job.completed_at < cutoff_date
            and not hasattr(job, 'archived_at') or not job.archived_at
            and job.folder_name  # Only process jobs with folder_name
        ]

        logger.info(f"Found {len(jobs_to_archive)} jobs to archive")

        for job in jobs_to_archive:
            stats["processed"] += 1

            try:
                # Get source directory
                source_dir = Path(settings.STORAGE_JOBS_PATH) / f"{job.folder_name}_{job.id}"

                if not source_dir.exists():
                    logger.warning(f"Source directory not found: {source_dir}")
                    stats["skipped"] += 1
                    continue

                # Get archive path
                archive_path = _get_archive_path(job.folder_name, job.id)

                if dry_run:
                    logger.info(f"[DRY RUN] Would archive: {source_dir} -> {archive_path}")
                    stats["archived"] += 1
                    continue

                # Compress folder
                if not _compress_folder(source_dir, archive_path):
                    stats["failed"] += 1
                    stats["errors"].append(f"Failed to compress {job.id}")
                    continue

                # Update database
                # Note: You'll need to add archived_at and archive_path fields to Job model
                # For now, we'll update via raw SQL
                db.execute(
                    "UPDATE jobs SET archived_at = :archived_at, archive_path = :archive_path WHERE id = :job_id",
                    {
                        "archived_at": datetime.now(),
                        "archive_path": str(archive_path),
                        "job_id": job.id,
                    }
                )
                db.commit()

                # Remove original folder
                shutil.rmtree(source_dir)

                stats["archived"] += 1
                logger.info(f"Successfully archived job {job.id}")

            except Exception as e:
                logger.error(f"Failed to archive job {job.id}: {e}", exc_info=True)
                stats["failed"] += 1
                stats["errors"].append(f"Job {job.id}: {str(e)}")
                db.rollback()

        db.close()

        logger.info(f"Archival task complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Archival task failed: {e}", exc_info=True)
        stats["errors"].append(f"Task failure: {str(e)}")
        return stats


@celery_app.task(name="api.jobs.maintenance_tasks.cleanup_old_runs")
def cleanup_old_runs(days: int = 30, dry_run: bool = False, strategy: str = "soft") -> Dict[str, Any]:
    """
    Delete archived runs older than specified days.

    Args:
        days: Delete runs older than this many days (default: 30)
        dry_run: If True, only report what would be deleted without doing it
        strategy: Deletion strategy - "soft" (keep DB record) or "hard" (remove DB record)

    Returns:
        Dictionary with deletion statistics
    """
    logger.info(f"Starting cleanup task for runs older than {days} days (dry_run={dry_run}, strategy={strategy})")

    stats = {
        "processed": 0,
        "deleted": 0,
        "failed": 0,
        "errors": [],
    }

    try:
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get jobs to delete
        db = get_db_session()
        repo = JobRepository(db)

        # Find archived jobs older than cutoff
        # Note: This query assumes archived_at field exists
        jobs_to_delete = []
        all_jobs = repo.get_all(limit=10000)

        for job in all_jobs:
            if (hasattr(job, 'archived_at') and job.archived_at and
                job.archived_at < cutoff_date and
                (not hasattr(job, 'deleted_at') or not job.deleted_at)):
                jobs_to_delete.append(job)

        logger.info(f"Found {len(jobs_to_delete)} jobs to delete")

        for job in jobs_to_delete:
            stats["processed"] += 1

            try:
                # Get archive path
                archive_path = None
                if hasattr(job, 'archive_path') and job.archive_path:
                    archive_path = Path(job.archive_path)

                if dry_run:
                    logger.info(f"[DRY RUN] Would delete: {job.id} (archive: {archive_path})")
                    stats["deleted"] += 1
                    continue

                # Delete archive file if it exists
                if archive_path and archive_path.exists():
                    archive_path.unlink()
                    logger.info(f"Deleted archive file: {archive_path}")

                if strategy == "soft":
                    # Soft delete: mark as deleted but keep record
                    db.execute(
                        "UPDATE jobs SET deleted_at = :deleted_at WHERE id = :job_id",
                        {
                            "deleted_at": datetime.now(),
                            "job_id": job.id,
                        }
                    )
                    db.commit()
                    logger.info(f"Soft deleted job {job.id}")

                elif strategy == "hard":
                    # Hard delete: create audit record then delete
                    audit_data = {
                        "job_id": str(job.id),
                        "job_name": job.name,
                        "folder_name": job.folder_name,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                        "archived_at": job.archived_at.isoformat() if hasattr(job, 'archived_at') and job.archived_at else None,
                        "deleted_at": datetime.now().isoformat(),
                        "stats": job.stats,
                        "created_by": str(job.created_by),
                    }

                    # Note: You'll need to create job_audit table
                    # For now, just log it
                    logger.info(f"Audit record: {audit_data}")

                    # Delete job record
                    repo.delete(job.id)
                    db.commit()
                    logger.info(f"Hard deleted job {job.id}")

                stats["deleted"] += 1

            except Exception as e:
                logger.error(f"Failed to delete job {job.id}: {e}", exc_info=True)
                stats["failed"] += 1
                stats["errors"].append(f"Job {job.id}: {str(e)}")
                db.rollback()

        db.close()

        logger.info(f"Cleanup task complete: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        stats["errors"].append(f"Task failure: {str(e)}")
        return stats


@celery_app.task(name="api.jobs.maintenance_tasks.restore_archived_run")
def restore_archived_run(job_id: str) -> Dict[str, Any]:
    """
    Restore an archived run back to active storage.

    Args:
        job_id: Job UUID as string

    Returns:
        Dictionary with restoration status
    """
    logger.info(f"Restoring archived run {job_id}")

    try:
        job_uuid = UUID(job_id)

        # Get job from database
        db = get_db_session()
        repo = JobRepository(db)
        job = repo.get_by_id(job_uuid)

        if not job:
            return {
                "success": False,
                "error": "Job not found",
            }

        if not hasattr(job, 'archive_path') or not job.archive_path:
            return {
                "success": False,
                "error": "Job is not archived",
            }

        archive_path = Path(job.archive_path)

        if not archive_path.exists():
            return {
                "success": False,
                "error": f"Archive file not found: {archive_path}",
            }

        # Decompress to original location
        dest_dir = Path(settings.STORAGE_JOBS_PATH) / f"{job.folder_name}_{job.id}"

        if dest_dir.exists():
            return {
                "success": False,
                "error": "Destination directory already exists",
            }

        if not _decompress_folder(archive_path, dest_dir):
            return {
                "success": False,
                "error": "Failed to decompress archive",
            }

        # Update database - clear archive info
        db.execute(
            "UPDATE jobs SET archived_at = NULL, archive_path = NULL WHERE id = :job_id",
            {"job_id": job_uuid}
        )
        db.commit()
        db.close()

        logger.info(f"Successfully restored job {job_id}")

        return {
            "success": True,
            "job_id": job_id,
            "restored_path": str(dest_dir),
        }

    except Exception as e:
        logger.error(f"Failed to restore job {job_id}: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@celery_app.task(name="api.jobs.maintenance_tasks.get_storage_stats")
def get_storage_stats() -> Dict[str, Any]:
    """
    Get storage statistics for runs.

    Returns:
        Dictionary with storage statistics
    """
    logger.info("Calculating storage statistics")

    try:
        storage_path = Path(settings.STORAGE_JOBS_PATH)
        archive_path = Path(settings.STORAGE_BASE_PATH) / "archive"

        # Calculate active storage
        active_size = 0
        active_count = 0
        if storage_path.exists():
            for item in storage_path.iterdir():
                if item.is_dir():
                    active_count += 1
                    active_size += sum(f.stat().st_size for f in item.rglob('*') if f.is_file())

        # Calculate archive storage
        archive_size = 0
        archive_count = 0
        if archive_path.exists():
            for item in archive_path.rglob('*.tar.gz'):
                archive_count += 1
                archive_size += item.stat().st_size

        # Get database counts
        db = get_db_session()
        repo = JobRepository(db)
        total_jobs = repo.count()
        db.close()

        stats = {
            "active": {
                "count": active_count,
                "size_bytes": active_size,
                "size_mb": round(active_size / (1024 * 1024), 2),
                "size_gb": round(active_size / (1024 * 1024 * 1024), 2),
            },
            "archived": {
                "count": archive_count,
                "size_bytes": archive_size,
                "size_mb": round(archive_size / (1024 * 1024), 2),
                "size_gb": round(archive_size / (1024 * 1024 * 1024), 2),
            },
            "total": {
                "count": active_count + archive_count,
                "size_bytes": active_size + archive_size,
                "size_mb": round((active_size + archive_size) / (1024 * 1024), 2),
                "size_gb": round((active_size + archive_size) / (1024 * 1024 * 1024), 2),
            },
            "database": {
                "total_jobs": total_jobs,
            },
        }

        logger.info(f"Storage stats: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get storage stats: {e}", exc_info=True)
        return {
            "error": str(e),
        }
