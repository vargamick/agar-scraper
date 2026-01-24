# Ask Agar Web Scraper - Complete Deployment and Operations Guide

**Version:** 1.0.0
**Last Updated:** 2025-01-22
**Target Environment:** AWS LightSail Production Deployment

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Core Technologies](#core-technologies)
4. [Configuration Management](#configuration-management)
5. [User Interface Operations](#user-interface-operations)
6. [Data Storage and Access](#data-storage-and-access)
7. [AWS LightSail Deployment](#aws-lightsail-deployment)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Integration with Coolify](#integration-with-coolify)
10. [Troubleshooting Guide](#troubleshooting-guide)
11. [Appendices](#appendices)

---

## Executive Summary

The **Ask Agar Web Scraper** is a production-ready web scraping platform specifically configured for scraping [Agar Cleaning Systems](https://agar.com.au) product catalog. Built on the 3DN Scraper Template framework, it provides a complete solution for automated product data extraction, document management, and cloud storage integration.

### Key Capabilities

- **Automated Product Scraping**: Discovers categories, collects product URLs, and extracts detailed product information
- **Document Management**: Downloads and organizes SDS (Safety Data Sheets) and PDS (Product Data Sheets)
- **Cloud Storage**: Automatic upload to AWS S3 with configurable retention policies
- **Web Interface**: Modern dashboard for job creation, monitoring, and management
- **REST API**: Complete API for programmatic access and integration
- **Production Ready**: Containerized deployment with health monitoring and auto-recovery

### Target Users

- **Administrators**: Deploy and maintain the scraping infrastructure
- **Operators**: Create and monitor scraping jobs through the UI
- **Developers**: Integrate scraping data into downstream applications
- **DevOps Teams**: Deploy to AWS LightSail or Coolify environments

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     AWS LightSail Instance                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Nginx Reverse Proxy (Port 80/443)            │  │
│  │    - SSL/TLS termination with Let's Encrypt               │  │
│  │    - Rate limiting and security headers                   │  │
│  │    - Static file caching                                  │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │                                          │
│  ┌─────────────────────┴─────────────────────────────────────┐  │
│  │              Docker Compose Network                        │  │
│  │                                                             │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────┐│  │
│  │  │ PostgreSQL │  │   Redis    │  │ Crawl4AI   │  │  UI  ││  │
│  │  │  (5432)    │  │  (6379)    │  │ (11235)    │  │(8080)││  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────┘│  │
│  │                                                             │  │
│  │  ┌────────────┐  ┌──────────────────────────────────────┐ │  │
│  │  │    API     │  │       Celery Worker                  │ │  │
│  │  │  (3010)    │  │  - Job execution                     │ │  │
│  │  └────────────┘  │  - S3 uploads                        │ │  │
│  │                  │  - Maintenance tasks                 │ │  │
│  │                  └──────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  AWS S3 Bucket│
                    │ agar-documentation
                    │ (ap-southeast-2)│
                    └───────────────┘
```

### Component Roles

| Component | Purpose | Technology | Port |
|-----------|---------|------------|------|
| **PostgreSQL** | Stores job metadata, user accounts, logs, and job state | PostgreSQL 15 | 5432 (internal) |
| **Redis** | Job queue management and caching | Redis 7 | 6379 (internal) |
| **Crawl4AI** | Core web scraping engine | Crawl4AI + Playwright | 11235 (internal) |
| **API Server** | REST API and business logic | FastAPI + Python 3.11 | 3010 → 80/443 |
| **Celery Worker** | Background job processing | Celery + Python | N/A |
| **UI Server** | Web dashboard interface | Python HTTP Server | 8080 → 80/443 |
| **Nginx** | Reverse proxy and SSL termination | Nginx 1.24 | 80, 443 |
| **S3 Storage** | Long-term data storage | AWS S3 | HTTPS |

### Data Flow

```
┌──────────┐
│   User   │
└────┬─────┘
     │ 1. Create Job (UI/API)
     ▼
┌────────────┐    2. Queue    ┌─────────┐
│    API     │─────────────────▶  Redis  │
└────┬───────┘                 └─────────┘
     │ 3. Store Job                 │
     ▼                              │ 4. Dequeue
┌────────────┐                      ▼
│ PostgreSQL │              ┌────────────────┐
└────┬───────┘              │ Celery Worker  │
     │                      └───────┬────────┘
     │ 5. Update Progress           │
     │◀─────────────────────────────┤
     │                              │ 6. Scrape
     │                              ▼
     │                      ┌────────────────┐
     │                      │   Crawl4AI     │
     │                      │  - Categories  │
     │                      │  - Products    │
     │                      │  - PDFs        │
     │                      └───────┬────────┘
     │                              │ 7. Save Results
     │                              ▼
     │                      ┌────────────────┐
     │ 8. Mark Complete     │  File System   │
     │◀─────────────────────│  /scraper_data │
     │                      └───────┬────────┘
     │                              │ 9. Upload
     │ 10. Store S3 URLs            ▼
     │◀─────────────────────┌────────────────┐
     │                      │    AWS S3      │
     ▼                      │ agar-documentation/
┌────────────┐              │   agar/YYYYMMDD_*
│    User    │              └────────────────┘
│  (Results) │
└────────────┘
```

---

## Core Technologies

### Crawl4AI Integration

**Crawl4AI** is the core web scraping engine that powers the Ask Agar scraper. It provides intelligent web crawling with JavaScript rendering, CSS extraction, and content processing.

#### Key Features Utilized

1. **AsyncWebCrawler**
   - **Purpose**: Asynchronous web page crawling with Playwright backend
   - **Usage**: All page fetching operations (categories, products, PDFs)
   - **Configuration**: Custom timeouts, user agents, and wait conditions per page type

2. **JsonCssExtractionStrategy**
   - **Purpose**: Extract structured data using CSS selectors
   - **Usage**: Product details extraction (name, description, images, SKUs)
   - **Schema**: Client-specific extraction schemas defined in `config/clients/agar/extraction_strategies.py`

3. **CrawlerRunConfig**
   - **Purpose**: Configure crawler behavior per request
   - **Settings**:
     - `cache_mode`: Always BYPASS for fresh data
     - `screenshot`: Enable for product pages (stored locally and optionally on S3)
     - `wait_for`: CSS selectors to ensure page is fully loaded
     - `page_timeout`: 30-60 seconds depending on page type
     - `delay_before_return_html`: 2-second delay for dynamic content

4. **Page Rendering**
   - **JavaScript Execution**: Full browser rendering with Playwright
   - **Wait Strategies**: CSS selector-based wait conditions
   - **Content Extraction**: Post-render HTML parsing

#### Crawl4AI Functions in Use

| Module | Crawl4AI Function | Purpose | Configuration |
|--------|-------------------|---------|---------------|
| `category_scraper.py` | `AsyncWebCrawler.arun()` | Discover product categories from homepage | `wait_for=".product-categories"` |
| `product_collector.py` | `AsyncWebCrawler.arun()` | Collect product URLs from category pages | `wait_for=".products"` |
| `product_scraper.py` | `JsonCssExtractionStrategy` | Extract product details with CSS selectors | Custom schema per client |
| `product_pdf_scraper.py` | `AsyncWebCrawler.arun()` | Extract PDF document links | `wait_for=".downloads"` |

#### Example: Product Scraping with Crawl4AI

```python
# From core/product_scraper.py

# Define extraction schema (client-specific)
product_detail_schema = {
    "name": "Product Details",
    "baseSelector": "body",
    "fields": [
        {"name": "product_name", "selector": "h1.product_title", "type": "text"},
        {"name": "main_image", "selector": ".woocommerce-product-gallery__image img",
         "type": "attribute", "attribute": "src"},
        {"name": "product_overview", "selector": ".product-overview", "type": "text"},
        {"name": "product_description", "selector": "#tab-description", "type": "text"},
        {"name": "product_skus", "selector": ".sku", "type": "list"}
    ]
}

# Create extraction strategy
extraction_strategy = JsonCssExtractionStrategy(schema=product_detail_schema)

# Configure crawler
crawler_config = CrawlerRunConfig(
    extraction_strategy=extraction_strategy,
    cache_mode=CacheMode.BYPASS,
    screenshot=True,
    wait_for="css:.product_title",
    page_timeout=60000,  # 60 seconds
    delay_before_return_html=2.0
)

# Execute crawl
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(product_url, config=crawler_config)

    if result.success and result.extracted_content:
        product_data = json.loads(result.extracted_content)
```

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Web Scraping** | Crawl4AI | Latest | Core scraping engine with Playwright |
| **Browser Automation** | Playwright | Latest | JavaScript rendering and page interaction |
| **Backend Framework** | FastAPI | 0.104+ | REST API server |
| **Task Queue** | Celery | 5.3+ | Background job processing |
| **Message Broker** | Redis | 7.0+ | Job queue and caching |
| **Database** | PostgreSQL | 15+ | Job metadata and state management |
| **ORM** | SQLAlchemy | 2.0+ | Database abstraction |
| **Authentication** | JWT | Latest | Token-based authentication |
| **Cloud Storage** | boto3 | 1.28+ | AWS S3 integration |
| **Web Server** | Nginx | 1.24+ | Reverse proxy and SSL |
| **Containerization** | Docker | 24+ | Application packaging |
| **Orchestration** | Docker Compose | 2.20+ | Multi-container management |

---

## Configuration Management

### Client Configuration - Agar

The Agar client configuration is defined in `config/clients/agar/client_config.py`:

```python
class ClientConfig(BaseConfig):
    # Client Identification
    CLIENT_NAME = "agar"
    CLIENT_FULL_NAME = "Agar Cleaning Systems"

    # Website Configuration
    BASE_URL = "https://agar.com.au"

    # URL Patterns
    CATEGORY_URL_PATTERN = "/product-category/{slug}/"
    PRODUCT_URL_PATTERN = "/product/{slug}/"

    # Output Configuration
    OUTPUT_PREFIX = "AgarScrape"
    BASE_OUTPUT_DIR = "agar_scrapes"

    # PDF/Document Configuration
    HAS_SDS_DOCUMENTS = True  # Safety Data Sheets
    HAS_PDS_DOCUMENTS = True  # Product Data Sheets
    SDS_FIELD_NAME = "sds_url"
    PDS_FIELD_NAME = "pds_url"

    # Product Schema Mapping
    PRODUCT_SCHEMA = {
        "name_field": "product_name",
        "url_field": "product_url",
        "image_field": "product_image_url",
        "overview_field": "product_overview",
        "description_field": "product_description",
        "sku_field": "product_skus",
        "categories_field": "product_categories"
    }
```

### Extraction Strategies - Agar

CSS selectors for data extraction are defined in `config/clients/agar/extraction_strategies.py`:

```python
class AgarExtractionStrategy:
    @staticmethod
    def get_product_detail_schema():
        """Product detail page CSS extraction schema"""
        return {
            "name": "Product Details",
            "baseSelector": "body",
            "fields": [
                {
                    "name": "product_name",
                    "selector": "h1.product_title",
                    "type": "text"
                },
                {
                    "name": "main_image",
                    "selector": ".woocommerce-product-gallery__image img",
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "product_overview",
                    "selector": ".product-overview",
                    "type": "text"
                },
                {
                    "name": "product_description",
                    "selector": "#tab-description",
                    "type": "text"
                },
                {
                    "name": "product_skus",
                    "selector": ".sku",
                    "type": "list"
                }
            ]
        }
```

### Environment Configuration

**Production Environment Variables** (`.env` file):

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Application
SECRET_KEY=<generated-secret-key>
API_VERSION=v1

# Database
DATABASE_URL=postgresql://scraper_user:strong_password@postgres:5432/scraper_db
POSTGRES_USER=scraper_user
POSTGRES_PASSWORD=strong_password
POSTGRES_DB=scraper_db

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# CORS
CORS_ORIGINS=https://askagar.com,https://www.askagar.com

# S3 Configuration
S3_ENABLED=true
S3_BUCKET_NAME=agar-documentation
S3_REGION=ap-southeast-2
S3_ACCESS_KEY_ID=<your-access-key>
S3_SECRET_ACCESS_KEY=<your-secret-key>
S3_UPLOAD_ON_COMPLETION=true
S3_PREFIX=agar/

# Run Management
ARCHIVE_AFTER_DAYS=7
DELETE_AFTER_DAYS=30
DELETION_STRATEGY=soft

# Storage Paths
STORAGE_BASE_PATH=./scraper_data
STORAGE_JOBS_PATH=./scraper_data/jobs
ARCHIVE_BASE_PATH=./scraper_data/archive

# Crawl4AI Service
CRAWL4AI_API_URL=http://crawl4ai-service:11235
```

### Docker Compose Configuration

**Production Deployment** (`docker-compose.prod.yml`):

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: scraper-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G

  redis:
    image: redis:7-alpine
    container_name: scraper-redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M

  crawl4ai-service:
    image: unclecode/crawl4ai:latest
    container_name: crawl4ai-service
    ports:
      - "11235:11235"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11235/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G

  api:
    build: .
    container_name: scraper-api
    command: uvicorn api.main:app --host 0.0.0.0 --port 3010
    ports:
      - "3010:3010"
    env_file:
      - .env
    volumes:
      - ./scraper_data:/app/scraper_data
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      crawl4ai-service:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3010/api/scraper/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G

  celery-worker:
    build: .
    container_name: scraper-celery-worker
    command: celery -A api.jobs.celery_app worker --loglevel=info
    env_file:
      - .env
    volumes:
      - ./scraper_data:/app/scraper_data
      - ./logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      crawl4ai-service:
        condition: service_healthy
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G

  ui:
    build:
      context: ./ui
      dockerfile: Dockerfile
    container_name: scraper-ui
    ports:
      - "8080:8080"
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 128M

volumes:
  postgres_data:
```

---

## User Interface Operations

### Accessing the Dashboard

**Production URL**: `https://askagar.com`
**Development URL**: `http://localhost:8080`

### Authentication

#### Registration
1. Navigate to the UI homepage
2. Click **Register**
3. Provide:
   - Username (unique)
   - Email address
   - Full name
   - Password (minimum 8 characters)
4. Click **Create Account**
5. You'll be automatically logged in

#### Login
1. Enter username or email
2. Enter password
3. Click **Login**
4. JWT tokens are stored in browser localStorage
5. Auto-refresh keeps you logged in for 7 days

### Creating a Scraping Job

#### Step 1: Navigate to Create Job Tab

Click the **Create Job** tab in the navigation bar.

#### Step 2: Configure Basic Information

- **Job Name** (required): Descriptive name for the scraping run
  - Example: `Agar Full Catalog - January 2025`
- **Description** (optional): Additional context
  - Example: `Complete product catalog scrape for quarterly update`

#### Step 3: Configure Scraping Parameters

**Start URLs** (required):
```
https://www.agar.com.au
```

**Advanced Settings**:
- **Max Pages**: Maximum number of product pages to scrape
  - Default: `100`
  - Full scrape: `0` (unlimited)
  - Test run: `10-20`
- **Crawl Depth**: How deep to follow links
  - Recommended: `3` (homepage → categories → products)
- **Follow Links**: Enable to discover linked pages
  - Recommended: `Yes` for full catalog
- **Respect robots.txt**: Honor site crawling rules
  - Recommended: `Yes` for production

#### Step 4: Configure Output Settings

**File Format**:
- `JSON` (recommended for data processing)
- `Markdown` (for documentation)
- `HTML` (for archival)

**Save Files Locally**: Always `Yes` (enables local storage before S3 upload)

#### Step 5: Configure S3 Upload (Optional but Recommended)

- **Enable S3 Upload**: `Yes`
- **S3 Bucket**: Leave empty to use default (`agar-documentation`)
- **S3 Path Prefix**: Leave empty to use default (`agar/`)
- **Upload PDFs**: `Yes` (includes SDS and PDS documents)
- **Upload Screenshots**: `No` (unless needed for debugging)
- **Upload Categories**: `Yes` (includes category metadata)

#### Step 6: Submit Job

Click **Create Job** button. You'll be redirected to the Jobs tab with your new job visible.

### Monitoring a Scraping Job

#### Real-Time Progress

Jobs display real-time progress indicators:

- **Status Badge**:
  - `Pending` (gray): Queued, waiting to start
  - `Running` (blue): Currently executing
  - `Completed` (green): Finished successfully
  - `Failed` (red): Encountered errors
  - `Cancelled` (dark gray): Manually stopped

- **Progress Bar**: Visual representation of completion
  - Shows pages scraped vs. total pages
  - Updates every 5 seconds

- **Statistics**:
  - Items extracted
  - Categories found
  - Products found
  - Errors encountered

#### Job Details View

Click any job card to view detailed information:

**Info Tab**:
- Job configuration
- Current status and progress
- Start/completion timestamps
- Full configuration JSON
- Output file locations

**Logs Tab**:
- Real-time job logs
- Color-coded by severity (INFO, WARNING, ERROR)
- Last 100 log entries
- Timestamp for each entry

**Results Tab**:
- Scraped data preview
- Product information
- PDF links
- Pagination (50 items per page)

### Managing Jobs

#### Pause a Running Job
1. Click the job card
2. Click **Pause** button
3. Job state is saved, can be resumed later

#### Resume a Paused Job
1. Click the paused job card
2. Click **Resume** button
3. Job continues from where it paused

#### Cancel a Job
1. Click the job card
2. Click **Cancel** button
3. Confirm cancellation
4. Job stops immediately, partial results are saved

#### Delete a Completed/Failed Job
1. Click the job card
2. Click **Delete** button
3. Confirm deletion
4. Job and local files are removed (S3 files remain)

### Dashboard Statistics

The **Overview** tab displays aggregate statistics:

- **Total Jobs**: All jobs created
- **Running Jobs**: Currently executing
- **Queued Jobs**: Waiting to start
- **Completed Jobs**: Successfully finished
- **Failed Jobs**: Encountered errors
- **Total Pages Scraped**: Across all jobs

Auto-refreshes every 5 seconds to show current status.

---

## Data Storage and Access

### File System Storage

#### Directory Structure

```
scraper_data/
├── jobs/                                    # Active jobs (0-7 days)
│   ├── 20250122_143052_8dafff36-6b15-478a-88fc-19cdbbcfca5f5/
│   │   ├── all_products.json               # All scraped products with metadata
│   │   ├── categories.json                 # Discovered categories
│   │   ├── results.json                    # Consolidated results
│   │   ├── products/                       # Individual product JSON files
│   │   │   ├── product_001.json
│   │   │   └── product_002.json
│   │   ├── PDFs/                           # Downloaded PDF documents
│   │   │   ├── [product-name]/
│   │   │   │   ├── [product-name]_SDS.pdf  # Safety Data Sheet
│   │   │   │   └── [product-name]_PDS.pdf  # Product Data Sheet
│   │   └── screenshots/                    # Product page screenshots
│   │       ├── product_001.png
│   │       └── product_002.png
│   └── 20250123_091230_a1b2c3d4-e5f6-7890-abcd-ef1234567890/
│       └── ...
│
├── archive/                                 # Archived jobs (7-30 days)
│   └── 2025/
│       └── 01/
│           ├── 20250106_143052_uuid.tar.gz  # Compressed archive
│           └── 20250107_091230_uuid.tar.gz
│
└── exports/                                 # Manual exports (future feature)
```

#### Folder Naming Convention

Format: `YYYYMMDD_HHMMSS_{job_id}`

**Example**: `20250122_143052_8dafff36-6b15-478a-88fc-19cdbbcfca5f5`

- **Date**: `20250122` → January 22, 2025
- **Time**: `143052` → 14:30:52 (2:30:52 PM)
- **Job ID**: UUID for uniqueness and database reference

**Benefits**:
- Human-readable and sortable chronologically
- Easy to identify run date without checking database
- Unique identifier prevents conflicts

#### Data Files

| File | Description | Format | Size (typical) |
|------|-------------|--------|----------------|
| `all_products.json` | Complete product data with metadata | JSON | 2-10 MB |
| `categories.json` | Discovered category hierarchy | JSON | 50-200 KB |
| `results.json` | Consolidated scraping results | JSON | 2-10 MB |
| `products/product_*.json` | Individual product details | JSON | 5-20 KB each |
| `PDFs/*.pdf` | Product documentation | PDF | 100 KB - 5 MB each |
| `screenshots/*.png` | Product page screenshots | PNG | 200-500 KB each |

### Database Storage

#### Schema Overview

The PostgreSQL database stores job metadata, state, and relationships.

**Key Tables**:

1. **jobs** - Job metadata and status
2. **users** - User accounts and authentication
3. **logs** - Job execution logs
4. **job_audit** - Deletion audit trail

#### Jobs Table Structure

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,

    -- Configuration
    config JSONB NOT NULL,           -- Scraping parameters
    output JSONB,                    -- Output configuration and S3 metadata

    -- Folder management
    folder_name VARCHAR(255) INDEX,  -- YYYYMMDD_HHMMSS format

    -- Progress tracking
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    pages_scraped INTEGER DEFAULT 0,
    total_pages INTEGER,
    progress NUMERIC(5,2),           -- Percentage (0.00 - 100.00)

    -- Statistics
    stats JSONB,                     -- items_extracted, errors, retries, etc.

    -- Archival tracking
    archived_at TIMESTAMP WITH TIME ZONE,
    archive_path VARCHAR(512),

    -- Soft deletion
    deleted_at TIMESTAMP WITH TIME ZONE,
    deletion_reason TEXT,

    -- Ownership
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_jobs_status ON jobs(status);
CREATE INDEX ix_jobs_created_at ON jobs(created_at);
CREATE INDEX ix_jobs_folder_name ON jobs(folder_name);
CREATE INDEX ix_jobs_archived_at ON jobs(archived_at);
```

#### Sample Job Record

```json
{
  "id": "8dafff36-6b15-478a-88fc-19cdbbcfca5f5",
  "name": "Agar Full Catalog - January 2025",
  "description": "Complete product catalog scrape",
  "type": "web",
  "status": "completed",
  "folder_name": "20250122_143052",

  "config": {
    "startUrls": ["https://www.agar.com.au"],
    "maxPages": 0,
    "crawlDepth": 3,
    "client_name": "agar",
    "test_mode": false,
    "save_screenshots": true
  },

  "output": {
    "saveFiles": true,
    "fileFormat": "json",
    "uploadToS3": {
      "enabled": true,
      "status": "success",
      "uploadedAt": "2025-01-22T15:30:25.123456Z",
      "filesUploaded": 520,
      "bytesUploaded": 52428800,
      "s3Urls": {
        "all_products_json": "s3://agar-documentation/agar/20250122_143052_8dafff36.../all_products.json",
        "categories_json": "s3://agar-documentation/agar/20250122_143052_8dafff36.../categories.json",
        "pdfs_dir": "s3://agar-documentation/agar/20250122_143052_8dafff36.../pdfs/"
      }
    }
  },

  "stats": {
    "items_extracted": 512,
    "categories_found": 58,
    "products_found": 512,
    "pdfs_downloaded": 987,
    "bytes_downloaded": 52428800,
    "errors": 3,
    "retries": 7
  },

  "started_at": "2025-01-22T14:30:52Z",
  "completed_at": "2025-01-22T15:28:15Z",
  "pages_scraped": 512,
  "total_pages": 512,
  "progress": 100.00,

  "created_by": "396fc713-56b4-4c1c-a005-515bd7f1482c",
  "created_at": "2025-01-22T14:30:45Z",
  "updated_at": "2025-01-22T15:30:30Z"
}
```

#### Querying Job Data

**Get job with S3 URLs**:
```sql
SELECT
    id,
    name,
    folder_name,
    status,
    output->'uploadToS3'->'s3Urls'->>'all_products_json' as s3_products_url,
    output->'uploadToS3'->>'status' as upload_status,
    stats->>'items_extracted' as items,
    completed_at
FROM jobs
WHERE status = 'completed'
  AND output->'uploadToS3'->>'status' = 'success'
ORDER BY completed_at DESC
LIMIT 10;
```

**Get active jobs**:
```sql
SELECT id, name, status, progress, pages_scraped, total_pages
FROM jobs
WHERE status IN ('pending', 'running')
ORDER BY created_at DESC;
```

**Get storage statistics**:
```sql
SELECT
    status,
    COUNT(*) as job_count,
    SUM((stats->>'bytes_downloaded')::bigint) as total_bytes,
    AVG((stats->>'items_extracted')::integer) as avg_items
FROM jobs
WHERE deleted_at IS NULL
GROUP BY status;
```

### S3 Storage

#### Bucket Structure

```
s3://agar-documentation/
└── agar/
    ├── 20250122_143052_8dafff36-6b15-478a-88fc-19cdbbcfca5f5/
    │   ├── all_products.json
    │   ├── categories.json
    │   ├── results.json
    │   ├── pdfs/
    │   │   ├── Product-A_SDS.pdf
    │   │   ├── Product-A_PDS.pdf
    │   │   ├── Product-B_SDS.pdf
    │   │   └── Product-B_PDS.pdf
    │   └── screenshots/             # Optional
    │       ├── product_001.png
    │       └── product_002.png
    └── 20250123_091230_a1b2c3d4-e5f6-7890-abcd-ef1234567890/
        └── ...
```

#### S3 Configuration

- **Bucket Name**: `agar-documentation`
- **Region**: `ap-southeast-2` (Sydney)
- **Prefix**: `agar/`
- **IAM User**: `agar-s3-user`

**Required IAM Permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::agar-documentation/*",
        "arn:aws:s3:::agar-documentation"
      ]
    }
  ]
}
```

#### Accessing S3 Data

**Using AWS CLI**:

List all scraping runs:
```bash
aws s3 ls s3://agar-documentation/agar/ \
  --region ap-southeast-2
```

List files in a specific run:
```bash
aws s3 ls s3://agar-documentation/agar/20250122_143052_8dafff36.../ \
  --recursive --human-readable
```

Download all files from a run:
```bash
aws s3 sync \
  s3://agar-documentation/agar/20250122_143052_8dafff36.../ \
  ./local_download/ \
  --region ap-southeast-2
```

Download a specific file:
```bash
aws s3 cp \
  s3://agar-documentation/agar/20250122_143052_8dafff36.../all_products.json \
  ./all_products.json \
  --region ap-southeast-2
```

**Using Boto3 (Python)**:

```python
import boto3
import json

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name='ap-southeast-2',
    aws_access_key_id='YOUR_ACCESS_KEY',
    aws_secret_access_key='YOUR_SECRET_KEY'
)

# Download and parse product data
bucket = 'agar-documentation'
key = 'agar/20250122_143052_8dafff36.../all_products.json'

response = s3_client.get_object(Bucket=bucket, Key=key)
products = json.loads(response['Body'].read().decode('utf-8'))

# Process products
for product in products:
    print(f"{product['product_name']}: {product['product_url']}")
```

**Using API**:

Query the database to get S3 URLs, then download directly:

```bash
# Get job details including S3 URLs
curl -X GET "https://askagar.com/api/scraper/jobs/{job_id}" \
  -H "Authorization: Bearer {token}" | jq '.data.output.uploadToS3.s3Urls'

# Output:
{
  "all_products_json": "s3://agar-documentation/agar/20250122_143052.../all_products.json",
  "categories_json": "s3://agar-documentation/agar/20250122_143052.../categories.json",
  "pdfs_dir": "s3://agar-documentation/agar/20250122_143052.../pdfs/"
}
```

### Knowledge Graph Integration (Memento)

The scraper integrates with the Memento Knowledge Graph API to populate entities and relationships for the Ask Agar assistant.

#### Product Application Matrix

A Product Application Matrix (`AskAgar_ProductsData_v1.xlsx`) contains structured data about:
- **Surfaces**: What surfaces each product is suitable for (or incompatible with)
- **Soilage**: What types of soilage each product handles
- **Locations**: Where each product should be used (hospitals, kitchens, etc.)
- **Benefits**: Key benefits of each product

**S3 Location**:
```
s3://agar-documentation/agar/reference-data/application-matrix/AskAgar_ProductsData_v1.xlsx
```

#### Entity Types Created

| Entity Type | Description | Example Count |
|------------|-------------|---------------|
| Product | Cleaning products | ~200 |
| Surface | Floor/wall types | ~600 |
| Soilage | Dirt/stain types | ~370 |
| Location | Usage locations | ~190 |
| Benefit | Product benefits | ~740 |

#### Relationship Types

| Relationship | Description |
|-------------|-------------|
| `SUITABLE_FOR` | Product works well on this surface |
| `INCOMPATIBLE_WITH` | Product should NOT be used on this surface |
| `HANDLES` | Product effectively cleans this soilage type |
| `UNSUITABLE_FOR` | Product cannot handle this soilage |
| `USED_IN` | Product is designed for this location |
| `HAS_BENEFIT` | Product provides this benefit |

#### Enabling Knowledge Graph Processing

1. **Set environment variables** in `.env`:
```bash
MEMENTO_ENABLED=true
MEMENTO_API_URL=https://your-memento-api-url
MEMENTO_API_KEY=your-api-key
MEMENTO_DEFAULT_INSTANCE=ask-agar
```

2. **Processing triggers automatically** after each scraping job completes (if enabled)

3. **Manual processing** can be triggered via Celery:
```python
from api.jobs.tasks import process_application_matrix

# Process with existing scraped data
result = process_application_matrix.delay(
    matrix_file_path="/app/scraper_data/reference/AskAgar_ProductsData_v1.xlsx",
    scraped_products_path="/app/scraper_data/jobs/latest/all_products.json",
)
```

#### Testing Matrix Processing

Run the test script to verify parsing without sending to Memento:
```bash
python scripts/test_matrix_processing.py --matrix-file scraper_data/reference/AskAgar_ProductsData_v1.xlsx
```

Expected output:
```
Products:      201
Entities:      2096
Relationships: 4204
Match rate:    93.5%
```

---

### Data Lifecycle Management

#### Active Phase (0-7 days)

- **Location**: `/app/scraper_data/jobs/{folder_name}_{job_id}/`
- **Access**: Full read/write via API and file system
- **Status**: All job data immediately available
- **Actions**: Job monitoring, result viewing, data processing

#### Archive Phase (7-30 days)

- **Location**: `/app/scraper_data/archive/{YYYY}/{MM}/{folder_name}_{job_id}.tar.gz`
- **Access**: Read-only via restoration API
- **Compression**: tar.gz (40-60% space savings)
- **Restoration**: On-demand decompression back to active storage

**Automatic Archival** (runs daily at 2:00 AM):
```python
# Celery task: api.jobs.maintenance_tasks.archive_old_runs
# Archives completed jobs older than 7 days
```

**Manual Archival**:
```bash
curl -X POST "https://askagar.com/api/maintenance/archive?days=7" \
  -H "Authorization: Bearer {admin_token}"
```

#### Deletion Phase (30+ days)

- **Location**: N/A (removed from file system)
- **Database**: Soft delete (record retained) or hard delete (record removed)
- **Audit Trail**: Summary statistics preserved in `job_audit` table
- **S3 Data**: Remains in S3 bucket (configurable retention)

**Automatic Deletion** (runs daily at 3:00 AM):
```python
# Celery task: api.jobs.maintenance_tasks.cleanup_old_runs
# Deletes archived jobs older than 30 days
```

**Manual Deletion**:
```bash
curl -X POST "https://askagar.com/api/maintenance/cleanup?days=30&strategy=soft" \
  -H "Authorization: Bearer {admin_token}"
```

#### Configuration

Set retention periods in `.env`:

```bash
ARCHIVE_AFTER_DAYS=7      # Archive completed jobs after 7 days
DELETE_AFTER_DAYS=30      # Delete archived jobs after 30 days
DELETION_STRATEGY=soft     # 'soft' (keep DB record) or 'hard' (remove all)
```

---

## AWS LightSail Deployment

### Prerequisites

#### Required Resources

- **AWS Account** with billing enabled
- **Domain Name**: `askagar.com` (or subdomain)
- **DNS Access**: Ability to create A records
- **SSH Key Pair**: For server access
- **S3 Credentials**: IAM user with S3 permissions

#### LightSail Instance Specifications

**Recommended Production Configuration**:

| Specification | Value |
|---------------|-------|
| **Plan** | 8GB RAM / 4 vCPUs |
| **Storage** | 160GB SSD |
| **Operating System** | Ubuntu 22.04 LTS |
| **Region** | Sydney (ap-southeast-2) |
| **Monthly Cost** | ~$48 USD |

**Minimum Development Configuration**:

| Specification | Value |
|---------------|-------|
| **Plan** | 4GB RAM / 2 vCPUs |
| **Storage** | 80GB SSD |
| **Operating System** | Ubuntu 22.04 LTS |
| **Monthly Cost** | ~$24 USD |

### Step-by-Step Deployment

#### Step 1: Create LightSail Instance

1. Log in to [AWS LightSail Console](https://lightsail.aws.amazon.com/)
2. Click **Create instance**
3. Select **Instance location**: Sydney (ap-southeast-2-a)
4. Select **Platform**: Linux/Unix
5. Select **Blueprint**: OS Only → Ubuntu 22.04 LTS
6. Select **Instance plan**: 8GB ($48/month) or 4GB ($24/month)
7. **Name your instance**: `ask-agar-scraper`
8. Click **Create instance**

#### Step 2: Configure Networking

**Create Static IP**:
1. Go to **Networking** tab
2. Click **Create static IP**
3. Attach to your instance
4. Name: `ask-agar-static-ip`
5. Note the IP address (e.g., `13.238.XXX.XXX`)

**Configure Firewall**:
1. Go to instance **Networking** tab
2. Under **IPv4 Firewall**, add rules:

| Application | Protocol | Port | Source |
|-------------|----------|------|--------|
| SSH | TCP | 22 | Your IP (restricted) |
| HTTP | TCP | 80 | Anywhere |
| HTTPS | TCP | 443 | Anywhere |

#### Step 3: Configure DNS

Point your domain to the LightSail static IP:

```dns
Type: A
Name: @  (or askagar)
Value: 13.238.XXX.XXX
TTL: 300
```

Wait for DNS propagation (5-60 minutes). Verify:

```bash
dig askagar.com +short
# Should return: 13.238.XXX.XXX
```

#### Step 4: SSH Access and Initial Setup

**Connect via SSH**:

```bash
# Download SSH key from LightSail console
chmod 400 ~/Downloads/LightsailDefaultKey-ap-southeast-2.pem

# Connect
ssh -i ~/Downloads/LightsailDefaultKey-ap-southeast-2.pem ubuntu@13.238.XXX.XXX
```

**Update System**:

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

Wait 2 minutes, then reconnect.

#### Step 5: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo apt install docker-compose -y

# Verify installations
docker --version
docker-compose --version

# Log out and back in for group membership
exit
```

Reconnect via SSH.

#### Step 6: Clone Repository and Configure

```bash
# Create app directory
mkdir -p ~/apps
cd ~/apps

# Clone repository
git clone https://github.com/vargamick/agar-scraper.git
cd agar-scraper

# Create environment file
cp deployment/production.env .env
nano .env
```

**Configure `.env` file**:

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

# Database (use strong password)
POSTGRES_PASSWORD=$(openssl rand -base64 24)

# AWS S3
S3_ENABLED=true
S3_BUCKET_NAME=agar-documentation
S3_REGION=ap-southeast-2
S3_ACCESS_KEY_ID=<YOUR_ACCESS_KEY>
S3_SECRET_ACCESS_KEY=<YOUR_SECRET_KEY>

# CORS
CORS_ORIGINS=https://askagar.com,https://www.askagar.com

# Other settings use defaults
```

Save and exit (`Ctrl+X`, `Y`, `Enter`).

#### Step 7: Build and Start Services

```bash
# Build containers
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

Wait for all services to be healthy (2-3 minutes). Press `Ctrl+C` to exit logs.

#### Step 8: Create Admin User

```bash
docker-compose -f docker-compose.prod.yml exec api python /app/scripts/utilities/create_admin.py
```

Follow prompts to create admin account:
- Username: `admin`
- Password: (choose strong password)
- Email: `admin@askagar.com`
- Full Name: `Administrator`

#### Step 9: Install and Configure Nginx

**Install Nginx**:

```bash
sudo apt install nginx -y
```

**Create site configuration**:

```bash
sudo nano /etc/nginx/sites-available/askagar
```

**Paste configuration** (from `deployment/nginx/askagar.conf`):

```nginx
upstream api_backend {
    server localhost:3010;
}

upstream ui_backend {
    server localhost:8080;
}

server {
    listen 80;
    server_name askagar.com www.askagar.com;

    # Redirect to HTTPS (will be handled by Certbot)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name askagar.com www.askagar.com;

    # SSL certificates (managed by Certbot)
    # ssl_certificate /etc/letsencrypt/live/askagar.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/askagar.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API endpoints
    location /api/ {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }

    # UI
    location / {
        proxy_pass http://ui_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Save and exit.

**Enable site**:

```bash
sudo ln -s /etc/nginx/sites-available/askagar /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 10: Install SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d askagar.com -d www.askagar.com

# Follow prompts:
# - Enter email address
# - Agree to Terms of Service
# - Choose whether to share email
# - Certbot will automatically configure SSL
```

**Verify SSL**:
- Visit `https://askagar.com` in browser
- Should show secure padlock icon

#### Step 11: Configure Auto-Start

Create systemd service:

```bash
sudo nano /etc/systemd/system/agar-scraper.service
```

Paste:

```ini
[Unit]
Description=Agar Web Scraper
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/apps/agar-scraper
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable agar-scraper
sudo systemctl start agar-scraper
sudo systemctl status agar-scraper
```

#### Step 12: Configure Firewall

```bash
# Enable firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Verify
sudo ufw status
```

#### Step 13: Verify Deployment

**Test Health Endpoints**:

```bash
# API health
curl https://askagar.com/api/scraper/health

# Expected output:
{"status":"healthy","version":"1.0.0"}
```

**Test UI**:
- Visit `https://askagar.com` in browser
- Should see login page

**Test Job Creation**:
1. Log in with admin credentials
2. Navigate to **Create Job** tab
3. Create a small test job (10 pages)
4. Monitor in **Jobs** tab
5. Verify completion and S3 upload

#### Step 14: Set Up Monitoring

**Create monitoring script**:

```bash
nano ~/monitor.sh
```

Paste (from `deployment/scripts/monitor.sh`):

```bash
#!/bin/bash
# Health monitoring script

cd ~/apps/agar-scraper

# Check container health
UNHEALTHY=$(docker ps --filter "health=unhealthy" -q)

if [ ! -z "$UNHEALTHY" ]; then
    echo "WARNING: Unhealthy containers detected"
    docker ps --filter "health=unhealthy"
    # Optional: Send alert email
fi

# Check API health
API_HEALTH=$(curl -s https://askagar.com/api/scraper/health | jq -r '.status')

if [ "$API_HEALTH" != "healthy" ]; then
    echo "WARNING: API health check failed"
    # Optional: Send alert email
fi

# Check disk space
DISK_USAGE=$(df -h /home/ubuntu/apps/agar-scraper/scraper_data | awk 'NR==2 {print $5}' | sed 's/%//')

if [ "$DISK_USAGE" -gt 80 ]; then
    echo "WARNING: Disk usage is $DISK_USAGE%"
    # Optional: Send alert email
fi
```

Make executable and schedule:

```bash
chmod +x ~/monitor.sh

# Add to crontab
crontab -e

# Add lines:
# */5 * * * * ~/monitor.sh >> ~/monitor.log 2>&1
# 0 2 * * * ~/apps/agar-scraper/deployment/scripts/backup.sh
```

### Post-Deployment Verification Checklist

- [ ] All Docker containers running and healthy
- [ ] API accessible at `https://askagar.com/api/scraper/health`
- [ ] UI accessible at `https://askagar.com`
- [ ] SSL certificate valid and auto-renewing
- [ ] Admin account created and can login
- [ ] Test job completes successfully
- [ ] S3 upload works and files are in bucket
- [ ] Monitoring cron jobs configured
- [ ] Firewall configured and enabled
- [ ] Auto-start service enabled
- [ ] Database backups configured

---

## Monitoring and Maintenance

### Health Monitoring

#### Container Health

**Check container status**:

```bash
docker-compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                    STATUS                   PORTS
scraper-postgres        Up (healthy)
scraper-redis           Up (healthy)
scraper-api             Up (healthy)             0.0.0.0:3010->3010/tcp
scraper-celery-worker   Up
scraper-ui              Up                       0.0.0.0:8080->8080/tcp
crawl4ai-service        Up (healthy)             0.0.0.0:11235->11235/tcp
```

**Check resource usage**:

```bash
docker stats
```

#### API Health Endpoint

```bash
curl https://askagar.com/api/scraper/health | jq
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy",
    "crawl4ai": "healthy"
  },
  "uptime_seconds": 86400
}
```

#### Database Health

```bash
docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U scraper_user
```

#### Queue Health

```bash
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Log Management

#### View Logs

**All services**:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

**Specific service**:
```bash
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f celery-worker
```

**Last N lines**:
```bash
docker-compose -f docker-compose.prod.yml logs --tail=100 api
```

**Filter by time**:
```bash
docker-compose -f docker-compose.prod.yml logs --since="2025-01-22T10:00:00" api
```

#### Log Rotation

Docker automatically rotates logs. Configure in `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Apply:
```bash
sudo systemctl restart docker
```

### Database Maintenance

#### Backup Database

**Manual backup**:

```bash
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
  -U scraper_user scraper_db > ~/backups/scraper_db_$(date +%Y%m%d_%H%M%S).sql
```

**Automated backup** (configured in crontab):

```bash
#!/bin/bash
# deployment/scripts/backup.sh

BACKUP_DIR=~/backups/agar-scraper
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
  -U scraper_user scraper_db | gzip > $BACKUP_DIR/database_$TIMESTAMP.sql.gz

# Backup scraper data
tar -czf $BACKUP_DIR/scraper_data_$TIMESTAMP.tar.gz scraper_data/

# Optional: Upload to S3
if [ "$S3_BACKUP_ENABLED" = "true" ]; then
    aws s3 cp $BACKUP_DIR/database_$TIMESTAMP.sql.gz \
      s3://agar-documentation/backups/database/ \
      --region ap-southeast-2
fi

# Clean up old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

#### Restore Database

```bash
# Stop services
docker-compose -f docker-compose.prod.yml stop api celery-worker

# Restore
gunzip < ~/backups/agar-scraper/database_20250122_020000.sql.gz | \
  docker-compose -f docker-compose.prod.yml exec -T postgres psql \
  -U scraper_user scraper_db

# Restart services
docker-compose -f docker-compose.prod.yml start api celery-worker
```

### Storage Management

#### Check Disk Usage

```bash
# Overall disk usage
df -h

# Scraper data usage
du -sh ~/apps/agar-scraper/scraper_data/*

# Docker usage
docker system df
```

#### Clean Up Old Data

**Manual cleanup**:

```bash
# Remove jobs older than 30 days
find ~/apps/agar-scraper/scraper_data/jobs -type d -mtime +30 -exec rm -rf {} +

# Clean Docker resources
docker system prune -a --volumes
```

**Automated cleanup** (configured maintenance tasks):

API endpoints for storage management:

```bash
# Get storage statistics
curl -X GET "https://askagar.com/api/maintenance/storage-stats" \
  -H "Authorization: Bearer {token}"

# Archive jobs older than 7 days
curl -X POST "https://askagar.com/api/maintenance/archive?days=7" \
  -H "Authorization: Bearer {admin_token}"

# Delete archived jobs older than 30 days
curl -X POST "https://askagar.com/api/maintenance/cleanup?days=30&strategy=soft" \
  -H "Authorization: Bearer {admin_token}"
```

### System Updates

#### Update Application

```bash
cd ~/apps/agar-scraper

# Pull latest code
git pull origin master

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Verify
docker-compose -f docker-compose.prod.yml ps
```

#### Update System Packages

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Reboot if kernel updated
sudo reboot
```

#### Update SSL Certificate

Certbot auto-renews certificates. Verify:

```bash
sudo certbot renew --dry-run
```

Force renewal (if needed):

```bash
sudo certbot renew --force-renewal
sudo systemctl reload nginx
```

### Performance Monitoring

#### Container Resource Limits

Set in `docker-compose.prod.yml`:

```yaml
services:
  celery-worker:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

#### Monitor Performance

**Real-time stats**:
```bash
docker stats
```

**Prometheus metrics** (future enhancement):
- Integrate Prometheus for metrics collection
- Grafana dashboards for visualization

---

## Integration with Coolify

### What is Coolify?

[Coolify](https://coolify.io/) is an open-source, self-hostable platform-as-a-service (PaaS) alternative to Heroku/Netlify. It provides a web UI for deploying and managing applications with Git integration, automatic SSL, and monitoring.

### Benefits for Ask Agar Scraper

- **Simplified Deployment**: Deploy from GitHub with one click
- **Automatic Updates**: Git push triggers automatic rebuilds
- **Built-in Monitoring**: Resource usage and health monitoring
- **Environment Management**: Manage environment variables via UI
- **Automatic SSL**: Let's Encrypt integration
- **Backup Management**: Built-in backup and restore

### Coolify Deployment Requirements

#### Server Requirements

- **OS**: Ubuntu 22.04 LTS (same as current LightSail)
- **RAM**: 8GB minimum (same as current)
- **Storage**: 160GB SSD (same as current)
- **Docker**: 24.0+ (already installed)
- **Open Ports**: 22, 80, 443, 8000 (Coolify dashboard)

#### Coolify Installation

On LightSail instance:

```bash
curl -fsSL https://get.coolify.io | bash
```

This installs:
- Coolify server
- Traefik reverse proxy
- PostgreSQL (for Coolify metadata)
- Docker registry (optional)

Access Coolify dashboard: `https://askagar.com:8000`

### Preparing Repository for Coolify

#### Required Files

1. **Dockerfile** (already exists)
2. **docker-compose.yml** (already exists as `docker-compose.prod.yml`)
3. **.coolify.yml** (create new)

#### Create `.coolify.yml`

In repository root:

```yaml
# .coolify.yml
version: '1.0'

project:
  name: ask-agar-scraper
  description: Agar product catalog web scraper

services:
  - name: postgres
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: $POSTGRES_USER
      POSTGRES_PASSWORD: $POSTGRES_PASSWORD
      POSTGRES_DB: $POSTGRES_DB
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "$POSTGRES_USER"]
      interval: 10s
      timeout: 5s
      retries: 5

  - name: redis
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  - name: crawl4ai
    image: unclecode/crawl4ai:latest
    ports:
      - "11235:11235"

  - name: api
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3010:3010"
    environment:
      - DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$POSTGRES_DB
      - REDIS_URL=redis://redis:6379/0
      - S3_ENABLED=$S3_ENABLED
      - S3_BUCKET_NAME=$S3_BUCKET_NAME
      - S3_ACCESS_KEY_ID=$S3_ACCESS_KEY_ID
      - S3_SECRET_ACCESS_KEY=$S3_SECRET_ACCESS_KEY
    depends_on:
      - postgres
      - redis
      - crawl4ai
    volumes:
      - scraper_data:/app/scraper_data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3010/api/scraper/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  - name: celery-worker
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A api.jobs.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@postgres:5432/$POSTGRES_DB
      - REDIS_URL=redis://redis:6379/0
      - S3_ENABLED=$S3_ENABLED
      - S3_BUCKET_NAME=$S3_BUCKET_NAME
      - S3_ACCESS_KEY_ID=$S3_ACCESS_KEY_ID
      - S3_SECRET_ACCESS_KEY=$S3_SECRET_ACCESS_KEY
    depends_on:
      - postgres
      - redis
      - crawl4ai
    volumes:
      - scraper_data:/app/scraper_data

  - name: ui
    build:
      context: ./ui
      dockerfile: Dockerfile
    ports:
      - "8080:8080"

volumes:
  postgres_data:
  scraper_data:

routes:
  - domain: askagar.com
    service: ui
    port: 8080
    ssl: true
  - domain: askagar.com
    path: /api
    service: api
    port: 3010
    ssl: true
```

Commit and push to GitHub:

```bash
git add .coolify.yml
git commit -m "Add Coolify deployment configuration"
git push origin master
```

### Deploying to Coolify

#### 1. Connect GitHub Repository

1. Log in to Coolify dashboard: `https://askagar.com:8000`
2. Go to **Projects** → **New Project**
3. Name: `Ask Agar Scraper`
4. Click **Create**

#### 2. Add Application

1. In project, click **New Resource** → **Application**
2. Select **GitHub** as source
3. Authorize GitHub access
4. Select repository: `vargamick/agar-scraper`
5. Branch: `master`
6. Build method: **Docker Compose**
7. Docker Compose file: `docker-compose.prod.yml` (or `.coolify.yml` if created)

#### 3. Configure Environment Variables

In Coolify UI, add environment variables:

| Variable | Value |
|----------|-------|
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `SECRET_KEY` | (generate with `openssl rand -hex 32`) |
| `POSTGRES_USER` | `scraper_user` |
| `POSTGRES_PASSWORD` | (strong password) |
| `POSTGRES_DB` | `scraper_db` |
| `S3_ENABLED` | `true` |
| `S3_BUCKET_NAME` | `agar-documentation` |
| `S3_REGION` | `ap-southeast-2` |
| `S3_ACCESS_KEY_ID` | (your AWS key) |
| `S3_SECRET_ACCESS_KEY` | (your AWS secret) |
| `CORS_ORIGINS` | `https://askagar.com` |

#### 4. Configure Domains

1. Go to **Domains** tab
2. Add domain: `askagar.com`
3. Enable **SSL/TLS** (automatic Let's Encrypt)
4. Add domain: `api.askagar.com` (optional, for API-only access)

#### 5. Deploy

1. Click **Deploy** button
2. Coolify will:
   - Clone repository
   - Build Docker images
   - Start containers
   - Configure SSL
   - Set up health checks

Monitor deployment in **Deployments** tab.

#### 6. Post-Deployment

1. **Create admin user**:
   - Go to **Terminal** tab
   - Select `api` container
   - Run: `python /app/scripts/utilities/create_admin.py`

2. **Verify deployment**:
   - Visit `https://askagar.com`
   - Test job creation
   - Verify S3 upload

### Coolify Benefits

#### Automatic Deployments

- **Git Push to Deploy**: Push to `master` branch automatically triggers rebuild
- **Rollback**: Easy rollback to previous deployments
- **Preview Environments**: Create preview deployments from feature branches

#### Monitoring

- **Resource Usage**: CPU, memory, disk usage per container
- **Logs**: Centralized log viewing
- **Health Checks**: Automatic health monitoring with alerts
- **Uptime**: Service uptime tracking

#### Backup and Restore

- **Database Backups**: Scheduled PostgreSQL backups
- **Volume Backups**: Automatic volume snapshots
- **One-Click Restore**: Restore from any backup point

#### Environment Management

- **Secrets Management**: Secure environment variable storage
- **Multiple Environments**: Separate production, staging, development
- **Environment Sync**: Copy environments for testing

### Migration from Manual to Coolify

#### Pre-Migration Checklist

- [ ] Backup current database
- [ ] Backup current scraper data
- [ ] Document current environment variables
- [ ] Test `.coolify.yml` configuration locally
- [ ] Ensure GitHub repository is up to date

#### Migration Steps

1. **Install Coolify** on current LightSail instance
2. **Deploy via Coolify** alongside manual deployment
3. **Test Coolify deployment** thoroughly
4. **Migrate data**:
   - Export database from manual deployment
   - Import into Coolify deployment
5. **Update DNS** to point to Coolify deployment
6. **Shut down manual deployment** after verification
7. **Remove manual deployment resources**

#### Rollback Plan

If issues occur:
1. Revert DNS to manual deployment IP
2. Restart manual deployment containers
3. Debug Coolify deployment offline
4. Retry migration when resolved

---

## Troubleshooting Guide

### Common Issues

#### Issue: API Container Won't Start

**Symptoms**:
- `docker-compose ps` shows API as `Restarting` or `Exited`
- Unable to access API at `http://localhost:3010`

**Diagnosis**:
```bash
docker-compose -f docker-compose.prod.yml logs api
```

**Common Causes**:

1. **Database connection failed**
   - **Solution**: Verify PostgreSQL is running and credentials are correct
   ```bash
   docker-compose -f docker-compose.prod.yml exec postgres psql -U scraper_user -d scraper_db
   ```

2. **Missing environment variables**
   - **Solution**: Check `.env` file has all required variables
   ```bash
   docker-compose -f docker-compose.prod.yml exec api env | grep DATABASE_URL
   ```

3. **Port already in use**
   - **Solution**: Check if port 3010 is already bound
   ```bash
   sudo lsof -i :3010
   # Kill process if found
   sudo kill <PID>
   ```

#### Issue: Celery Worker Not Processing Jobs

**Symptoms**:
- Jobs stuck in `pending` status
- No progress updates

**Diagnosis**:
```bash
docker-compose -f docker-compose.prod.yml logs celery-worker
```

**Common Causes**:

1. **Redis connection failed**
   - **Solution**: Verify Redis is running
   ```bash
   docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
   # Should return: PONG
   ```

2. **Worker crashed**
   - **Solution**: Restart worker
   ```bash
   docker-compose -f docker-compose.prod.yml restart celery-worker
   ```

3. **Queue full**
   - **Solution**: Check queue length
   ```bash
   docker-compose -f docker-compose.prod.yml exec redis redis-cli llen celery
   ```

#### Issue: S3 Upload Fails

**Symptoms**:
- Job completes but S3 upload status is `failed`
- `output.uploadToS3.status` is `failed` in database

**Diagnosis**:
```bash
docker-compose -f docker-compose.prod.yml logs celery-worker | grep -i s3
```

**Common Causes**:

1. **Invalid credentials**
   - **Solution**: Verify AWS credentials
   ```bash
   docker-compose -f docker-compose.prod.yml exec api python -c "
   import boto3
   s3 = boto3.client('s3', region_name='ap-southeast-2')
   print(s3.list_buckets())
   "
   ```

2. **Bucket doesn't exist**
   - **Solution**: Create bucket or update `S3_BUCKET_NAME` in `.env`
   ```bash
   aws s3 ls s3://agar-documentation --region ap-southeast-2
   ```

3. **Insufficient permissions**
   - **Solution**: Verify IAM permissions include `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`

#### Issue: Crawl4AI Service Not Responding

**Symptoms**:
- Jobs fail during scraping phase
- Error: "Connection refused" to `crawl4ai-service:11235`

**Diagnosis**:
```bash
docker-compose -f docker-compose.prod.yml logs crawl4ai-service
curl http://localhost:11235/health
```

**Solutions**:

1. **Restart service**
   ```bash
   docker-compose -f docker-compose.prod.yml restart crawl4ai-service
   ```

2. **Increase memory limit** (in `docker-compose.prod.yml`)
   ```yaml
   crawl4ai-service:
     deploy:
       resources:
         limits:
           memory: 4G  # Increased from 2G
   ```

3. **Check service health**
   ```bash
   docker-compose -f docker-compose.prod.yml exec crawl4ai-service curl localhost:11235/health
   ```

#### Issue: UI Not Loading

**Symptoms**:
- Blank page at `http://localhost:8080`
- 502 Bad Gateway error

**Diagnosis**:
```bash
docker-compose -f docker-compose.prod.yml logs ui
curl http://localhost:8080
```

**Solutions**:

1. **Restart UI container**
   ```bash
   docker-compose -f docker-compose.prod.yml restart ui
   ```

2. **Check API connectivity** (UI connects to API)
   - In browser console, check for CORS errors
   - Verify `CORS_ORIGINS` in `.env` includes UI URL

3. **Clear browser cache**
   - Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+F5` (Windows)

#### Issue: SSL Certificate Fails

**Symptoms**:
- Certbot fails with "Connection refused" or "DNS resolution failed"
- Website shows "Not Secure" warning

**Diagnosis**:
```bash
sudo certbot certificates
sudo nginx -t
```

**Solutions**:

1. **Verify DNS is propagated**
   ```bash
   dig askagar.com +short
   # Should return your server IP
   ```

2. **Check Nginx configuration**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

3. **Retry Certbot**
   ```bash
   sudo certbot --nginx -d askagar.com -d www.askagar.com --force-renewal
   ```

4. **Check port 80 is accessible** (Certbot needs HTTP for verification)
   ```bash
   curl -I http://askagar.com
   ```

#### Issue: High Disk Usage

**Symptoms**:
- Disk space warning
- Docker commands slow or fail

**Diagnosis**:
```bash
df -h
du -sh ~/apps/agar-scraper/scraper_data/*
docker system df
```

**Solutions**:

1. **Clean up old scraper data**
   ```bash
   # Manually delete jobs older than 30 days
   find ~/apps/agar-scraper/scraper_data/jobs -type d -mtime +30 -exec rm -rf {} +
   ```

2. **Run archival task**
   ```bash
   curl -X POST "https://askagar.com/api/maintenance/archive?days=7" \
     -H "Authorization: Bearer {admin_token}"
   ```

3. **Clean Docker resources**
   ```bash
   docker system prune -a --volumes
   # Warning: Removes all unused images and volumes
   ```

4. **Expand storage** (LightSail)
   - Create and attach block storage volume
   - Mount to `/mnt/scraper-data`
   - Update volume mounts in `docker-compose.prod.yml`

#### Issue: Database Migration Fails

**Symptoms**:
- Alembic migration fails
- Database schema out of sync

**Diagnosis**:
```bash
docker-compose -f docker-compose.prod.yml exec api alembic current
docker-compose -f docker-compose.prod.yml exec api alembic history
```

**Solutions**:

1. **Check migration status**
   ```bash
   docker-compose -f docker-compose.prod.yml exec api alembic current
   ```

2. **Run migration manually**
   ```bash
   docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
   ```

3. **Rollback and retry**
   ```bash
   docker-compose -f docker-compose.prod.yml exec api alembic downgrade -1
   docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
   ```

4. **Reset database** (development only, destroys data)
   ```bash
   docker-compose -f docker-compose.prod.yml down -v
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Performance Issues

#### Slow Scraping

**Symptoms**:
- Jobs take much longer than expected
- Progress updates very slowly

**Solutions**:

1. **Increase Crawl4AI resources**
   ```yaml
   # docker-compose.prod.yml
   crawl4ai-service:
     deploy:
       resources:
         limits:
           memory: 4G
           cpus: '2'
   ```

2. **Reduce concurrent scraping**
   - Adjust `RATE_LIMIT_DELAY` in client config
   - Increase delays between requests

3. **Check network connectivity**
   ```bash
   docker-compose -f docker-compose.prod.yml exec api ping -c 4 agar.com.au
   ```

#### High Memory Usage

**Symptoms**:
- Containers OOM (Out Of Memory) killed
- Server becomes unresponsive

**Solutions**:

1. **Monitor resource usage**
   ```bash
   docker stats
   ```

2. **Increase memory limits** (in `docker-compose.prod.yml`)
   ```yaml
   celery-worker:
     deploy:
       resources:
         limits:
           memory: 6G  # Increased from 4G
   ```

3. **Reduce max_pages** for jobs
   - Limit jobs to smaller batches
   - Run multiple smaller jobs instead of one large job

4. **Upgrade server** (LightSail)
   - Upgrade to 16GB plan ($96/month)

### Getting Help

If issues persist:

1. **Check Documentation**:
   - [docs/LIGHTSAIL_DEPLOYMENT.md](docs/LIGHTSAIL_DEPLOYMENT.md)
   - [docs/quickstart/troubleshooting.md](docs/quickstart/troubleshooting.md)

2. **Review Logs**:
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

3. **Check GitHub Issues**:
   - [https://github.com/vargamick/agar-scraper/issues](https://github.com/vargamick/agar-scraper/issues)

4. **Contact Support**:
   - Create issue with:
     - Detailed error description
     - Relevant log excerpts
     - Environment details (OS, Docker version, etc.)
     - Steps to reproduce

---

## Appendices

### Appendix A: File Locations Reference

| File/Directory | Location | Purpose |
|----------------|----------|---------|
| **Environment Config** | `/home/ubuntu/apps/agar-scraper/.env` | Production environment variables |
| **Docker Compose** | `/home/ubuntu/apps/agar-scraper/docker-compose.prod.yml` | Production container orchestration |
| **Scraper Data** | `/home/ubuntu/apps/agar-scraper/scraper_data/jobs/` | Active job outputs |
| **Archives** | `/home/ubuntu/apps/agar-scraper/scraper_data/archive/` | Compressed old jobs |
| **Logs** | `/home/ubuntu/apps/agar-scraper/logs/` | Application logs |
| **Backups** | `/home/ubuntu/backups/agar-scraper/` | Database and data backups |
| **Nginx Config** | `/etc/nginx/sites-available/askagar` | Nginx reverse proxy config |
| **SSL Certificates** | `/etc/letsencrypt/live/askagar.com/` | Let's Encrypt SSL certificates |
| **Systemd Service** | `/etc/systemd/system/agar-scraper.service` | Auto-start service |
| **Monitoring Script** | `/home/ubuntu/monitor.sh` | Health monitoring cron script |

### Appendix B: API Endpoints Reference

**Base URL**: `https://askagar.com/api`

#### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create user account |
| POST | `/auth/login` | Authenticate and get tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET | `/auth/me` | Get current user info |

#### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scraper/jobs` | List all jobs |
| POST | `/scraper/jobs` | Create new job |
| GET | `/scraper/jobs/{id}` | Get job details |
| POST | `/scraper/jobs/{id}/control` | Control job (pause/resume/cancel) |
| DELETE | `/scraper/jobs/{id}` | Delete job |
| GET | `/scraper/jobs/{id}/logs` | Get job logs |
| GET | `/scraper/jobs/{id}/results` | Get job results |

#### Maintenance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/maintenance/storage-stats` | Get storage statistics |
| POST | `/maintenance/archive` | Manually archive old jobs |
| POST | `/maintenance/cleanup` | Manually delete archived jobs |
| POST | `/maintenance/restore/{id}` | Restore archived job |
| GET | `/maintenance/health` | Get maintenance system health |

#### Statistics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scraper/stats` | Get aggregate statistics |
| GET | `/scraper/health` | API health check |

### Appendix C: Environment Variables Reference

**Complete list of environment variables for production:**

```bash
# Environment
ENVIRONMENT=production
DEBUG=false
API_VERSION=v1

# Security
SECRET_KEY=<64-char-hex-string>

# Database
DATABASE_URL=postgresql://scraper_user:<password>@postgres:5432/scraper_db
POSTGRES_USER=scraper_user
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=scraper_db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=20

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_TASK_TIME_LIMIT=7200
CELERY_TASK_SOFT_TIME_LIMIT=3600

# CORS
CORS_ORIGINS=https://askagar.com,https://www.askagar.com

# S3
S3_ENABLED=true
S3_BUCKET_NAME=agar-documentation
S3_REGION=ap-southeast-2
S3_ACCESS_KEY_ID=<AWS-access-key>
S3_SECRET_ACCESS_KEY=<AWS-secret-key>
S3_UPLOAD_ON_COMPLETION=true
S3_PREFIX=agar/
S3_UPLOAD_TIMEOUT=300
S3_MAX_RETRIES=3

# Storage Paths
STORAGE_BASE_PATH=./scraper_data
STORAGE_JOBS_PATH=./scraper_data/jobs
ARCHIVE_BASE_PATH=./scraper_data/archive

# Run Management
ARCHIVE_AFTER_DAYS=7
DELETE_AFTER_DAYS=30
ARCHIVE_COMPRESSION=gzip
DELETION_STRATEGY=soft

# Crawl4AI
CRAWL4AI_API_URL=http://crawl4ai-service:11235
CRAWL4AI_TIMEOUT=60

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Appendix D: Database Queries Reference

**Useful SQL queries for monitoring and reporting:**

```sql
-- Get recent successful jobs with S3 URLs
SELECT
    id,
    name,
    folder_name,
    output->'uploadToS3'->'s3Urls'->>'all_products_json' as s3_url,
    stats->>'items_extracted' as items,
    completed_at
FROM jobs
WHERE status = 'completed'
  AND output->'uploadToS3'->>'status' = 'success'
ORDER BY completed_at DESC
LIMIT 10;

-- Get jobs by status
SELECT status, COUNT(*) as count
FROM jobs
WHERE deleted_at IS NULL
GROUP BY status;

-- Get storage usage by month
SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as job_count,
    SUM((stats->>'bytes_downloaded')::bigint) as total_bytes
FROM jobs
WHERE deleted_at IS NULL
GROUP BY month
ORDER BY month DESC;

-- Get failed jobs with errors
SELECT
    id,
    name,
    stats->>'errors' as error_count,
    created_at,
    completed_at
FROM jobs
WHERE status = 'failed'
ORDER BY created_at DESC
LIMIT 20;

-- Get user activity
SELECT
    u.username,
    COUNT(j.id) as job_count,
    SUM((j.stats->>'items_extracted')::integer) as total_items
FROM users u
LEFT JOIN jobs j ON j.created_by = u.id
GROUP BY u.id, u.username
ORDER BY job_count DESC;

-- Get jobs pending archival
SELECT
    id,
    name,
    folder_name,
    completed_at,
    AGE(NOW(), completed_at) as age
FROM jobs
WHERE status = 'completed'
  AND archived_at IS NULL
  AND completed_at < NOW() - INTERVAL '7 days'
ORDER BY completed_at ASC;
```

### Appendix E: Glossary

| Term | Definition |
|------|------------|
| **Celery** | Distributed task queue system for background job processing |
| **Crawl4AI** | Web scraping library with Playwright integration for JavaScript rendering |
| **CSS Selector** | Pattern used to select HTML elements for data extraction |
| **Docker Compose** | Tool for defining and running multi-container Docker applications |
| **FastAPI** | Modern Python web framework for building APIs |
| **Job** | A scraping task with configuration, status, and results |
| **LightSail** | AWS service for simple virtual private servers |
| **Nginx** | High-performance web server and reverse proxy |
| **Playwright** | Browser automation library for web scraping |
| **PostgreSQL** | Open-source relational database system |
| **Redis** | In-memory data store used for caching and message queueing |
| **S3** | AWS Simple Storage Service for object storage |
| **SQLAlchemy** | Python SQL toolkit and Object-Relational Mapping (ORM) library |
| **Systemd** | Linux system and service manager |
| **UUID** | Universally Unique Identifier (128-bit number) |

### Appendix F: Quick Command Reference

**Docker Operations**:
```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# View logs (all services)
docker-compose -f docker-compose.prod.yml logs -f

# View logs (specific service)
docker-compose -f docker-compose.prod.yml logs -f api

# Restart service
docker-compose -f docker-compose.prod.yml restart api

# Check status
docker-compose -f docker-compose.prod.yml ps

# Execute command in container
docker-compose -f docker-compose.prod.yml exec api bash

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

**Database Operations**:
```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres psql -U scraper_user -d scraper_db

# Backup database
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump \
  -U scraper_user scraper_db > backup.sql

# Restore database
cat backup.sql | docker-compose -f docker-compose.prod.yml exec -T postgres \
  psql -U scraper_user -d scraper_db

# Run migration
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

**Monitoring Operations**:
```bash
# Check API health
curl https://askagar.com/api/scraper/health

# View resource usage
docker stats

# Check disk usage
df -h
du -sh ~/apps/agar-scraper/scraper_data/*

# View system logs
sudo journalctl -u agar-scraper -f
```

**Maintenance Operations**:
```bash
# Archive old jobs
curl -X POST "https://askagar.com/api/maintenance/archive?days=7" \
  -H "Authorization: Bearer {admin_token}"

# Get storage stats
curl -X GET "https://askagar.com/api/maintenance/storage-stats" \
  -H "Authorization: Bearer {token}"

# Clean Docker resources
docker system prune -a --volumes

# Update SSL certificate
sudo certbot renew
```

---

## Document Metadata

**Document Version**: 1.0.0
**Last Updated**: 2025-01-22
**Author**: AI Assistant
**Audience**: Administrators, Operators, Developers, DevOps
**Related Documents**:
- [README.md](README.md) - Project overview
- [docs/LIGHTSAIL_DEPLOYMENT.md](docs/LIGHTSAIL_DEPLOYMENT.md) - Detailed deployment guide
- [docs/UI_GUIDE.md](docs/UI_GUIDE.md) - User interface documentation
- [docs/S3_INTEGRATION.md](docs/S3_INTEGRATION.md) - S3 integration details
- [docs/RUN_MANAGEMENT_STRATEGY.md](docs/RUN_MANAGEMENT_STRATEGY.md) - Data lifecycle management

**Change Log**:
- 2025-01-22: Initial comprehensive documentation created

---

**End of Document**
