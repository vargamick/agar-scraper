#!/bin/bash
###############################################################################
# Quick S3 Scrape Test
#
# Assumes:
# - Docker containers are already running
# - .env is configured with S3 credentials
# - boto3 dependencies are installed in containers
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:3010"
TEST_USER="testuser"
TEST_PASS="testpass123"
S3_BUCKET="agar-documentation"
S3_PREFIX="agar/"
AWS_REGION="us-east-1"

# Load AWS Credentials from environment
# Set these in your shell or .env file:
# export AWS_ACCESS_KEY_ID=your_access_key
# export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-$AWS_REGION}

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

###############################################################################
# Pre-flight Checks
###############################################################################

echo ""
echo "========================================================================="
echo "S3 Scraper Integration Test"
echo "========================================================================="
echo ""

log_info "Checking prerequisites..."

# Check Docker is running
if ! docker ps >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker Desktop first."
    exit 1
fi
log_success "Docker is running"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI is not installed"
    exit 1
fi
log_success "AWS CLI is installed"

# Check S3 bucket access
log_info "Verifying S3 bucket access..."
if aws s3 ls "s3://${S3_BUCKET}/" >/dev/null 2>&1; then
    log_success "Bucket ${S3_BUCKET} is accessible"
else
    log_error "Cannot access bucket ${S3_BUCKET}"
    exit 1
fi

# Check containers are running
log_info "Checking Docker containers..."
REQUIRED_CONTAINERS=("scraper-api" "scraper-postgres" "scraper-redis" "scraper-celery-worker" "crawl4ai-service")
for container in "${REQUIRED_CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        log_success "Container ${container} is running"
    else
        log_error "Container ${container} is not running"
        log_info "Start containers with: docker-compose up -d"
        exit 1
    fi
done

###############################################################################
# Step 1: Authenticate
###############################################################################

echo ""
log_info "Step 1: Authenticating with API..."

LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/scraper/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${TEST_USER}\",\"password\":\"${TEST_PASS}\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.data.access_token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    log_error "Failed to authenticate"
    echo "$LOGIN_RESPONSE" | jq .
    exit 1
fi

log_success "Authenticated successfully"

###############################################################################
# Step 2: Create Scrape Job with S3 Upload
###############################################################################

echo ""
log_info "Step 2: Creating scrape job with S3 upload enabled..."

JOB_PAYLOAD=$(cat <<EOF
{
  "name": "S3 Integration Test - $(date +%Y%m%d_%H%M%S)",
  "description": "End-to-end test of S3 upload integration",
  "type": "web",
  "config": {
    "startUrls": ["https://www.agar.com.au"],
    "maxPages": 50,
    "client_name": "agar",
    "test_mode": false,
    "save_screenshots": true
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

JOB_RESPONSE=$(curl -s -X POST "${API_URL}/api/scraper/jobs" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$JOB_PAYLOAD")

JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.data.jobId // .data.id')

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    log_error "Failed to create job"
    echo "$JOB_RESPONSE" | jq .
    exit 1
fi

log_success "Job created with ID: ${JOB_ID}"

###############################################################################
# Step 3: Monitor Job Progress
###############################################################################

echo ""
log_info "Step 3: Monitoring job progress..."
log_info "Job ID: ${JOB_ID}"
echo ""

TIMEOUT=600  # 10 minutes
ELAPSED=0
INTERVAL=10

while [ $ELAPSED -lt $TIMEOUT ]; do
    JOB_STATUS=$(curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" \
        -H "Authorization: Bearer ${TOKEN}" | jq -r '.data.status')

    PROGRESS=$(curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" \
        -H "Authorization: Bearer ${TOKEN}" | jq -r '.data.stats.itemsExtracted // 0')

    echo -ne "\r${BLUE}[INFO]${NC} Status: ${JOB_STATUS} | Items extracted: ${PROGRESS}"

    if [ "$JOB_STATUS" = "completed" ]; then
        echo ""
        log_success "Job completed successfully"
        break
    elif [ "$JOB_STATUS" = "failed" ]; then
        echo ""
        log_error "Job failed"
        curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" \
            -H "Authorization: Bearer ${TOKEN}" | jq '.data.error'
        exit 1
    fi

    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo ""
    log_error "Job timed out after ${TIMEOUT} seconds"
    exit 1
fi

###############################################################################
# Step 4: Wait for S3 Upload
###############################################################################

echo ""
log_info "Step 4: Waiting for S3 upload to complete..."

UPLOAD_TIMEOUT=120  # 2 minutes
UPLOAD_ELAPSED=0

while [ $UPLOAD_ELAPSED -lt $UPLOAD_TIMEOUT ]; do
    S3_STATUS=$(curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" \
        -H "Authorization: Bearer ${TOKEN}" | jq -r '.data.output.uploadToS3.status // "pending"')

    echo -ne "\r${BLUE}[INFO]${NC} S3 Upload Status: ${S3_STATUS}"

    if [ "$S3_STATUS" = "success" ]; then
        echo ""
        log_success "S3 upload completed"
        break
    elif [ "$S3_STATUS" = "failed" ]; then
        echo ""
        log_error "S3 upload failed"
        curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" \
            -H "Authorization: Bearer ${TOKEN}" | jq '.data.output.uploadToS3.errors'
        exit 1
    fi

    sleep 5
    UPLOAD_ELAPSED=$((UPLOAD_ELAPSED + 5))
done

if [ $UPLOAD_ELAPSED -ge $UPLOAD_TIMEOUT ]; then
    echo ""
    log_warning "S3 upload status check timed out (may still be uploading in background)"
fi

###############################################################################
# Step 5: Verify Files in S3
###############################################################################

echo ""
log_info "Step 5: Verifying files in S3..."

# Get job details
JOB_DETAILS=$(curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" \
    -H "Authorization: Bearer ${TOKEN}")

FOLDER_NAME=$(echo "$JOB_DETAILS" | jq -r '.data.folder_name')
S3_URLS=$(echo "$JOB_DETAILS" | jq -r '.data.output.uploadToS3.s3Urls')

log_info "Folder name: ${FOLDER_NAME}"
echo ""

# Construct S3 path
S3_PATH="${S3_PREFIX}${FOLDER_NAME}_${JOB_ID}/"

log_info "Listing files in S3: s3://${S3_BUCKET}/${S3_PATH}"
echo ""

if aws s3 ls "s3://${S3_BUCKET}/${S3_PATH}" --recursive; then
    log_success "Files found in S3"
else
    log_error "No files found in S3 path"
    exit 1
fi

###############################################################################
# Step 6: Display Results
###############################################################################

echo ""
echo "========================================================================="
log_success "S3 Integration Test Completed"
echo "========================================================================="
echo ""

# Get final stats
STATS=$(echo "$JOB_DETAILS" | jq -r '.data.stats')
S3_INFO=$(echo "$JOB_DETAILS" | jq -r '.data.output.uploadToS3')

echo "Job Statistics:"
echo "---------------"
echo "$STATS" | jq '{
    itemsExtracted,
    categoriesFound,
    pdfsDownloaded,
    bytesDownloaded
}'

echo ""
echo "S3 Upload Information:"
echo "----------------------"
echo "$S3_INFO" | jq '{
    status,
    uploadedAt,
    filesUploaded,
    bytesUploaded,
    s3Urls
}'

echo ""
echo "S3 Location:"
echo "------------"
echo "Bucket: s3://${S3_BUCKET}/${S3_PATH}"
echo ""

# Extract one file as verification
log_info "Downloading sample file for verification..."
PRODUCTS_FILE="${S3_PATH}all_products.json"

if aws s3 cp "s3://${S3_BUCKET}/${PRODUCTS_FILE}" /tmp/s3_test_products.json 2>/dev/null; then
    PRODUCT_COUNT=$(jq '. | length' /tmp/s3_test_products.json)
    log_success "Downloaded all_products.json (${PRODUCT_COUNT} products)"
    rm /tmp/s3_test_products.json
fi

echo ""
log_success "All tests passed!"
echo ""
echo "To view files in S3:"
echo "  aws s3 ls s3://${S3_BUCKET}/${S3_PATH} --recursive"
echo ""
echo "To download all files:"
echo "  aws s3 sync s3://${S3_BUCKET}/${S3_PATH} ./s3_download/"
echo ""
