#!/bin/bash

# Start the Web Scraper Dashboard UI

echo ""
echo "================================================"
echo "  Web Scraper Dashboard - Starting UI Server"
echo "================================================"
echo ""

# Check if API is running
API_HEALTH=$(curl -s http://localhost:3010/api/scraper/health 2>/dev/null)
if [ $? -ne 0 ]; then
    echo "WARNING: API does not appear to be running at http://localhost:3010"
    echo ""
    echo "Please start the API first:"
    echo "  docker-compose up"
    echo ""
    read -p "Press Ctrl+C to cancel, or Enter to continue anyway... "
fi

echo ""
echo "Starting UI server..."
echo ""

cd "$(dirname "$0")/ui"
python3 server.py
