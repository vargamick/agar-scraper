#!/bin/bash

# Login and get token
echo "Logging in..."
curl -s -X POST http://localhost:3010/api/scraper/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' \
  -o /tmp/token_full.json

TOKEN=$(cat /tmp/token_full.json | jq -r '.data.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "Login failed:"
    cat /tmp/token_full.json | jq .
    exit 1
fi

echo "Login successful! Token obtained."
echo ""

# Create full scraping job
echo "Creating full scraping job..."
curl -s -X POST http://localhost:3010/api/scraper/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Full Agar Product Catalog Scrape",
    "description": "Complete scrape of all Agar products with PDF downloads",
    "type": "web",
    "config": {
      "startUrls": ["https://www.agar.com.au/"],
      "maxPages": 1000,
      "client_name": "agar",
      "test_mode": false,
      "save_screenshots": true
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }' \
  -o /tmp/job_response.json

echo ""
cat /tmp/job_response.json | jq .

# Extract job ID
JOB_ID=$(cat /tmp/job_response.json | jq -r '.data.jobId')

if [ "$JOB_ID" != "null" ] && [ ! -z "$JOB_ID" ]; then
    echo ""
    echo "Job created successfully! Job ID: $JOB_ID"
    echo "Job output will be in: /app/scraper_data/jobs/$JOB_ID/"
    echo ""
    echo "Monitor progress with:"
    echo "  docker-compose logs -f celery-worker"
    echo ""
    echo "Check status with:"
    echo "  curl -H 'Authorization: Bearer \$TOKEN' http://localhost:3010/api/scraper/jobs/$JOB_ID > /tmp/job_status.json && cat /tmp/job_status.json | jq ."
else
    echo "Failed to create job"
    exit 1
fi
