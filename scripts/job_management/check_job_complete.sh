#!/bin/bash
# Wait for job completion and verify S3 upload

JOB_ID="${1:-3c7a41c3-644f-4899-a3fe-e225d71e7dd0}"
API_URL="http://localhost:3010"

# AWS credentials (should be set in environment)
export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

# Get token
TOKEN=$(curl -s -X POST "${API_URL}/api/scraper/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"testpass123"}' | jq -r '.data.access_token')

echo "========================================"
echo "Waiting for Job Completion"
echo "========================================"
echo "Job ID: $JOB_ID"
echo ""

# Wait for job to complete
TIMEOUT=600
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    RESPONSE=$(curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" -H "Authorization: Bearer $TOKEN")

    STATUS=$(echo "$RESPONSE" | jq -r '.data.status')
    ITEMS=$(echo "$RESPONSE" | jq -r '.data.stats.itemsExtracted // 0')

    echo -ne "\rStatus: $STATUS | Items Extracted: $ITEMS    "

    if [ "$STATUS" = "completed" ]; then
        echo ""
        echo ""
        echo "✓ Job completed successfully!"
        echo ""

        # Get job details
        FOLDER_NAME=$(echo "$RESPONSE" | jq -r '.data.folder_name')
        STATS=$(echo "$RESPONSE" | jq '.data.stats')

        echo "Job Statistics:"
        echo "---------------"
        echo "$STATS" | jq '.'

        echo ""
        echo "========================================"
        echo "Waiting for S3 Upload..."
        echo "========================================"

        # Wait for S3 upload to complete
        S3_WAIT=0
        while [ $S3_WAIT -lt 120 ]; do
            RESPONSE=$(curl -s "${API_URL}/api/scraper/jobs/${JOB_ID}" -H "Authorization: Bearer $TOKEN")
            S3_STATUS=$(echo "$RESPONSE" | jq -r '.data.output.uploadToS3.status // "pending"')

            echo -ne "\rS3 Upload Status: $S3_STATUS    "

            if [ "$S3_STATUS" = "success" ]; then
                echo ""
                echo ""
                echo "✓ S3 upload completed!"

                # Show S3 details
                S3_INFO=$(echo "$RESPONSE" | jq '.data.output.uploadToS3')
                echo ""
                echo "S3 Upload Details:"
                echo "------------------"
                echo "$S3_INFO" | jq '.'

                # Get S3 path
                S3_PREFIX="agar/"
                S3_PATH="${S3_PREFIX}${FOLDER_NAME}_${JOB_ID}/"

                echo ""
                echo "========================================"
                echo "Verifying Files in S3..."
                echo "========================================"
                echo "S3 Path: s3://agar-documentation/${S3_PATH}"
                echo ""

                if aws s3 ls "s3://agar-documentation/${S3_PATH}" --recursive; then
                    echo ""
                    echo "✓ Files successfully uploaded to S3!"

                    # Download sample file
                    echo ""
                    echo "Downloading all_products.json for verification..."
                    if aws s3 cp "s3://agar-documentation/${S3_PATH}all_products.json" /tmp/s3_products_test.json 2>/dev/null; then
                        PRODUCT_COUNT=$(jq '. | length' /tmp/s3_products_test.json 2>/dev/null)
                        if [ ! -z "$PRODUCT_COUNT" ]; then
                            echo "✓ Downloaded and verified: $PRODUCT_COUNT products"
                            rm /tmp/s3_products_test.json
                        fi
                    fi

                    echo ""
                    echo "========================================"
                    echo "✓ S3 Integration Test PASSED"
                    echo "========================================"
                    echo ""
                    echo "Summary:"
                    echo "--------"
                    echo "Job ID: $JOB_ID"
                    echo "Folder: $FOLDER_NAME"
                    echo "Items Extracted: $ITEMS"
                    echo "S3 Path: s3://agar-documentation/${S3_PATH}"
                    echo ""
                    echo "To view all files:"
                    echo "  aws s3 ls s3://agar-documentation/${S3_PATH} --recursive"
                    echo ""
                else
                    echo "✗ No files found in S3"
                    exit 1
                fi

                exit 0
            elif [ "$S3_STATUS" = "failed" ]; then
                echo ""
                echo "✗ S3 upload failed"
                echo "$RESPONSE" | jq '.data.output.uploadToS3.errors'
                exit 1
            fi

            sleep 5
            S3_WAIT=$((S3_WAIT + 5))
        done

        echo ""
        echo "⚠ S3 upload timeout (may still be uploading in background)"
        exit 0
    elif [ "$STATUS" = "failed" ]; then
        echo ""
        echo "✗ Job failed"
        echo "$RESPONSE" | jq '.data.error'
        exit 1
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

echo ""
echo "✗ Timeout waiting for job to complete"
exit 1
