#!/bin/bash
###############################################################################
# End-to-End S3 Integration Test
#
# This script tests the complete workflow:
# 1. Setup AWS S3 bucket
# 2. Configure environment
# 3. Start Docker containers
# 4. Run a scrape job
# 5. Verify S3 upload
# 6. Query results from database
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Test configuration
TEST_BUCKET_NAME="${S3_BUCKET_NAME:-agar-documentation}"
TEST_REGION="${S3_REGION:-us-east-1}"
S3_PREFIX="${S3_PREFIX:-agar/}"
API_URL="http://localhost:3010"
TEST_USER="testuser"
TEST_PASS="testpass123"

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local max_attempts=30
    local attempt=0

    log_info "Waiting for service at $url..."

    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "Service is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done

    log_error "Service failed to become ready after $max_attempts attempts"
    return 1
}

###############################################################################
# Step 1: Pre-flight Checks
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  AWS S3 Integration - End-to-End Test"
echo "═══════════════════════════════════════════════════════════"
echo ""

log_info "Running pre-flight checks..."

# Check required commands
for cmd in docker docker-compose aws curl jq; do
    if ! command_exists "$cmd"; then
        log_error "Required command '$cmd' not found. Please install it first."
        exit 1
    fi
done

log_success "All required commands are available"

# Check AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$S3_ACCESS_KEY_ID" ]; then
    log_error "AWS credentials not found in environment"
    log_info "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
    log_info "Or configure AWS CLI with: aws configure"
    exit 1
fi

log_success "AWS credentials found"

###############################################################################
# Step 2: Create S3 Bucket
###############################################################################

echo ""
log_info "Step 2: Creating S3 bucket..."

# Check if bucket already exists
if aws s3 ls "s3://${TEST_BUCKET_NAME}" 2>/dev/null; then
    log_warning "Bucket ${TEST_BUCKET_NAME} already exists, using it"
else
    log_info "Creating bucket: ${TEST_BUCKET_NAME} in region ${TEST_REGION}"

    if [ "$TEST_REGION" = "us-east-1" ]; then
        # us-east-1 doesn't need LocationConstraint
        aws s3api create-bucket \
            --bucket "${TEST_BUCKET_NAME}" \
            --region "${TEST_REGION}"
    else
        aws s3api create-bucket \
            --bucket "${TEST_BUCKET_NAME}" \
            --region "${TEST_REGION}" \
            --create-bucket-configuration LocationConstraint="${TEST_REGION}"
    fi

    log_success "Bucket created successfully"
fi

# Verify bucket access
log_info "Verifying bucket access..."
if aws s3 ls "s3://${TEST_BUCKET_NAME}" >/dev/null 2>&1; then
    log_success "Bucket is accessible"
else
    log_error "Cannot access bucket. Check permissions."
    exit 1
fi

###############################################################################
# Step 3: Update Configuration
###############################################################################

echo ""
log_info "Step 3: Updating .env configuration..."

# Backup .env if it exists
if [ -f .env ]; then
    cp .env .env.backup.$(date +%s)
    log_info "Backed up existing .env file"
fi

# Update S3 configuration in .env
if grep -q "S3_BUCKET_NAME=" .env 2>/dev/null; then
    # Update existing value
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|S3_BUCKET_NAME=.*|S3_BUCKET_NAME=${TEST_BUCKET_NAME}|" .env
    else
        # Linux
        sed -i "s|S3_BUCKET_NAME=.*|S3_BUCKET_NAME=${TEST_BUCKET_NAME}|" .env
    fi
    log_success "Updated S3_BUCKET_NAME in .env"
else
    log_warning "S3_BUCKET_NAME not found in .env, configuration may be incomplete"
fi

# Display current S3 configuration
log_info "Current S3 configuration:"
grep -E "^S3_" .env | while read line; do
    # Mask the secret key
    if [[ $line == S3_SECRET_ACCESS_KEY=* ]]; then
        echo "  S3_SECRET_ACCESS_KEY=***MASKED***"
    else
        echo "  $line"
    fi
done

###############################################################################
# Step 4: Start Docker Containers
###############################################################################

echo ""
log_info "Step 4: Starting Docker containers..."

# Stop existing containers
log_info "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start containers
log_info "Building and starting containers..."
docker-compose up -d --build

# Wait for services to be ready
log_info "Waiting for services to start..."
sleep 5

# Check service health
log_info "Checking service health..."
wait_for_service "$API_URL/api/scraper/health"

# Check Celery worker
if ! docker-compose ps celery-worker | grep -q "Up"; then
    log_error "Celery worker is not running"
    docker-compose logs celery-worker
    exit 1
fi

log_success "All services are running"

###############################################################################
# Step 5: Authenticate
###############################################################################

echo ""
log_info "Step 5: Authenticating with API..."

# Login and get token
AUTH_RESPONSE=$(curl -s -X POST "$API_URL/api/scraper/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USER}\",\"password\":\"${TEST_PASS}\"}")

# Check if login was successful
if ! echo "$AUTH_RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
    log_error "Authentication failed"
    echo "$AUTH_RESPONSE" | jq .
    exit 1
fi

# Extract token
TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.data.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    log_error "Failed to get access token"
    echo "$AUTH_RESPONSE" | jq .
    exit 1
fi

log_success "Authentication successful"

###############################################################################
# Step 6: Create Scrape Job
###############################################################################

echo ""
log_info "Step 6: Creating scrape job..."

# Create job with S3 upload enabled
JOB_PAYLOAD=$(cat <<EOF
{
  "name": "S3 Integration Test - $(date +%Y%m%d_%H%M%S)",
  "description": "End-to-end test of S3 upload functionality",
  "type": "web",
  "config": {
    "startUrls": ["https://www.agar.com.au"],
    "maxPages": 50,
    "client_name": "agar",
    "test_mode": false,
    "save_screenshots": false,
    "crawlDepth": 2,
    "followLinks": true
  },
  "output": {
    "saveFiles": true,
    "fileFormat": "json",
    "uploadToS3": {
      "enabled": true,
      "uploadPdfs": true,
      "uploadScreenshots": false,
      "uploadCategories": true
    }
  }
}
EOF
)

# Submit job
JOB_RESPONSE=$(curl -s -X POST "$API_URL/api/scraper/jobs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$JOB_PAYLOAD")

# Check if job creation was successful
if ! echo "$JOB_RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
    log_error "Job creation failed"
    echo "$JOB_RESPONSE" | jq .
    exit 1
fi

# Extract job ID
JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.data.jobId')

if [ -z "$JOB_ID" ] || [ "$JOB_ID" = "null" ]; then
    log_error "Failed to get job ID"
    echo "$JOB_RESPONSE" | jq .
    exit 1
fi

log_success "Job created with ID: $JOB_ID"

###############################################################################
# Step 7: Monitor Job Progress
###############################################################################

echo ""
log_info "Step 7: Monitoring job progress..."

MAX_WAIT=600  # 10 minutes
ELAPSED=0
POLL_INTERVAL=10

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Get job status
    STATUS_RESPONSE=$(curl -s "$API_URL/api/scraper/jobs/$JOB_ID" \
        -H "Authorization: Bearer $TOKEN")

    JOB_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status')
    PROGRESS=$(echo "$STATUS_RESPONSE" | jq -r '.data.progress.percentage // 0')
    PAGES_SCRAPED=$(echo "$STATUS_RESPONSE" | jq -r '.data.progress.pagesScraped // 0')

    echo -ne "\r  Status: $JOB_STATUS | Progress: ${PROGRESS}% | Pages: ${PAGES_SCRAPED}     "

    # Check if job completed
    if [ "$JOB_STATUS" = "completed" ]; then
        echo ""
        log_success "Job completed successfully!"
        break
    fi

    # Check if job failed
    if [ "$JOB_STATUS" = "failed" ]; then
        echo ""
        log_error "Job failed"
        echo "$STATUS_RESPONSE" | jq '.data'
        exit 1
    fi

    sleep $POLL_INTERVAL
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    log_error "Job did not complete within $MAX_WAIT seconds"
    exit 1
fi

###############################################################################
# Step 8: Wait for S3 Upload
###############################################################################

echo ""
log_info "Step 8: Waiting for S3 upload to complete..."

MAX_WAIT=120  # 2 minutes
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Get job status
    STATUS_RESPONSE=$(curl -s "$API_URL/api/scraper/jobs/$JOB_ID" \
        -H "Authorization: Bearer $TOKEN")

    S3_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.output.uploadToS3.status // "pending"')

    echo -ne "\r  S3 Upload Status: $S3_STATUS     "

    if [ "$S3_STATUS" = "success" ]; then
        echo ""
        log_success "S3 upload completed successfully!"
        break
    fi

    if [ "$S3_STATUS" = "failed" ]; then
        echo ""
        log_error "S3 upload failed"
        echo "$STATUS_RESPONSE" | jq '.data.output.uploadToS3'
        exit 1
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo ""
    log_warning "S3 upload status not confirmed, checking manually..."
fi

###############################################################################
# Step 9: Verify S3 Upload
###############################################################################

echo ""
log_info "Step 9: Verifying files in S3..."

# Get S3 URLs from job
S3_URLS=$(echo "$STATUS_RESPONSE" | jq -r '.data.output.uploadToS3.s3Urls')

echo ""
echo "S3 URLs:"
echo "$S3_URLS" | jq .

# Extract folder name and construct S3 prefix
FOLDER_NAME=$(echo "$STATUS_RESPONSE" | jq -r '.data.folder_name // ""')

if [ -z "$FOLDER_NAME" ] || [ "$FOLDER_NAME" = "null" ]; then
    log_error "Could not determine folder name"
    exit 1
fi

S3_PREFIX="scraper-outputs/${FOLDER_NAME}_${JOB_ID}/"

log_info "Checking S3 path: s3://${TEST_BUCKET_NAME}/${S3_PREFIX}"

# List files in S3
S3_FILES=$(aws s3 ls "s3://${TEST_BUCKET_NAME}/${S3_PREFIX}" --recursive)

if [ -z "$S3_FILES" ]; then
    log_error "No files found in S3"
    exit 1
fi

# Count files
FILE_COUNT=$(echo "$S3_FILES" | wc -l | tr -d ' ')
TOTAL_SIZE=$(echo "$S3_FILES" | awk '{sum+=$3} END {print sum}')

log_success "Found $FILE_COUNT files in S3"
log_info "Total size: $(numfmt --to=iec-i --suffix=B $TOTAL_SIZE 2>/dev/null || echo "$TOTAL_SIZE bytes")"

echo ""
echo "Files in S3:"
echo "$S3_FILES" | head -20
if [ "$FILE_COUNT" -gt 20 ]; then
    echo "... and $((FILE_COUNT - 20)) more files"
fi

###############################################################################
# Step 10: Query Database
###############################################################################

echo ""
log_info "Step 10: Querying database for S3 metadata..."

# Query database through Docker
DB_QUERY="SELECT
    id,
    name,
    folder_name,
    status,
    completed_at,
    output->'uploadToS3'->>'status' as s3_status,
    output->'uploadToS3'->>'filesUploaded' as files_uploaded,
    output->'uploadToS3'->>'bytesUploaded' as bytes_uploaded,
    output->'uploadToS3'->'s3Urls'->>'all_products_json' as products_url,
    output->'uploadToS3'->'s3Urls'->>'categories_json' as categories_url
FROM jobs
WHERE id = '$JOB_ID';"

DB_RESULT=$(docker-compose exec -T postgres psql -U scraper_user -d scraper_db -c "$DB_QUERY" 2>/dev/null)

echo ""
echo "Database Query Result:"
echo "$DB_RESULT"

###############################################################################
# Step 11: Download and Verify a Sample File
###############################################################################

echo ""
log_info "Step 11: Downloading and verifying sample file from S3..."

# Download all_products.json
PRODUCTS_S3_KEY="${S3_PREFIX}all_products.json"
TEMP_FILE="/tmp/s3_test_products_${JOB_ID}.json"

log_info "Downloading: s3://${TEST_BUCKET_NAME}/${PRODUCTS_S3_KEY}"

if aws s3 cp "s3://${TEST_BUCKET_NAME}/${PRODUCTS_S3_KEY}" "$TEMP_FILE" 2>/dev/null; then
    log_success "Downloaded successfully"

    # Verify it's valid JSON and count products
    if PRODUCT_COUNT=$(jq '. | length' "$TEMP_FILE" 2>/dev/null); then
        log_success "Valid JSON file with $PRODUCT_COUNT products"

        # Show sample product
        echo ""
        echo "Sample product (first entry):"
        jq '.[0] | {name: .product_name, url: .product_url, category: .category}' "$TEMP_FILE"
    else
        log_error "Invalid JSON file"
        exit 1
    fi

    # Cleanup
    rm -f "$TEMP_FILE"
else
    log_error "Failed to download file from S3"
    exit 1
fi

###############################################################################
# Summary Report
###############################################################################

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Test Summary"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Get final stats
FINAL_STATS=$(curl -s "$API_URL/api/scraper/jobs/$JOB_ID" \
    -H "Authorization: Bearer $TOKEN" | jq '.data')

ITEMS_EXTRACTED=$(echo "$FINAL_STATS" | jq -r '.stats.itemsExtracted // 0')
FILES_UPLOADED=$(echo "$FINAL_STATS" | jq -r '.output.uploadToS3.filesUploaded // 0')
BYTES_UPLOADED=$(echo "$FINAL_STATS" | jq -r '.output.uploadToS3.bytesUploaded // 0')
DURATION=$(echo "$FINAL_STATS" | jq -r '
    if .startedAt and .completedAt then
        (((.completedAt | fromdateiso8601) - (.startedAt | fromdateiso8601)) | floor)
    else
        "N/A"
    end
')

log_success "✓ Job ID: $JOB_ID"
log_success "✓ S3 Bucket: $TEST_BUCKET_NAME"
log_success "✓ S3 Path: ${S3_PREFIX}"
log_success "✓ Items Extracted: $ITEMS_EXTRACTED"
log_success "✓ Files Uploaded to S3: $FILES_UPLOADED"
log_success "✓ Bytes Uploaded: $(numfmt --to=iec-i --suffix=B $BYTES_UPLOADED 2>/dev/null || echo "$BYTES_UPLOADED")"
if [ "$DURATION" != "N/A" ]; then
    log_success "✓ Total Duration: ${DURATION}s"
fi

echo ""
echo "S3 URLs for downstream applications:"
echo "$FINAL_STATS" | jq -r '.output.uploadToS3.s3Urls | to_entries[] | "  \(.key): \(.value)"'

echo ""
log_success "═══════════════════════════════════════════════════════════"
log_success "  All tests passed! S3 integration is working correctly."
log_success "═══════════════════════════════════════════════════════════"
echo ""

# Cleanup instructions
echo "Cleanup commands:"
echo "  # View files in S3:"
echo "  aws s3 ls s3://${TEST_BUCKET_NAME}/${S3_PREFIX} --recursive"
echo ""
echo "  # Download entire job output:"
echo "  aws s3 sync s3://${TEST_BUCKET_NAME}/${S3_PREFIX} ./test-output/"
echo ""
echo "  # Delete test bucket (when done):"
echo "  aws s3 rb s3://${TEST_BUCKET_NAME} --force"
echo ""

exit 0
