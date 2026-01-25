# Agar Scraper - Dockerfile
# Single-stage build optimized for Coolify deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (including those needed for Playwright)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers with system dependencies
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create output directories
RUN mkdir -p agar_scrapes logs scraper_data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3010/api/scraper/health || exit 1

# Default command (overridden by docker-compose)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "3010"]
