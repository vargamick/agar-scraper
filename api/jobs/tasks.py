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


@celery_app.task(name="api.jobs.tasks.upload_job_to_s3")
def upload_job_to_s3(
    job_id: str,
    folder_name: str,
    output_path: str,
    s3_config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Upload job output files to AWS S3.

    This task is triggered after a job completes to upload all output
    files to S3 for long-term storage and downstream processing.

    Args:
        job_id: Job UUID as string
        folder_name: Timestamp folder name (YYYYMMDD_HHMMSS)
        output_path: Local output directory path
        s3_config: Optional S3 configuration override

    Returns:
        Result dictionary with upload status and S3 URLs
    """
    from api.services.s3_uploader import S3Uploader, S3UploadError
    from api.config import settings
    from datetime import datetime

    logger.info(f"Starting S3 upload for job {job_id}")

    # Check if S3 is enabled
    if not settings.S3_ENABLED:
        logger.warning(f"S3 upload skipped for job {job_id}: S3 is disabled")
        return {
            "job_id": job_id,
            "status": "skipped",
            "message": "S3 upload is disabled",
        }

    try:
        # Initialize S3 uploader
        uploader = S3Uploader(
            job_id=UUID(job_id),
            folder_name=folder_name,
            output_path=output_path,
            s3_config=s3_config or {}
        )

        # Upload job outputs
        upload_results = uploader.upload_job_outputs()

        # Get upload statistics
        upload_stats = uploader.get_upload_stats()

        # Update job output in database with S3 information
        try:
            db = get_db_session()
            repo = JobRepository(db)

            # Get current job
            job = repo.get_by_id(UUID(job_id))
            if job:
                # Update output JSONB with S3 info
                if job.output is None:
                    job.output = {}

                job.output['uploadToS3'] = {
                    'enabled': True,
                    'status': upload_results['status'],
                    'uploadedAt': datetime.utcnow().isoformat(),
                    's3Urls': upload_results['s3_urls'],
                    'bytesUploaded': upload_stats['total_bytes'],
                    'filesUploaded': upload_stats['total_files'],
                    'errors': upload_results.get('errors', [])
                }

                # Update job stats with upload info
                if job.stats is None:
                    job.stats = {}

                job.stats['s3Upload'] = {
                    'bytesUploaded': upload_stats['total_bytes'],
                    'filesUploaded': upload_stats['total_files']
                }

                db.commit()
                logger.info(f"Updated job {job_id} with S3 upload information")

            db.close()

        except Exception as e:
            logger.error(f"Failed to update job with S3 info: {e}")
            # Don't fail the task if database update fails

        logger.info(f"S3 upload completed for job {job_id}: {upload_results['status']}")

        return {
            "job_id": job_id,
            "status": upload_results['status'],
            "s3_urls": upload_results['s3_urls'],
            "stats": upload_stats,
            "errors": upload_results.get('errors', [])
        }

    except S3UploadError as e:
        logger.error(f"S3 upload failed for job {job_id}: {e}")

        # Update job with error status
        try:
            db = get_db_session()
            repo = JobRepository(db)
            job = repo.get_by_id(UUID(job_id))
            if job:
                if job.output is None:
                    job.output = {}
                job.output['uploadToS3'] = {
                    'enabled': True,
                    'status': 'failed',
                    'error': str(e),
                    'uploadedAt': datetime.utcnow().isoformat()
                }
                db.commit()
            db.close()
        except Exception as update_error:
            logger.error(f"Failed to update job with S3 error: {update_error}")

        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }

    except Exception as e:
        logger.error(f"Unexpected error in S3 upload for job {job_id}: {e}", exc_info=True)

        return {
            "job_id": job_id,
            "status": "error",
            "error": str(e)
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


@celery_app.task(name="api.jobs.tasks.process_application_matrix")
def process_application_matrix(
    job_id: str = None,
    matrix_file_path: str = None,
    scraped_products_path: str = None,
    memento_config: Dict[str, Any] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Process Product Application Matrix and send to Memento knowledge graph.

    This task parses the application matrix file, extracts entities and
    relationships, and uploads them to the Memento API.

    Can be triggered:
    - After a scraping job completes (with job_id)
    - Independently for matrix-only processing

    Args:
        job_id: Optional job UUID (for linking to scraping job)
        matrix_file_path: Path to the matrix CSV/Excel file
        scraped_products_path: Path to scraped all_products.json
        memento_config: Memento configuration override
        dry_run: If True, don't actually send to Memento

    Returns:
        Result dictionary with processing statistics
    """
    from pathlib import Path
    from datetime import datetime
    from api.config import settings
    from config.matrix_config import S3_CONFIG

    logger.info(f"Starting matrix processing{f' for job {job_id}' if job_id else ''}")

    # Determine matrix file path
    if not matrix_file_path:
        # Use default from S3 config
        matrix_file_path = f"/app/scraper_data/reference/{S3_CONFIG['default_matrix_file']}"
        logger.info(f"Using default matrix file: {matrix_file_path}")

    # Check if Memento is enabled
    if not settings.MEMENTO_ENABLED and not dry_run:
        logger.warning("Memento integration is disabled")
        return {
            "job_id": job_id,
            "status": "skipped",
            "message": "Memento integration is disabled (set MEMENTO_ENABLED=true)",
        }

    try:
        # Import here to avoid circular imports
        from core.matrix.processor import MatrixProcessor, ProcessorConfig

        # Build configuration
        config = ProcessorConfig(
            matrix_file_path=Path(matrix_file_path),
            scraped_products_path=Path(scraped_products_path) if scraped_products_path else None,
            memento_instance_id=(memento_config or {}).get('instanceId') or settings.MEMENTO_DEFAULT_INSTANCE,
            memento_api_url=settings.MEMENTO_API_URL,
            memento_api_key=settings.MEMENTO_API_KEY,
            match_threshold=0.85,
            dry_run=dry_run,
        )

        # Create processor
        processor = MatrixProcessor(config)

        # Run processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(processor.process())
        finally:
            loop.close()

        # Update job in database if job_id provided
        if job_id and not dry_run:
            try:
                db = get_db_session()
                repo = JobRepository(db)
                job = repo.get_by_id(UUID(job_id))

                if job:
                    if job.output is None:
                        job.output = {}

                    job.output['mementoProcessing'] = {
                        'enabled': True,
                        'status': 'success' if result.success else 'failed',
                        'processedAt': datetime.utcnow().isoformat(),
                        'entitiesCreated': result.entities_created,
                        'relationshipsCreated': result.relationships_created,
                        'productsMatched': result.products_matched,
                        'productsUnmatched': result.products_unmatched,
                        'processingTimeSeconds': result.processing_time_seconds,
                        'errors': result.errors,
                    }
                    db.commit()
                    logger.info(f"Updated job {job_id} with Memento processing results")

                db.close()

            except Exception as e:
                logger.error(f"Failed to update job with Memento results: {e}")

        logger.info(
            f"Matrix processing completed: "
            f"{result.entities_created} entities, {result.relationships_created} relationships"
        )

        return {
            "job_id": job_id,
            "status": "success" if result.success else "failed",
            "entities_created": result.entities_created,
            "relationships_created": result.relationships_created,
            "products_matched": result.products_matched,
            "products_unmatched": result.products_unmatched,
            "processing_time_seconds": result.processing_time_seconds,
            "errors": result.errors,
        }

    except FileNotFoundError as e:
        logger.error(f"Matrix file not found: {e}")
        return {
            "job_id": job_id,
            "status": "failed",
            "error": f"Matrix file not found: {e}",
        }

    except Exception as e:
        logger.error(f"Matrix processing failed: {e}", exc_info=True)
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e),
        }
