# AWS LightSail Deployment Guide

## Overview

This guide will walk you through deploying the Agar Web Scraper to AWS LightSail as Docker containers, matching your local development setup.

## Prerequisites

- AWS LightSail instance (recommended: 4GB RAM minimum, 8GB+ for production)
- Domain name pointing to your LightSail instance (for AskAgar server)
- SSH access to the LightSail instance
- Docker and Docker Compose installed on LightSail instance

## Architecture

The deployment consists of 5 Docker containers:

1. **PostgreSQL** - Database for jobs, users, and scraping state
2. **Redis** - Job queue and caching
3. **Crawl4AI** - Web scraping engine
4. **API Server** - FastAPI application (port 3010)
5. **Celery Worker** - Background job processor
6. **UI Server** - Simple HTTP server for web interface (port 8080)

## Instance Specifications

### Recommended LightSail Plan

- **Instance Size**: 4GB RAM / 2 vCPUs minimum
- **Storage**: 80GB SSD minimum (for scraped data storage)
- **OS**: Ubuntu 22.04 LTS
- **Static IP**: Attached to instance

### Estimated Costs (Sydney Region)

- 4GB plan: ~$24/month
- 8GB plan: ~$48/month (recommended for production)
- Additional storage as needed

## Pre-Deployment Checklist

- [ ] LightSail instance created and running
- [ ] Static IP attached to instance
- [ ] SSH key configured for access
- [ ] Domain DNS configured (A record pointing to static IP)
- [ ] Firewall rules configured (ports 80, 443, 22)
- [ ] AWS credentials ready for S3 integration

## Installation Steps

### 1. Prepare LightSail Instance

SSH into your LightSail instance:

```bash
ssh ubuntu@your-instance-ip
```

Update system packages:

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installations
docker --version
docker-compose --version
```

Log out and back in for docker group membership to take effect.

### 3. Clone Repository

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone your repository
git clone https://github.com/vargamick/agar-scraper.git
cd agar-scraper
```

### 4. Configure Environment Variables

Copy and edit the production environment file:

```bash
cp deployment/production.env .env
nano .env
```

**Critical settings to update:**

```bash
# Set to production
ENVIRONMENT=production
DEBUG=false

# Generate a strong secret key (use the provided script)
SECRET_KEY=your-generated-secret-key-here

# Database (use strong passwords)
POSTGRES_PASSWORD=your-strong-db-password

# AWS S3 Configuration
S3_ENABLED=true
S3_BUCKET_NAME=agar-documentation
S3_REGION=ap-southeast-2
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key

# CORS - Add your domain
CORS_ORIGINS=https://askagar.com,https://www.askagar.com,http://localhost:8080
```

### 5. Generate Secret Key

Use the provided utility:

```bash
python3 deployment/scripts/generate_secret.py
```

Copy the output and paste into your `.env` file.

### 6. Configure Production Docker Compose

The repository includes a production-ready `docker-compose.prod.yml` file:

```bash
# Review the production configuration
cat docker-compose.prod.yml
```

Key differences from development:
- No exposed database/redis ports
- Proper restart policies
- Resource limits configured
- Health checks enabled
- Production-grade logging

### 7. Start Services

```bash
# Build and start all containers
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 8. Create Admin User

Once containers are running:

```bash
# Run admin creation script inside API container
docker-compose -f docker-compose.prod.yml exec api python /app/scripts/utilities/create_admin.py
```

Default credentials (change these immediately):
- Username: `admin`
- Password: `admin123`
- Email: `admin@example.com`

### 9. Configure Nginx Reverse Proxy

Install and configure Nginx:

```bash
sudo apt install nginx -y
```

Create site configuration:

```bash
sudo nano /etc/nginx/sites-available/askagar
```

Paste the configuration from `deployment/nginx/askagar.conf`

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/askagar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Install SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d askagar.com -d www.askagar.com
```

Follow the prompts to configure SSL.

### 11. Configure Firewall

```bash
# Allow required ports
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Post-Deployment

### Verify Deployment

1. **Health Check**: Visit `https://askagar.com/api/scraper/health`
2. **UI Access**: Visit `https://askagar.com`
3. **API Documentation**: Visit `https://askagar.com/api/scraper/docs`

### Test Scraping Job

```bash
# From your local machine or the server
./deployment/scripts/test_deployment.sh https://askagar.com
```

### Monitor Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f celery-worker

# Follow recent logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

## Maintenance

### Update Application

```bash
cd ~/apps/agar-scraper
git pull origin master
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup Database

```bash
# Create backup directory
mkdir -p ~/backups

# Backup PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
  -U scraper_user scraper_db > ~/backups/scraper_db_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql \
  -U scraper_user scraper_db < ~/backups/scraper_db_20250119_120000.sql
```

### View Resource Usage

```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df
```

### Clean Up Old Data

```bash
# Remove old scraped data (older than 30 days)
find ~/apps/agar-scraper/scraper_data -type f -mtime +30 -delete

# Clean up Docker resources
docker system prune -a
```

## Scaling Considerations

### Increase Celery Workers

Edit `docker-compose.prod.yml`:

```yaml
celery-worker:
  deploy:
    replicas: 3  # Run 3 worker instances
```

Then:

```bash
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=3
```

### Add More Storage

1. Create and attach a block storage volume in LightSail
2. Mount it to `/mnt/scraper-data`
3. Update docker-compose volumes to use the new path

### Database Performance

For high-volume scraping:

```bash
# Edit .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check environment variables
docker-compose -f docker-compose.prod.yml exec api env

# Restart individual service
docker-compose -f docker-compose.prod.yml restart api
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec api python -c \
  "from api.database import engine; print(engine.connect())"
```

### High Memory Usage

```bash
# Check memory usage
free -h
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

### SSL Certificate Renewal

Certbot auto-renews, but to manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

## Security Considerations

### Environment Variables

- Never commit `.env` to version control
- Use strong passwords for database
- Rotate SECRET_KEY periodically
- Restrict AWS IAM permissions to minimum required

### Network Security

- Keep firewall enabled
- Only expose necessary ports
- Use VPC/private networking if available
- Implement rate limiting at Nginx level

### Regular Updates

```bash
# Update system packages monthly
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Monitoring

### Set Up Log Monitoring

Create a systemd service to monitor critical errors:

```bash
sudo cp deployment/systemd/scraper-monitor.service /etc/systemd/system/
sudo systemctl enable scraper-monitor
sudo systemctl start scraper-monitor
```

### Basic Monitoring Script

```bash
# Create monitoring script
nano ~/monitor.sh
```

Paste from `deployment/scripts/monitor.sh` and make executable:

```bash
chmod +x ~/monitor.sh
```

Add to crontab:

```bash
crontab -e
# Add: */5 * * * * ~/monitor.sh
```

## Support and Documentation

- [API Documentation](API_DOCUMENTATION.md)
- [S3 Integration Guide](S3_INTEGRATION.md)
- [UI Guide](UI_GUIDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

## Quick Reference

### Useful Commands

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart service
docker-compose -f docker-compose.prod.yml restart api

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Execute command in container
docker-compose -f docker-compose.prod.yml exec api bash

# View running containers
docker-compose -f docker-compose.prod.yml ps
```

### Directory Structure

```
~/apps/agar-scraper/
├── scraper_data/        # Scraped data (jobs, exports)
├── logs/                # Application logs
├── config/              # Client configurations
├── deployment/          # Deployment scripts and configs
├── docker-compose.prod.yml
└── .env                 # Production environment variables
```
