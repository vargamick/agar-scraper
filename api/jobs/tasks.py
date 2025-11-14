"""
Celery tasks for background job processing.

Defines tasks for executing scraper jobs, sending webhooks, etc.
"""

import logging
import asyncio
from uuid import UUID
from typing import Dict, Any

from celery import Task

from api.jobs.celery_app import celery_app
from api.scraper.adapter import ScraperAdapter
from api.database.connection import get_db_session
from api.database.repositories import JobRepository
from api.database.models import JobStatus

logger = logging.getLogger(__name__)


class JobTask(Task):
    """
    Base class for job tasks with error handling.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Handle task failure.

        Args:
            exc: Exception that was raised
            task_id: Task ID
            args: Task arguments
            kwargs: Task keyword arguments
            einfo: Exception info
        """
        logger.error(f"Task {task_id} failed: {exc}", exc_info=einfo)

        # Update job status to failed
        if args and len(args) > 0:
            job_id = args[0]
            try:
                db = get_db_session()
                repo = JobRepository(db)
                repo.update_status(UUID(job_id), JobStatus.FAILED)
                db.commit()
                db.close()
            except Exception as e:
                logger.error(f"Failed to update job status: {e}")

    def on_success(self, retval, task_id, args, kwargs):
        """
        Handle task success.

        Args:
            retval: Return value
            task_id: Task ID
            args: Task arguments
            kwargs: Task keyword arguments
        """
        logger.info(f"Task {task_id} completed successfully")


@celery_app.task(base=JobTask, bind=True, name="api.jobs.tasks.execute_scraper_job")
def execute_scraper_job(
    self,
    job_id: str,
    job_config: Dict[str, Any],
    output_config: Dict[str, Any],
    folder_name: str = None,
) -> Dict[str, Any]:
    """
    Execute a scraper job in the background.

    Args:
        job_id: Job UUID as string
        job_config: Job configuration dictionary
        output_config: Output configuration dictionary
        folder_name: Optional folder name for output (defaults to timestamp)

    Returns:
        Result dictionary with job info
    """
    logger.info(f"Starting scraper job {job_id}")

    try:
        # Convert job_id to UUID
        job_uuid = UUID(job_id)

        # Create scraper adapter
        adapter = ScraperAdapter(
            job_id=job_uuid,
            job_config=job_config,
            output_config=output_config,
            folder_name=folder_name,
        )

        # Execute scraper
        # Run async code in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(adapter.execute())
        finally:
            loop.close()

        logger.info(f"Scraper job {job_id} completed")

        return {
            "job_id": job_id,
            "status": "completed",
            "message": "Job completed successfully",
        }

    except Exception as e:
        logger.error(f"Scraper job {job_id} failed: {e}", exc_info=True)
        raise


@celery_app.task(name="api.jobs.tasks.send_webhook")
def send_webhook(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Send webhook notification.

    Args:
        url: Webhook URL
        payload: Webhook payload
        headers: Custom headers
        max_retries: Maximum retry attempts

    Returns:
        Result dictionary
    """
    import httpx

    logger.info(f"Sending webhook to {url}")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                json=payload,
                headers=headers or {},
            )
            response.raise_for_status()

        logger.info(f"Webhook sent successfully to {url}")

        return {
            "url": url,
            "status_code": response.status_code,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Webhook failed: {e}")

        # Retry if we haven't exceeded max retries
        if self.request.retries < max_retries:
            raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds

        return {
            "url": url,
            "success": False,
            "error": str(e),
        }


@celery_app.task(name="api.jobs.tasks.scheduled_job_runner")
def scheduled_job_runner(scheduled_job_id: str) -> Dict[str, Any]:
    """
    Run a scheduled job.

    Args:
        scheduled_job_id: Scheduled job UUID

    Returns:
        Result dictionary
    """
    logger.info(f"Running scheduled job {scheduled_job_id}")

    try:
        # Get scheduled job from database
        db = get_db_session()
        # In full implementation, fetch scheduled job and create new job
        # For now, just log
        db.close()

        return {
            "scheduled_job_id": scheduled_job_id,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Scheduled job {scheduled_job_id} failed: {e}")
        raise
