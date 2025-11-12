"""
Celery application configuration.

Configures Celery for background job processing.
"""

import logging
from celery import Celery
from celery.signals import worker_ready, worker_shutdown, worker_process_init

from api.config import settings

logger = logging.getLogger(__name__)

# Create Celery application
celery_app = Celery(
    "scraper_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,

    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,

    # Task routing
    task_routes={
        "api.jobs.tasks.execute_scraper_job": {"queue": "scraper"},
        "api.jobs.tasks.send_webhook": {"queue": "webhooks"},
    },

    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["api.jobs"])


@worker_process_init.connect
def init_worker_process(**kwargs):
    """Called when a worker process initializes."""
    from api.database.connection import init_database
    try:
        init_database(settings.DATABASE_URL)
        logger.info("Database initialized for worker process")
    except Exception as e:
        logger.error(f"Failed to initialize database in worker process: {e}")


@worker_ready.connect
def on_worker_ready(**kwargs):
    """Called when worker is ready."""
    logger.info("Celery worker is ready and waiting for tasks")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    """Called when worker is shutting down."""
    logger.info("Celery worker is shutting down")


# Task decorators and utilities
def get_task_info(task_id: str) -> dict:
    """
    Get information about a task.

    Args:
        task_id: Celery task ID

    Returns:
        Task information dictionary
    """
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "state": result.state,
        "info": result.info,
        "result": result.result if result.ready() else None,
    }


def revoke_task(task_id: str, terminate: bool = False):
    """
    Revoke (cancel) a task.

    Args:
        task_id: Celery task ID
        terminate: Whether to terminate the task if it's running
    """
    celery_app.control.revoke(task_id, terminate=terminate)
    logger.info(f"Task {task_id} revoked (terminate={terminate})")
