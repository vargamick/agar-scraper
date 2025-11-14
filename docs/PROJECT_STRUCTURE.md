# Project Structure

This document outlines the organization of the 3DN Scraper project.

## Root Directory

```
agar/
├── README.md                    # Main project README
├── PROJECT_STRUCTURE.md         # This file - project organization guide
├── main.py                      # Main entry point for legacy scraper
├── requirements.txt             # Python dependencies
├── alembic.ini                 # Database migration configuration
├── docker-compose.yml          # Docker orchestration
│
├── api/                        # FastAPI REST API
│   ├── auth/                   # Authentication system
│   ├── database/               # Database models and connections
│   ├── jobs/                   # Job management and Celery tasks
│   ├── routes/                 # API endpoints
│   ├── scraper/                # Scraper adapter for API
│   ├── schemas/                # Pydantic schemas
│   ├── config.py               # API configuration
│   └── main.py                 # FastAPI application entry point
│
├── config/                     # Configuration system
│   ├── base_config.py          # Base configuration class
│   ├── config_loader.py        # Dynamic client loader
│   └── clients/                # Client-specific configurations
│       └── agar/               # Agar client configuration
│
├── core/                       # Core scraping modules
│   ├── category_scraper.py     # Category discovery
│   ├── product_collector.py    # Product URL collection
│   ├── product_scraper.py      # Product detail extraction
│   ├── product_pdf_scraper.py  # PDF link extraction
│   ├── pdf_downloader.py       # PDF file download
│   └── utils.py                # Shared utilities
│
├── strategies/                 # Strategy interfaces
│   └── base_strategy.py        # Base extraction strategy
│
├── data/                       # Static data files
│   └── categories.json         # Category data
│
├── docker/                     # Docker configuration
│   ├── Dockerfile              # Container image definition
│   ├── .dockerignore           # Docker ignore patterns
│   ├── .env.template           # Environment template for legacy scraper
│   └── .env.api.template       # Environment template for API
│
├── docs/                       # Documentation
│   ├── README.md               # Documentation index
│   ├── api/                    # API documentation
│   │   ├── README_API.md       # API quick reference
│   │   ├── API_QUICKSTART.md   # API setup guide
│   │   ├── TESTING_GUIDE.md    # Testing instructions
│   │   └── ...
│   ├── quickstart/             # Getting started guides
│   │   ├── QUICK_START.md      # 5-minute quick start
│   │   ├── DOCKER_QUICKSTART.md # Docker setup
│   │   └── ...
│   ├── deployment/             # Deployment guides
│   ├── architecture/           # Architecture documentation
│   ├── migration/              # Migration history
│   └── legacy/                 # Legacy scraper docs
│
├── scripts/                    # Utility scripts
│   ├── start-and-test.sh       # Start services and run tests
│   ├── test-api.sh             # Run API tests
│   ├── setup_venv.sh           # Python environment setup
│   └── activate.sh             # Activate virtual environment
│
├── agar_scrapes/               # Legacy scraper output (generated)
├── scraper_data/               # API scraper output (generated)
│   ├── jobs/                   # Job-specific data
│   └── exports/                # Exported results
│
└── logs/                       # Application logs (generated)
```

## Key Directories

### Source Code

- **`api/`** - Complete FastAPI REST API implementation
- **`core/`** - Reusable scraping modules (legacy and API)
- **`config/`** - Configuration system for multiple clients
- **`strategies/`** - Extraction strategy interfaces

### Configuration

- **`docker/`** - All Docker-related files (Dockerfile, .dockerignore, .env templates)
- **`.env`** - Active environment configuration (in root, not committed)
- **`alembic.ini`** - Database migration settings
- **`docker-compose.yml`** - Service orchestration

### Documentation

- **`docs/`** - All project documentation organized by topic
  - `api/` - API implementation and usage
  - `quickstart/` - Getting started guides
  - `deployment/` - Deployment instructions
  - `architecture/` - System design
  - `migration/` - Project history
  - `legacy/` - Legacy scraper docs

### Scripts

- **`scripts/`** - All executable scripts
  - Shell scripts for starting, testing, setup
  - Python utility scripts (future)

### Data

- **`data/`** - Static data files used by scrapers
- **`agar_scrapes/`** - Output from legacy CLI scraper
- **`scraper_data/`** - Output from API-based scraper
- **`logs/`** - Application and scraper logs

## Quick Start

### For API Development
```bash
# Start all services
./scripts/start-and-test.sh

# Run tests
./scripts/test-api.sh

# View API docs
open http://localhost:3010/api/scraper/docs
```

### For Legacy Scraper
```bash
# Test scrape
python main.py --client agar --test

# Full scrape
python main.py --client agar --full
```

### For Documentation
```bash
# View documentation index
cat docs/README.md

# Quick start guide
cat docs/quickstart/QUICK_START.md
```

## Environment Files

| File | Location | Purpose |
|------|----------|---------|
| `.env` | Root | Active environment config (created by user) |
| `.env.template` | `docker/` | Template for legacy scraper |
| `.env.api.template` | `docker/` | Template for API services |

## Generated Directories

These directories are created automatically during operation:

- `agar_scrapes/` - Legacy scraper output
- `scraper_data/` - API scraper output
- `logs/` - Application logs
- `__pycache__/` - Python bytecode cache
- `venv/` - Python virtual environment (if using local installation)

## Configuration Files in Root

Only essential configuration files remain in the root:

- `README.md` - Project overview
- `PROJECT_STRUCTURE.md` - This file
- `main.py` - CLI entry point
- `requirements.txt` - Dependencies
- `alembic.ini` - Database migrations
- `docker-compose.yml` - Service orchestration
- `.env` - Environment config (user-created, not committed)
- `.gitignore` - Git ignore rules
- `.python-version` - Python version specification
- `__init__.py` - Python package marker

## Notes

- All documentation moved to `docs/` with organized subdirectories
- All scripts moved to `scripts/` directory
- All Docker files moved to `docker/` directory
- All data files moved to `data/` directory
- Project root is clean and focused on essential configuration only

---

**Last Updated**: 2025-01-12
**Version**: 1.0.0
