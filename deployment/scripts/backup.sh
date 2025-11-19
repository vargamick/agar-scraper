#!/bin/bash
# Backup script for Agar Scraper
# Backs up database and scraper data

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/agar-scraper}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Agar Scraper Backup Script"
echo "========================================="
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

cd "$PROJECT_DIR" || exit 1

# Backup database
echo "Backing up PostgreSQL database..."
DB_BACKUP_FILE="$BACKUP_DIR/database_${TIMESTAMP}.sql"

docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
    -U scraper_user scraper_db > "$DB_BACKUP_FILE"

# Compress database backup
gzip "$DB_BACKUP_FILE"
echo -e "${GREEN}✓ Database backup complete: ${DB_BACKUP_FILE}.gz${NC}"

# Backup scraper data (jobs and exports)
echo ""
echo "Backing up scraper data..."
DATA_BACKUP_FILE="$BACKUP_DIR/scraper_data_${TIMESTAMP}.tar.gz"

tar -czf "$DATA_BACKUP_FILE" \
    -C "$PROJECT_DIR" \
    scraper_data/jobs \
    scraper_data/exports \
    2>/dev/null || true

echo -e "${GREEN}✓ Scraper data backup complete: ${DATA_BACKUP_FILE}${NC}"

# Backup configuration
echo ""
echo "Backing up configuration..."
CONFIG_BACKUP_FILE="$BACKUP_DIR/config_${TIMESTAMP}.tar.gz"

tar -czf "$CONFIG_BACKUP_FILE" \
    -C "$PROJECT_DIR" \
    .env \
    config/ \
    2>/dev/null || true

echo -e "${GREEN}✓ Configuration backup complete: ${CONFIG_BACKUP_FILE}${NC}"

# Clean up old backups
echo ""
echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
echo -e "${GREEN}✓ Old backups cleaned up${NC}"

# Display backup summary
echo ""
echo "========================================="
echo "Backup Summary"
echo "========================================="
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Files created:"
ls -lh "$BACKUP_DIR"/*_${TIMESTAMP}* 2>/dev/null || true
echo ""

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "Total backup size: $TOTAL_SIZE"
echo ""

# Upload to S3 (optional)
if [ "${S3_BACKUP_ENABLED:-false}" = "true" ]; then
    echo "Uploading backups to S3..."

    S3_BUCKET="${S3_BACKUP_BUCKET:-agar-backups}"
    S3_PREFIX="${S3_BACKUP_PREFIX:-backups/}"

    aws s3 sync "$BACKUP_DIR" "s3://${S3_BUCKET}/${S3_PREFIX}" \
        --exclude "*" \
        --include "*_${TIMESTAMP}*" \
        --region ap-southeast-2

    echo -e "${GREEN}✓ Backups uploaded to S3${NC}"
    echo ""
fi

echo -e "${GREEN}Backup complete!${NC}"
