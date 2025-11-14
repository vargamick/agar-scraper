# Deployment Status - Output Folder Management

**Date**: 2025-01-13
**Status**: ✅ Successfully Deployed

## Container Rebuild

All Docker containers have been successfully rebuilt and deployed with the new output folder management implementation.

### Containers Status

| Container | Status | Health | Port |
|-----------|--------|--------|------|
| scraper-api | ✅ Running | Healthy | 3010 |
| scraper-celery-worker | ✅ Running | Healthy | - |
| scraper-postgres | ✅ Running | Healthy | 5432 |
| scraper-redis | ✅ Running | Healthy | 6379 |
| crawl4ai-service | ✅ Running | Healthy | 11235 |

### API Health Check

```bash
curl http://localhost:3010/api/scraper/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}
```

## Implemented Features

### 1. ✅ Meaningful Folder Names

**Format**: `YYYYMMDD_HHMMSS_{job_id}`

**Example**: `20250113_143052_8dafff36-6b15-478a-88fc-19cdbbcfca5f5`

**Implementation**:
- [api/database/models.py](api/database/models.py) - Added `folder_name` field
- [api/scraper/config_builder.py](api/scraper/config_builder.py) - Folder name generation
- [api/routes/scraper.py](api/routes/scraper.py) - Job creation with folder_name
- [api/jobs/tasks.py](api/jobs/tasks.py) - Pass folder_name to workers

### 2. ✅ Database Schema

**New Field**: `folder_name` in `jobs` table
- Type: VARCHAR(255)
- Indexed: Yes
- Nullable: Yes (for backward compatibility)

**Migration File**: [api/database/migrations/versions/001_add_folder_name_to_jobs.py](api/database/migrations/versions/001_add_folder_name_to_jobs.py)

### 3. ✅ Run Management Strategy

**Documentation**: [docs/RUN_MANAGEMENT_STRATEGY.md](docs/RUN_MANAGEMENT_STRATEGY.md)

**Lifecycle**:
1. **Active** (0-7 days) - Full access in `./scraper_data/jobs/`
2. **Archived** (7-30 days) - Compressed in `./scraper_data/archive/{YYYY}/{MM}/`
3. **Deleted** (30+ days) - Removed with audit trail

### 4. ✅ Maintenance Tasks

**File**: [api/jobs/maintenance_tasks.py](api/jobs/maintenance_tasks.py)

**Available Tasks**:
- `archive_old_runs()` - Archive runs older than 7 days
- `cleanup_old_runs()` - Delete runs older than 30 days
- `restore_archived_run()` - Restore archived run to active storage
- `get_storage_stats()` - Calculate storage usage

### 5. ✅ Automated Scheduling

**File**: [api/jobs/beat_schedule.py](api/jobs/beat_schedule.py)

**Schedule**:
- **2:00 AM UTC** - Archive old runs (7 days)
- **3:00 AM UTC** - Cleanup old runs (30 days)
- **Every 6 hours** - Update storage statistics

### 6. ✅ API Endpoints

**File**: [api/routes/maintenance.py](api/routes/maintenance.py)

**New Endpoints**:
- `POST /api/maintenance/archive` - Manual archival
- `POST /api/maintenance/cleanup` - Manual cleanup
- `POST /api/maintenance/restore/{job_id}` - Restore archived run
- `GET /api/maintenance/storage-stats` - Storage statistics
- `GET /api/maintenance/health` - System health

## Next Steps

### 1. Database Migration (Required)

Apply the database migration to add the `folder_name` field:

```bash
# Enter API container
docker-compose exec api bash

# Run migration
alembic upgrade head

# Verify
psql $DATABASE_URL -c "\d jobs"

# Exit container
exit
```

### 2. Test Folder Naming (Recommended)

Create a test job to verify folder naming:

```bash
# Get auth token (use your credentials)
TOKEN="your_jwt_token_here"

# Create test job
curl -X POST http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Folder Naming",
    "type": "web",
    "config": {
      "startUrls": ["https://example.com"],
      "maxPages": 5,
      "client_name": "agar",
      "test_mode": true
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }'

# Wait for job to start, then check folder
docker-compose exec api ls -la ./scraper_data/jobs/
# Should see: 20250113_HHMMSS_{uuid}/
```

### 3. Set Up Celery Beat (Optional - for automation)

To enable automatic archival and cleanup, add Celery Beat to docker-compose:

**Edit `docker-compose.yml`**, add:

```yaml
  celery-beat:
    build: .
    command: celery -A api.jobs.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://scraper_user:scraper_pass@postgres:5432/scraper_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - scraper-network
    restart: unless-stopped
```

Then start it:

```bash
docker-compose up -d celery-beat
```

### 4. Test Maintenance Endpoints (Recommended)

```bash
# Get storage statistics
curl http://localhost:3010/api/maintenance/storage-stats \
  -H "Authorization: Bearer $TOKEN" | jq

# Test archival (dry-run)
curl -X POST "http://localhost:3010/api/maintenance/archive?days=0&dry_run=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Check maintenance health
curl http://localhost:3010/api/maintenance/health \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Configuration

### Environment Variables (Optional)

Add to `.env` file to customize behavior:

```bash
# Run Management Settings
ARCHIVE_AFTER_DAYS=7
DELETE_AFTER_DAYS=30
ARCHIVE_COMPRESSION=gzip
DELETION_STRATEGY=soft

# Storage Paths (already configured)
STORAGE_BASE_PATH=./scraper_data
STORAGE_JOBS_PATH=./scraper_data/jobs
```

## Monitoring

### Check Container Logs

```bash
# API logs
docker-compose logs -f api

# Celery worker logs
docker-compose logs -f celery-worker

# All logs
docker-compose logs -f
```

### Verify Database Connection

```bash
docker-compose exec api python -c "
from api.database.connection import get_db_engine
engine = get_db_engine()
print('Database connected:', engine.url)
"
```

### Check Storage Usage

```bash
# Check active storage
du -sh ./scraper_data/jobs/

# Check archive storage (after archival runs)
du -sh ./scraper_data/archive/
```

## Rollback Plan

If issues occur, rollback by:

1. **Stop containers**:
   ```bash
   docker-compose down
   ```

2. **Restore previous images** (if needed):
   ```bash
   docker-compose pull
   ```

3. **Start containers**:
   ```bash
   docker-compose up -d
   ```

4. **Rollback database migration**:
   ```bash
   docker-compose exec api alembic downgrade -1
   ```

## Documentation

- **Implementation Summary**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Quick Start Guide**: [QUICK_START_RUN_MANAGEMENT.md](QUICK_START_RUN_MANAGEMENT.md)
- **Strategy Document**: [docs/RUN_MANAGEMENT_STRATEGY.md](docs/RUN_MANAGEMENT_STRATEGY.md)

## Support

### Common Issues

**Issue**: API not starting
```bash
docker-compose logs api
# Check for import errors or configuration issues
```

**Issue**: Celery worker not connecting
```bash
docker-compose logs celery-worker
# Verify Redis is healthy
docker-compose ps redis
```

**Issue**: Database migration fails
```bash
docker-compose exec api alembic current
docker-compose exec api alembic upgrade head
```

### Verification Checklist

- [x] All containers running and healthy
- [x] API responding to health checks
- [x] Celery worker connected to Redis
- [ ] Database migration applied (`folder_name` field added)
- [ ] Test job created with meaningful folder name
- [ ] Celery Beat configured (optional)
- [ ] Maintenance endpoints tested

## Summary

✅ **Docker containers rebuilt successfully**
✅ **All services healthy and running**
✅ **Code changes deployed**
⏳ **Database migration pending** (run `alembic upgrade head`)
⏳ **Celery Beat setup pending** (optional, for automation)

The system is ready for the database migration and testing of the new folder naming features.
