#!/bin/bash
# Monitoring script for Agar Scraper
# Checks service health and sends alerts if issues detected

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$PROJECT_DIR/logs/monitor.log"
ALERT_EMAIL="${ALERT_EMAIL:-}"  # Set via environment variable

# API endpoint
API_URL="http://localhost:3010/api/scraper"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if service is healthy
check_health() {
    local service="$1"
    local url="$2"

    if curl -sf "$url" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check container status
check_container() {
    local container="$1"

    if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
        return 0
    else
        return 1
    fi
}

# Send alert (email or webhook)
send_alert() {
    local subject="$1"
    local message="$2"

    log "ALERT: $subject - $message"

    # Send email if configured
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "[Agar Scraper] $subject" "$ALERT_EMAIL" 2>/dev/null || true
    fi

    # Add webhook integration here if needed
}

# Main monitoring loop
log "Starting monitoring check..."

cd "$PROJECT_DIR" || exit 1

# Check API health
if check_health "API" "${API_URL}/health"; then
    log "✓ API is healthy"
else
    send_alert "API Down" "API health check failed at ${API_URL}/health"
fi

# Check containers
CONTAINERS=("scraper-postgres" "scraper-redis" "crawl4ai-service" "scraper-api" "scraper-celery-worker")

for container in "${CONTAINERS[@]}"; do
    if check_container "$container"; then
        log "✓ Container $container is running"
    else
        send_alert "Container Down" "Container $container is not running"
    fi
done

# Check disk space
DISK_USAGE=$(df -h "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    send_alert "Disk Space Warning" "Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEMORY_USAGE" -gt 90 ]; then
    send_alert "Memory Warning" "Memory usage is at ${MEMORY_USAGE}%"
fi

# Check for failed jobs (requires database access)
FAILED_JOBS=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U scraper_user -d scraper_db -t -c "SELECT COUNT(*) FROM jobs WHERE status='failed' AND updated_at > NOW() - INTERVAL '1 hour';" 2>/dev/null | xargs)

if [ -n "$FAILED_JOBS" ] && [ "$FAILED_JOBS" -gt 5 ]; then
    send_alert "Multiple Failed Jobs" "$FAILED_JOBS jobs failed in the last hour"
fi

log "Monitoring check complete"
