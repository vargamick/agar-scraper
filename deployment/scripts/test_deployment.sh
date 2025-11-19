#!/bin/bash
# Test deployment script - verifies all services are working

set -e

# Configuration
API_URL="${1:-http://localhost:3010}"
BASE_URL="${API_URL}/api/scraper"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "Testing Agar Scraper Deployment"
echo "API URL: $API_URL"
echo "========================================="
echo ""

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    echo -n "Testing $name... "

    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1); then
        if [ "$response" = "$expected_status" ]; then
            echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $response)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Connection failed)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Run tests
echo "Running health checks..."
echo ""

test_endpoint "Health endpoint" "${BASE_URL}/health"
test_endpoint "API docs" "${BASE_URL}/docs" 200
test_endpoint "OpenAPI schema" "${BASE_URL}/openapi.json"

echo ""
echo "Testing authentication endpoints..."
echo ""

# Test registration (should fail without proper data, but endpoint should exist)
echo -n "Testing registration endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE_URL}/auth/register" \
    -H "Content-Type: application/json" \
    -d '{"username":"test","email":"test@example.com","password":"test123"}')

if [ "$response" = "400" ] || [ "$response" = "422" ] || [ "$response" = "200" ] || [ "$response" = "201" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $response - endpoint exists)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "Testing job endpoints..."
echo ""

# Test jobs endpoint (should require auth)
echo -n "Testing jobs endpoint (unauthenticated)... "
response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/jobs")

if [ "$response" = "401" ] || [ "$response" = "403" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $response - auth required as expected)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
elif [ "$response" = "200" ]; then
    echo -e "${YELLOW}⚠ WARN${NC} (HTTP $response - endpoint accessible without auth)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo "Testing stats endpoint..."
echo ""

echo -n "Testing stats endpoint... "
response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/stats")

if [ "$response" = "200" ] || [ "$response" = "401" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $response)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test Docker containers (if running on the server)
echo ""
echo "Checking Docker containers..."
echo ""

if command -v docker >/dev/null 2>&1; then
    if docker-compose -f docker-compose.prod.yml ps >/dev/null 2>&1; then
        CONTAINERS=$(docker-compose -f docker-compose.prod.yml ps --services)

        for container in postgres redis crawl4ai api celery-worker ui; do
            echo -n "Checking $container container... "
            if echo "$CONTAINERS" | grep -q "$container"; then
                if docker-compose -f docker-compose.prod.yml ps $container | grep -q "Up"; then
                    echo -e "${GREEN}✓ Running${NC}"
                    TESTS_PASSED=$((TESTS_PASSED + 1))
                else
                    echo -e "${RED}✗ Not running${NC}"
                    TESTS_FAILED=$((TESTS_FAILED + 1))
                fi
            else
                echo -e "${YELLOW}⚠ Not found${NC}"
            fi
        done
    else
        echo -e "${YELLOW}⚠ Docker Compose not available or not running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Docker not available (skipping container checks)${NC}"
fi

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please check the logs.${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check container logs: docker-compose -f docker-compose.prod.yml logs"
    echo "2. Check container status: docker-compose -f docker-compose.prod.yml ps"
    echo "3. Verify .env configuration"
    exit 1
fi
