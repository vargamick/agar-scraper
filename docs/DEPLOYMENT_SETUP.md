# Agar Scraper - GitHub Deployment Setup

This guide provides the complete setup for deploying the Agar scraper application from GitHub to your AWS LightSail server.

---

## 1. SSH Deploy Key

### Public Key (Add to GitHub)
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICsaYmwYW+0uNZcYmPOdSrq11vXGUYiSA+/gbu//D3Ty agar-scraper-deployment
```

### Private Key (Stored Securely - NOT in Git)
**NOTE**: The private key has been provided to you separately via secure channel.
**NEVER commit private keys to Git!**

The private key file should be saved as `/tmp/agar_deploy_key` on your local machine.

---

## 2. GitHub Repository Setup

### A. Add Deploy Key to GitHub

1. Go to your GitHub repository settings
2. Navigate to: **Settings** → **Deploy keys** → **Add deploy key**
3. Configure the deploy key:
   - **Title**: `LightSail Production Server`
   - **Key**: Paste the **Public Key** from above
   - **Allow write access**: ❌ Leave unchecked (read-only is sufficient)
4. Click **Add key**

### B. Repository Information
- **Repository URL (HTTPS)**: `https://github.com/YOUR_USERNAME/agar.git`
- **Repository URL (SSH)**: `git@github.com:YOUR_USERNAME/agar.git`

---

## 3. LightSail Server Setup

### A. Install Git (if not already installed)
```bash
sudo apt update
sudo apt install -y git
```

### B. Create Deployment User (Recommended)
```bash
# Create dedicated deployment user
sudo useradd -m -s /bin/bash agar-deploy

# Switch to deployment user
sudo su - agar-deploy
```

### C. Set Up SSH Key on Server
```bash
# Create .ssh directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Create private key file
# Copy the private key that was provided to you separately
nano ~/.ssh/agar_deploy_key
# Paste the private key content and save

# Set correct permissions
chmod 600 ~/.ssh/agar_deploy_key

# Configure SSH to use this key for GitHub
cat > ~/.ssh/config << 'EOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/agar_deploy_key
    IdentitiesOnly yes
    StrictHostKeyChecking no
EOF

chmod 600 ~/.ssh/config
```

### D. Test SSH Connection to GitHub
```bash
ssh -T git@github.com
```

Expected output:
```
Hi YOUR_USERNAME! You've successfully authenticated, but GitHub does not provide shell access.
```

---

## 4. Clone Repository

```bash
# Choose deployment location
cd /opt  # or /home/agar-deploy or wherever you prefer

# Clone repository
git clone git@github.com:YOUR_USERNAME/agar.git

# Navigate to project
cd agar

# Verify clone
git status
git log -1
```

---

## 5. Install Dependencies

### A. Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Verify Docker installation
docker --version
docker-compose --version
```

### B. Install Docker Compose (if not included)
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

---

## 6. Configure Environment

### A. Create Environment File
```bash
# Copy example environment file
cp .env.example .env

# Edit environment variables
nano .env
```

### B. Required Environment Variables
```env
# Database
POSTGRES_DB=scraper_db
POSTGRES_USER=scraper_user
POSTGRES_PASSWORD=<STRONG_PASSWORD_HERE>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# API
API_SECRET_KEY=<GENERATE_STRONG_SECRET_KEY>
API_HOST=0.0.0.0
API_PORT=3010

# JWT
JWT_SECRET_KEY=<GENERATE_STRONG_JWT_SECRET>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Output
OUTPUT_BASE_PATH=/app/scraper_data
```

### C. Generate Secrets
```bash
# Generate API secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 7. Deploy Application

### A. Build and Start Services
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### B. Initialize Database
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create default user
docker-compose exec api python -c "
from api.database.connection import get_db_manager
from api.database.models import User
from api.auth.password import get_password_hash
import uuid

db = get_db_manager()
session = next(db.get_session())

user = User(
    id=uuid.uuid4(),
    username='admin',
    email='admin@agar.local',
    full_name='Admin User',
    hashed_password=get_password_hash('CHANGE_THIS_PASSWORD'),
    is_active=True,
    is_superuser=True
)

session.add(user)
session.commit()
print('Admin user created')
"
```

---

## 8. Set Up Automatic Updates

### A. Create Update Script
```bash
cat > /opt/agar/scripts/deploy.sh << 'EOF'
#!/bin/bash

# Deployment script for Agar scraper
set -e

echo "==== Starting deployment ===="

# Navigate to project directory
cd /opt/agar

# Pull latest changes
echo "Pulling latest code from GitHub..."
git pull origin main

# Rebuild containers
echo "Rebuilding Docker containers..."
docker-compose build --no-cache

# Restart services
echo "Restarting services..."
docker-compose down
docker-compose up -d

# Run migrations
echo "Running database migrations..."
docker-compose exec -T api alembic upgrade head

# Show status
echo "Checking service status..."
docker-compose ps

echo "==== Deployment complete ===="
EOF

chmod +x /opt/agar/scripts/deploy.sh
```

### B. Manual Deployment
```bash
cd /opt/agar
./scripts/deploy.sh
```

### C. Set Up GitHub Webhook (Optional)
For automatic deployments on push, you can:
1. Set up a webhook listener service on your server
2. Use GitHub Actions to SSH into your server and run the deploy script
3. Use a CI/CD tool like Jenkins, GitLab CI, or CircleCI

---

## 9. Firewall Configuration

### A. Open Required Ports
```bash
# Allow HTTP (if using reverse proxy)
sudo ufw allow 80/tcp

# Allow HTTPS (if using SSL)
sudo ufw allow 443/tcp

# Allow API port (or use reverse proxy)
sudo ufw allow 3010/tcp

# Enable firewall
sudo ufw enable
```

### B. Configure Reverse Proxy (Nginx - Recommended)
```bash
# Install Nginx
sudo apt install -y nginx

# Create configuration
sudo nano /etc/nginx/sites-available/agar-api
```

Nginx configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/agar-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 10. Monitoring and Maintenance

### A. View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f postgres
```

### B. Check Service Status
```bash
docker-compose ps
```

### C. Restart Services
```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
```

### D. Database Backup
```bash
# Create backup script
cat > /opt/agar/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/agar/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

docker-compose exec -T postgres pg_dump -U scraper_user scraper_db > \
  $BACKUP_DIR/backup_$TIMESTAMP.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql" -mtime +7 -delete

echo "Backup completed: backup_$TIMESTAMP.sql"
EOF

chmod +x /opt/agar/scripts/backup.sh
```

Set up daily backups with cron:
```bash
crontab -e
```

Add:
```
0 2 * * * /opt/agar/scripts/backup.sh
```

---

## 11. Troubleshooting

### A. Container Issues
```bash
# Check container logs
docker-compose logs [service-name]

# Restart containers
docker-compose restart

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### B. Permission Issues
```bash
# Fix ownership
sudo chown -R agar-deploy:agar-deploy /opt/agar

# Fix Docker permissions
sudo usermod -aG docker agar-deploy
newgrp docker
```

### C. Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test database connection
docker-compose exec postgres psql -U scraper_user -d scraper_db -c "SELECT 1;"
```

### D. Git Issues
```bash
# Reset local changes
git reset --hard origin/main

# Test SSH connection
ssh -T git@github.com

# Re-configure SSH key
chmod 600 ~/.ssh/agar_deploy_key
```

---

## 12. Security Checklist

- [ ] Change default admin password
- [ ] Use strong secrets for API_SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure firewall (UFW)
- [ ] Set up SSL/TLS with Let's Encrypt
- [ ] Keep SSH private key secure (600 permissions)
- [ ] Regularly update Docker images
- [ ] Set up automated backups
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for sensitive data
- [ ] Never commit .env file to repository

---

## 13. Quick Reference Commands

### Deployment
```bash
cd /opt/agar
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

### Status Check
```bash
docker-compose ps
docker-compose logs --tail 50
```

### Restart
```bash
docker-compose restart
```

### Stop
```bash
docker-compose down
```

### Full Rebuild
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review documentation in `/docs` directory
- Check GitHub issues

---

**Generated**: 2025-11-13
**Key Type**: ED25519
**Key Purpose**: Read-only deployment from GitHub
