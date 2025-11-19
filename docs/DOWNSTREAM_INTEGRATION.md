# Downstream Integration Guide

This document explains how downstream applications (vector embeddings, knowledge graph population, etc.) can query the scraper database to discover and process scraped data.

## Table of Contents
1. [Database Schema Overview](#database-schema-overview)
2. [What's Stored for Each Run](#whats-stored-for-each-run)
3. [Querying for Latest Run](#querying-for-latest-run)
4. [AWS S3 Integration](#aws-s3-integration)
5. [Python Integration Examples](#python-integration-examples)
6. [REST API Integration](#rest-api-integration)
7. [File System Structure](#file-system-structure)

---

## Database Schema Overview

### Jobs Table Structure

The `jobs` table is the primary source of information about scrape runs:

```sql
CREATE TABLE jobs (
    -- Identity
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    description TEXT,

    -- Output folder information
    folder_name VARCHAR(255),  -- Format: YYYYMMDD_HHMMSS

    -- Status tracking
    type VARCHAR(50),          -- 'web', 'api', etc.
    status VARCHAR(50),        -- 'pending', 'running', 'completed', 'failed'

    -- Configuration (JSON)
    config JSONB,              -- Scrape configuration
    output JSONB,              -- Output settings
    schedule JSONB,            -- Schedule info (if scheduled)

    -- Progress tracking (JSON)
    progress JSONB,            -- {percentage, pagesScraped, totalPages, startedAt, estimatedCompletion}

    -- Statistics (JSON)
    stats JSONB,               -- {bytesDownloaded, itemsExtracted, errors, retries}

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Ownership
    created_by UUID REFERENCES users(id)
);
```

### Indexes for Efficient Queries

The following indexes are available for fast queries:

- `idx_job_status_created` on (status, created_at)
- `idx_job_type_status` on (type, status)
- `ix_jobs_folder_name` on (folder_name)

---

## What's Stored for Each Run

For each scrape run, the database stores:

### Core Metadata
- **Job ID** (UUID): Unique identifier for the job
- **Job Name**: Human-readable name
- **Folder Name**: Timestamp in format `YYYYMMDD_HHMMSS`
- **Status**: Current state (pending, running, completed, failed, etc.)

### Timestamps
- **created_at**: When the job was created
- **started_at**: When scraping began
- **completed_at**: When scraping finished
- **updated_at**: Last update time

### Configuration (JSON)
```json
{
  "startUrls": ["https://www.agar.com.au"],
  "maxPages": 200,
  "client_name": "agar",
  "test_mode": false,
  "save_screenshots": true,
  "crawlDepth": 3,
  "followLinks": true
}
```

### Statistics (JSON)
```json
{
  "bytesDownloaded": 15728640,
  "itemsExtracted": 199,
  "errors": 0,
  "retries": 2
}
```

### Progress (JSON)
```json
{
  "percentage": 100,
  "pagesScraped": 199,
  "totalPages": 200,
  "startedAt": "2025-11-14T01:18:39.505315",
  "estimatedCompletion": null
}
```

### Output Path Construction

The full output path is constructed as:
```
{base_path}/{folder_name}_{job_id}/
```

Example:
```
/app/scraper_data/jobs/20251114_011839_73395058-e599-4bf7-a35f-79da2264afa8/
```

---

## Querying for Latest Run

### SQL Query

```sql
-- Get the most recent completed run
SELECT
    id,
    name,
    folder_name,
    CONCAT(folder_name, '_', id::text) as full_folder_name,
    status,
    completed_at,
    stats,
    config
FROM jobs
WHERE status = 'completed'
  AND type = 'web'
ORDER BY completed_at DESC
LIMIT 1;
```

### Example Result

```
id                  | 73395058-e599-4bf7-a35f-79da2264afa8
name                | Agar Complete Dataset Test - Fresh Rebuild
folder_name         | 20251114_011839
full_folder_name    | 20251114_011839_73395058-e599-4bf7-a35f-79da2264afa8
status              | completed
completed_at        | 2025-11-14 01:35:00.123456+00
stats               | {"bytesDownloaded": 15728640, "itemsExtracted": 199, ...}
config              | {"client_name": "agar", "startUrls": [...], ...}
```

---

## AWS S3 Integration

Starting from version 1.1.0, the scraper automatically uploads job outputs to AWS S3 for cloud storage and easy access by downstream applications.

### How It Works

When a scrape job completes:
1. Job outputs are saved locally in `/app/scraper_data/jobs/{folder_name}_{job_id}/`
2. If S3 is enabled, a background task uploads files to S3
3. S3 URLs are stored in the job's `output` JSONB field in the database
4. Downstream applications can access data from either local storage OR S3

### S3 Data Storage Structure

Files are uploaded to S3 with the following structure:

```
s3://{bucket}/{prefix}/{folder_name}_{job_id}/
├── all_products.json
├── categories.json
├── results.json
├── pdfs/
│   ├── SDS/
│   │   ├── Product1-SDS.pdf
│   │   └── Product2-SDS.pdf
│   └── PDS/
│       ├── Product1-PDS.pdf
│       └── Product2-PDS.pdf
└── screenshots/ (optional)
```

**Example S3 path:**
```
s3://my-scraper-bucket/scraper-outputs/20251114_011839_73395058-e599-4bf7-a35f-79da2264afa8/all_products.json
```

### Querying for S3 URLs

#### SQL Query to Get S3 URLs

```sql
SELECT
    id,
    folder_name,
    output->'uploadToS3'->'s3Urls'->>'all_products_json' as s3_products_url,
    output->'uploadToS3'->'s3Urls'->>'categories_json' as s3_categories_url,
    output->'uploadToS3'->'s3Urls'->>'pdfs_dir' as s3_pdfs_url,
    output->'uploadToS3'->>'status' as s3_upload_status,
    output->'uploadToS3'->>'uploadedAt' as s3_uploaded_at,
    output->'uploadToS3'->>'bytesUploaded' as s3_bytes_uploaded
FROM jobs
WHERE status = 'completed'
  AND type = 'web'
  AND output->'uploadToS3'->>'status' = 'success'
ORDER BY completed_at DESC
LIMIT 1;
```

#### Example Result

```json
{
  "id": "73395058-e599-4bf7-a35f-79da2264afa8",
  "folder_name": "20251114_011839",
  "s3_products_url": "s3://my-bucket/scraper-outputs/20251114_011839_73395058.../all_products.json",
  "s3_categories_url": "s3://my-bucket/scraper-outputs/20251114_011839_73395058.../categories.json",
  "s3_pdfs_url": "s3://my-bucket/scraper-outputs/20251114_011839_73395058.../pdfs/",
  "s3_upload_status": "success",
  "s3_uploaded_at": "2025-11-14T01:35:30.123456Z",
  "s3_bytes_uploaded": "16777216"
}
```

### Output JSONB Structure with S3

When S3 upload completes, the `output` JSONB field is updated:

```json
{
  "saveFiles": true,
  "fileFormat": "json",
  "uploadToS3": {
    "enabled": true,
    "status": "success",
    "uploadedAt": "2025-11-14T01:35:30.123456Z",
    "s3Urls": {
      "all_products_json": "s3://bucket/prefix/folder/all_products.json",
      "categories_json": "s3://bucket/prefix/folder/categories.json",
      "results_json": "s3://bucket/prefix/folder/results.json",
      "pdfs_dir": "s3://bucket/prefix/folder/pdfs/"
    },
    "bytesUploaded": 16777216,
    "filesUploaded": 320,
    "errors": []
  }
}
```

### Python Example: Access Data from S3

```python
import boto3
import json
from scraper_data_discovery import ScraperDataDiscovery

class S3DataProcessor:
    """Process scraper data from S3."""

    def __init__(self, aws_access_key_id, aws_secret_access_key, region='us-east-1'):
        self.s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

    def get_latest_from_s3(self, db_config):
        """Get latest scrape data from S3."""
        # Discover latest job from database
        discovery = ScraperDataDiscovery(db_config)
        latest = discovery.get_latest_completed_run(client_name="agar")

        if not latest:
            return None

        # Check if S3 upload completed
        s3_info = latest.get('output', {}).get('uploadToS3', {})

        if s3_info.get('status') != 'success':
            print("S3 upload not available, using local files")
            return self._load_from_local(latest)

        # Get S3 URLs
        s3_urls = s3_info.get('s3Urls', {})
        products_url = s3_urls.get('all_products_json')

        if not products_url:
            return self._load_from_local(latest)

        # Parse S3 URL
        # Format: s3://bucket/key/path
        s3_parts = products_url.replace('s3://', '').split('/', 1)
        bucket = s3_parts[0]
        key = s3_parts[1]

        # Download from S3
        print(f"Downloading from S3: {products_url}")
        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        products = json.loads(response['Body'].read())

        print(f"Loaded {len(products)} products from S3")
        return products

    def _load_from_local(self, job_info):
        """Fallback to local file if S3 not available."""
        import json
        with open(job_info['all_products_json'], 'r') as f:
            return json.load(f)

# Usage
processor = S3DataProcessor(
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET'
)

db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "scraper_db",
    "user": "scraper_user",
    "password": "scraper_password"
}

products = processor.get_latest_from_s3(db_config)
```

### Benefits for Downstream Applications

1. **Cloud-Native Access**: No need for shared file systems or network drives
2. **Scalability**: Multiple downstream services can access S3 simultaneously
3. **Durability**: S3 provides 99.999999999% durability
4. **Cross-Region Access**: Data accessible from anywhere
5. **Version Control**: Can enable S3 versioning for audit trails
6. **Cost-Effective**: Cheaper than EBS for archival storage
7. **Hybrid Mode**: Data available both locally and in S3

### Checking S3 Upload Status

```python
def get_s3_upload_status(job_id, db_config):
    """Check if S3 upload completed for a job."""
    import psycopg2

    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    cur.execute("""
        SELECT
            output->'uploadToS3'->>'status' as upload_status,
            output->'uploadToS3'->>'uploadedAt' as uploaded_at,
            output->'uploadToS3'->>'filesUploaded' as files_uploaded,
            output->'uploadToS3'->'errors' as errors
        FROM jobs
        WHERE id = %s
    """, (job_id,))

    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        status, uploaded_at, files_uploaded, errors = result
        return {
            'status': status,
            'uploaded_at': uploaded_at,
            'files_uploaded': files_uploaded,
            'errors': errors or []
        }

    return None
```

---

## Python Integration Examples

### Using psycopg2 (Direct Database Connection)

```python
import psycopg2
import json
from datetime import datetime

class ScraperDataDiscovery:
    """Helper class to discover latest scraper runs for downstream processing."""

    def __init__(self, db_config):
        """
        Initialize with database connection config.

        Args:
            db_config: Dict with keys: host, port, database, user, password
        """
        self.db_config = db_config
        self.base_path = "/app/scraper_data/jobs"

    def get_latest_completed_run(self, client_name=None):
        """
        Get the most recent completed scrape run.

        Args:
            client_name: Optional filter by client (e.g., 'agar')

        Returns:
            Dict with job metadata and output path
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        query = """
            SELECT
                id,
                name,
                folder_name,
                status,
                created_at,
                started_at,
                completed_at,
                stats,
                config
            FROM jobs
            WHERE status = 'completed'
              AND type = 'web'
        """

        params = []
        if client_name:
            query += " AND config->>'client_name' = %s"
            params.append(client_name)

        query += " ORDER BY completed_at DESC LIMIT 1"

        cur.execute(query, params)
        row = cur.fetchone()

        if not row:
            return None

        job_id, name, folder_name, status, created_at, started_at, completed_at, stats, config = row

        # Construct full output path
        full_folder_name = f"{folder_name}_{job_id}"
        output_path = f"{self.base_path}/{full_folder_name}"

        result = {
            "job_id": str(job_id),
            "name": name,
            "folder_name": folder_name,
            "full_folder_name": full_folder_name,
            "output_path": output_path,
            "status": status,
            "created_at": created_at,
            "started_at": started_at,
            "completed_at": completed_at,
            "stats": stats,
            "config": config,

            # Convenience fields
            "all_products_json": f"{output_path}/all_products.json",
            "categories_json": f"{output_path}/categories.json",
            "results_json": f"{output_path}/results.json",
        }

        cur.close()
        conn.close()

        return result

    def get_runs_since(self, last_processed_timestamp):
        """
        Get all completed runs since a given timestamp.

        Args:
            last_processed_timestamp: datetime object or ISO string

        Returns:
            List of dicts with job metadata
        """
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()

        query = """
            SELECT
                id,
                folder_name,
                completed_at,
                stats->>'itemsExtracted' as items_extracted
            FROM jobs
            WHERE status = 'completed'
              AND type = 'web'
              AND completed_at > %s
            ORDER BY completed_at ASC
        """

        cur.execute(query, (last_processed_timestamp,))
        rows = cur.fetchall()

        results = []
        for row in rows:
            job_id, folder_name, completed_at, items_extracted = row
            full_folder_name = f"{folder_name}_{job_id}"

            results.append({
                "job_id": str(job_id),
                "folder_name": folder_name,
                "full_folder_name": full_folder_name,
                "output_path": f"{self.base_path}/{full_folder_name}",
                "completed_at": completed_at,
                "items_extracted": int(items_extracted) if items_extracted else 0,
            })

        cur.close()
        conn.close()

        return results


# Usage Example
if __name__ == "__main__":
    # Database configuration
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "scraper_db",
        "user": "scraper_user",
        "password": "scraper_password"
    }

    # Initialize discovery helper
    discovery = ScraperDataDiscovery(db_config)

    # Get latest run for Agar client
    latest_run = discovery.get_latest_completed_run(client_name="agar")

    if latest_run:
        print(f"Latest run: {latest_run['name']}")
        print(f"Completed at: {latest_run['completed_at']}")
        print(f"Output path: {latest_run['output_path']}")
        print(f"Items extracted: {latest_run['stats']['itemsExtracted']}")
        print(f"\nData files:")
        print(f"  - All products: {latest_run['all_products_json']}")
        print(f"  - Categories: {latest_run['categories_json']}")

        # Now you can load and process the data
        import json
        with open(latest_run['all_products_json'], 'r') as f:
            products = json.load(f)
            print(f"\nLoaded {len(products)} products for processing")
    else:
        print("No completed runs found")

    # Get all runs since last processing
    last_processed = "2025-11-14 00:00:00"
    new_runs = discovery.get_runs_since(last_processed)
    print(f"\nFound {len(new_runs)} new runs since {last_processed}")
```

### Using SQLAlchemy (ORM)

```python
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from api.database.models import Job, JobStatus, JobType
from datetime import datetime

class ScraperDataDiscoveryORM:
    """SQLAlchemy-based data discovery."""

    def __init__(self, database_url):
        """
        Initialize with SQLAlchemy database URL.

        Args:
            database_url: e.g., "postgresql://user:pass@localhost:5432/scraper_db"
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.base_path = "/app/scraper_data/jobs"

    def get_latest_completed_run(self, client_name=None):
        """Get the most recent completed scrape run."""
        session = self.Session()

        query = session.query(Job).filter(
            Job.status == JobStatus.COMPLETED,
            Job.type == JobType.WEB
        )

        if client_name:
            query = query.filter(Job.config['client_name'].astext == client_name)

        job = query.order_by(desc(Job.completed_at)).first()

        if not job:
            session.close()
            return None

        full_folder_name = f"{job.folder_name}_{job.id}"
        output_path = f"{self.base_path}/{full_folder_name}"

        result = {
            "job_id": str(job.id),
            "name": job.name,
            "folder_name": job.folder_name,
            "full_folder_name": full_folder_name,
            "output_path": output_path,
            "status": job.status.value,
            "completed_at": job.completed_at,
            "stats": job.stats,
            "config": job.config,
            "all_products_json": f"{output_path}/all_products.json",
            "categories_json": f"{output_path}/categories.json",
        }

        session.close()
        return result

# Usage
discovery = ScraperDataDiscoveryORM("postgresql://scraper_user:scraper_password@localhost:5432/scraper_db")
latest = discovery.get_latest_completed_run(client_name="agar")
```

---

## REST API Integration

If you prefer to use the REST API instead of direct database access:

### Get Latest Completed Job

```bash
# Authenticate
TOKEN=$(curl -s -X POST http://localhost:3010/api/scraper/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_pass"}' | jq -r '.data.access_token')

# Get all completed jobs
curl -s http://localhost:3010/api/scraper/jobs?status=completed&limit=1 \
  -H "Authorization: Bearer $TOKEN" | jq .

# Get specific job by ID
curl -s http://localhost:3010/api/scraper/jobs/{job_id} \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Python REST API Client

```python
import requests
import json

class ScraperAPIClient:
    """REST API client for scraper service."""

    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = self._authenticate(username, password)
        self.base_path = "/app/scraper_data/jobs"

    def _authenticate(self, username, password):
        """Get JWT token."""
        response = requests.post(
            f"{self.base_url}/api/scraper/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        return response.json()['data']['access_token']

    def get_latest_completed_run(self):
        """Get latest completed job."""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(
            f"{self.base_url}/api/scraper/jobs",
            params={"status": "completed", "limit": 1, "sort": "completed_at:desc"},
            headers=headers
        )
        response.raise_for_status()

        jobs = response.json()['data']
        if not jobs:
            return None

        job = jobs[0]
        folder_name = job.get('folder_name', '')
        job_id = job['jobId']
        full_folder_name = f"{folder_name}_{job_id}"

        return {
            "job_id": job_id,
            "name": job['name'],
            "folder_name": folder_name,
            "full_folder_name": full_folder_name,
            "output_path": f"{self.base_path}/{full_folder_name}",
            "completed_at": job.get('completedAt'),
            "stats": job.get('stats', {}),
        }

# Usage
client = ScraperAPIClient(
    base_url="http://localhost:3010",
    username="your_user",
    password="your_pass"
)
latest = client.get_latest_completed_run()
print(f"Process data at: {latest['output_path']}")
```

---

## File System Structure

Once you have the output path, the data is organized as follows:

```
{output_path}/
├── all_products.json          # All scraped products (199 items)
├── categories.json            # All categories (57 items)
├── results.json               # Detailed results array
├── categories/                # Category-organized data
│   ├── air-fresheners/
│   │   ├── air-fresheners_detergent-deodorisers.json
│   │   └── air-fresheners_detergent-deodorisers_products.json
│   ├── carpet-cleaners/
│   ├── floor-care/
│   └── ...
├── pdfs/                      # Downloaded PDF documents (SDS/PDS)
│   ├── Breeze-SDS-GHS7.pdf
│   ├── Breeze-PDS.pdf
│   └── ...
├── screenshots/               # Page screenshots (if enabled)
└── reports/                   # Processing reports
```

### Key Data Files

1. **all_products.json**: Contains all products with full details
   ```json
   [
     {
       "product_name": "Breeze",
       "product_url": "https://agar.com.au/product/breeze/",
       "product_image_url": "https://...",
       "product_overview": "...",
       "product_description": "...",
       "product_skus": "BRE5, BRE20",
       "product_categories": ["Detergent Deodorisers"],
       "category": "Detergent Deodorisers",
       "category_slug": "detergent-deodorisers",
       "sds_url": "https://...",
       "pds_url": "https://...",
       "scraped_at": "2025-11-14T01:31:41.115855"
     }
   ]
   ```

2. **categories.json**: Category hierarchy and metadata

3. **results.json**: Raw scrape results with additional metadata

---

## Integration Workflow Example

Here's a complete workflow for a downstream application:

```python
from scraper_data_discovery import ScraperDataDiscovery
import json
import os

class VectorEmbeddingProcessor:
    """Example downstream processor for vector embeddings."""

    def __init__(self, db_config, last_processed_file="last_processed.txt"):
        self.discovery = ScraperDataDiscovery(db_config)
        self.last_processed_file = last_processed_file

    def get_last_processed_timestamp(self):
        """Read the last processed timestamp from file."""
        if os.path.exists(self.last_processed_file):
            with open(self.last_processed_file, 'r') as f:
                return f.read().strip()
        return None

    def save_last_processed_timestamp(self, timestamp):
        """Save the last processed timestamp."""
        with open(self.last_processed_file, 'w') as f:
            f.write(str(timestamp))

    def process_new_runs(self):
        """Process all new runs since last processing."""
        last_processed = self.get_last_processed_timestamp()

        if last_processed:
            # Get all new runs
            new_runs = self.discovery.get_runs_since(last_processed)
            print(f"Found {len(new_runs)} new runs to process")
        else:
            # First time - get latest run only
            latest = self.discovery.get_latest_completed_run()
            new_runs = [latest] if latest else []
            print(f"First run - processing latest scrape")

        for run in new_runs:
            self.process_run(run)
            self.save_last_processed_timestamp(run['completed_at'])

    def process_run(self, run):
        """Process a single scrape run."""
        print(f"\nProcessing run: {run['name']}")
        print(f"Output path: {run['output_path']}")

        # Load product data
        products_file = f"{run['output_path']}/all_products.json"
        with open(products_file, 'r') as f:
            products = json.load(f)

        print(f"Loaded {len(products)} products")

        # Process each product
        for product in products:
            self.process_product(product)

        print(f"✓ Completed processing run {run['job_id']}")

    def process_product(self, product):
        """
        Process individual product for vector embeddings.

        This is where you would:
        - Generate embeddings from product description
        - Update knowledge graph
        - Store in vector database
        - etc.
        """
        # Your processing logic here
        text_to_embed = f"{product['product_name']}: {product['product_overview']} {product['product_description']}"

        # Example: Generate embedding (pseudo-code)
        # embedding = your_embedding_model.encode(text_to_embed)
        # vector_db.insert(product['product_url'], embedding, metadata=product)

        print(f"  - Processed: {product['product_name']}")

# Run the processor
if __name__ == "__main__":
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "scraper_db",
        "user": "scraper_user",
        "password": "scraper_password"
    }

    processor = VectorEmbeddingProcessor(db_config)
    processor.process_new_runs()
```

---

## Database Connection Details

### Local Docker Development
```python
db_config = {
    "host": "localhost",
    "port": 5432,
    "database": "scraper_db",
    "user": "scraper_user",
    "password": "scraper_password"
}
```

### AWS LightSail Production
```python
db_config = {
    "host": "your-lightsail-ip",  # or hostname
    "port": 5432,
    "database": "scraper_db",
    "user": "scraper_user",
    "password": "scraper_password"  # Use environment variable in production
}
```

### Connection String Format
```
postgresql://scraper_user:scraper_password@localhost:5432/scraper_db
```

---

## Summary

Your downstream application should:

1. **Connect to the PostgreSQL database** (credentials in docker-compose.yml)
2. **Query the `jobs` table** for latest completed runs
3. **Extract the `folder_name` and `id`** to construct the output path
4. **Read data files** from the constructed path
5. **Track last processed timestamp** to avoid reprocessing

The key fields you need:
- `folder_name`: Timestamp folder (e.g., "20251114_011839")
- `id`: Job UUID
- `completed_at`: When the scrape finished
- **Full path**: `{base_path}/{folder_name}_{id}/`

All product data is in `all_products.json` with full details ready for embedding and knowledge graph processing.
