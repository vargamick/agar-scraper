# 3DN Scraper API - Testing Guide

Quick guide to test the complete API implementation.

---

## Prerequisites

- Docker and Docker Compose installed
- `curl` or similar HTTP client
- `jq` (optional, for pretty JSON)

---

## Quick Start

### 1. Start All Services

```bash
# Start all containers
docker-compose up -d

# Check services are running
docker-compose ps

# Expected output: postgres, redis, crawl4ai, api, celery-worker all "Up"
```

### 2. Initialize Database

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Check health
curl http://localhost:3010/api/scraper/health | jq
```

---

## Test Authentication

### Register a User

```bash
curl -X POST http://localhost:3010/api/scraper/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }' | jq

# Save the access_token from the response
export TOKEN="your_access_token_here"
```

### Login (if needed)

```bash
curl -X POST http://localhost:3010/api/scraper/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }' | jq

export TOKEN="your_new_access_token"
```

### Get Current User

```bash
curl http://localhost:3010/api/scraper/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Test Job Management

### Create a Simple Job

```bash
curl -X POST http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-scrape-001",
    "description": "Test scraping job",
    "type": "web",
    "config": {
      "startUrls": ["https://example.com"],
      "maxPages": 5,
      "crawlDepth": 1,
      "respectRobotsTxt": true
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }' | jq

# Save the jobId
export JOB_ID="your_job_id_here"
```

### List Jobs

```bash
# List all jobs
curl "http://localhost:3010/api/scraper/jobs?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq

# Filter by status
curl "http://localhost:3010/api/scraper/jobs?status=running&limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Get Job Details

```bash
curl http://localhost:3010/api/scraper/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Monitor Job Progress

```bash
# Watch job status (run in loop)
watch -n 2 "curl -s http://localhost:3010/api/scraper/jobs/$JOB_ID \
  -H 'Authorization: Bearer $TOKEN' | jq '.data.progress, .data.status'"
```

### Get Job Logs

```bash
# Get all logs
curl "http://localhost:3010/api/scraper/jobs/$JOB_ID/logs?limit=100" \
  -H "Authorization: Bearer $TOKEN" | jq

# Filter by level
curl "http://localhost:3010/api/scraper/jobs/$JOB_ID/logs?level=error" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Get Job Results

```bash
# Get results
curl "http://localhost:3010/api/scraper/jobs/$JOB_ID/results?limit=50" \
  -H "Authorization: Bearer $TOKEN" | jq

# Count results
curl "http://localhost:3010/api/scraper/jobs/$JOB_ID/results" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.itemsCount'
```

---

## Test Job Control

### Pause a Running Job

```bash
curl -X POST http://localhost:3010/api/scraper/jobs/$JOB_ID/control \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "pause"}' | jq
```

### Resume a Paused Job

```bash
curl -X POST http://localhost:3010/api/scraper/jobs/$JOB_ID/control \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "resume"}' | jq
```

### Cancel a Job

```bash
curl -X POST http://localhost:3010/api/scraper/jobs/$JOB_ID/control \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "cancel"}' | jq
```

---

## Test Statistics

```bash
curl http://localhost:3010/api/scraper/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Test Job Deletion

```bash
# Delete a job (must be stopped first if running)
curl -X DELETE http://localhost:3010/api/scraper/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Advanced Testing

### Create Job with Full Configuration

```bash
curl -X POST http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "advanced-scrape",
    "description": "Advanced scraping with full config",
    "type": "web",
    "config": {
      "startUrls": [
        "https://example.com/products",
        "https://example.com/blog"
      ],
      "maxPages": 50,
      "crawlDepth": 3,
      "rateLimit": {
        "requests": 5,
        "per": "second"
      },
      "selectors": {
        "css": [".product", ".article"]
      },
      "headers": {
        "User-Agent": "3DN-Scraper/1.0"
      },
      "followLinks": true,
      "respectRobotsTxt": true
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json",
      "sendToMemento": {
        "enabled": false,
        "instanceId": "main-knowledge",
        "processingOptions": {
          "chunking": true,
          "embedding": true
        }
      }
    }
  }' | jq
```

### Test Pagination

```bash
# First page
curl "http://localhost:3010/api/scraper/jobs?limit=5&offset=0" \
  -H "Authorization: Bearer $TOKEN" | jq

# Second page
curl "http://localhost:3010/api/scraper/jobs?limit=5&offset=5" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Test Error Handling

```bash
# Invalid job (should return validation error)
curl -X POST http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",
    "config": {}
  }' | jq

# Get non-existent job (should return 404)
curl http://localhost:3010/api/scraper/jobs/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $TOKEN" | jq

# Invalid token (should return 401)
curl http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer invalid_token" | jq
```

---

## Check Backend Logs

### API Logs
```bash
docker-compose logs -f api
```

### Celery Worker Logs
```bash
docker-compose logs -f celery-worker
```

### Database Logs
```bash
docker-compose logs -f postgres
```

### All Logs
```bash
docker-compose logs -f
```

---

## Database Inspection

### Connect to PostgreSQL

```bash
docker-compose exec postgres psql -U scraper_user -d scraper_db
```

### Useful Queries

```sql
-- Count jobs by status
SELECT status, COUNT(*) FROM jobs GROUP BY status;

-- Recent jobs
SELECT id, name, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;

-- Job with most results
SELECT j.name, COUNT(r.id) as result_count
FROM jobs j
LEFT JOIN job_results r ON j.id = r.job_id
GROUP BY j.id, j.name
ORDER BY result_count DESC;

-- Job logs summary
SELECT job_id, level, COUNT(*) FROM job_logs GROUP BY job_id, level;
```

---

## Performance Testing

### Create Multiple Jobs

```bash
# Create 5 jobs quickly
for i in {1..5}; do
  curl -X POST http://localhost:3010/api/scraper/jobs \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"batch-job-$i\",
      \"type\": \"web\",
      \"config\": {
        \"startUrls\": [\"https://example.com\"],
        \"maxPages\": 3
      },
      \"output\": {
        \"saveFiles\": true,
        \"fileFormat\": \"json\"
      }
    }"
  echo ""
  sleep 1
done
```

### Monitor Worker Load

```bash
# Check Celery worker status
docker-compose exec celery-worker celery -A api.jobs.celery_app inspect active

# Check queue size
docker-compose exec redis redis-cli LLEN celery
```

---

## API Documentation

### Access Interactive Docs

- **Swagger UI**: http://localhost:3010/api/scraper/docs
- **ReDoc**: http://localhost:3010/api/scraper/redoc

### Test from Browser

1. Open http://localhost:3010/api/scraper/docs
2. Click "Authorize" button
3. Enter: `Bearer YOUR_TOKEN`
4. Try out endpoints interactively

---

## Cleanup

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Reset Database

```bash
# Drop and recreate tables
docker-compose exec api python -c "
from api.database.connection import init_database
from api.config import settings
db = init_database(settings.DATABASE_URL)
db.drop_all_tables()
db.create_all_tables()
"

# Or use Alembic
docker-compose exec api alembic downgrade base
docker-compose exec api alembic upgrade head
```

---

## Troubleshooting

### API Won't Start

```bash
# Check logs
docker-compose logs api

# Check if port is available
lsof -i :3010

# Restart service
docker-compose restart api
```

### Celery Worker Not Processing Jobs

```bash
# Check worker logs
docker-compose logs celery-worker

# Check Redis connection
docker-compose exec celery-worker python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"

# Restart worker
docker-compose restart celery-worker
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose exec postgres pg_isready

# Check connection from API
docker-compose exec api python -c "
from api.database.connection import init_database
from api.config import settings
db = init_database(settings.DATABASE_URL)
print('Database connection successful')
"
```

### Jobs Stuck in Pending

```bash
# Check if Celery worker is running
docker-compose ps celery-worker

# Check Celery queue
docker-compose exec redis redis-cli KEYS "*celery*"

# Purge queue (WARNING: cancels all pending jobs)
docker-compose exec celery-worker celery -A api.jobs.celery_app purge
```

---

## Success Criteria

After running the tests, you should see:

✅ User registration and login working
✅ Jobs created and queued successfully
✅ Jobs transitioning through states (pending → running → completed)
✅ Real-time progress updates
✅ Logs being generated
✅ Results being stored
✅ Statistics being calculated
✅ Job control operations working
✅ All endpoints returning proper response format

---

## Next Steps

Once testing is complete:

1. Review logs for any errors or warnings
2. Check database for data integrity
3. Test with your actual scraping targets
4. Configure rate limiting for production
5. Set up monitoring and alerting
6. Document any custom configurations
7. Train users on API usage

---

**Happy Testing! 🎉**
