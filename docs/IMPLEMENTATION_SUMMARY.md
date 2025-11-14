# Output Folder Management - Implementation Summary

## Overview

This document summarizes the changes made to implement meaningful output folder names and automated run management for the Agar Scraper system.

## Changes Implemented

### 1. Database Schema Updates

#### New Field: `folder_name`

Added to the `jobs` table to store human-readable folder names:

**File**: [api/database/models.py:101](api/database/models.py#L101)

```python
# Output folder name with timestamp (format: YYYYMMDD_HHMMSS)
folder_name = Column(String(255), nullable=True, index=True)
```

#### Database Migration

**File**: [api/database/migrations/versions/001_add_folder_name_to_jobs.py](api/database/migrations/versions/001_add_folder_name_to_jobs.py)

- Adds `folder_name` column to `jobs` table
- Creates index for efficient lookups
- Includes upgrade and downgrade functions

**To apply migration:**
```bash
cd /Users/mick/AI/c4ai/agar
alembic upgrade head
```

### 2. Folder Naming Implementation

#### Format: `YYYYMMDD_HHMMSS_{job_id}`

**Example**: `20250113_143052_8dafff36-6b15-478a-88fc-19cdbbcfca5f5`

#### Updated Files

1. **ConfigBuilder** - [api/scraper/config_builder.py:41-48](api/scraper/config_builder.py#L41-L48)
   - Added `_generate_folder_name()` method
   - Updated `get_output_path()` to use meaningful names
   - Added `folder_name` parameter to constructor

2. **ScraperAdapter** - [api/scraper/adapter.py:35-55](api/scraper/adapter.py#L35-L55)
   - Added `folder_name` parameter
   - Passes folder_name to ConfigBuilder

3. **Job Creation Route** - [api/routes/scraper.py:73-82](api/routes/scraper.py#L73-L82)
   - Generates folder_name on job creation
   - Stores in database
   - Passes to Celery task

4. **Celery Task** - [api/jobs/tasks.py:66-98](api/jobs/tasks.py#L66-L98)
   - Added `folder_name` parameter
   - Passes to ScraperAdapter

### 3. Run Management Strategy

**Documentation**: [docs/RUN_MANAGEMENT_STRATEGY.md](docs/RUN_MANAGEMENT_STRATEGY.md)

Comprehensive strategy document covering:

#### Lifecycle Stages

1. **Active Runs (0-7 days)**
   - Location: `./scraper_data/jobs/{YYYYMMDD_HHMMSS}_{job_id}/`
   - Status: Fully accessible
   - Actions: Read/write access

2. **Archived Runs (7-30 days)**
   - Location: `./scraper_data/archive/{YYYY}/{MM}/{YYYYMMDD_HHMMSS}_{job_id}.tar.gz`
   - Status: Compressed archive
   - Actions: Read-only, can be restored

3. **Deleted Runs (30+ days)**
   - Location: N/A (removed from filesystem)
   - Status: Soft-deleted (metadata retained) or hard-deleted
   - Actions: Audit trail only

#### Key Features

- **Compression**: tar.gz format for 40-60% storage savings
- **Organization**: Archived by year/month for easy management
- **Configurability**: Adjustable retention periods
- **Safety**: Dry-run mode for testing

### 4. Maintenance Tasks Implementation

**File**: [api/jobs/maintenance_tasks.py](api/jobs/maintenance_tasks.py)

#### Implemented Tasks

1. **`archive_old_runs(days=7, dry_run=False)`**
   - Compresses completed runs older than specified days
   - Moves to archive location
   - Updates database with archive metadata
   - Removes original folder

2. **`cleanup_old_runs(days=30, dry_run=False, strategy='soft')`**
   - Deletes archived runs older than specified days
   - Supports soft delete (keep DB record) or hard delete (remove all)
   - Creates audit trail for compliance

3. **`restore_archived_run(job_id)`**
   - Decompresses archived run back to active storage
   - Updates database to remove archive metadata
   - Available via API for on-demand restoration

4. **`get_storage_stats()`**
   - Calculates active and archived storage usage
   - Returns counts and sizes
   - Useful for monitoring and capacity planning

#### Helper Functions

- `_get_archive_path()`: Generates archive file path
- `_compress_folder()`: Compresses folder to tar.gz
- `_decompress_folder()`: Extracts tar.gz archive

### 5. Automated Scheduling

**File**: [api/jobs/beat_schedule.py](api/jobs/beat_schedule.py)

#### Scheduled Tasks

1. **Daily Archival** - 2:00 AM UTC
   ```python
   'archive-old-runs': {
       'task': 'api.jobs.maintenance_tasks.archive_old_runs',
       'schedule': crontab(hour=2, minute=0),
       'kwargs': {'days': 7, 'dry_run': False},
   }
   ```

2. **Daily Cleanup** - 3:00 AM UTC
   ```python
   'cleanup-old-runs': {
       'task': 'api.jobs.maintenance_tasks.cleanup_old_runs',
       'schedule': crontab(hour=3, minute=0),
       'kwargs': {'days': 30, 'dry_run': False, 'strategy': 'soft'},
   }
   ```

3. **Storage Stats** - Every 6 hours
   ```python
   'storage-stats': {
       'task': 'api.jobs.maintenance_tasks.get_storage_stats',
       'schedule': crontab(minute=0, hour='*/6'),
   }
   ```

### 6. API Endpoints

**File**: [api/routes/maintenance.py](api/routes/maintenance.py)

#### New Endpoints

1. **`POST /api/maintenance/archive`**
   - Manually trigger archival
   - Query params: `days`, `dry_run`
   - Admin only

2. **`POST /api/maintenance/cleanup`**
   - Manually trigger cleanup
   - Query params: `days`, `dry_run`, `strategy`
   - Admin only

3. **`POST /api/maintenance/restore/{job_id}`**
   - Restore archived run
   - Job owner or admin

4. **`GET /api/maintenance/storage-stats`**
   - Get storage statistics
   - All authenticated users

5. **`GET /api/maintenance/health`**
   - Get maintenance system health
   - All authenticated users

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Run Management Settings
ARCHIVE_AFTER_DAYS=7
DELETE_AFTER_DAYS=30
ARCHIVE_COMPRESSION=gzip
DELETION_STRATEGY=soft

# Storage Paths
STORAGE_BASE_PATH=./scraper_data
STORAGE_JOBS_PATH=./scraper_data/jobs
ARCHIVE_BASE_PATH=./scraper_data/archive
```

### Celery Configuration

Update your Celery worker configuration to include beat schedule:

**File**: `api/jobs/celery_app.py` (add import)

```python
from api.jobs.beat_schedule import beat_config

# Add to celery_app configuration
celery_app.conf.update(beat_config)
```

## Deployment Steps

### Step 1: Database Migration

```bash
cd /Users/mick/AI/c4ai/agar

# Run migration
alembic upgrade head

# Verify
docker-compose exec postgres psql -U scraper_user -d scraper_db -c "\d jobs"
```

### Step 2: Update API Code

All code changes are already in place. Restart the API service:

```bash
docker-compose restart api
```

### Step 3: Start Celery Beat

If not already running, start Celery Beat scheduler:

```bash
# In docker-compose.yml, add beat service
celery-beat:
  build: .
  command: celery -A api.jobs.celery_app beat --loglevel=info
  environment:
    - DATABASE_URL=postgresql://scraper_user:scraper_pass@postgres:5432/scraper_db
    - REDIS_URL=redis://redis:6379/0
  depends_on:
    - redis
    - postgres
```

Then:
```bash
docker-compose up -d celery-beat
```

### Step 4: Test the Implementation

#### Manual Testing

1. **Create a test job:**
   ```bash
   curl -X POST http://localhost:8000/api/scraper/jobs \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Job", "type": "web", "config": {...}, "output": {...}}'
   ```

2. **Verify folder name:**
   ```bash
   ls -la ./scraper_data/jobs/
   # Should see: 20250113_HHMMSS_{uuid}/
   ```

3. **Test dry-run archival:**
   ```bash
   curl -X POST "http://localhost:8000/api/maintenance/archive?days=0&dry_run=true" \
     -H "Authorization: Bearer ADMIN_TOKEN"
   ```

4. **Check storage stats:**
   ```bash
   curl -X GET http://localhost:8000/api/maintenance/storage-stats \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

#### Automated Testing

Run the test suite (when available):
```bash
pytest tests/test_maintenance.py -v
```

### Step 5: Monitor

1. **Check Celery logs:**
   ```bash
   docker-compose logs -f celery
   docker-compose logs -f celery-beat
   ```

2. **Verify scheduled tasks:**
   ```bash
   celery -A api.jobs.celery_app inspect scheduled
   ```

3. **Monitor storage:**
   ```bash
   watch -n 60 'curl -s http://localhost:8000/api/maintenance/storage-stats \
     -H "Authorization: Bearer YOUR_TOKEN" | jq'
   ```

## Benefits

### 1. Meaningful Folder Names
- ✅ Easy to identify run dates without checking database
- ✅ Chronological sorting in file managers
- ✅ Unique identifiers prevent conflicts

### 2. Automated Management
- ✅ Automatic archival after 7 days (configurable)
- ✅ Automatic deletion after 30 days (configurable)
- ✅ No manual intervention required

### 3. Storage Efficiency
- ✅ 40-60% storage savings through compression
- ✅ Organized archive structure by year/month
- ✅ Configurable retention policies

### 4. Audit & Compliance
- ✅ Complete audit trail of all operations
- ✅ Soft delete option preserves metadata
- ✅ Restoration capability for archived runs

### 5. Operational Safety
- ✅ Dry-run mode for testing
- ✅ Manual override options
- ✅ Health monitoring endpoints

## Folder Structure Examples

### Before (UUID only)
```
scraper_data/
└── jobs/
    ├── 8dafff36-6b15-478a-88fc-19cdbbcfca5f5/
    ├── a1b2c3d4-e5f6-7890-abcd-ef1234567890/
    └── f9e8d7c6-b5a4-3210-9876-fedcba098765/
```

### After (Meaningful names)
```
scraper_data/
├── jobs/                                           # Active (0-7 days)
│   ├── 20250113_143052_8dafff36.../
│   └── 20250114_091230_a1b2c3d4.../
│
└── archive/                                        # Archived (7-30 days)
    └── 2025/
        └── 01/
            ├── 20250106_143052_8dafff36...tar.gz
            └── 20250107_091230_a1b2c3d4...tar.gz
```

## Troubleshooting

### Issue: Migration fails

**Solution:**
```bash
# Check current migration status
alembic current

# If stuck, mark as applied manually
alembic stamp 001

# Then try again
alembic upgrade head
```

### Issue: Archival task not running

**Solution:**
```bash
# Check Celery beat is running
docker-compose ps celery-beat

# Check beat schedule
celery -A api.jobs.celery_app inspect scheduled

# Manually trigger for testing
curl -X POST "http://localhost:8000/api/maintenance/archive?days=0&dry_run=true" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Issue: Cannot restore archived job

**Solution:**
```bash
# Verify archive file exists
ls -la scraper_data/archive/2025/01/*.tar.gz

# Check file integrity
tar -tzf scraper_data/archive/2025/01/20250106_143052_*.tar.gz | head

# Try restore via API
curl -X POST "http://localhost:8000/api/maintenance/restore/{job_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Next Steps

1. **Apply database migration** (required)
2. **Configure environment variables** (optional, has defaults)
3. **Set up Celery Beat** (required for automation)
4. **Test with dry-run mode** (recommended)
5. **Enable automatic archival** (when ready)
6. **Set up monitoring** (recommended)

## Questions?

For issues or questions:
- Check [docs/RUN_MANAGEMENT_STRATEGY.md](docs/RUN_MANAGEMENT_STRATEGY.md) for detailed strategy
- Review implementation files listed above
- Check Celery logs for task execution details

## Summary

All requested features have been implemented:

✅ **1. Store folder name in database** - Added `folder_name` field to `jobs` table

✅ **2. Define archival/deletion implementation** - Comprehensive strategy documented in [docs/RUN_MANAGEMENT_STRATEGY.md](docs/RUN_MANAGEMENT_STRATEGY.md)

✅ **3. Use YYYYMMDD_HHMMSS format** - Implemented throughout the system

The system now provides:
- Meaningful, sortable folder names
- Automated archival after 7 days
- Automated deletion after 30 days
- Manual override capabilities
- Storage statistics and monitoring
- Complete audit trail
- Restoration functionality
