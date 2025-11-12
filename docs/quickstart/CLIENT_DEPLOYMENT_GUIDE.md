# 3DN Scraper Template - Client Deployment Guide

**Version:** 1.0  
**Last Updated:** 2025-01-11  
**Template Version:** 1.0.0

---

## Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Quick Start Workflow](#quick-start-workflow)
4. [Detailed Deployment Process](#detailed-deployment-process)
5. [Phase-by-Phase Configuration](#phase-by-phase-configuration)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Next Steps](#next-steps)

---

## Introduction

The **3DN Scraper Template** is a professional, reusable web scraping framework designed to rapidly deploy client-specific scraping projects. This guide walks you through deploying the template for a new client organization.

### What is the 3DN Scraper Template?

The 3DN Scraper Template provides:

- **Client-agnostic core modules** that work across different websites
- **Configuration-based customization** without modifying core code
- **Automated deployment tools** for rapid setup
- **Comprehensive validation** to catch configuration errors early
- **Testing utilities** to validate before full production scrape

### Time to Deploy

- **Experienced users:** 15-30 minutes for basic deployment
- **First-time users:** 1-2 hours including testing and refinement
- **Complex sites:** 2-4 hours with iterative selector refinement

---

## Prerequisites

### Required Knowledge

- Basic understanding of web scraping concepts
- Familiarity with CSS selectors (for extraction strategy)
- Ability to use browser developer tools (F12)
- Basic command-line usage
- Understanding of JSON data format

### Required Software

- **Python 3.11+** (required for Crawl4AI)
- **Git** (for version control)
- **Code editor** (VS Code recommended)
- **Modern web browser** (Chrome, Firefox, or Edge)

### System Requirements

- **OS:** macOS, Linux, or Windows
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 1GB for template + client data
- **Network:** Stable internet connection

---

## Quick Start Workflow

For experienced users, here's the condensed deployment workflow:

```bash
# 1. Deploy new client structure
python scripts/deploy_new_client.py

# 2. Validate configuration
python scripts/validate_config.py --client clientname

# 3. Test website connection
python scripts/test_connection.py --client clientname

# 4. Configure extraction selectors (edit files)
# Edit: config/clients/{clientname}/extraction_strategies.py

# 5. Test extraction on sample URL
python scripts/test_extraction.py --client clientname --url "sample-url"

# 6. Run test scrape (limited products)
python main.py --client clientname --test

# 7. Review results, iterate on configuration

# 8. Run full production scrape
python main.py --client clientname
```

**Continue reading for detailed step-by-step instructions.**

---

## Detailed Deployment Process

### Overview of Deployment Phases

The deployment process follows six distinct phases:

1. **Initial Setup** - Create client directory structure and basic config
2. **URL Pattern Discovery** - Understand how the website is structured
3. **Extraction Strategy** - Define CSS selectors for data extraction
4. **Data Schema Mapping** - Map extracted fields to output format
5. **Category Discovery** - Configure product categories
6. **Performance Tuning** - Optimize timeouts and limits

Each phase builds on the previous one, and you'll test frequently to ensure everything works correctly.

---

## Phase-by-Phase Configuration

### Phase 1: Initial Setup

**Objective:** Create the basic client deployment structure.

#### Step 1.1: Run Deployment Script

```bash
python scripts/deploy_new_client.py
```

This interactive script will prompt you for:

1. **Client short name:**
   - Lowercase, no spaces
   - Alphanumeric and hyphens only
   - Example: `acme-chemicals` or `cleaningco`

2. **Client full name:**
   - Display name for reports
   - Example: `ACME Chemicals Ltd` or `Cleaning Company Inc`

3. **Client website URL:**
   - Must start with `http://` or `https://`
   - Example: `https://www.acme-chemicals.com`

4. **Output prefix:**
   - Used in directory names
   - Example: `AcmeChemScrape` or `CleaningCoScrape`

5. **Base output directory:**
   - Where scrape data will be stored
   - Example: `acme_scrapes` or `cleaningco_scrapes`

#### Step 1.2: Review Generated Files

The script creates:

```
config/clients/{client_name}/
├── __init__.py
├── client_config.py           # Basic configuration (edit this)
├── extraction_strategies.py   # CSS selectors (edit this next)
└── README.md                  # Client-specific notes

{client_name}_scrapes/         # Output directory
```

#### Step 1.3: Validate Initial Configuration

```bash
python scripts/validate_config.py --client clientname
```

**Expected Output:**
```
✓ Client directory structure valid
✓ Configuration loaded successfully
✓ Required fields present: CLIENT_NAME, BASE_URL, etc.
```

If validation fails, review error messages and fix issues in `client_config.py`.

#### Step 1.4: Test Website Connection

```bash
python scripts/test_connection.py --client clientname --base-only
```

**Expected Output:**
```
Testing connection to: https://client-website.com
✓ DNS resolution successful
✓ Connection successful (200 OK)
✓ Response time: 1.23s
```

If connection fails:
- Verify URL is correct
- Check if site requires authentication
- Check if site blocks automated requests
- See [Troubleshooting](#troubleshooting) section

---

### Phase 2: URL Pattern Discovery

**Objective:** Understand how the client's website structures URLs for categories and products.

#### Step 2.1: Manual Website Exploration

Open the client's website in your browser and:

1. **Find a category page:**
   - Look for product listings, categories, or collections
   - Example: `https://client.com/products/category-name/`
   - Note the URL pattern

2. **Find a product detail page:**
   - Click on a product from the category
   - Example: `https://client.com/products/product-name/`
   - Note the URL pattern

3. **Identify the pattern:**
   - What part changes between different categories/products?
   - This is the "slug" - typically the last part of the URL

#### Step 2.2: Document URL Patterns

Edit `config/clients/{clientname}/client_config.py`:

```python
# URL patterns (replace {slug} with actual category/product identifier)
CATEGORY_URL_PATTERN = "/product-category/{slug}/"
PRODUCT_URL_PATTERN = "/product/{slug}/"
```

**Common Patterns:**

| Website Structure | Category Pattern | Product Pattern |
|------------------|------------------|----------------|
| WooCommerce | `/product-category/{slug}/` | `/product/{slug}/` |
| Shopify | `/collections/{slug}` | `/products/{slug}` |
| Custom | `/categories/{slug}/` | `/item/{slug}/` |
| Custom | `/shop/{slug}` | `/product-detail/{slug}` |

#### Step 2.3: Test URL Generation

```bash
python scripts/test_connection.py --client clientname
```

This will test both:
- Base URL connection
- Category URL pattern (using first known category)

**Expected Output:**
```
✓ Base URL: https://client.com (200 OK)
✓ Category URL: https://client.com/category/test-category/ (200 OK)
```

---

### Phase 3: Extraction Strategy

**Objective:** Define CSS selectors to extract data from web pages.

This is the most critical and iterative phase. Take your time to get selectors right.

#### Step 3.1: Understand CSS Selectors

CSS selectors identify HTML elements on a page:

| Selector Type | Syntax | Example |
|--------------|--------|---------|
| Class | `.classname` | `.product-title` |
| ID | `#idname` | `#product-123` |
| Tag | `tagname` | `h1` or `div` |
| Attribute | `[attr=value]` | `[data-product]` |
| Descendant | `parent child` | `.product .title` |
| Multiple | `selector1, selector2` | `.title, h1` |

#### Step 3.2: Open Browser Developer Tools

1. Open the client's website
2. Navigate to a category page
3. Press **F12** to open Developer Tools
4. Click the **Inspector** or **Elements** tab

#### Step 3.3: Identify Category Page Selectors

**What to find:**

1. **Product container** - The element that wraps ALL products
2. **Individual product** - The repeating element for each product
3. **Product link** - The `<a>` tag with the product URL
4. **Product name** - The text element with product name

**How to find selectors:**

1. **Right-click on a product** → **Inspect Element**
2. Examine the HTML structure
3. Look for unique classes or IDs
4. Test selector in browser console:

```javascript
// Test if selector finds elements
document.querySelectorAll("your-selector-here")

// Should return an array of elements
// Example: document.querySelectorAll(".product")
```

**Example HTML Structure:**

```html
<div class="products-grid">
    <div class="product-item">
        <a href="/product/cleaning-solution/" class="product-link">
            <h3 class="product-title">Cleaning Solution</h3>
        </a>
    </div>
    <div class="product-item">
        <a href="/product/disinfectant/" class="product-link">
            <h3 class="product-title">Disinfectant</h3>
        </a>
    </div>
</div>
```

**Resulting selectors:**

```python
CATEGORY_SELECTORS = {
    "products": "div.product-item",           # Each product card
    "product_link": "a.product-link",         # Link within product card
    "product_name": "h3.product-title"        # Name within product card
}
```

#### Step 3.4: Identify Product Page Selectors

Navigate to a product detail page and identify:

1. **Product name** - Main title/heading
2. **Product image** - Main product image
3. **Description** - Product description or overview
4. **SKU** - Product code (if available)
5. **Categories** - Product categories/tags
6. **Price** - Product price (optional)

**Test each selector in browser console:**

```javascript
// Test product name
document.querySelector("h1.product-title").textContent

// Test product image
document.querySelector(".product-image img").src

// Test description
document.querySelector(".product-description").textContent
```

**Example Product Selectors:**

```python
PRODUCT_SELECTORS = {
    "name": "h1.product-title",
    "image": ".product-image img",
    "overview": ".product-overview",
    "description": ".product-description",
    "sku": ".product-sku",
    "categories": ".product-categories a"
}
```

#### Step 3.5: Identify PDF/Document Selectors (if applicable)

If the client's products have downloadable documents (SDS, PDS, datasheets):

```python
PDF_SELECTORS = {
    "sds_link": "a[href*='SDS']",           # Link containing 'SDS'
    "pds_link": "a[href*='PDS']",           # Link containing 'PDS'
    "document_section": ".product-documents" # Container with documents
}
```

#### Step 3.6: Update Extraction Strategy File

Edit `config/clients/{clientname}/extraction_strategies.py`:

```python
"""
3DN Scraper Template - Extraction Strategies
Client: Your Client Name
"""

from typing import Dict, List
from strategies.base_strategy import ExtractionStrategy

class ClientExtractionStrategy(ExtractionStrategy):
    """Client-specific CSS selectors and extraction logic"""
    
    # Category page selectors
    CATEGORY_SELECTORS = {
        "products": "CSS selector for product list",
        "product_link": "CSS selector for product URL",
        "product_name": "CSS selector for product name"
    }
    
    # Product detail page selectors
    PRODUCT_SELECTORS = {
        "name": "CSS selector for product name",
        "image": "CSS selector for main image",
        "overview": "CSS selector for overview/summary",
        "description": "CSS selector for full description",
        "sku": "CSS selector for SKU",
        "categories": "CSS selector for categories"
    }
    
    # PDF/Document selectors (if applicable)
    PDF_SELECTORS = {
        "sds_link": "CSS selector for SDS document",
        "pds_link": "CSS selector for PDS document",
        "document_section": "CSS selector for document area"
    }
```

#### Step 3.7: Test Extraction

Test your selectors on a real page:

```bash
# Test on a category page
python scripts/test_extraction.py \
    --client clientname \
    --url "https://client.com/category/example/" \
    --type category

# Test on a product page
python scripts/test_extraction.py \
    --client clientname \
    --url "https://client.com/product/example-product/"
```

**Expected Output:**

```
================================================================================
Testing Extraction: category page
URL: https://client.com/category/example/
================================================================================

Category Page Extraction:
  ✓ products: 12 found
  ✓ product_link: 12 found
  ✓ product_name: 12 found

Sample Products:
  1. Product Name 1 → /product/product-1/
  2. Product Name 2 → /product/product-2/
  3. Product Name 3 → /product/product-3/

✓ All required selectors found data
================================================================================
```

#### Step 3.8: Iterate and Refine

If selectors don't work:

1. **Review error messages** - they indicate which selectors failed
2. **Check selector specificity** - too generic or too specific?
3. **Verify selector in browser console** first
4. **Try alternative selectors** - use parent/child relationships
5. **Test on multiple pages** - ensure selectors work consistently

**Common Issues:**

| Issue | Solution |
|-------|----------|
| Selector finds 0 elements | Selector too specific or doesn't exist |
| Selector finds wrong elements | Selector too generic |
| Selector works on one page but not others | Add more specific parent context |
| Content is in JavaScript | May need to wait for page load |

---

### Phase 4: Data Schema Mapping

**Objective:** Map extracted data fields to output JSON structure.

#### Step 4.1: Review Extracted Data

Run a test extraction and review the output:

```bash
python scripts/test_extraction.py \
    --client clientname \
    --url "https://client.com/product/example/" \
    --save
```

This saves the extracted data to a JSON file for review.

#### Step 4.2: Configure Product Schema

Edit `config/clients/{clientname}/client_config.py`:

```python
# Product schema mapping
PRODUCT_SCHEMA = {
    "name_field": "product_name",
    "url_field": "product_url",
    "image_field": "product_image_url",
    "overview_field": "product_overview",
    "description_field": "product_description",
    "sku_field": "product_sku",
    "categories_field": "product_categories"
}
```

**Field Descriptions:**

| Field | Description | Required |
|-------|-------------|----------|
| name_field | Product name/title | Yes |
| url_field | Product URL | Yes |
| image_field | Main product image URL | Recommended |
| overview_field | Short description | Optional |
| description_field | Full description | Recommended |
| sku_field | Product SKU/code | Optional |
| categories_field | Product categories | Optional |

#### Step 4.3: Configure PDF/Document Settings

If the client has downloadable documents:

```python
# PDF/Document configuration
HAS_SDS_DOCUMENTS = True        # Safety Data Sheets
HAS_PDS_DOCUMENTS = True        # Product Data Sheets
SDS_FIELD_NAME = "sds_url"      # Field name in output
PDS_FIELD_NAME = "pds_url"      # Field name in output
```

If no documents:

```python
HAS_SDS_DOCUMENTS = False
HAS_PDS_DOCUMENTS = False
```

#### Step 4.4: Test Complete Workflow

Run a limited test scrape:

```bash
python main.py --client clientname --test
```

**Expected Output:**

```
3DN Scraper Template v1.0.0
Client: Your Client Name
Mode: TEST (limited to 2 categories, 5 products)

Discovering categories...
✓ Found 5 categories

Processing category 1/2: Category Name
  ✓ Found 8 products
  ✓ Scraped 5/8 products (test limit)

Processing category 2/2: Another Category
  ✓ Found 12 products
  ✓ Scraped 5/12 products (test limit)

Scraping complete!
  Total products: 10
  Output: clientname_scrapes/run_20250111_153045/
```

#### Step 4.5: Review Output

Check the output directory:

```
clientname_scrapes/run_20250111_153045/
├── categories/
│   ├── category-1.json
│   └── category-2.json
├── products/
│   ├── product-1.json
│   ├── product-2.json
│   └── ...
├── pdfs/              # If documents enabled
├── screenshots/       # Page screenshots
├── logs/             # Scraping logs
└── reports/          # Summary reports
```

Verify:
- [ ] All expected fields are present in product JSON files
- [ ] Data looks correct and complete
- [ ] PDFs downloaded (if applicable)
- [ ] No major errors in logs

---

### Phase 5: Category Discovery

**Objective:** Configure which product categories to scrape.

#### Option A: Manual Category List (Recommended)

Best for sites with a manageable number of categories.

Edit `config/clients/{clientname}/client_config.py`:

```python
# Known categories (manual list)
KNOWN_CATEGORIES = [
    "category-slug-1",
    "category-slug-2",
    "category-slug-3",
    "category-slug-4"
]
```

**How to find category slugs:**

1. Browse the client's website
2. Note the URL of each category page
3. Extract the slug from the URL

Example:
- URL: `https://client.com/category/cleaning-supplies/`
- Slug: `cleaning-supplies`

#### Option B: Automatic Discovery (Advanced)

For sites with many categories or when you want automatic discovery:

```python
# Automatic category discovery
CATEGORY_DISCOVERY_ENABLED = True
CATEGORY_NAV_SELECTOR = "nav.product-categories li a"  # Selector for nav links
CATEGORY_EXTRACT_SLUG_FROM_URL = True
```

**Test category discovery:**

```bash
python core/category_scraper.py --client clientname --discover
```

#### Step 5.1: Test Category Access

Verify all categories are accessible:

```bash
python scripts/test_connection.py --client clientname
```

This tests each category URL pattern.

---

### Phase 6: Performance Tuning

**Objective:** Optimize scraping performance and handle rate limiting.

#### Step 6.1: Monitor Initial Performance

Run test scrape and monitor:
- Page load times
- Timeout errors
- Rate limiting issues
- Memory usage

#### Step 6.2: Adjust Timeouts (if needed)

Edit `config/clients/{clientname}/client_config.py`:

```python
# Timeout configuration (milliseconds)
PAGE_TIMEOUT = 60000          # Default: 60 seconds
DETAIL_PAGE_TIMEOUT = 35000   # Default: 35 seconds

# If pages load slowly, increase:
PAGE_TIMEOUT = 90000          # 90 seconds
DETAIL_PAGE_TIMEOUT = 60000   # 60 seconds
```

#### Step 6.3: Adjust Rate Limiting

If getting blocked or rate limited:

```python
# Rate limiting
RATE_LIMIT_DELAY = 2          # Default: 2 seconds between requests

# If getting blocked, increase:
RATE_LIMIT_DELAY = 5          # 5 seconds between requests
```

#### Step 6.4: Configure Retry Logic

```python
# Retry configuration
MAX_RETRIES = 3               # Default: 3 retries
RETRY_DELAY = 5               # Default: 5 seconds wait

# For unreliable connections:
MAX_RETRIES = 5
RETRY_DELAY = 10
```

#### Step 6.5: Adjust Test Mode Limits

```python
# Test mode configuration
TEST_CATEGORY_LIMIT = 2       # Number of categories in test mode
TEST_PRODUCT_LIMIT = 5        # Products per category in test mode

# For faster testing:
TEST_CATEGORY_LIMIT = 1
TEST_PRODUCT_LIMIT = 3

# For more thorough testing:
TEST_CATEGORY_LIMIT = 3
TEST_PRODUCT_LIMIT = 10
```

---

## Testing & Validation

### Validation Checklist

Before running a full production scrape:

- [ ] **Configuration validated:** `python scripts/validate_config.py --client clientname`
- [ ] **Connection tested:** `python scripts/test_connection.py --client clientname`
- [ ] **Extraction tested:** Test on multiple sample URLs
- [ ] **Test scrape completed:** `python main.py --client clientname --test`
- [ ] **Output reviewed:** All expected fields present and correct
- [ ] **PDFs downloaded:** If applicable, verify PDFs are downloaded
- [ ] **No major errors:** Review logs for critical issues
- [ ] **Performance acceptable:** No excessive timeouts or blocks

### Running Production Scrape

Once validation is complete:

```bash
# Full production scrape
python main.py --client clientname
```

**Monitor the scrape:**
- Watch console output for errors
- Check logs periodically
- Monitor output directory size
- Watch for rate limiting issues

**Typical scrape times:**

| Products | Approximate Time |
|----------|------------------|
| 100 products | 10-15 minutes |
| 500 products | 45-60 minutes |
| 1000 products | 1.5-2 hours |

*Times vary based on website speed, rate limiting, and PDF downloads.*

---

## Troubleshooting

### Common Issues

#### 1. Connection Errors

**Symptom:** `Connection failed` or `DNS resolution failed`

**Solutions:**
- Verify URL is correct (include `https://`)
- Check if website is accessible in browser
- Check if site requires authentication
- Try with `--base-only` flag first
- Check firewall/proxy settings

#### 2. No Products Found

**Symptom:** `Found 0 products` on category page

**Solutions:**
- Verify category URL is correct
- Check `CATEGORY_SELECTORS` - test in browser console
- Verify page has products (some may be empty)
- Check if content is JavaScript-rendered (wait for load)
- Use `--save` flag to inspect HTML

#### 3. Extraction Fails

**Symptom:** `Field extraction failed` or missing data

**Solutions:**
- Test selectors in browser console first
- Check if selector is too specific or too generic
- Verify HTML structure hasn't changed
- Try alternative selectors
- Check if content is in JavaScript/AJAX

#### 4. Timeout Errors

**Symptom:** `Page load timeout` errors

**Solutions:**
- Increase `PAGE_TIMEOUT` in config
- Check website speed in browser
- Verify network connection is stable
- Try reducing concurrent requests

#### 5. Rate Limiting

**Symptom:** `403 Forbidden` or `429 Too Many Requests`

**Solutions:**
- Increase `RATE_LIMIT_DELAY` in config
- Reduce concurrent requests
- Add random delays between requests
- Check if site requires authentication
- Consider using proxy rotation

#### 6. PDF Download Failures

**Symptom:** PDFs not downloading or errors

**Solutions:**
- Verify `PDF_SELECTORS` are correct
- Check if PDFs require authentication
- Increase `PDF_TIMEOUT` in config
- Check PDF URLs are valid (test in browser)
- Verify disk space available

### Getting Help

If issues persist:

1. **Review logs:** Check `{client}_scrapes/run_*/logs/`
2. **Test incrementally:** Test each phase separately
3. **Check documentation:** Review [configuration-guide.md](configuration-guide.md)
4. **Review examples:** Compare with Agar client configuration
5. **Contact support:** Provide error logs and configuration

---

## Best Practices

### Configuration Management

- **Version control:** Commit working configurations
- **Document changes:** Add comments for non-obvious settings
- **Test after changes:** Always test after modifying config
- **Backup before major changes:** Save working configurations

### Selector Design

- **Be specific:** Use unique classes/IDs when available
- **Test on multiple pages:** Ensure selectors work consistently
- **Avoid brittle selectors:** Don't rely on exact HTML structure
- **Use data attributes:** `[data-product]` often more stable
- **Document complex selectors:** Add comments explaining why

### Testing Strategy

- **Test early, test often:** Test after each configuration phase
- **Use test mode:** Always test before full production scrape
- **Test on different pages:** Category, product, edge cases
- **Monitor initial runs:** Watch first production scrape closely
- **Keep test data:** Save test outputs for comparison

### Performance Optimization

- **Start conservative:** Begin with longer delays/timeouts
- **Optimize incrementally:** Reduce only after testing
- **Monitor resource usage:** Watch memory, disk, network
- **Respect robots.txt:** Check website's crawling rules
- **Don't overwhelm servers:** Use appropriate rate limiting

### Data Quality

- **Validate output:** Review sample outputs regularly
- **Check for completeness:** Verify all expected fields present
- **Monitor for changes:** Websites change, selectors may break
- **Archive raw HTML:** Save page HTML for debugging
- **Document quirks:** Note any website-specific behaviors

---

## Next Steps

### After Successful Deployment

1. **Schedule regular scrapes:**
   - Set up cron job or scheduler
   - Monitor for failures
   - Handle website changes

2. **Optimize performance:**
   - Fine-tune timeouts and delays
   - Consider parallel processing
   - Implement caching strategies

3. **Enhance extraction:**
   - Add more data fields
   - Implement change detection
   - Add data validation rules

4. **Set up monitoring:**
   - Error notifications
   - Success/failure alerts
   - Data quality monitoring

5. **Document client-specific details:**
   - Update `config/clients/{clientname}/README.md`
   - Document any quirks or special handling
   - Record contact information and schedules

### Additional Features

Consider implementing:

- **Database integration:** Store data in PostgreSQL/MongoDB
- **API endpoints:** Expose scraped data via REST API
- **Change detection:** Track product changes over time
- **Data enrichment:** Add additional data sources
- **Advanced scheduling:** Time-based or event-based scraping
- **Cloud deployment:** Deploy to AWS/GCP/Azure
- **Containerization:** Docker deployment for consistency

---

## Appendix

### Quick Reference Commands

```bash
# Deployment
python scripts/deploy_new_client.py

# Validation
python scripts/validate_config.py --client CLIENTNAME

# Testing
python scripts/test_connection.py --client CLIENTNAME
python scripts/test_extraction.py --client CLIENTNAME --url "URL"

# Scraping
python main.py --client CLIENTNAME --test      # Test mode
python main.py --client CLIENTNAME             # Full scrape
```

### Configuration File Locations

```
config/clients/{clientname}/
├── client_config.py           # Main configuration
├── extraction_strategies.py   # CSS selectors
└── README.md                  # Client notes
```

### Output Directory Structure

```
{clientname}_scrapes/run_YYYYMMDD_HHMMSS/
├── categories/       # Category page data
├── products/        # Product detail data
├── pdfs/           # Downloaded documents
├── screenshots/    # Page screenshots
├── logs/          # Scraping logs
└── reports/       # Summary reports
```

### Support Resources

- **Configuration Guide:** [configuration-guide.md](configuration-guide.md)
- **Extraction Strategies:** [extraction-strategies.md](extraction-strategies.md)
- **Troubleshooting:** [troubleshooting.md](troubleshooting.md)
- **API Reference:** [api-reference.md](api-reference.md)
- **Architecture:** [architecture.md](architecture.md)

---

**Need Help?** Review the troubleshooting section or contact 3DN support.

**Found a Bug?** Report issues with detailed error logs and configuration.

**Have Suggestions?** We welcome feedback to improve the 3DN Scraper Template!

---

*3DN Scraper Template v1.0.0 - Professional Web Scraping Framework*
