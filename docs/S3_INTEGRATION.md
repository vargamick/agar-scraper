# AWS S3 Integration Guide

This document provides complete instructions for setting up and using AWS S3 integration with the 3DN Scraper API.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [AWS S3 Setup](#aws-s3-setup)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Monitoring Uploads](#monitoring-uploads)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

The S3 integration automatically uploads scraper job outputs to AWS S3 for:
- **Long-term storage**: Durable, scalable cloud storage
- **Downstream processing**: Easy access for vector embeddings, knowledge graphs, etc.
- **Cross-region access**: Data available from anywhere
- **Cost optimization**: Cheaper than local storage for archival

### How It Works

1. Job runs and outputs are saved locally
2. After completion, a Celery background task uploads files to S3
3. S3 URLs are stored in the database
4. Downstream applications can access data from S3 or local storage

---

## Prerequisites

### AWS Requirements

- AWS Account
- IAM User with S3 permissions
- S3 Bucket (standard or intelligent-tiering)

### Application Requirements

- boto3 Python package (included in requirements.txt)
- Redis (for Celery task queue)
- PostgreSQL database

---

## AWS S3 Setup

### 1. Create an S3 Bucket

**Via AWS Console:**
1. Go to S3 service in AWS Console
2. Click "Create bucket"
3. Configure:
   - **Bucket name**: `your-scraper-outputs` (must be globally unique)
   - **Region**: `ap-southeast-2` (or your preferred region)
   - **Block Public Access**: Keep enabled (recommended)
   - **Versioning**: Optional (recommended for audit trails)
   - **Encryption**: Enable SSE-S3 (recommended)
4. Click "Create bucket"

**Via AWS CLI:**
```bash
# Create bucket
aws s3api create-bucket \
    --bucket your-scraper-outputs \
    --region ap-southeast-2

# Enable versioning (optional)
aws s3api put-bucket-versioning \
    --bucket your-scraper-outputs \
    --versioning-configuration Status=Enabled

# Enable encryption (optional)
aws s3api put-bucket-encryption \
    --bucket your-scraper-outputs \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'
```

### 2. Create IAM User

**Via AWS Console:**
1. Go to IAM service
2. Click "Users" → "Create user"
3. Username: `scraper-s3-user`
4. Select "Attach policies directly"
5. Click "Create policy" (opens new tab):
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
                   "arn:aws:s3:::your-scraper-outputs",
                   "arn:aws:s3:::your-scraper-outputs/*"
               ]
           }
       ]
   }
   ```
6. Name policy: `ScraperS3Policy`
7. Return to user creation, attach `ScraperS3Policy`
8. Create user

**Create Access Keys:**
1. Select the user `scraper-s3-user`
2. Go to "Security credentials" tab
3. Click "Create access key"
4. Use case: "Application running outside AWS"
5. Save the Access Key ID and Secret Access Key

### 3. Configure Bucket Lifecycle (Optional)

To automatically transition old scrapes to cheaper storage:

```json
{
    "Rules": [
        {
            "Id": "ArchiveOldScrapes",
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 90,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            }
        }
    ]
}
```

Apply via CLI:
```bash
aws s3api put-bucket-lifecycle-configuration \
    --bucket your-scraper-outputs \
    --lifecycle-configuration file://lifecycle.json
```

---

## Configuration

### 1. Update Environment Variables

Edit `.env` file:

```bash
# =============================================================================
# AWS S3 CONFIGURATION
# =============================================================================

# Enable S3 upload integration
S3_ENABLED=true

# S3 Bucket Configuration
S3_BUCKET_NAME=your-scraper-outputs
S3_REGION=ap-southeast-2

# AWS Credentials
S3_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
S3_SECRET_ACCESS_KEY=your-secret-access-key-here

# S3 Upload Settings
S3_UPLOAD_ON_COMPLETION=true              # Auto-upload when job completes
S3_PREFIX=scraper-outputs/                 # Folder prefix in S3
S3_UPLOAD_TIMEOUT=300                      # Upload timeout (seconds)
S3_MAX_RETRIES=3                           # Max retry attempts
```

### 2. Docker Compose Configuration

The `docker-compose.yml` is already configured to pass S3 environment variables to both `api` and `celery-worker` services.

Verify these lines exist:

```yaml
environment:
  - S3_ENABLED=${S3_ENABLED:-false}
  - S3_BUCKET_NAME=${S3_BUCKET_NAME}
  - S3_REGION=${S3_REGION:-ap-southeast-2}
  - S3_ACCESS_KEY_ID=${S3_ACCESS_KEY_ID}
  - S3_SECRET_ACCESS_KEY=${S3_SECRET_ACCESS_KEY}
  - S3_UPLOAD_ON_COMPLETION=${S3_UPLOAD_ON_COMPLETION:-true}
  - S3_PREFIX=${S3_PREFIX:-scraper-outputs/}
```

### 3. Per-Job Configuration (Optional)

Override S3 settings for specific jobs via API:

```json
{
  "name": "Custom S3 Upload Job",
  "type": "web",
  "config": {
    "startUrls": ["https://example.com"],
    "maxPages": 100
  },
  "output": {
    "saveFiles": true,
    "fileFormat": "json",
    "uploadToS3": {
      "enabled": true,
      "bucket": "different-bucket",          // Override bucket
      "prefix": "custom-prefix/",             // Override prefix
      "includeFiles": [
        "all_products.json",
        "categories.json"
      ],
      "uploadPdfs": true,
      "uploadScreenshots": false,
      "uploadCategories": false
    }
  }
}
```

---

## Usage

### Automatic Upload

With `S3_ENABLED=true` and `S3_UPLOAD_ON_COMPLETION=true`, every completed job automatically uploads to S3.

### Manual Upload Trigger

To manually trigger S3 upload for a specific job:

```python
from api.jobs.tasks import upload_job_to_s3

upload_job_to_s3.delay(
    job_id="73395058-e599-4bf7-a35f-79da2264afa8",
    folder_name="20251114_011839",
    output_path="/app/scraper_data/jobs/20251114_011839_73395058-e599-4bf7-a35f-79da2264afa8",
    s3_config={}
)
```

### Disable S3 for Specific Job

```json
{
  "output": {
    "saveFiles": true,
    "uploadToS3": {
      "enabled": false
    }
  }
}
```

---

## Monitoring Uploads

### Check Upload Status via Database

```sql
SELECT
    id,
    name,
    output->'uploadToS3'->>'status' as s3_status,
    output->'uploadToS3'->>'uploadedAt' as uploaded_at,
    output->'uploadToS3'->>'filesUploaded' as files_uploaded,
    output->'uploadToS3'->>'bytesUploaded' as bytes_uploaded,
    output->'uploadToS3'->'errors' as errors
FROM jobs
WHERE id = 'YOUR-JOB-ID';
```

### Check Upload Status via API

```bash
TOKEN="your-jwt-token"
JOB_ID="73395058-e599-4bf7-a35f-79da2264afa8"

curl -s http://localhost:3010/api/scraper/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.data.output.uploadToS3'
```

Expected response:
```json
{
  "enabled": true,
  "status": "success",
  "uploadedAt": "2025-11-14T01:35:30.123456Z",
  "s3Urls": {
    "all_products_json": "s3://bucket/prefix/folder/all_products.json",
    "categories_json": "s3://bucket/prefix/folder/categories.json",
    "pdfs_dir": "s3://bucket/prefix/folder/pdfs/"
  },
  "bytesUploaded": 16777216,
  "filesUploaded": 320,
  "errors": []
}
```

### Monitor Celery Task Logs

```bash
docker-compose logs -f celery-worker | grep -i s3
```

### Verify Files in S3

```bash
# List files for a specific job
aws s3 ls s3://your-bucket/scraper-outputs/20251114_011839_73395058-e599-4bf7-a35f-79da2264afa8/ --recursive

# Check file size
aws s3 ls s3://your-bucket/scraper-outputs/ --recursive --summarize
```

---

## Troubleshooting

### Issue: "Access Denied" Errors

**Cause**: IAM user lacks necessary permissions

**Solution**:
1. Verify IAM policy includes all required actions:
   ```json
   {
       "Effect": "Allow",
       "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:ListBucket"
       ],
       "Resource": [
           "arn:aws:s3:::your-bucket",
           "arn:aws:s3:::your-bucket/*"
       ]
   }
   ```
2. Check bucket policy doesn't deny access
3. Verify credentials are correct in `.env`

### Issue: "Bucket Does Not Exist"

**Cause**: Bucket name incorrect or wrong region

**Solution**:
1. Verify bucket name in `.env` matches exactly
2. Check bucket exists in specified region:
   ```bash
   aws s3api head-bucket --bucket your-bucket-name
   ```

### Issue: Upload Times Out

**Cause**: Large files or slow network

**Solution**:
1. Increase timeout in `.env`:
   ```bash
   S3_UPLOAD_TIMEOUT=600
   ```
2. Check network connectivity to S3:
   ```bash
   aws s3 ls s3://your-bucket/
   ```

### Issue: Upload Shows "Partial" Status

**Cause**: Some files failed to upload

**Solution**:
1. Check errors in database:
   ```sql
   SELECT output->'uploadToS3'->'errors' FROM jobs WHERE id = 'JOB_ID';
   ```
2. Review Celery logs for specific error messages
3. Retry upload manually if needed

### Issue: S3 Upload Disabled

**Cause**: `S3_ENABLED=false` or missing credentials

**Solution**:
1. Verify `.env` settings:
   ```bash
   S3_ENABLED=true
   S3_BUCKET_NAME=your-bucket
   S3_ACCESS_KEY_ID=AKIAXXXXXXXX
   S3_SECRET_ACCESS_KEY=xxxxxxxxxxxxxx
   ```
2. Restart containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## Best Practices

### Security

1. **Never Commit Credentials**: Use `.env` file and add to `.gitignore`
2. **Use IAM Roles** (when on AWS): Prefer IAM roles over access keys for EC2/ECS
3. **Rotate Keys Regularly**: Rotate access keys every 90 days
4. **Principle of Least Privilege**: Grant only required S3 permissions
5. **Enable Encryption**: Use SSE-S3 or SSE-KMS for data at rest
6. **Use VPC Endpoints**: If running on AWS, use VPC endpoints for S3 access

### Cost Optimization

1. **Lifecycle Policies**: Transition old data to Glacier
   - STANDARD_IA after 30 days
   - GLACIER after 90 days
   - Delete after 1 year (if appropriate)

2. **Intelligent Tiering**: Let AWS automatically optimize storage class

3. **Compress Before Upload**: Enable compression for JSON files:
   ```python
   # Custom implementation in S3Uploader if needed
   ```

4. **Selective Upload**: Don't upload screenshots by default:
   ```json
   {
     "uploadToS3": {
       "uploadScreenshots": false
     }
   }
   ```

### Performance

1. **Parallel Uploads**: Celery handles uploads in background
2. **Large File Optimization**: boto3 automatically uses multipart upload > 25MB
3. **Regional Bucket**: Use bucket in same region as application
4. **CloudFront** (optional): Use CDN for frequently accessed data

### Monitoring

1. **Enable S3 Access Logging**: Track all S3 access
2. **CloudWatch Metrics**: Monitor upload success/failure rates
3. **Database Tracking**: Query upload statistics regularly
4. **Alert on Failures**: Set up alerts for failed uploads

### Data Organization

1. **Consistent Prefix**: Use `S3_PREFIX=scraper-outputs/`
2. **Folder Structure**: Maintain consistent naming:
   ```
   scraper-outputs/
     ├── 20251114_011839_uuid/
     ├── 20251115_093045_uuid/
     └── 20251115_142317_uuid/
   ```
3. **Tagging**: Add S3 object tags for easier management:
   - `client:agar`
   - `type:scrape-output`
   - `date:2025-11-14`

---

## Example: Complete Setup Workflow

```bash
# 1. Create S3 bucket
aws s3 mb s3://my-scraper-outputs --region ap-southeast-2

# 2. Create IAM user and policy (via Console or CLI)

# 3. Update .env file
cat >> .env << 'EOF'
S3_ENABLED=true
S3_BUCKET_NAME=my-scraper-outputs
S3_REGION=ap-southeast-2
S3_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
S3_SECRET_ACCESS_KEY=your-secret-key-here
S3_UPLOAD_ON_COMPLETION=true
S3_PREFIX=scraper-outputs/
EOF

# 4. Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# 5. Run a test job
TOKEN=$(curl -s -X POST http://localhost:3010/api/scraper/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123"}' | jq -r '.data.access_token')

curl -X POST http://localhost:3010/api/scraper/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "S3 Test Job",
    "type": "web",
    "config": {
      "startUrls": ["https://www.agar.com.au"],
      "maxPages": 10
    },
    "output": {
      "saveFiles": true,
      "fileFormat": "json"
    }
  }'

# 6. Monitor upload (wait for job to complete)
sleep 60
JOB_ID="<job-id-from-above>"

curl -s http://localhost:3010/api/scraper/jobs/$JOB_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.data.output.uploadToS3'

# 7. Verify in S3
aws s3 ls s3://my-scraper-outputs/scraper-outputs/ --recursive
```

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review Celery worker logs: `docker-compose logs celery-worker`
3. Check API logs: `docker-compose logs api`
4. Consult [DOWNSTREAM_INTEGRATION.md](./DOWNSTREAM_INTEGRATION.md) for usage examples

---

## Related Documentation

- [Downstream Integration Guide](./DOWNSTREAM_INTEGRATION.md) - How to access S3 data
- [Run Management Strategy](./RUN_MANAGEMENT_STRATEGY.md) - Archival and lifecycle
- [Deployment Setup](./DEPLOYMENT_SETUP.md) - Production deployment
