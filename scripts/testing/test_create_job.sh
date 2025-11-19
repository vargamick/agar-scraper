#!/bin/bash

# Test creating a job via the API

echo "Logging in..."
TOKEN=$(curl -s 'http://localhost:3010/api/scraper/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['data']['access_token'])")

echo "Token: ${TOKEN:0:50}..."
echo ""
echo "Creating test job..."

curl -s -X POST 'http://localhost:3010/api/scraper/jobs' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Test Scrape",
    "description": "Test job created from script",
    "type": "web",
    "config": {
      "startUrls": ["https://example.com"],
      "maxPages": 5,
      "crawlDepth": 2,
      "followLinks": true,
      "respectRobotsTxt": true
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json",
      "uploadToS3": {
        "enabled": true,
        "uploadPdfs": true,
        "uploadScreenshots": false
      }
    }
  }' | python3 -m json.tool

echo ""
echo "Job created! Check the UI to see it."
