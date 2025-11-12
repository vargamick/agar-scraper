# Docker Deployment - Quick Start Guide

Get the Agar scraper running with Docker in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 4GB+ RAM available
- 2GB+ free disk space

## Quick Start

### 1. Create Environment File

```bash
cp .env.template .env
```

The defaults work fine for Docker deployment.

### 2. Start Services

```bash
# Build and start both services
docker-compose up -d
```

This will:
- Pull the Crawl4AI Docker image (first time only)
- Build the Agar scraper image
- Start both services
- Wait for Crawl4AI to be healthy

### 3. Verify Services Are Running

```bash
# Check status
docker-compose ps

# Both services should show "Up"
# crawl4ai-service should show "(healthy)"
```

### 4. Run Test Scrape

```bash
# Test mode: 2 categories, 5 products
docker-compose run --rm agar-scraper python main.py --client agar --test
```

### 5. Check Results

```bash
# List scrape outputs
ls -la agar_scrapes/

# View latest scrape
cd agar_scrapes/agarScrape_*_TEST
ls -la
```

## Common Commands

### Run Full Scrape

```bash
docker-compose run --rm agar-scraper python main.py --client agar --full
```

### View Logs

```bash
# All services
docker-compose logs -f

# Just the scraper
docker-compose logs -f agar-scraper

# Just Crawl4AI
docker-compose logs -f crawl4ai
```

### Stop Services

```bash
docker-compose down
```

### Restart Services

```bash
docker-compose restart
```

### Access Container Shell

```bash
docker exec -it agar-scraper /bin/bash
```

## Troubleshooting

### Services Won't Start

```bash
# View logs for errors
docker-compose logs

# Try rebuilding
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Out of Memory

```bash
# Check resource usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Minimum: 4GB, Recommended: 8GB
```

### Can't Connect to Crawl4AI

```bash
# Verify Crawl4AI is running
curl http://localhost:11235/health

# Should return: {"status":"healthy"}

# If not, check Crawl4AI logs
docker-compose logs crawl4ai
```

### Permission Errors

```bash
# Fix output directory permissions
sudo chown -R $(id -u):$(id -g) agar_scrapes/ logs/
```

## Architecture

```
┌──────────────────┐         ┌───────────────────┐
│  Crawl4AI        │         │   Agar Scraper    │
│  (Port 11235)    │◄────────│   Application     │
│  unclecode/      │  HTTP   │   Custom Build    │
│  crawl4ai:latest │  API    │                   │
└──────────────────┘         └───────────────────┘
        │                              │
        │                              ▼
        │                         Host Volumes:
        │                         ./agar_scrapes
        ▼                         ./logs
  localhost:11235                 ./config
  (Optional debug)
```

## What's Running?

1. **Crawl4AI Service** (`crawl4ai-service`)
   - Official Docker image from unclecode/crawl4ai
   - Provides web scraping engine via REST API
   - Accessible at http://crawl4ai:11235 (internal network)
   - Optionally at http://localhost:11235 (for debugging)

2. **Agar Scraper** (`agar-scraper`)
   - Custom image built from this repository
   - Connects to Crawl4AI service automatically
   - Outputs data to mounted `./agar_scrapes` directory
   - Logs to mounted `./logs` directory

## Next Steps

- Read the full [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT_GUIDE.md)
- Set up [scheduled scraping](docs/DOCKER_DEPLOYMENT_GUIDE.md#scheduled-scraping)
- Configure [monitoring](docs/DOCKER_DEPLOYMENT_GUIDE.md#monitoring)
- Review [production considerations](docs/DOCKER_DEPLOYMENT_GUIDE.md#production-considerations)

## Need Help?

- **Full Documentation**: See `docs/DOCKER_DEPLOYMENT_GUIDE.md`
- **Configuration Guide**: See `docs/configuration-guide.md`
- **Troubleshooting**: See `docs/troubleshooting.md`
- **Crawl4AI Issues**: https://github.com/unclecode/crawl4ai/issues
