#!/bin/bash

# Helper script to check job status safely
# Usage: ./check_job.sh <job_id>

if [ -z "$1" ]; then
    echo "Usage: $0 <job_id>"
    exit 1
fi

JOB_ID=$1

# Login and get token
echo "Logging in..."
curl -s -X POST http://localhost:3010/api/scraper/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  > /tmp/check_token.json

TOKEN=$(cat /tmp/check_token.json | jq -r '.data.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "Login failed:"
    cat /tmp/check_token.json | jq .
    exit 1
fi

echo "Login successful!"
echo ""

# Check job status
echo "Checking job status for: $JOB_ID"
curl -s http://localhost:3010/api/scraper/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" \
  > /tmp/job_check.json

cat /tmp/job_check.json | jq .
