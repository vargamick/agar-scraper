#!/bin/bash
# Minimal virtual environment setup for Agar scraper
# Only ensures Python 3.11.4 is used - NO dependencies installed

set -e

echo "=========================================="
echo "Agar Scraper Virtual Environment Setup"
echo "=========================================="

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 not found!"
    echo "Please install Python 3.11 first:"
    echo "  brew install python@3.11"
    exit 1
fi

PYTHON_VERSION=$(python3.11 --version 2>&1 | cut -d' ' -f2)
echo "✓ Found Python: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment with Python 3.11..."
    python3.11 -m venv venv --system-site-packages
    echo "✓ Virtual environment created (with access to system packages)"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "This is a minimal virtual environment that only"
echo "ensures Python 3.11.4 is used when running scripts."
echo ""
echo "The venv has access to system-installed packages"
echo "(Crawl4AI, etc.) via --system-site-packages flag."
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "Or use the helper script:"
echo "  source activate.sh"
echo ""
echo "To run scripts with this Python version:"
echo "  python main.py --test"
echo ""
