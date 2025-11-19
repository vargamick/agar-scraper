#!/bin/bash
# Automated deployment script for AWS LightSail
# Run this script on the LightSail instance after initial setup

set -e  # Exit on error

echo "========================================="
echo "Agar Scraper - Deployment Script"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Do not run this script as root${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please create .env file from deployment/production.env"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Pull latest changes from git (optional)
if [ -d .git ]; then
    echo "Pulling latest changes from git..."
    git pull origin master || echo -e "${YELLOW}Warning: Could not pull from git${NC}"
    echo ""
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true
echo ""

# Build images
echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache
echo ""

# Start services
echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d
echo ""

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

MAX_WAIT=120
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker-compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
        echo -e "${GREEN}✓ Services are healthy${NC}"
        break
    fi
    echo "Waiting... ($WAITED/$MAX_WAIT seconds)"
    sleep 5
    WAITED=$((WAITED + 5))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo -e "${YELLOW}Warning: Services may not be fully healthy yet${NC}"
fi

echo ""

# Show status
echo "Container status:"
docker-compose -f docker-compose.prod.yml ps
echo ""

# Check health endpoint
echo "Checking API health..."
sleep 5
if curl -f http://localhost:3010/api/scraper/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${RED}✗ API is not responding${NC}"
    echo "Check logs with: docker-compose -f docker-compose.prod.yml logs api"
fi

echo ""
echo "========================================="
echo "Deployment complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure Nginx reverse proxy (if not done)"
echo "2. Set up SSL certificate with certbot"
echo "3. Create admin user:"
echo "   docker-compose -f docker-compose.prod.yml exec api python /app/scripts/utilities/create_admin.py"
echo ""
echo "View logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "Monitor status:"
echo "   docker-compose -f docker-compose.prod.yml ps"
echo ""
