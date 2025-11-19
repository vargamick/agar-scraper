#!/bin/bash
# Simple wrapper to wait for job completion and verify S3

JOB_ID="3c7a41c3-644f-4899-a3fe-e225d71e7dd0"
FOLDER="20251118_010221_3c7a41c3-644f-4899-a3fe-e225d71e7dd0"

echo "Monitoring job: $JOB_ID"
echo "Folder: $FOLDER"
echo ""

# Wait for job files to stop changing (indicating completion)
PREV_SIZE=0
STABLE_COUNT=0

while true; do
    # Check if all_products.json exists
    if [ -f "/Users/mick/AI/c4ai/agar/scraper_data/jobs/$FOLDER/all_products.json" ]; then
        CURRENT_SIZE=$(wc -c < "/Users/mick/AI/c4ai/agar/scraper_data/jobs/$FOLDER/all_products.json")

        if [ "$CURRENT_SIZE" -eq "$PREV_SIZE" ]; then
            STABLE_COUNT=$((STABLE_COUNT + 1))
            echo "File size stable: $CURRENT_SIZE bytes (${STABLE_COUNT}/3)"

            if [ $STABLE_COUNT -ge 3 ]; then
                echo ""
                echo "✓ Job appears complete!"

                # Count products
                PRODUCT_COUNT=$(jq '. | length' "/Users/mick/AI/c4ai/agar/scraper_data/jobs/$FOLDER/all_products.json")
                echo "Products extracted: $PRODUCT_COUNT"

                # Wait a bit for S3 upload
                echo ""
                echo "Waiting 60 seconds for S3 upload..."
                sleep 60

                # Check S3 (requires AWS credentials to be set in environment)
                export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}

                S3_PATH="agar/$FOLDER/"
                echo ""
                echo "Checking S3: s3://agar-documentation/$S3_PATH"
                echo ""

                if aws s3 ls "s3://agar-documentation/$S3_PATH" --recursive | head -20; then
                    echo ""
                    echo "✓ FILES FOUND IN S3!"
                    echo ""
                    echo "Full path: s3://agar-documentation/$S3_PATH"
                    echo ""
                    echo "To list all files:"
                    echo "  aws s3 ls s3://agar-documentation/$S3_PATH --recursive"
                else
                    echo "✗ No files in S3 yet"
                fi

                exit 0
            fi
        else
            STABLE_COUNT=0
            echo "File growing: $PREV_SIZE -> $CURRENT_SIZE bytes"
        fi

        PREV_SIZE=$CURRENT_SIZE
    else
        echo "Waiting for all_products.json..."
    fi

    sleep 10
done
