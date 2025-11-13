#!/bin/bash

# Login and get token
echo "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:3010/api/scraper/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.data.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "Login failed:"
    echo $LOGIN_RESPONSE | jq .
    exit 1
fi

echo "Login successful! Token obtained."
echo ""

# Create scraping job
echo "Creating scraping job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:3010/api/scraper/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Fixed Implementation",
    "description": "Testing the fixed scraper implementation with real core modules",
    "type": "web",
    "config": {
      "startUrls": ["https://www.agar.com.au/"],
      "maxPages": 3,
      "client_name": "agar",
      "test_mode": true,
      "save_screenshots": false
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }')

echo $JOB_RESPONSE | jq .

# Extract job ID
JOB_ID=$(echo $JOB_RESPONSE | jq -r '.data.jobId')

if [ "$JOB_ID" != "null" ] && [ ! -z "$JOB_ID" ]; then
    echo ""
    echo "Job created successfully! Job ID: $JOB_ID"
    echo ""
    echo "Monitoring job status..."

    for i in {1..30}; do
        sleep 2
        # Save response to file to avoid shell parsing issues
        curl -s http://localhost:3010/api/scraper/jobs/$JOB_ID \
          -H "Authorization: Bearer $TOKEN" > /tmp/status_response.json

        STATUS=$(cat /tmp/status_response.json | jq -r '.data.status')
        echo "Status: $STATUS"

        if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
            echo ""
            echo "Job finished with status: $STATUS"
            cat /tmp/status_response.json | jq .
            break
        fi
    done
fi
