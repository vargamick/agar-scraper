# AWS LightSail Deployment Verification

**Date:** 2025-11-09  
**Instance:** AskAgar1 (52.63.86.55)  
**Status:** ✅ SUCCESSFULLY DEPLOYED

---

## Deployment Summary

The Agar scraper Docker setup has been successfully deployed to AWS LightSail instance with full functionality verified through a complete test scrape.

### Instance Details
- **IP Address:** 52.63.86.55
- **Instance Name:** AskAgar1
- **Resources:** 8GB RAM, 2 CPU cores, 135GB disk
- **OS:** Ubuntu
- **SSH Key:** `/Users/mick/AI/security/ask-agar-lightsail.pem`
- **Deployment Directory:** `~/agar-scraper`

---

## Docker Services

### Service Architecture
Two Docker services running in orchestrated configuration:

1. **crawl4ai-service**
   - Image: `unclecode/crawl4ai:latest`
   - Port: 11235 (internal Docker network)
   - Health: ✅ Healthy
   - Purpose: Provides REST API for browser automation

2. **agar-scraper**
   - Image: Custom built from local Dockerfile
   - Depends on: crawl4ai-service
   - Health: ✅ Healthy
   - Purpose: Main scraping application

### Service Status
```bash
# Both services running and healthy
✓ crawl4ai-service: healthy
✓ agar-scraper: healthy
```

---

## Critical Fix: Playwright Dependencies

### Problem Encountered
Chromium browser failed to launch due to missing system libraries:
```
error while loading shared libraries: libglib-2.0.so.0: cannot open shared object file
```

### Root Cause
Multi-stage Docker build was copying Playwright browser binaries but not the ~100 system dependencies required by the `--with-deps` flag (fonts, X11 libraries, Mesa drivers, etc.)

### Solution Implemented
Modified Dockerfile to install Playwright with system dependencies in the **final stage**:

```dockerfile
# Stage 2: Final runtime stage
FROM python:3.11-slim

# Copy Python packages and executables from base stage
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# CRITICAL: Install Playwright with system dependencies in final stage
# This installs ~100 system packages needed for Chromium to run
RUN playwright install --with-deps chromium
```

### Build Command Used
```bash
docker compose build --no-cache agar-scraper
```

---

## Test Scrape Results

### Execution Details
- **Run ID:** agarScrape_20251109_024249_TEST
- **Mode:** TEST (limited to 2 categories)
- **Duration:** 2 minutes 8 seconds
- **Start Time:** 2025-11-09 02:42:49 UTC
- **End Time:** 2025-11-09 02:44:57 UTC

### Success Metrics
```json
{
  "total_attempted": 5,
  "total_scraped": 5,
  "total_failed": 0,
  "success_rate": "100.0%"
}
```

### PDF Download Results
```json
{
  "total_pdfs": 10,
  "successful_downloads": 10,
  "failed_downloads": 0,
  "skipped": 0,
  "total_size_bytes": 2002140
}
```

### Data Quality Verification
All scraped products contain complete metadata:
- Product name and URL
- Product image URL
- Overview and description
- SKUs
- Categories
- SDS/PDS URLs
- Timestamps

**Sample Product Data (Breeze):**
```json
{
  "product_name": "Breeze",
  "product_url": "https://agar.com.au/product/breeze/",
  "product_image_url": "https://agar.com.au/wp-content/uploads/2023/08/Breeze-5L-1000x1000.png",
  "product_overview": "What is Breeze?BREEZE is a strong odour-masking deodoriser...",
  "product_description": "DescriptionHow Does It Work?BREEZE is a concentrate...",
  "product_skus": "BRE5, BRE20",
  "product_categories": ["Detergent Deodorisers"],
  "sds_url": "https://agar.com.au/wp-content/uploads/2024/12/Breeze-SDS-GHS7.pdf",
  "pds_url": "https://agar.com.au/wp-content/uploads/2025/07/Breeze-PDS.pdf",
  "total_pdfs_found": 4
}
```

### File Structure Generated
```
agar_scrapes/agarScrape_20251109_024249_TEST/
├── all_products_data.json
├── categories.json
├── categories/
│   ├── air-fresheners.json
│   ├── air-fresheners/
│   │   ├── air-fresheners_detergent-deodorisers.json
│   │   └── air-fresheners_detergent-deodorisers_products.json
│   ├── air-fresheners_products.json
│   ├── all-purpose-floor-cleaners.json
│   └── all-purpose-floor-cleaners_products.json
├── pdfs/
│   ├── Breeze_pdfs.json
│   ├── Everfresh_pdfs.json
│   ├── Floral_pdfs.json
│   ├── Freshaire_pdfs.json
│   ├── Lavender_pdfs.json
│   ├── PDS/
│   │   ├── Breeze_PDS.pdf
│   │   ├── Everfresh_PDS.pdf
│   │   ├── Floral_PDS.pdf
│   │   ├── Freshaire_PDS.pdf
│   │   └── Lavender_PDS.pdf
│   └── SDS/
│       ├── Breeze_SDS.pdf
│       ├── Everfresh_SDS.pdf
│       ├── Floral_SDS.pdf
│       ├── Freshaire_SDS.pdf
│       └── Lavender_SDS.pdf
├── products/
│   ├── Breeze.json
│   ├── Everfresh.json
│   ├── Floral.json
│   ├── Freshaire.json
│   └── Lavender.json
├── reports/
│   ├── final_report.json
│   └── pdf_download_report.json
└── screenshots/
    ├── Breeze.png
    ├── Everfresh.png
    ├── Floral.png
    ├── Freshaire.png
    └── Lavender.png
```

---

## Access and Management

### SSH Access
```bash
ssh -i /Users/mick/AI/security/ask-agar-lightsail.pem ubuntu@52.63.86.55
```

### Docker Management Commands
```bash
# View service status
docker compose ps

# View logs
docker compose logs -f agar-scraper
docker compose logs -f crawl4ai-service

# Restart services
docker compose restart

# Stop services
docker compose down

# Start services
docker compose up -d

# Rebuild scraper service
docker compose build --no-cache agar-scraper
docker compose up -d
```

### Running Scrapes

**Test Scrape (2 categories):**
```bash
docker compose run --rm agar-scraper python main.py --test
```

**Full Scrape (all categories):**
```bash
docker compose run --rm agar-scraper python main.py
```

**View Scrape Results:**
```bash
# List all scrape runs
ls -la agar_scrapes/

# View latest scrape
ls -la agar_scrapes/agarScrape_*/
```

---

## Configuration

### Environment Variables
Located in `/home/ubuntu/agar-scraper/.env`:
```bash
# Crawl4AI Configuration
CRAWL4AI_API_BASE_URL=http://crawl4ai:11235
CRAWL4AI_API_TOKEN=

# Optional: Firecrawl API (not currently used)
FIRECRAWL_API_KEY=
```

### Docker Compose Configuration
- Service networking: Both services on same Docker network
- Volume mounts: Persistent data in `./agar_scrapes`
- Health checks: Both services monitored for availability
- Restart policy: Always restart on failure

---

## Verification Checklist

- [x] Docker services deployed and running
- [x] Playwright browser dependencies installed
- [x] Crawl4AI service accessible from agar-scraper
- [x] Test scrape completed successfully (100% success rate)
- [x] All 5 products scraped with complete metadata
- [x] All 10 PDFs downloaded (5 SDS + 5 PDS)
- [x] Screenshots captured for all products
- [x] Reports generated correctly
- [x] File structure organized properly
- [x] Data quality verified

---

## Next Steps

### Recommended Actions

1. **Run Full Scrape**
   - Execute a complete scrape of all categories
   - Monitor for any edge cases or errors
   - Verify storage capacity for full dataset

2. **Set Up Automation** (Optional)
   - Configure cron job for scheduled scrapes
   - Set up log rotation
   - Configure backup/archive strategy

3. **Monitoring** (Optional)
   - Set up monitoring for Docker service health
   - Configure alerts for scrape failures
   - Monitor disk space usage

### Example Cron Job for Daily Scrapes
```bash
# Add to crontab: crontab -e
0 2 * * * cd /home/ubuntu/agar-scraper && docker compose run --rm agar-scraper python main.py >> /home/ubuntu/scrape.log 2>&1
```

---

## Troubleshooting

### If Services Stop
```bash
# Check service status
docker compose ps

# Restart services
docker compose up -d

# Check logs for errors
docker compose logs --tail=100 agar-scraper
```

### If Scrape Fails
```bash
# Check scraper logs
docker compose logs agar-scraper

# Check crawl4ai service
docker compose logs crawl4ai-service

# Restart both services
docker compose restart
```

### If Playwright Issues Occur
```bash
# Rebuild with no cache to reinstall dependencies
docker compose build --no-cache agar-scraper
docker compose up -d
```

---

## Deployment Success

✅ **Deployment Status:** FULLY OPERATIONAL

All components verified and working correctly. The scraper is ready for production use.

---

**Documentation Created:** 2025-11-09  
**Last Verified:** 2025-11-09  
**Next Review:** As needed
