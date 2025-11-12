# 3DN Scraper API

A production-ready RESTful API for managing web scraping jobs with real-time progress tracking, background processing, and comprehensive job management.

---

## 🚀 Quick Start (5 Minutes)

```bash
# One command to start everything and run tests
./scripts/start-and-test.sh
```

That's it! The script will:
- Start all services (API, PostgreSQL, Redis, Celery, Crawl4AI)
- Run database migrations
- Execute comprehensive API tests
- Show you the results

**See [QUICK_START.md](QUICK_START.md) for detailed instructions.**

---

## 📋 What's Included

### ✅ Phase 1: Foundation (COMPLETE)
- **Database Layer** - SQLAlchemy ORM with PostgreSQL/SQLite support
- **FastAPI Application** - Modern async web framework with auto-docs
- **Authentication System** - JWT bearer tokens with user management
- **Docker Setup** - Complete orchestration for all services

### ✅ Phase 2: Job Management (COMPLETE)
- **Job Creation** - Create scraping jobs with full configuration
- **Background Processing** - Celery workers execute jobs asynchronously
- **Real-time Progress** - Track job status, percentage, ETA
- **Result Management** - Store and retrieve scraped data
- **Log System** - Comprehensive logging with multiple levels
- **Job Control** - Start, pause, resume, stop, cancel operations
- **Statistics** - System-wide metrics and insights

---

## 🎯 Features

- ✅ **Complete API** - All endpoints from specification implemented
- ✅ **Real-time Updates** - Live progress tracking and status
- ✅ **Background Jobs** - Asynchronous processing with Celery
- ✅ **Comprehensive Logging** - All events captured and queryable
- ✅ **Result Export** - Multiple formats (JSON, Markdown, HTML)
- ✅ **Job Control** - Full lifecycle management
- ✅ **Statistics** - Overall system metrics
- ✅ **Security** - JWT authentication, permission checks
- ✅ **Validation** - Pydantic request/response validation
- ✅ **Documentation** - Auto-generated OpenAPI/Swagger docs
- ✅ **Docker Ready** - Complete containerization
- ✅ **Production Ready** - Error handling, logging, monitoring

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| **[QUICK_START.md](QUICK_START.md)** | 5-minute quick start guide |
| **[docs/API_QUICKSTART.md](docs/API_QUICKSTART.md)** | Detailed API setup guide |
| **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** | Comprehensive testing instructions |
| **[docs/PHASE_2_COMPLETE.md](docs/PHASE_2_COMPLETE.md)** | Phase 2 implementation details |
| **[docs/API_IMPLEMENTATION_SUMMARY.md](docs/API_IMPLEMENTATION_SUMMARY.md)** | Complete technical overview |

**Interactive API Docs:** http://localhost:3010/api/scraper/docs (when running)

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │ (Your application)
└──────┬──────┘
       │ HTTP/REST
       ↓
┌─────────────────────────────────────────┐
│           FastAPI REST API              │
│  • Authentication (JWT)                 │
│  • Request Validation                   │
│  • Response Formatting                  │
└──────┬──────────────────────┬───────────┘
       │                      │
       ↓                      ↓
┌─────────────┐      ┌──────────────┐
│  PostgreSQL │      │ Redis Queue  │
│  Database   │      │  (Celery)    │
└─────────────┘      └──────┬───────┘
                            │
                            ↓
                   ┌─────────────────┐
                   │ Celery Workers  │
                   │ • Job Execution │
                   │ • Progress      │
                   │ • Results       │
                   └────────┬────────┘
                            │
                            ↓
                   ┌─────────────────┐
                   │ Existing Scraper│
                   │ • Categories    │
                   │ • Products      │
                   │ • PDFs          │
                   └─────────────────┘
```

---

## 🔧 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `POST /auth/refresh` - Refresh token
- `GET /auth/me` - Get current user

### Job Management
- `POST /jobs` - Create job
- `GET /jobs` - List jobs (with filtering)
- `GET /jobs/{id}` - Get job details
- `POST /jobs/{id}/control` - Control job (start/pause/stop/cancel)
- `GET /jobs/{id}/logs` - Get job logs
- `GET /jobs/{id}/results` - Get job results
- `DELETE /jobs/{id}` - Delete job

### Statistics
- `GET /stats` - Get overall statistics

### Health
- `GET /health` - Health check

---

## 🎨 Example Usage

### Create a Scraping Job

```bash
curl -X POST http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example-scrape",
    "description": "Scrape example website",
    "type": "web",
    "config": {
      "startUrls": ["https://example.com"],
      "maxPages": 10,
      "crawlDepth": 2,
      "respectRobotsTxt": true
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }'
```

### Monitor Job Progress

```bash
curl http://localhost:3010/api/scraper/jobs/JOB_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Results

```bash
curl http://localhost:3010/api/scraper/jobs/JOB_ID/results \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Testing

### Automated Tests

```bash
# Run all tests
./scripts/test-api.sh

# Start services without tests
./scripts/start-and-test.sh --no-tests
```

### Manual Testing

```bash
# View interactive API docs
open http://localhost:3010/api/scraper/docs

# Run individual curl commands
curl http://localhost:3010/api/scraper/health | jq
```

---

## 🔍 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
```

### Check Status

```bash
# Service status
docker-compose ps

# API health
curl http://localhost:3010/api/scraper/health
```

### Database Inspection

```bash
# Connect to database
docker-compose exec postgres psql -U scraper_user -d scraper_db

# Query jobs
SELECT name, status, created_at FROM jobs ORDER BY created_at DESC LIMIT 10;
```

---

## 🛠️ Development

### Start Services

```bash
docker-compose up -d
```

### Run Migrations

```bash
docker-compose exec api alembic upgrade head
```

### Restart After Code Changes

```bash
docker-compose restart api celery-worker
```

### Stop Services

```bash
docker-compose down      # Stop (keep data)
docker-compose down -v   # Stop and remove data
```

---

## 📦 What's Running

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| API | scraper-api | 3001 | REST API server |
| Celery Worker | scraper-celery-worker | - | Background job processor |
| PostgreSQL | scraper-postgres | 5432 | Database |
| Redis | scraper-redis | 6379 | Job queue & cache |
| Crawl4AI | crawl4ai-service | 11235 | Web scraping engine |

---

## 🔒 Security

- **JWT Authentication** - Bearer tokens with expiration
- **Password Hashing** - Bcrypt for secure storage
- **Permission Checks** - User-scoped access to jobs
- **Input Validation** - Pydantic schemas validate all inputs
- **CORS Configuration** - Configurable allowed origins
- **SQL Injection Protection** - SQLAlchemy ORM prevents attacks

---

## 📊 Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM with PostgreSQL/SQLite
- **Celery** - Distributed task queue
- **Redis** - Message broker and cache
- **Pydantic** - Data validation
- **Alembic** - Database migrations
- **JWT** - Authentication tokens
- **Docker** - Containerization
- **Uvicorn** - ASGI server

---

## 🚦 Status

| Component | Status | Notes |
|-----------|--------|-------|
| Phase 1: Foundation | ✅ COMPLETE | Database, FastAPI, Auth |
| Phase 2: Job System | ✅ COMPLETE | All endpoints, background jobs |
| Documentation | ✅ COMPLETE | API docs, guides, examples |
| Testing | ✅ COMPLETE | Automated test suite |
| Docker Setup | ✅ COMPLETE | Full orchestration |

---

## 📝 Configuration

Edit `.env` file to customize:

```bash
# API
API_PORT=3001
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://scraper_user:scraper_password@postgres:5432/scraper_db

# Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis
REDIS_URL=redis://redis:6379/0

# See .env.api.template for all options
```

---

## 🤝 Contributing

1. Make changes to the code
2. Restart services: `docker-compose restart api celery-worker`
3. Run tests: `./scripts/test-api.sh`
4. Check logs: `docker-compose logs -f api`

---

## 📞 Support

- **Quick Start Issues**: See [QUICK_START.md](QUICK_START.md)
- **API Questions**: Check [docs/API_QUICKSTART.md](docs/API_QUICKSTART.md)
- **Testing Help**: Read [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)
- **Technical Details**: Review [docs/PHASE_2_COMPLETE.md](docs/PHASE_2_COMPLETE.md)

---

## 🎉 Summary

**One Command to Start:**
```bash
./scripts/start-and-test.sh
```

**Access API:**
- REST API: http://localhost:3010/api/scraper
- Interactive Docs: http://localhost:3010/api/scraper/docs

**Run Tests:**
```bash
./scripts/test-api.sh
```

**View Logs:**
```bash
docker-compose logs -f api
```

**Stop:**
```bash
docker-compose down
```

---

**Built with ❤️ for efficient web scraping at scale**
