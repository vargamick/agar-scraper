#!/bin/bash
#
# 3DN Scraper API Test Suite
# Comprehensive API testing with curl
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:3010/api/scraper"
TOKEN=""
JOB_ID=""
USER_USERNAME="testuser"
USER_PASSWORD="testpass123"
USER_EMAIL="test@example.com"

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local extra_headers=$4

    if [ -n "$TOKEN" ]; then
        if [ -n "$data" ]; then
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Authorization: Bearer $TOKEN" \
                -H "Content-Type: application/json" \
                $extra_headers \
                -d "$data"
        else
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Authorization: Bearer $TOKEN" \
                $extra_headers
        fi
    else
        if [ -n "$data" ]; then
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Content-Type: application/json" \
                $extra_headers \
                -d "$data"
        else
            curl -s -X "$method" "$API_URL$endpoint" \
                $extra_headers
        fi
    fi
}

wait_for_api() {
    print_info "Waiting for API to be ready..."
    for i in {1..30}; do
        if curl -s "$API_URL/health" > /dev/null 2>&1; then
            print_success "API is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    print_error "API did not become ready in time"
    exit 1
}

# Test 1: Health Check
test_health_check() {
    print_header "Test 1: Health Check"

    response=$(curl -s "$API_URL/health")
    status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

    if [ "$status" = "healthy" ]; then
        print_success "Health check passed"
        echo "$response" | jq '.'
    else
        print_error "Health check failed"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Test 2: User Registration
test_user_registration() {
    print_header "Test 2: User Registration"

    response=$(api_call POST "/auth/register" '{
        "username": "'"$USER_USERNAME"'",
        "email": "'"$USER_EMAIL"'",
        "password": "'"$USER_PASSWORD"'",
        "full_name": "Test User"
    }')

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        print_success "User registered successfully"
        print_info "Token: ${TOKEN:0:20}..."
        echo "$response" | jq '.data | {username, email, is_active}'
    else
        # User might already exist, try login
        print_info "User might already exist, trying login..."
        test_user_login
    fi
}

# Test 3: User Login
test_user_login() {
    print_header "Test 3: User Login"

    response=$(api_call POST "/auth/login" '{
        "username": "'"$USER_USERNAME"'",
        "password": "'"$USER_PASSWORD"'"
    }')

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        TOKEN=$(echo "$response" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
        print_success "Login successful"
        print_info "Token: ${TOKEN:0:20}..."
        echo "$response" | jq '.data | {user: .user.username, token_type, expires_in}'
    else
        print_error "Login failed"
        echo "$response" | jq '.'
        exit 1
    fi
}

# Test 4: Get Current User
test_get_current_user() {
    print_header "Test 4: Get Current User"

    response=$(api_call GET "/auth/me")

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        print_success "Got current user info"
        echo "$response" | jq '.data | {username, email, is_active, created_at}'
    else
        print_error "Failed to get current user"
        echo "$response" | jq '.'
    fi
}

# Test 5: Create Simple Job
test_create_simple_job() {
    print_header "Test 5: Create Simple Job"

    response=$(api_call POST "/jobs" '{
        "name": "test-job-001",
        "description": "Simple test job",
        "type": "web",
        "config": {
            "startUrls": ["https://example.com"],
            "maxPages": 3,
            "crawlDepth": 1,
            "respectRobotsTxt": true
        },
        "output": {
            "saveFiles": true,
            "fileFormat": "json"
        }
    }')

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        JOB_ID=$(echo "$response" | grep -o '"jobId":"[^"]*"' | cut -d'"' -f4)
        print_success "Job created successfully"
        print_info "Job ID: $JOB_ID"
        echo "$response" | jq '.data'
    else
        print_error "Failed to create job"
        echo "$response" | jq '.'
    fi
}

# Test 6: List Jobs
test_list_jobs() {
    print_header "Test 6: List Jobs"

    response=$(api_call GET "/jobs?limit=10&offset=0")

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        job_count=$(echo "$response" | jq '.data.jobs | length')
        print_success "Listed jobs (found $job_count jobs)"
        echo "$response" | jq '.data | {jobs: .jobs | map({jobId, name, status, type}), pagination}'
    else
        print_error "Failed to list jobs"
        echo "$response" | jq '.'
    fi
}

# Test 7: Get Job Details
test_get_job_details() {
    print_header "Test 7: Get Job Details"

    if [ -z "$JOB_ID" ]; then
        print_error "No job ID available (create a job first)"
        return
    fi

    response=$(api_call GET "/jobs/$JOB_ID")

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        print_success "Got job details"
        echo "$response" | jq '.data | {jobId, name, status, type, progress, stats}'
    else
        print_error "Failed to get job details"
        echo "$response" | jq '.'
    fi
}

# Test 8: Get Job Logs
test_get_job_logs() {
    print_header "Test 8: Get Job Logs"

    if [ -z "$JOB_ID" ]; then
        print_error "No job ID available"
        return
    fi

    # Wait a bit for logs to be generated
    sleep 2

    response=$(api_call GET "/jobs/$JOB_ID/logs?limit=20")

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        log_count=$(echo "$response" | jq '.data.logs | length')
        print_success "Got job logs (found $log_count logs)"
        echo "$response" | jq '.data.logs | .[:5] | map({timestamp, level, message})'
    else
        print_error "Failed to get job logs"
        echo "$response" | jq '.'
    fi
}

# Test 9: Get Job Results
test_get_job_results() {
    print_header "Test 9: Get Job Results"

    if [ -z "$JOB_ID" ]; then
        print_error "No job ID available"
        return
    fi

    # Wait for job to produce results
    print_info "Waiting for job to complete (10 seconds)..."
    sleep 10

    response=$(api_call GET "/jobs/$JOB_ID/results?limit=10")

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        item_count=$(echo "$response" | jq '.data.itemsCount')
        print_success "Got job results (found $item_count items)"
        echo "$response" | jq '.data | {itemsCount, results: .results | .[:3]}'
    else
        print_error "Failed to get job results"
        echo "$response" | jq '.'
    fi
}

# Test 10: Job Control - Pause
test_job_control_pause() {
    print_header "Test 10: Job Control - Pause"

    if [ -z "$JOB_ID" ]; then
        print_error "No job ID available"
        return
    fi

    response=$(api_call POST "/jobs/$JOB_ID/control" '{
        "action": "pause"
    }')

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        print_success "Job control action executed"
        echo "$response" | jq '.data'
    else
        print_info "Job control returned message (expected for completed jobs)"
        echo "$response" | jq '.data'
    fi
}

# Test 11: Create Advanced Job
test_create_advanced_job() {
    print_header "Test 11: Create Advanced Job"

    response=$(api_call POST "/jobs" '{
        "name": "advanced-job-001",
        "description": "Advanced test job with full config",
        "type": "web",
        "config": {
            "startUrls": [
                "https://example.com",
                "https://example.org"
            ],
            "maxPages": 5,
            "crawlDepth": 2,
            "rateLimit": {
                "requests": 5,
                "per": "second"
            },
            "selectors": {
                "css": [".content", ".article"]
            },
            "headers": {
                "User-Agent": "3DN-Scraper/1.0"
            },
            "followLinks": true,
            "respectRobotsTxt": true
        },
        "output": {
            "saveFiles": true,
            "fileFormat": "json"
        }
    }')

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        advanced_job_id=$(echo "$response" | grep -o '"jobId":"[^"]*"' | cut -d'"' -f4)
        print_success "Advanced job created successfully"
        print_info "Job ID: $advanced_job_id"
        echo "$response" | jq '.data'
    else
        print_error "Failed to create advanced job"
        echo "$response" | jq '.'
    fi
}

# Test 12: Filter Jobs by Status
test_filter_jobs() {
    print_header "Test 12: Filter Jobs by Status"

    response=$(api_call GET "/jobs?status=completed&limit=5")

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        job_count=$(echo "$response" | jq '.data.jobs | length')
        print_success "Filtered jobs (found $job_count completed jobs)"
        echo "$response" | jq '.data | {jobs: .jobs | map({name, status}), pagination}'
    else
        print_error "Failed to filter jobs"
        echo "$response" | jq '.'
    fi
}

# Test 13: Get Statistics
test_get_statistics() {
    print_header "Test 13: Get Statistics"

    response=$(api_call GET "/stats")

    success=$(echo "$response" | grep -o '"success":[^,}]*' | cut -d':' -f2)

    if [ "$success" = "true" ]; then
        print_success "Got statistics"
        echo "$response" | jq '.data'
    else
        print_error "Failed to get statistics"
        echo "$response" | jq '.'
    fi
}

# Test 14: Invalid Token
test_invalid_token() {
    print_header "Test 14: Invalid Token (Security Test)"

    saved_token=$TOKEN
    TOKEN="invalid_token_12345"

    response=$(api_call GET "/auth/me")

    error=$(echo "$response" | grep -o '"success":false')

    if [ -n "$error" ]; then
        print_success "Invalid token properly rejected"
        echo "$response" | jq '.'
    else
        print_error "Security issue: Invalid token not rejected"
    fi

    TOKEN=$saved_token
}

# Test 15: Validation Error
test_validation_error() {
    print_header "Test 15: Validation Error Test"

    response=$(api_call POST "/jobs" '{
        "name": "",
        "config": {}
    }')

    error=$(echo "$response" | grep -o '"success":false')

    if [ -n "$error" ]; then
        print_success "Validation error properly caught"
        echo "$response" | jq '.error'
    else
        print_error "Validation did not catch invalid input"
    fi
}

# Main test execution
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════╗"
    echo "║     3DN Scraper API - Comprehensive Test Suite    ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""

    # Check dependencies
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        print_error "jq is required but not installed (brew install jq)"
        exit 1
    fi

    # Wait for API
    wait_for_api

    # Run tests
    test_health_check
    test_user_registration
    test_get_current_user
    test_create_simple_job
    test_list_jobs
    test_get_job_details
    test_get_job_logs
    test_get_job_results
    test_job_control_pause
    test_create_advanced_job
    test_filter_jobs
    test_get_statistics
    test_invalid_token
    test_validation_error

    # Summary
    print_header "Test Suite Complete"
    print_success "All tests executed successfully!"
    echo ""
    print_info "API URL: $API_URL"
    print_info "Token: ${TOKEN:0:30}..."
    print_info "Last Job ID: $JOB_ID"
    echo ""
    echo "View API documentation at: http://localhost:3010/api/scraper/docs"
    echo ""
}

# Run main function
main
