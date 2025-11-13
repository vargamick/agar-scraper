#!/bin/bash

# Monitor job status
# Usage: ./monitor_job.sh <job_id>

if [ -z "$1" ]; then
    echo "Usage: $0 <job_id>"
    exit 1
fi

JOB_ID=$1

# Get token from saved file
TOKEN=$(cat /tmp/monitor_token.txt)

if [ -z "$TOKEN" ]; then
    echo "No token found. Please run run_full_scrape.sh first."
    exit 1
fi

echo "Monitoring job: $JOB_ID"
echo ""

for i in {1..60}; do
    sleep 5

    # Call API to get job status
    curl -s http://localhost:3010/api/scraper/jobs/$JOB_ID \
      -H "Authorization: Bearer $TOKEN" \
      > /tmp/job_monitor.json

    # Extract status and progress
    STATUS=$(cat /tmp/job_monitor.json | jq -r '.data.status')
    PROGRESS=$(cat /tmp/job_monitor.json | jq -r '.data.progress.percentage')
    PAGES=$(cat /tmp/job_monitor.json | jq -r '.data.progress.pagesScraped')
    ITEMS=$(cat /tmp/job_monitor.json | jq -r '.data.stats.itemsExtracted')

    echo "[$i] Status: $STATUS | Progress: $PROGRESS% | Pages: $PAGES | Items: $ITEMS"

    if [ "$STATUS" == "completed" ] || [ "$STATUS" == "failed" ]; then
        echo ""
        echo "==================== JOB FINISHED ===================="
        cat /tmp/job_monitor.json | jq .
        echo ""
        echo "Output folder: /app/scraper_data/jobs/$JOB_ID/"
        break
    fi
done
