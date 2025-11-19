# Scripts Directory

Organized collection of utility scripts for the Agar Web Scraper project.

## Directory Structure

```
scripts/
├── job_management/      # Scripts for managing scraping jobs
├── testing/            # Test and integration scripts
└── utilities/          # General utility scripts
```

## Job Management Scripts

Located in `job_management/`

### run_full_scrape.sh
Full Agar website scrape with default settings.

**Usage:**
```bash
cd scripts/job_management
./run_full_scrape.sh
```

### run_s3_scrape.sh
Complete S3 integration test - creates job, monitors progress, verifies S3 upload.

**Usage:**
```bash
cd scripts/job_management
./run_s3_scrape.sh
```

**Prerequisites:**
- Docker containers running
- AWS credentials configured
- S3 bucket accessible

### monitor_job.sh
Monitor a running job's progress.

**Usage:**
```bash
cd scripts/job_management
./monitor_job.sh <job_id>
```

### check_job_complete.sh
Check if a job has completed and view results.

**Usage:**
```bash
cd scripts/job_management
./check_job_complete.sh <job_id>
```

## Testing Scripts

Located in `testing/`

### test_s3_integration.sh
Comprehensive S3 integration test with pre-flight checks.

**Usage:**
```bash
cd scripts/testing
./test_s3_integration.sh
```

**Features:**
- Verifies Docker containers
- Checks AWS credentials
- Tests S3 bucket access
- Monitors job completion
- Verifies uploaded files

### test_create_job.sh
Simple test to create a job via API.

**Usage:**
```bash
cd scripts/testing
./test_create_job.sh
```

## Utility Scripts

Located in `utilities/`

### create_admin.py
Create or update admin user account.

**Usage:**
```bash
cd scripts/utilities
python3 create_admin.py
```

**Creates:**
- Username: admin
- Email: admin@example.com
- Password: admin123

### scraper_data_discovery.py
Analyze and discover scraped data files.

**Usage:**
```bash
cd scripts/utilities
python3 scraper_data_discovery.py
```

**Features:**
- Finds all scraper output folders
- Analyzes file contents
- Reports on products, categories, PDFs

## Common Patterns

### Creating Jobs

All job creation scripts follow this pattern:
1. Authenticate with API
2. Get access token
3. Create job with configuration
4. Return job ID

### Monitoring Jobs

Job monitoring scripts:
1. Poll job status endpoint
2. Display progress updates
3. Exit when complete or failed
4. Show final statistics

### S3 Operations

S3-related scripts:
1. Verify AWS credentials
2. Check bucket access
3. Upload or download files
4. Verify file integrity

## Environment Variables

Scripts may use these environment variables:

```bash
# API Configuration
API_URL="http://localhost:3010"

# AWS Configuration
AWS_ACCESS_KEY_ID="your_key"
AWS_SECRET_ACCESS_KEY="your_secret"
AWS_DEFAULT_REGION="us-east-1"

# S3 Configuration
S3_BUCKET="scraper-outputs"
S3_PREFIX="agar/"
```

## Best Practices

1. **Always run from script directory** - Scripts use relative paths
2. **Check prerequisites first** - Verify Docker/API is running
3. **Use test scripts before production** - Validate with small jobs first
4. **Monitor resource usage** - Large scrapes consume memory/CPU
5. **Check logs on failure** - `docker-compose logs api` or `celery-worker`

## Troubleshooting

### Script won't execute
```bash
chmod +x script_name.sh
```

### API connection refused
```bash
# Check if containers are running
docker-compose ps

# Start if needed
docker-compose up -d
```

### Authentication failed
```bash
# Verify user exists
python3 utilities/create_admin.py

# Check credentials in script
```

### S3 upload failed
```bash
# Verify credentials
aws s3 ls s3://your-bucket/

# Check bucket permissions
```

## Related Documentation

- [API Documentation](../../docs/API_DOCUMENTATION.md)
- [S3 Integration Guide](../../docs/S3_INTEGRATION.md)
- [UI Guide](../../docs/UI_GUIDE.md)
- [Deployment Guide](../../docs/DEPLOYMENT.md)
