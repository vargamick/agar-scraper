# 3DN Scraper API - Quick Start Guide

Get up and running in 5 minutes!

---

## One-Command Start + Test

```bash
./scripts/start-and-test.sh
```

This script will:
1. ✅ Check prerequisites (Docker, curl, jq)
2. ✅ Stop any existing services
3. ✅ Start all Docker containers (PostgreSQL, Redis, API, Celery, Crawl4AI)
4. ✅ Wait for services to be ready
5. ✅ Run database migrations
6. ✅ Execute comprehensive API tests
7. ✅ Show you the results

**Expected Duration:** 2-3 minutes

---

## What Gets Started

When you run the script, these services start:

| Service | Port | Description |
|---------|------|-------------|
| **API** | 3001 | FastAPI REST API |
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Job queue & cache |
| **Celery Worker** | - | Background job processor |
| **Crawl4AI** | 11235 | Web scraping engine |

---

## API Endpoints Tested

The test script will verify all these endpoints:

1. **Health Check** - `GET /health`
2. **User Registration** - `POST /auth/register`
3. **User Login** - `POST /auth/login`
4. **Get Current User** - `GET /auth/me`
5. **Create Job** - `POST /jobs`
6. **List Jobs** - `GET /jobs`
7. **Get Job Details** - `GET /jobs/{id}`
8. **Get Job Logs** - `GET /jobs/{id}/logs`
9. **Get Job Results** - `GET /jobs/{id}/results`
10. **Control Job** - `POST /jobs/{id}/control`
11. **Get Statistics** - `GET /stats`
12. **Security Tests** - Invalid tokens, validation errors

---

## Example Test Output

```
╔════════════════════════════════════════════════════╗
║     3DN Scraper API - Comprehensive Test Suite    ║
╚════════════════════════════════════════════════════╝

ℹ Waiting for API to be ready...
✓ API is ready!

========================================
Test 1: Health Check
========================================
✓ Health check passed
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected"
}

========================================
Test 2: User Registration
========================================
✓ User registered successfully
ℹ Token: eyJhbGciOiJIUzI1NiIs...

... (continues with all tests)

========================================
Test Suite Complete
========================================
✓ All tests executed successfully!
```

---

## Manual Testing

If you want to test manually:

### 1. Start Services Only (No Tests)

```bash
./scripts/start-and-test.sh --no-tests
```

### 2. Run Tests Separately

```bash
./scripts/test-api.sh
```

### 3. Manual curl Commands

```bash
# Get health status
curl http://localhost:3010/api/scraper/health | jq

# Register user
curl -X POST http://localhost:3010/api/scraper/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "myuser",
    "email": "my@email.com",
    "password": "mypassword123"
  }' | jq

# Save the token from response
TOKEN="your_access_token_here"

# Create a job
curl -X POST http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-test-job",
    "type": "web",
    "config": {
      "startUrls": ["https://example.com"],
      "maxPages": 5
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }' | jq

# List jobs
curl "http://localhost:3010/api/scraper/jobs?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## View API Documentation

Once services are running, open in your browser:

- **Swagger UI (Interactive)**: http://localhost:3010/api/scraper/docs
- **ReDoc (Readable)**: http://localhost:3010/api/scraper/redoc

You can test all endpoints directly from the Swagger UI!

---

## View Logs

```bash
# All logs
docker-compose logs -f

# Just API logs
docker-compose logs -f api

# Just Celery worker logs
docker-compose logs -f celery-worker

# Specific service
docker-compose logs -f postgres
```

---

## Check Service Status

```bash
# List all running containers
docker-compose ps

# Expected output:
NAME                  STATUS
scraper-api           Up
scraper-celery-worker Up
scraper-postgres      Up
scraper-redis         Up
crawl4ai-service      Up
```

---

## Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U scraper_user -d scraper_db

# Example queries
SELECT COUNT(*) FROM jobs;
SELECT name, status FROM jobs ORDER BY created_at DESC LIMIT 5;
\dt  # List all tables
\q   # Quit
```

---

## Stop Services

```bash
# Stop all services (keeps data)
docker-compose down

# Stop and remove all data (clean start)
docker-compose down -v
```

---

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -i :3010  # API
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill processes using the ports if needed
kill -9 <PID>

# Then restart
./scripts/start-and-test.sh
```

### API Not Responding

```bash
# Check API logs
docker-compose logs api

# Restart API service
docker-compose restart api

# Check health manually
curl http://localhost:3010/api/scraper/health
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose exec postgres pg_isready

# Check database exists
docker-compose exec postgres psql -U scraper_user -l

# Recreate database (WARNING: loses data)
docker-compose down -v
./scripts/start-and-test.sh
```

### Tests Failing

```bash
# Check if all services are healthy
docker-compose ps

# Check API health
curl http://localhost:3010/api/scraper/health

# View logs for errors
docker-compose logs api | grep ERROR
docker-compose logs celery-worker | grep ERROR

# Restart and try again
docker-compose restart
sleep 10
./scripts/test-api.sh
```

---

## Development Workflow

### 1. Make Code Changes

Edit files in your IDE...

### 2. Restart Services

```bash
docker-compose restart api celery-worker
```

### 3. Test Changes

```bash
./scripts/test-api.sh
```

### 4. View Logs

```bash
docker-compose logs -f api
```

---

## Clean Slate

To start completely fresh:

```bash
# Stop everything and remove all data
docker-compose down -v

# Remove generated files (optional)
rm -rf scraper_data/

# Start fresh
./scripts/start-and-test.sh
```

---

## What's Next?

1. **Explore API Docs**: http://localhost:3010/api/scraper/docs
2. **Read Full Documentation**: See `docs/` directory
3. **Customize Jobs**: Modify job configurations in test script
4. **Integrate Frontend**: Use the API with your frontend application
5. **Deploy to Production**: Follow deployment guides in `docs/`

---

## Prerequisites

Make sure you have installed:

- **Docker**: https://docs.docker.com/get-docker/
- **Docker Compose**: Usually comes with Docker Desktop
- **curl**: Usually pre-installed on macOS/Linux
- **jq** (optional but recommended): `brew install jq` (macOS) or `apt-get install jq` (Linux)

---

## Support

- **API Documentation**: `docs/API_QUICKSTART.md`
- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **Phase 2 Details**: `docs/PHASE_2_COMPLETE.md`
- **Issues**: Check Docker logs and API documentation

---

## Summary

```bash
# Full automated test
./scripts/start-and-test.sh

# Start without tests
./scripts/start-and-test.sh --no-tests

# Run tests only (after starting)
./scripts/test-api.sh

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Access API docs
open http://localhost:3010/api/scraper/docs
```

**That's it! You're ready to go! 🚀**
