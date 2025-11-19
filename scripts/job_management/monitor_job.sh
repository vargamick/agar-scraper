#!/bin/bash
# Monitor job progress

JOB_ID="${1:-3c7a41c3-644f-4899-a3fe-e225d71e7dd0}"
API_URL="http://localhost:3010"

# Get token
TOKEN=$(curl -s -X POST "${API_URL}/api/scraper/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"testpass123"}' | jq -r '.data.access_token')

echo "Monitoring job: $JOB_ID"
echo "================================"

while true; do
    RESPONSE=$(curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" -H "Authorization: Bearer $TOKEN")

    STATUS=$(echo "$RESPONSE" | jq -r '.data.status')
    ITEMS=$(echo "$RESPONSE" | jq -r '.data.stats.itemsExtracted // 0')
    PAGES=$(echo "$RESPONSE" | jq -r '.data.progress.pagesScraped // 0')

    echo -ne "\rStatus: $STATUS | Items: $ITEMS | Pages: $PAGES      "

    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        echo ""
        echo "================================"
        echo "Job finished with status: $STATUS"

        # Show final stats
        echo "$RESPONSE" | jq '.data | {status, stats, completedAt}'

        # Check S3 upload status
        echo ""
        echo "S3 Upload Status:"
        echo "$RESPONSE" | jq '.data.output.uploadToS3'

        break
    fi

    sleep 5
done
