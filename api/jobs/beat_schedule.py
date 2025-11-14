"""
Celery Beat schedule configuration for periodic tasks.

Defines scheduled tasks for run management, archival, and cleanup.
"""

from celery.schedules import crontab

# Celery Beat schedule
beat_schedule = {
    # Archive old runs daily at 2:00 AM
    'archive-old-runs': {
        'task': 'api.jobs.maintenance_tasks.archive_old_runs',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM every day
        'kwargs': {
            'days': 7,  # Archive runs older than 7 days
            'dry_run': False,
        },
    },

    # Cleanup old archived runs daily at 3:00 AM
    'cleanup-old-runs': {
        'task': 'api.jobs.maintenance_tasks.cleanup_old_runs',
        'schedule': crontab(hour=3, minute=0),  # 3:00 AM every day
        'kwargs': {
            'days': 30,  # Delete runs older than 30 days
            'dry_run': False,
            'strategy': 'soft',  # Soft delete by default
        },
    },

    # Calculate storage statistics every 6 hours
    'storage-stats': {
        'task': 'api.jobs.maintenance_tasks.get_storage_stats',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
    },
}

# Configuration
beat_config = {
    'beat_schedule': beat_schedule,
    'timezone': 'UTC',
}
