# S3 Integration Setup - Complete

## Configuration Summary

The S3 integration has been fully configured and is ready to test.

### S3 Bucket Configuration

- **Bucket Name**: `agar-documentation`
- **Region**: `us-east-1`
- **S3 Prefix**: `agar/`
- **IAM User**: `agar-s3-user`

### File Naming Convention

All scraper outputs will be uploaded to S3 using this path structure:

```
s3://agar-documentation/agar/{YYYYMMDD_HHMMSS}_{job-uuid}/
├── all_products.json
├── categories.json
├── results.json
├── pdfs/
│   ├── SDS/
│   │   └── *.pdf
│   └── PDS/
│       └── *.pdf
└── category_*.json (if uploadCategories: true)
```

**Example Path**:
```
s3://agar-documentation/agar/20251118_143025_73395058-e599-4bf7-a35f-79da2264afa8/all_products.json
```

### Environment Configuration

The `.env` file has been updated with:

```bash
S3_ENABLED=true
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=your-access-key-id
S3_SECRET_ACCESS_KEY=your-secret-access-key
S3_UPLOAD_ON_COMPLETION=true
S3_PREFIX=agar/
S3_UPLOAD_TIMEOUT=300
S3_MAX_RETRIES=3
```

## How It Works

1. **Job Execution**: When a scrape job runs, all outputs are saved locally in `/app/scraper_data/jobs/{folder_name}_{job_id}/`

2. **Automatic Upload**: After job completion, a Celery background task automatically uploads files to S3 (if `S3_ENABLED=true`)

3. **Database Storage**: S3 URLs and upload metadata are stored in the `job.output` JSONB field:
   ```json
   {
     "uploadToS3": {
       "status": "success",
       "uploadedAt": "2025-11-18T03:45:30.123456Z",
       "s3Urls": {
         "all_products_json": "s3://agar-documentation/agar/20251118_143025_uuid/all_products.json",
         "categories_json": "s3://agar-documentation/agar/20251118_143025_uuid/categories.json",
         "pdfs_dir": "s3://agar-documentation/agar/20251118_143025_uuid/pdfs/"
       },
       "filesUploaded": 320,
       "bytesUploaded": 16777216
     }
   }
   ```

4. **Downstream Access**: Applications can query the database for S3 URLs and download files directly from S3

## Testing the Integration

### Prerequisites

1. **Start Docker Desktop**
2. **Rebuild containers** (first time only, to install boto3):
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Run the Test

Execute the test script:

```bash
./run_s3_scrape.sh
```

This script will:
1. ✓ Verify Docker is running
2. ✓ Verify AWS credentials and S3 bucket access
3. ✓ Authenticate with the API
4. ✓ Create a scrape job (50 pages from agar.com.au)
5. ✓ Monitor job progress in real-time
6. ✓ Wait for S3 upload to complete
7. ✓ Verify files in S3
8. ✓ Display job statistics and S3 URLs
9. ✓ Download a sample file to verify content

### Expected Output

```
=========================================================================
S3 Scraper Integration Test
=========================================================================

[INFO] Checking prerequisites...
[SUCCESS] Docker is running
[SUCCESS] AWS CLI is installed
[SUCCESS] Bucket agar-documentation is accessible
[SUCCESS] Container scraper-api is running
[SUCCESS] Container scraper-postgres is running
[SUCCESS] Container scraper-redis is running
[SUCCESS] Container scraper-celery-worker is running
[SUCCESS] Container crawl4ai-service is running

[INFO] Step 1: Authenticating with API...
[SUCCESS] Authenticated successfully

[INFO] Step 2: Creating scrape job with S3 upload enabled...
[SUCCESS] Job created with ID: 73395058-e599-4bf7-a35f-79da2264afa8

[INFO] Step 3: Monitoring job progress...
[INFO] Job ID: 73395058-e599-4bf7-a35f-79da2264afa8

[INFO] Status: running | Items extracted: 45
[INFO] Status: running | Items extracted: 98
[INFO] Status: running | Items extracted: 156
[INFO] Status: completed | Items extracted: 199
[SUCCESS] Job completed successfully

[INFO] Step 4: Waiting for S3 upload to complete...
[INFO] S3 Upload Status: uploading
[INFO] S3 Upload Status: success
[SUCCESS] S3 upload completed

[INFO] Step 5: Verifying files in S3...
[INFO] Folder name: 20251118_143025
[INFO] Listing files in S3: s3://agar-documentation/agar/20251118_143025_73395058-e599-4bf7-a35f-79da2264afa8/

2025-11-18 14:32:15     524288 all_products.json
2025-11-18 14:32:16      98304 categories.json
2025-11-18 14:32:16     131072 results.json
2025-11-18 14:32:17          0 pdfs/
2025-11-18 14:32:18    2097152 pdfs/SDS/Product1-SDS.pdf
...
[SUCCESS] Files found in S3

=========================================================================
[SUCCESS] S3 Integration Test Completed
=========================================================================

Job Statistics:
---------------
{
  "itemsExtracted": 199,
  "categoriesFound": 57,
  "pdfsDownloaded": 312,
  "bytesDownloaded": 15728640
}

S3 Upload Information:
----------------------
{
  "status": "success",
  "uploadedAt": "2025-11-18T03:32:30.123456Z",
  "filesUploaded": 320,
  "bytesUploaded": 16777216,
  "s3Urls": {
    "all_products_json": "s3://agar-documentation/agar/20251118_143025_.../all_products.json",
    "categories_json": "s3://agar-documentation/agar/20251118_143025_.../categories.json",
    "results_json": "s3://agar-documentation/agar/20251118_143025_.../results.json",
    "pdfs_dir": "s3://agar-documentation/agar/20251118_143025_.../pdfs/"
  }
}

S3 Location:
------------
Bucket: s3://agar-documentation/agar/20251118_143025_73395058-e599-4bf7-a35f-79da2264afa8/

[INFO] Downloading sample file for verification...
[SUCCESS] Downloaded all_products.json (199 products)

[SUCCESS] All tests passed!

To view files in S3:
  aws s3 ls s3://agar-documentation/agar/20251118_143025_73395058-e599-4bf7-a35f-79da2264afa8/ --recursive

To download all files:
  aws s3 sync s3://agar-documentation/agar/20251118_143025_73395058-e599-4bf7-a35f-79da2264afa8/ ./s3_download/
```

## Verifying S3 Upload Manually

### Using AWS CLI

List all scraper runs in S3:
```bash
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export AWS_DEFAULT_REGION=us-east-1

aws s3 ls s3://your-bucket-name/agar/
```

List files for a specific run:
```bash
aws s3 ls s3://agar-documentation/agar/20251118_143025_73395058-e599-4bf7-a35f-79da2264afa8/ --recursive
```

Download a file:
```bash
aws s3 cp s3://agar-documentation/agar/20251118_143025_uuid/all_products.json ./downloaded_products.json
```

### Using Database Query

Query the database to get S3 URLs:
```sql
SELECT
    id,
    folder_name,
    output->'uploadToS3'->'s3Urls'->>'all_products_json' as s3_products_url,
    output->'uploadToS3'->>'status' as upload_status,
    output->'uploadToS3'->>'filesUploaded' as files_uploaded,
    output->'uploadToS3'->>'bytesUploaded' as bytes_uploaded
FROM jobs
WHERE status = 'completed'
  AND output->'uploadToS3'->>'status' = 'success'
ORDER BY completed_at DESC
LIMIT 5;
```

## Next Steps

1. **Start Docker Desktop** (if not already running)

2. **Rebuild containers** to install boto3:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

   Wait for all containers to be healthy (~2-3 minutes)

3. **Run the test**:
   ```bash
   ./run_s3_scrape.sh
   ```

4. **Verify results** in S3:
   ```bash
   aws s3 ls s3://agar-documentation/agar/ --recursive
   ```

## Troubleshooting

### Issue: Docker not running
**Error**: `Cannot connect to the Docker daemon`
**Solution**: Start Docker Desktop and wait for it to fully initialize

### Issue: S3 Access Denied
**Error**: `An error occurred (AccessDenied) when calling the PutObject operation`
**Solution**: Verify IAM permissions for `agar-s3-user` include:
- `s3:PutObject`
- `s3:GetObject`
- `s3:ListBucket`

### Issue: S3 upload shows "failed" status
**Check Celery worker logs**:
```bash
docker-compose logs celery-worker | grep -i s3
```

**Check job error details**:
```bash
curl -s http://localhost:3010/api/scraper/jobs/{JOB_ID} \
  -H "Authorization: Bearer {TOKEN}" | jq '.data.output.uploadToS3.errors'
```

### Issue: boto3 module not found
**Error**: `ModuleNotFoundError: No module named 'boto3'`
**Solution**: Rebuild containers:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Documentation

- **Full S3 Integration Guide**: [docs/S3_INTEGRATION.md](docs/S3_INTEGRATION.md)
- **Downstream Integration**: [docs/DOWNSTREAM_INTEGRATION.md](docs/DOWNSTREAM_INTEGRATION.md)
- **API Documentation**: Available at `http://localhost:3010/docs` when API is running

## Summary

✅ S3 bucket configured: `agar-documentation`
✅ S3 prefix configured: `agar/`
✅ Folder naming: `YYYYMMDD_HHMMSS_{job-uuid}`
✅ AWS credentials configured
✅ Auto-upload enabled on job completion
✅ Database tracking of S3 URLs
✅ Test script ready: `./run_s3_scrape.sh`

**Ready to test!** Start Docker Desktop and run `./run_s3_scrape.sh`
