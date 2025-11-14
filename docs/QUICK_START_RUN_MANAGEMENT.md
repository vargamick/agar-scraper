# Quick Start: Run Management

## TL;DR

Output folders now use meaningful names like `20250113_143052_{uuid}` instead of just `{uuid}`.

Automatic archival after 7 days, deletion after 30 days.

## Apply Changes

### 1. Database Migration (Required)

```bash
cd /Users/mick/AI/c4ai/agar
alembic upgrade head
```

### 2. Restart API (Required)

```bash
docker-compose restart api
```

### 3. Start Celery Beat (Optional - for automation)

Add to `docker-compose.yml`:

```yaml
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

Then run:
```bash
docker-compose up -d celery-beat
```

## Test It

### 1. Create a job

```bash
curl -X POST http://localhost:8000/api/scraper/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Run",
    "type": "web",
    "config": {
      "startUrls": ["https://example.com"],
      "maxPages": 10
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }'
```

### 2. Check folder name

```bash
ls -la ./scraper_data/jobs/
# Should see: 20250113_143052_{uuid}/
```

### 3. Test archival (dry-run)

```bash
curl -X POST "http://localhost:8000/api/maintenance/archive?days=0&dry_run=true" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 4. Check storage stats

```bash
curl http://localhost:8000/api/maintenance/storage-stats \
  -H "Authorization: Bearer YOUR_TOKEN" | jq
```

## Configuration

Default settings (can be customized in `.env`):

```bash
ARCHIVE_AFTER_DAYS=7        # Archive after 7 days
DELETE_AFTER_DAYS=30        # Delete after 30 days
DELETION_STRATEGY=soft      # Keep DB records
```

## Folder Structure

```
scraper_data/
├── jobs/                                    # Active (0-7 days)
│   └── 20250113_143052_{uuid}/
│       ├── products/
│       ├── categories/
│       ├── screenshots/
│       └── all_products.json
│
└── archive/                                 # Archived (7-30 days)
    └── 2025/
        └── 01/
            └── 20250106_143052_{uuid}.tar.gz
```

## API Endpoints

### Maintenance Endpoints

| Endpoint | Method | Description | Access |
|----------|--------|-------------|--------|
| `/api/maintenance/archive` | POST | Trigger archival | Admin |
| `/api/maintenance/cleanup` | POST | Trigger cleanup | Admin |
| `/api/maintenance/restore/{job_id}` | POST | Restore archived run | Owner/Admin |
| `/api/maintenance/storage-stats` | GET | Get storage stats | All |
| `/api/maintenance/health` | GET | System health | All |

## Manual Operations

### Archive a specific job early

```bash
curl -X POST "http://localhost:8000/api/maintenance/archive?days=0" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Restore an archived job

```bash
curl -X POST "http://localhost:8000/api/maintenance/restore/{job_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get storage statistics

```bash
curl http://localhost:8000/api/maintenance/storage-stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Automated Schedule

When Celery Beat is running:

- **2:00 AM UTC** - Archive runs older than 7 days
- **3:00 AM UTC** - Delete archived runs older than 30 days
- **Every 6 hours** - Update storage statistics

## Troubleshooting

### Migration failed?
```bash
alembic current
alembic upgrade head
```

### Celery not running tasks?
```bash
docker-compose logs celery
docker-compose logs celery-beat
celery -A api.jobs.celery_app inspect scheduled
```

### Need more details?

See [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for complete documentation.

See [docs/RUN_MANAGEMENT_STRATEGY.md](docs/RUN_MANAGEMENT_STRATEGY.md) for the full strategy.
