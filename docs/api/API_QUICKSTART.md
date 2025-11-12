# 3DN Scraper API - Quick Start Guide

This guide will help you get the Scraper API up and running quickly.

## What's Been Implemented

### Phase 1: Foundation (COMPLETED)

The following components have been fully implemented:

1. **Database Layer**
   - SQLAlchemy ORM models (Users, Jobs, JobResults, JobLogs, ScheduledJobs, WebhookEndpoints)
   - Database connection management with pooling
   - Repository pattern for data access
   - Alembic migrations setup

2. **FastAPI Application**
   - Main application with middleware
   - CORS configuration
   - Exception handlers
   - Logging middleware

3. **Authentication System**
   - User registration and login
   - JWT token generation (access + refresh tokens)
   - Password hashing with bcrypt
   - Bearer token authentication
   - User management

4. **API Routes (Current)**
   - Health check endpoints
   - Authentication endpoints (register, login, refresh, me)
   - Scraper endpoints (stubs - will be implemented in Phase 2)

5. **Docker Setup**
   - PostgreSQL database
   - Redis for job queue
   - API service
   - Celery worker (ready for job processing)
   - Existing Crawl4AI integration

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (recommended)
- OR PostgreSQL + Redis (for manual setup)

## Quick Start (Docker - Recommended)

### 1. Setup Environment

```bash
# Copy environment template
cp .env.api.template .env

# Edit .env and set at minimum:
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
# - DATABASE_URL (already set for Docker)
```

### 2. Start Services

```bash
# Start all services (API, PostgreSQL, Redis, Crawl4AI)
docker-compose up -d

# Check logs
docker-compose logs -f api

# Check service status
docker-compose ps
```

### 3. Run Database Migrations

```bash
# Enter the API container
docker-compose exec api bash

# Run migrations
alembic upgrade head

# Exit container
exit
```

### 4. Test the API

```bash
# Health check
curl http://localhost:3010/api/scraper/health

# API root
curl http://localhost:3010/api/scraper
```

### 5. Create Your First User

```bash
# Register a new user
curl -X POST http://localhost:3010/api/scraper/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword123",
    "full_name": "Admin User"
  }'

# Response will include access_token and refresh_token
```

### 6. Access Protected Endpoints

```bash
# Get current user info (replace TOKEN with your access_token)
curl http://localhost:3010/api/scraper/auth/me \
  -H "Authorization: Bearer TOKEN"

# List jobs (placeholder)
curl http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer TOKEN"
```

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.api.template .env

# Edit .env and configure:
# - SECRET_KEY (generate new one)
# - DATABASE_URL (use SQLite for quick start: sqlite:///./scraper_api.db)
# - REDIS_URL (if running Redis locally)
```

### 3. Setup Database

```bash
# Run migrations
alembic upgrade head

# Or create tables directly (development only)
python -c "from api.database.connection import init_database; from api.config import settings; db = init_database(settings.DATABASE_URL); db.create_all_tables()"
```

### 4. Start the API

```bash
# Development mode (with auto-reload)
uvicorn api.main:app --reload --host 0.0.0.0 --port 3001

# Or run directly
python -m api.main
```

### 5. Access API Documentation

Open your browser and navigate to:
- Swagger UI: http://localhost:3010/api/scraper/docs
- ReDoc: http://localhost:3010/api/scraper/redoc

## Available Endpoints

### Authentication (No Auth Required)

- `POST /api/scraper/auth/register` - Register new user
- `POST /api/scraper/auth/login` - Login with credentials
- `POST /api/scraper/auth/refresh` - Refresh access token

### User Management (Auth Required)

- `GET /api/scraper/auth/me` - Get current user info
- `GET /api/scraper/auth/users` - List users (superuser only)

### Health & Monitoring (No Auth Required)

- `GET /api/scraper/health` - Health check with database status
- `GET /api/scraper/ping` - Simple ping endpoint

### Scraper Jobs (Auth Required - STUBS)

These endpoints are placeholders and will be fully implemented in Phase 2:

- `POST /api/scraper/jobs` - Create scraper job
- `GET /api/scraper/jobs` - List jobs
- `GET /api/scraper/jobs/{id}` - Get job details
- `POST /api/scraper/jobs/{id}/control` - Control job (start/pause/stop)
- `GET /api/scraper/jobs/{id}/logs` - Get job logs
- `GET /api/scraper/jobs/{id}/results` - Get job results
- `DELETE /api/scraper/jobs/{id}` - Delete job
- `GET /api/scraper/stats` - Get statistics

## Example: Complete Authentication Flow

```bash
# 1. Register
curl -X POST http://localhost:3010/api/scraper/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "mysecurepass123",
    "full_name": "John Doe"
  }' | jq

# Save the access_token from response

# 2. Login (if needed later)
curl -X POST http://localhost:3010/api/scraper/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "mysecurepass123"
  }' | jq

# 3. Use token to access protected endpoints
TOKEN="your-access-token-here"

curl http://localhost:3010/api/scraper/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Refresh token when it expires
curl -X POST http://localhost:3010/api/scraper/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "your-refresh-token-here"
  }' | jq
```

## Docker Commands Cheat Sheet

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f api
docker-compose logs -f celery-worker

# Restart a service
docker-compose restart api

# Enter API container
docker-compose exec api bash

# Run migrations in container
docker-compose exec api alembic upgrade head

# Check database
docker-compose exec postgres psql -U scraper_user -d scraper_db

# Clear volumes (WARNING: deletes data)
docker-compose down -v
```

## Troubleshooting

### Database Connection Failed

- Check if PostgreSQL is running: `docker-compose ps postgres`
- Check DATABASE_URL in .env file
- Run migrations: `alembic upgrade head`

### Import Errors

- Make sure you're in the project root directory
- Check that PYTHONPATH includes the project root
- Try: `export PYTHONPATH="${PYTHONPATH}:${PWD}"`

### Token Invalid/Expired

- Access tokens expire after 60 minutes (configurable)
- Use refresh token to get new access token
- Generate new SECRET_KEY if tokens from old key

### Port Already in Use

- Change API_PORT in .env
- Or stop the service using the port
- Check with: `lsof -i :3010`

## Next Steps

Phase 2 will implement:
- Complete job creation and management
- Background job processing with Celery
- Job queue and status tracking
- Log streaming and storage
- Result collection and export
- Webhook notifications
- Scheduling system
- Integration with existing scraper

## File Structure

```
agar/
├── api/                              # API layer
│   ├── main.py                       # FastAPI app
│   ├── config.py                     # Settings
│   ├── dependencies.py               # DI
│   ├── auth/                         # Authentication
│   ├── database/                     # Database layer
│   ├── middleware/                   # Middleware
│   ├── routes/                       # API endpoints
│   └── schemas/                      # Pydantic models
├── core/                             # Existing scraper
├── config/                           # Scraper configs
├── .env                              # Environment variables
├── alembic.ini                       # Alembic config
├── docker-compose.yml                # Docker services
└── requirements.txt                  # Dependencies
```

## Support

For issues or questions:
- Check the comprehensive documentation in `docs/`
- Review the API specification provided by the frontend team
- Check Docker logs for error messages
- Ensure all dependencies are installed

## Security Notes

- **IMPORTANT**: Change SECRET_KEY in production!
- Use strong passwords (min 8 characters)
- Enable HTTPS in production
- Configure CORS_ORIGINS appropriately
- Use environment variables for sensitive data
- Never commit .env files to version control
