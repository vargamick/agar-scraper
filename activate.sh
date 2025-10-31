#!/bin/bash
# Quick activation helper for Agar scraper virtual environment

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Run ./setup_venv.sh first to create the environment."
    exit 1
fi

source venv/bin/activate
echo "✓ Virtual environment activated"
echo "  Python version: $(python --version 2>&1)"
echo ""
echo "Note: This venv only provides Python 3.11 - all packages"
echo "are expected to be available in your system installation."
