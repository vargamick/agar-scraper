# 3DN Scraper API

RESTful API for managing web scraping jobs, scheduling, and results.

## Quick Start

See [API_QUICKSTART.md](../docs/API_QUICKSTART.md) for detailed setup instructions.

### Docker (Recommended)

```bash
# Copy environment template
cp .env.api.template .env

# Edit .env and set SECRET_KEY
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Check health
curl http://localhost:3010/api/scraper/health
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.api.template .env
# Edit .env file

# Run migrations
alembic upgrade head

# Start API
uvicorn api.main:app --reload --port 3001
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:3010/api/scraper/docs
- **ReDoc**: http://localhost:3010/api/scraper/redoc

## Architecture

```
api/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── dependencies.py      # Dependency injection
├── auth/                # Authentication (password, JWT)
├── database/            # Database layer (models, repos, migrations)
├── middleware/          # Request/response middleware
├── routes/              # API endpoints
└── schemas/             # Pydantic request/response models
```

## Authentication

All scraper endpoints require Bearer token authentication:

```bash
# Register
curl -X POST http://localhost:3010/api/scraper/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "securepass123"}'

# Use token
curl http://localhost:3010/api/scraper/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Database

The API uses SQLAlchemy ORM with support for:
- **PostgreSQL** (recommended for production)
- **SQLite** (good for development)

### Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

Key configuration variables (see `.env.api.template`):

- `DATABASE_URL` - Database connection string
- `SECRET_KEY` - JWT secret key (MUST be set in production)
- `REDIS_URL` - Redis connection for job queue
- `API_PORT` - API server port (default: 3001)
- `ENVIRONMENT` - Environment mode (development/production)

## Current Status

✅ **Phase 1 Complete**:
- Database models and migrations
- User authentication with JWT
- Health check endpoints
- Docker orchestration

⏳ **Phase 2 (Pending)**:
- Job creation and management
- Background job processing
- Result collection and export
- Webhook notifications
- Scheduling system

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=api --cov-report=html

# Run specific test
pytest tests/api/test_auth.py -v
```

### Code Style

```bash
# Format code
black api/

# Lint
ruff check api/

# Type checking
mypy api/
```

## Documentation

- [API Quick Start Guide](../docs/API_QUICKSTART.md)
- [Implementation Summary](../docs/API_IMPLEMENTATION_SUMMARY.md)
- [API Specification](../docs/COMPREHENSIVE_USER_GUIDE_PART1.md) (from frontend)

## Support

For issues or questions, see the documentation in the `docs/` directory.
