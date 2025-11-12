# Docker Deployment Guide

This guide covers deploying the Agar scraper using Docker with a separate Crawl4AI service container.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Crawl4AI Docker Service](#crawl4ai-docker-service)
4. [Agar Scraper Configuration](#agar-scraper-configuration)
5. [Deployment Steps](#deployment-steps)
6. [Usage Examples](#usage-examples)
7. [Monitoring and Logs](#monitoring-and-logs)
8. [Troubleshooting](#troubleshooting)
9. [Production Considerations](#production-considerations)

## Architecture Overview

The deployment uses two Docker containers orchestrated with Docker Compose:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                           │
│  ┌──────────────────┐         ┌───────────────────────┐ │
│  │  Crawl4AI        │         │   Agar Scraper        │ │
│  │  Service         │◄────────│   Application         │ │
│  │                  │         │                       │ │
│  │  Port: 11235     │         │   Depends on Crawl4AI │ │
│  │  (Internal)      │         │                       │ │
│  └──────────────────┘         └───────────────────────┘ │
│         │                                │               │
└─────────┼────────────────────────────────┼───────────────┘
          │                                │
          │ (Optional)                     │
          │ Port Mapping                   ▼
          ▼                          Host Volumes:
   localhost:11235                   - ./agar_scrapes
   (For debugging)                   - ./logs
                                     - ./config
```

### Key Components

1. **Crawl4AI Service**: 
   - Official Docker image: `unclecode/crawl4ai:latest`
   - Provides web scraping engine via REST API
   - Internal port: 11235
   - Requires 1GB shared memory

2. **Agar Scraper Service**:
   - Custom Docker image built from this repository
   - Communicates with Crawl4AI via internal network
   - Mounts volumes for persistence

## Prerequisites

### Required Software

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

### Installation

**macOS:**
```bash
# Install Docker Desktop
brew install --cask docker
```

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Windows:**
- Download and install Docker Desktop from https://www.docker.com/products/docker-desktop

### Verify Installation

```bash
docker --version
# Docker version 24.0.0 or higher

docker-compose --version
# Docker Compose version v2.20.0 or higher
```

## Crawl4AI Docker Service

### About Crawl4AI Docker Image

The official Crawl4AI Docker image provides:

- Pre-configured browser automation environment
- Chromium browser with necessary dependencies
- REST API interface on port 11235
- Built-in caching and optimization
- Playground UI for testing (optional)

### Configuration Options

The Crawl4AI service is configured in `docker-compose.yml`:

```yaml
crawl4ai:
  image: unclecode/crawl4ai:latest
  container_name: crawl4ai-service
  ports:
    - "11235:11235"  # Optional: Only expose for debugging
  environment:
    - PYTHONUNBUFFERED=1
  shm_size: 1g  # Required for browser operation
  restart: unless-stopped
```

### Resource Requirements

- **Memory**: Minimum 2GB RAM, 4GB recommended
- **Disk Space**: ~1GB for image, additional space for cache
- **CPU**: 2+ cores recommended for concurrent scraping

## Agar Scraper Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Edit `.env` and configure:

```bash
# Client to scrape
ACTIVE_CLIENT=agar

# Crawl4AI API endpoint (automatically set in docker-compose)
# Only needed if using external Crawl4AI service
# CRAWL4AI_API_BASE_URL=http://crawl4ai:11235

# Logging
LOG_LEVEL=INFO
```

### Volume Mounts

The scraper container mounts three directories:

1. **Output Directory** (`./agar_scrapes`): 
   - Stores all scraped data
   - Persists between container restarts
   - Structure: `agar_scrapes/[run_id]/`

2. **Logs Directory** (`./logs`):
   - Application logs
   - Error tracking

3. **Config Directory** (`./config`):
   - Read-only mount
   - Allows configuration updates without rebuild

## Deployment Steps

### 1. Clone and Prepare

```bash
# Clone repository (if not already done)
git clone <repository-url>
cd agar

# Verify files exist
ls -la Dockerfile docker-compose.yml .env.template
```

### 2. Configure Environment

```bash
# Create environment file
cp .env.template .env

# Edit if needed (optional for basic deployment)
nano .env
```

### 3. Build and Start Services

```bash
# Build the Agar scraper image and start all services
docker-compose up -d

# This will:
# 1. Pull the Crawl4AI image (if not present)
# 2. Build the Agar scraper image
# 3. Start both services
# 4. Wait for Crawl4AI to be healthy before starting scraper
```

### 4. Verify Deployment

```bash
# Check service status
docker-compose ps

# Should show both services as "Up" and healthy:
# NAME                IMAGE                        STATUS
# crawl4ai-service    unclecode/crawl4ai:latest   Up (healthy)
# agar-scraper        agar-scraper                Up

# Check Crawl4AI service
curl http://localhost:11235/health
# Should return: {"status":"healthy"}

# View logs
docker-compose logs -f
```

### 5. Run a Test Scrape

```bash
# Run test scrape (2 categories, 5 products)
docker-compose run --rm agar-scraper python main.py --client agar --test

# Or use docker exec if container is already running
docker exec -it agar-scraper python main.py --client agar --test
```

## Usage Examples

### Running Different Scrape Modes

**Test Mode** (2 categories, 5 products):
```bash
docker-compose run --rm agar-scraper python main.py --client agar --test
```

**Full Scrape** (all categories and products):
```bash
docker-compose run --rm agar-scraper python main.py --client agar --full
```

### Interactive Shell Access

```bash
# Access the scraper container
docker exec -it agar-scraper /bin/bash

# Now you can run commands inside the container
python main.py --client agar --test
ls -la agar_scrapes/
exit
```

### Accessing Crawl4AI Playground

If you want to test Crawl4AI directly:

```bash
# The playground is available at:
# http://localhost:11235/playground

# Or test the API directly:
curl http://localhost:11235/health
```

### Running as One-Off Command

```bash
# Run and auto-remove container after completion
docker-compose run --rm agar-scraper python main.py --client agar --test
```

### Background Scraping

```bash
# Update docker-compose.yml to set the command:
# Uncomment and modify this line in the agar-scraper service:
# command: ["python", "main.py", "--client", "agar", "--full"]

# Then restart:
docker-compose up -d agar-scraper

# Monitor progress:
docker-compose logs -f agar-scraper
```

## Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f agar-scraper
docker-compose logs -f crawl4ai

# Last 100 lines
docker-compose logs --tail=100 agar-scraper

# Since specific time
docker-compose logs --since="2024-01-01T00:00:00" agar-scraper
```

### Check Resource Usage

```bash
# Container stats
docker stats

# Specific container
docker stats agar-scraper crawl4ai-service
```

### Health Checks

```bash
# Check Crawl4AI health
docker exec crawl4ai-service curl -f http://localhost:11235/health

# Check scraper health
docker exec agar-scraper python -c "import sys; sys.exit(0)"
```

## Troubleshooting

### Common Issues

#### 1. Crawl4AI Service Not Starting

**Symptom**: `crawl4ai-service` exits immediately

**Solution**:
```bash
# Check logs
docker-compose logs crawl4ai

# Increase shared memory
# Edit docker-compose.yml:
# shm_size: 2g  # Increase from 1g

# Restart
docker-compose down
docker-compose up -d
```

#### 2. Scraper Can't Connect to Crawl4AI

**Symptom**: Connection refused errors

**Solution**:
```bash
# Verify Crawl4AI is healthy
docker-compose ps

# Check network connectivity
docker exec agar-scraper ping crawl4ai

# Verify environment variable
docker exec agar-scraper env | grep CRAWL4AI
# Should show: CRAWL4AI_API_BASE_URL=http://crawl4ai:11235

# Restart services
docker-compose restart
```

#### 3. Out of Disk Space

**Symptom**: Scraping fails, container can't write

**Solution**:
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Remove old scrape data
rm -rf agar_scrapes/agar*_TEST  # Keep only full scrapes
```

#### 4. Permission Issues on Mounted Volumes

**Symptom**: Can't write to mounted directories

**Solution**:
```bash
# Check permissions
ls -la agar_scrapes/ logs/

# Fix permissions
sudo chown -R $(id -u):$(id -g) agar_scrapes/ logs/

# Or run container with specific user (add to docker-compose.yml):
# user: "${UID}:${GID}"
```

#### 5. Port Already in Use

**Symptom**: `bind: address already in use`

**Solution**:
```bash
# Find what's using port 11235
lsof -i :11235
# or
netstat -an | grep 11235

# Kill the process or change port in docker-compose.yml:
# ports:
#   - "11236:11235"  # Map to different host port
```

### Debug Mode

To enable verbose logging:

```bash
# Edit .env file
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart agar-scraper

# View detailed logs
docker-compose logs -f agar-scraper
```

## Production Considerations

### Security

1. **Don't Expose Crawl4AI Port**:
   ```yaml
   # Remove this from docker-compose.yml in production:
   # ports:
   #   - "11235:11235"
   ```

2. **Use Secrets for Sensitive Data**:
   ```yaml
   # Use Docker secrets instead of environment variables
   secrets:
     - api_key
   ```

3. **Network Isolation**:
   ```yaml
   # Use custom network with restricted access
   networks:
     scraper-network:
       driver: bridge
       internal: true  # No external access
   ```

### Performance Optimization

1. **Resource Limits**:
   ```yaml
   agar-scraper:
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 4G
         reservations:
           memory: 2G
   ```

2. **Increase Concurrent Scraping**:
   - Modify client configuration to allow more concurrent requests
   - Ensure Crawl4AI has sufficient resources

3. **Enable Persistent Cache**:
   ```yaml
   volumes:
     - crawl4ai-cache:/root/.crawl4ai
   ```

### Monitoring

1. **Add Health Endpoints**:
   - Implement custom health checks in the scraper
   - Monitor with tools like Prometheus

2. **Log Aggregation**:
   - Use centralized logging (ELK, Splunk, etc.)
   - Configure Docker logging driver

3. **Alerts**:
   - Set up alerts for failures
   - Monitor disk usage and resource consumption

### Backup and Recovery

```bash
# Backup scraped data
tar -czf agar_scrapes_backup_$(date +%Y%m%d).tar.gz agar_scrapes/

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz config/

# Restore
tar -xzf agar_scrapes_backup_20240101.tar.gz
```

### Scaling

For high-volume scraping:

1. **Multiple Crawl4AI Instances**:
   ```yaml
   crawl4ai-1:
     image: unclecode/crawl4ai:latest
     # ...configuration...
   
   crawl4ai-2:
     image: unclecode/crawl4ai:latest
     # ...configuration...
   ```

2. **Load Balancer**:
   - Use nginx or HAProxy to distribute requests
   - Implement round-robin across Crawl4AI instances

3. **Queue System**:
   - Add Redis/RabbitMQ for job queuing
   - Scale scraper workers horizontally

## Maintenance

### Updating Services

```bash
# Pull latest Crawl4AI image
docker-compose pull crawl4ai

# Rebuild scraper (after code changes)
docker-compose build agar-scraper

# Restart with new images
docker-compose up -d
```

### Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: Deletes cached data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker system prune -a --volumes
```

### Scheduled Scraping

Use cron or scheduler to automate:

```bash
# Add to crontab
0 2 * * * cd /path/to/agar && docker-compose run --rm agar-scraper python main.py --client agar --full
```

## Additional Resources

- **Crawl4AI Documentation**: https://docs.crawl4ai.com
- **Crawl4AI GitHub**: https://github.com/unclecode/crawl4ai
- **Docker Documentation**: https://docs.docker.com
- **Docker Compose Reference**: https://docs.docker.com/compose

## Support

For issues with:
- **Agar Scraper**: Create an issue in this repository
- **Crawl4AI Service**: https://github.com/unclecode/crawl4ai/issues
- **Docker**: https://forums.docker.com

## Next Steps

1. Run a test scrape to verify deployment
2. Review output in `agar_scrapes/` directory
3. Configure monitoring and alerts
4. Set up automated scheduling if needed
5. Review security settings for production use
