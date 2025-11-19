# Quick Start Deployment Guide

This is a condensed guide for deploying to AWS LightSail. For detailed information, see [LIGHTSAIL_DEPLOYMENT.md](../docs/LIGHTSAIL_DEPLOYMENT.md).

## Prerequisites

- AWS LightSail instance (4GB+ RAM, Ubuntu 22.04)
- Domain pointing to instance
- SSH access

## Step-by-Step Deployment

### 1. SSH into LightSail Instance

```bash
ssh ubuntu@your-instance-ip
```

### 2. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
sudo apt install docker-compose -y
```

Log out and back in.

### 3. Clone Repository

```bash
mkdir -p ~/apps && cd ~/apps
git clone https://github.com/vargamick/agar-scraper.git
cd agar-scraper
```

### 4. Configure Environment

```bash
# Generate secrets
python3 deployment/scripts/generate_secret.py

# Copy production template
cp deployment/production.env .env

# Edit with your values
nano .env
```

Update these critical values in `.env`:
- `SECRET_KEY` - from generate_secret.py
- `POSTGRES_PASSWORD` - from generate_secret.py
- `DATABASE_URL` - update with new password
- `S3_ACCESS_KEY_ID` - your AWS key
- `S3_SECRET_ACCESS_KEY` - your AWS secret
- `CORS_ORIGINS` - add your domain

### 5. Deploy Application

```bash
./deployment/scripts/deploy.sh
```

### 6. Configure Nginx

```bash
sudo apt install nginx -y
sudo cp deployment/nginx/askagar.conf /etc/nginx/sites-available/askagar

# Edit domain name if needed
sudo nano /etc/nginx/sites-available/askagar

# Enable site
sudo ln -s /etc/nginx/sites-available/askagar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Install SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d askagar.com -d www.askagar.com
```

### 8. Configure Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 9. Create Admin User

```bash
docker-compose -f docker-compose.prod.yml exec api python /app/scripts/utilities/create_admin.py
```

### 10. Test Deployment

```bash
./deployment/scripts/test_deployment.sh https://askagar.com
```

## Verification

Visit these URLs to verify:

- **UI**: https://askagar.com
- **API Docs**: https://askagar.com/api/scraper/docs
- **Health**: https://askagar.com/api/scraper/health

## Maintenance Commands

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Update Application
```bash
git pull origin master
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup Database
```bash
./deployment/scripts/backup.sh
```

### Monitor Services
```bash
./deployment/scripts/monitor.sh
```

## Troubleshooting

### Container won't start
```bash
docker-compose -f docker-compose.prod.yml logs <service-name>
```

### API not responding
```bash
docker-compose -f docker-compose.prod.yml restart api
curl http://localhost:3010/api/scraper/health
```

### Database connection issues
```bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U scraper_user -d scraper_db
```

## Directory Structure

```
~/apps/agar-scraper/
├── .env                    # Production config (DO NOT COMMIT)
├── docker-compose.prod.yml # Production compose file
├── deployment/             # Deployment scripts & configs
│   ├── scripts/
│   │   ├── deploy.sh
│   │   ├── backup.sh
│   │   ├── monitor.sh
│   │   └── generate_secret.py
│   └── nginx/
│       └── askagar.conf
├── scraper_data/          # Scraped data
├── logs/                  # Application logs
└── config/                # Client configurations
```

## Need Help?

See the full deployment guide: [LIGHTSAIL_DEPLOYMENT.md](../docs/LIGHTSAIL_DEPLOYMENT.md)
