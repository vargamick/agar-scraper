# Run Management Strategy

## Overview

This document outlines the strategy for managing output folders, archiving historical runs, and cleaning up old data for the Agar Scraper system.

## Folder Naming Convention

### Format: `YYYYMMDD_HHMMSS_{job_id}`

All scraper runs now use a meaningful folder name that includes:
- **Date**: `YYYYMMDD` - Year, month, and day of the run
- **Time**: `HHMMSS` - Hour, minute, and second when the run started
- **Job ID**: The UUID of the job for uniqueness

**Examples:**
```
20250113_143052_8dafff36-6b15-478a-88fc-19cdbbcfca5f5
20250114_091230_a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Benefits:
1. **Human-readable**: Easy to identify when a run occurred
2. **Sortable**: Chronological ordering by filename
3. **Unique**: UUID ensures no conflicts
4. **Traceable**: Links directly to database record

## Database Schema

### Job Table Updates

The `jobs` table now includes a `folder_name` field:

```sql
ALTER TABLE jobs ADD COLUMN folder_name VARCHAR(255);
CREATE INDEX ix_jobs_folder_name ON jobs(folder_name);
```

**Field Details:**
- **Type**: `VARCHAR(255)`
- **Nullable**: `Yes` (for backward compatibility)
- **Indexed**: `Yes` (for fast lookups)
- **Format**: `YYYYMMDD_HHMMSS`

## Run Lifecycle Management

### 1. Active Runs (0-7 days)

**Status**: Immediately accessible
**Location**: `./scraper_data/jobs/{folder_name}_{job_id}/`
**Database Status**: All statuses (pending, running, completed, failed, cancelled)

**Actions:**
- Full read/write access
- Available via API
- Included in statistics
- Visible in job listings

### 2. Archived Runs (7-30 days)

**Status**: Moved to archive storage
**Location**: `./scraper_data/archive/{YYYY}/{MM}/{folder_name}_{job_id}/`
**Database Status**: Flagged with `archived_at` timestamp

**Actions:**
- Read-only access
- Available via special archive API endpoint
- Compressed for storage efficiency
- Not included in active job listings
- Metadata retained in database

### 3. Deleted Runs (30+ days)

**Status**: Permanently removed
**Location**: N/A (deleted from filesystem)
**Database Status**: Soft-deleted (optional) or hard-deleted

**Actions:**
- Files completely removed
- Database record either:
  - **Soft delete**: `deleted_at` timestamp set, record retained for audit
  - **Hard delete**: Record removed entirely
- Summary statistics preserved in separate audit table

## Implementation Design

### Phase 1: Automatic Archival (After 7 Days)

**Process:**
1. Scheduled task runs daily (e.g., 2:00 AM)
2. Identifies completed jobs older than 7 days
3. For each eligible job:
   - Compresses output folder to `.tar.gz`
   - Moves to archive location: `./scraper_data/archive/{YYYY}/{MM}/`
   - Updates database: sets `archived_at` timestamp
   - Removes original uncompressed folder

**Celery Task:**
```python
@celery_app.task(name="api.jobs.tasks.archive_old_runs")
def archive_old_runs():
    """Archive runs older than 7 days."""
    cutoff_date = datetime.now() - timedelta(days=7)
    # Find jobs completed before cutoff
    # Compress and move folders
    # Update database
```

### Phase 2: Automatic Deletion (After 30 Days)

**Process:**
1. Scheduled task runs daily (e.g., 3:00 AM)
2. Identifies archived jobs older than 30 days
3. For each eligible job:
   - Option A (Soft Delete):
     - Sets `deleted_at` timestamp
     - Keeps database record for audit
     - Deletes archive file
   - Option B (Hard Delete):
     - Saves summary to audit table
     - Removes database record
     - Deletes archive file

**Celery Task:**
```python
@celery_app.task(name="api.jobs.tasks.cleanup_old_runs")
def cleanup_old_runs():
    """Delete archived runs older than 30 days."""
    cutoff_date = datetime.now() - timedelta(days=30)
    # Find archived jobs before cutoff
    # Save audit records
    # Delete files and optionally database records
```

### Configuration

**Environment Variables:**
```bash
# Archival settings
ARCHIVE_AFTER_DAYS=7
DELETE_AFTER_DAYS=30
ARCHIVE_COMPRESSION=gzip  # or 'bz2', 'xz'

# Archive location
ARCHIVE_BASE_PATH=./scraper_data/archive

# Deletion strategy
DELETION_STRATEGY=soft  # or 'hard'
```

## API Endpoints

### List Archived Jobs

```
GET /api/scraper/jobs/archived
Query Parameters:
  - start_date: Filter by date range
  - end_date: Filter by date range
  - limit: Pagination limit
  - offset: Pagination offset
```

### Restore Archived Job

```
POST /api/scraper/jobs/{job_id}/restore
```

Decompresses an archived job back to active storage for analysis.

### Download Archived Results

```
GET /api/scraper/jobs/{job_id}/archive/download
```

Downloads the compressed archive file directly.

## Monitoring and Maintenance

### Daily Health Checks

1. **Storage Usage**: Monitor disk space usage
2. **Archive Success Rate**: Track archival task success/failures
3. **Deletion Logs**: Audit trail of deleted runs

### Alerts

Configure alerts for:
- Storage exceeding 80% capacity
- Archival task failures
- Unusual deletion patterns

### Manual Overrides

Administrators can:
- Manually archive a job early
- Manually delete a job immediately
- Extend retention for specific important runs
- Restore deleted jobs (if soft delete enabled)

## Database Schema Updates

### New Fields for Job Table

```sql
-- Archival tracking
ALTER TABLE jobs ADD COLUMN archived_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE jobs ADD COLUMN archive_path VARCHAR(512);

-- Deletion tracking (for soft delete)
ALTER TABLE jobs ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE jobs ADD COLUMN deletion_reason TEXT;

-- Indexes
CREATE INDEX ix_jobs_archived_at ON jobs(archived_at);
CREATE INDEX ix_jobs_deleted_at ON jobs(deleted_at);
```

### New Audit Table

```sql
CREATE TABLE job_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL,
    job_name VARCHAR(255),
    folder_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    archived_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE NOT NULL,
    stats JSONB,
    created_by UUID,
    deletion_reason TEXT
);

CREATE INDEX ix_job_audit_deleted_at ON job_audit(deleted_at);
CREATE INDEX ix_job_audit_job_id ON job_audit(job_id);
```

## Storage Efficiency

### Compression Ratios

Expected compression ratios for different content types:

| Content Type | Compression Ratio | Notes |
|--------------|-------------------|-------|
| JSON files | 80-90% | Highly compressible |
| Screenshots (PNG) | 10-20% | Already compressed |
| PDF files | 5-15% | Already compressed |
| Logs (text) | 85-95% | Highly compressible |

**Estimated Storage Savings**: 40-60% average across all content types

### Archive Structure

```
scraper_data/
├── jobs/                          # Active runs (0-7 days)
│   ├── 20250113_143052_{uuid}/
│   └── 20250114_091230_{uuid}/
│
└── archive/                       # Archived runs (7-30 days)
    ├── 2025/
    │   ├── 01/
    │   │   ├── 20250106_143052_{uuid}.tar.gz
    │   │   └── 20250107_091230_{uuid}.tar.gz
    │   └── 02/
    │       └── 20250201_143052_{uuid}.tar.gz
```

## Migration Path

### For Existing Runs

1. **Identify existing runs** with UUID-only folder names
2. **Read job creation timestamp** from database
3. **Generate folder_name** based on `created_at` timestamp
4. **Update database** with generated folder_name
5. **Rename folders** to new format (optional, can leave as-is)

**Migration Script:**
```python
@celery_app.task(name="api.jobs.tasks.migrate_folder_names")
def migrate_folder_names():
    """Migrate existing jobs to use folder_name field."""
    # Find jobs without folder_name
    # Generate folder_name from created_at
    # Update database
    # Optionally rename folders
```

## Security Considerations

1. **Access Control**: Only job owners and admins can access archived jobs
2. **Audit Trail**: All deletions are logged with user and reason
3. **Data Retention Compliance**: Configurable retention periods for compliance
4. **Secure Deletion**: Option to overwrite files before deletion (for sensitive data)

## Performance Considerations

1. **Background Processing**: All archival/deletion runs in background tasks
2. **Batch Operations**: Process multiple jobs per task execution
3. **Rate Limiting**: Limit concurrent compression operations
4. **Off-Peak Scheduling**: Run maintenance tasks during low-usage hours

## Testing Strategy

### Unit Tests
- Folder name generation
- Archive path calculation
- Compression/decompression

### Integration Tests
- End-to-end archival workflow
- End-to-end deletion workflow
- API endpoint functionality

### Load Tests
- Archive performance with large datasets
- Database query performance with archived jobs

## Rollout Plan

### Week 1: Database Migration
- Deploy database schema changes
- Run migration for existing jobs
- Verify data integrity

### Week 2: Folder Naming
- Deploy folder naming changes
- Monitor new job creation
- Verify folder structure

### Week 3: Archival System
- Deploy archival background task
- Enable archival for test jobs
- Monitor archival success rate

### Week 4: Deletion System
- Deploy deletion background task
- Enable deletion with safety limits
- Monitor storage savings

### Week 5: Full Deployment
- Enable automatic archival
- Enable automatic deletion
- Deploy monitoring dashboards

## Success Metrics

1. **Storage Reduction**: Target 40-60% reduction in active storage
2. **Archival Success Rate**: Target >99% success rate
3. **API Response Time**: <100ms for active jobs, <500ms for archived jobs
4. **Zero Data Loss**: No accidental deletions or corruption

## Support and Troubleshooting

### Common Issues

**Issue**: Archive task failing
- Check disk space
- Verify permissions on archive directory
- Review task logs for errors

**Issue**: Cannot access archived job
- Verify job exists in database
- Check archive file integrity
- Ensure user has access permissions

**Issue**: High storage usage despite archival
- Check archive compression ratio
- Verify deletion task is running
- Review retention settings

## Future Enhancements

1. **Cloud Storage Integration**: Archive to S3/Azure Blob/Google Cloud Storage
2. **Intelligent Retention**: Machine learning to identify important runs
3. **Incremental Archival**: Only archive new results, not entire folders
4. **Cross-Region Replication**: Disaster recovery for critical runs
5. **Analytics Dashboard**: Visualize storage trends and run patterns
