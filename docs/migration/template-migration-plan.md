# 3DN Scraper Template Migration Plan

**Version:** 1.0  
**Date:** 2025-01-11  
**Purpose:** Transform the Agar scraper into the **3DN Scraper Template** - a reusable product for deploying client-specific scraping projects

---

## Executive Summary

This document outlines the complete process for creating the **3DN Scraper Template** from the existing Agar scraper. The 3DN Scraper Template will be a reusable product that can be rapidly deployed for different clients/organizations by providing client-specific configuration. Agar will serve as the first example client deployment of this template, demonstrating the configuration process for future client deployments.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Template Architecture](#template-architecture)
3. [Configuration Layers](#configuration-layers)
4. [Implementation Stages](#implementation-stages)
5. [User Configuration Guide](#user-configuration-guide)
6. [Migration Checklist](#migration-checklist)
7. [Testing Strategy](#testing-strategy)

---

## Current State Analysis

### Current Client-Specific Elements (Agar)

The current scraper has the following client-specific elements that need to be abstracted into the 3DN Template:

1. **Hardcoded Values in `config.py`:**
   - `BASE_URL = "https://agar.com.au"`
   - `BASE_OUTPUT_DIR = "agar_scrapes"`
   - `KNOWN_CATEGORIES` - list of Agar product categories
   - Company-specific naming in directory creation

2. **Extraction Strategies:**
   - CSS selectors in `product_scraper.py` are Agar-specific
   - PDF extraction logic assumes Agar's document structure
   - Product data schema assumes Agar's field names

3. **Business Logic:**
   - Category URL pattern: `/product-category/{slug}/`
   - Product URL patterns
   - SDS/PDS document naming conventions

4. **Output Naming:**
   - "AgarScrape_" prefix in directory names
   - File naming conventions

### 3DN Template Core Components

These components are client-agnostic and will form the core of the 3DN Scraper Template:

1. **Architecture:**
   - Modular structure (category → product collection → detail scraping → PDF download)
   - Run management system
   - Test mode functionality
   - Error handling and retry logic

2. **Infrastructure:**
   - Virtual environment setup
   - Crawl4AI integration
   - Async processing
   - JSON data handling
   - Screenshot capture
   - Reporting system

---

## 3DN Template Architecture

### Directory Structure

```
3DN-scraper-template/
├── README.md                       # 3DN Template documentation
├── SETUP_GUIDE.md                  # Client deployment guide
├── requirements.txt                # Python dependencies
├── .gitignore
├── .python-version
├── setup_venv.sh                   # Environment setup script
├── activate.sh
│
├── config/                         # Configuration layer
│   ├── __init__.py
│   ├── base_config.py             # 3DN Template defaults
│   ├── client_config.template.py  # Client deployment template
│   └── clients/                   # Client deployments
│       ├── __init__.py
│       ├── agar/                  # First client deployment (example)
│       │   ├── __init__.py
│       │   ├── client_config.py   # Agar deployment config
│       │   └── extraction_strategies.py
│       └── example_client/        # Starter template for new clients
│           ├── __init__.py
│           ├── client_config.py
│           └── extraction_strategies.py
│
├── core/                          # 3DN Template core (client-agnostic)
│   ├── __init__.py
│   ├── category_scraper.py        # Abstracted category discovery
│   ├── product_collector.py       # Abstracted product collection
│   ├── product_scraper.py         # Abstracted detail scraping
│   ├── product_pdf_scraper.py     # Abstracted PDF extraction
│   ├── pdf_downloader.py          # PDF download logic
│   ├── orchestrator.py            # Main workflow orchestrator
│   └── utils.py                   # Utility functions
│
├── strategies/                    # Extraction strategies
│   ├── __init__.py
│   ├── base_strategy.py          # Strategy interface
│   └── css_strategy.py           # CSS-based extraction
│
├── scripts/                       # Setup and utility scripts
│   ├── deploy_new_client.py      # Interactive client deployment
│   ├── validate_config.py        # Configuration validator
│   └── test_connection.py        # Test client website
│
├── docs/                          # Documentation
│   ├── architecture.md
│   ├── configuration-guide.md
│   ├── extraction-strategies.md
│   ├── troubleshooting.md
│   └── api-reference.md
│
└── main.py                        # Entry point with client selection
```

---

## Configuration Layers

### Layer 1: Base Configuration (3DN Template Defaults)

**File:** `config/base_config.py`

Defines all 3DN Template defaults that apply to any client deployment:

```python
"""
3DN Scraper Template - Base Configuration
DO NOT EDIT - Override in client-specific config files
"""

from pathlib import Path
from typing import Dict, List, Optional

class BaseConfig:
    """Base configuration class"""
    
    # 3DN Template Version
    TEMPLATE_VERSION = "1.0.0"
    TEMPLATE_NAME = "3DN Scraper Template"
    
    # Timeouts (can be overridden per client)
    PAGE_TIMEOUT = 60000  # 60 seconds
    DETAIL_PAGE_TIMEOUT = 35000  # 35 seconds
    RATE_LIMIT_DELAY = 2  # seconds between requests
    
    # Test mode defaults
    TEST_CATEGORY_LIMIT = 2
    TEST_PRODUCT_LIMIT = 5
    
    # User agent (generic)
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Directory structure
    SUBDIRS = ["categories", "products", "screenshots", "logs", "reports", "pdfs", "PDFs"]
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # Screenshot settings
    SCREENSHOT_WIDTH = 1920
    SCREENSHOT_HEIGHT = 1080
    
    # PDF download settings
    PDF_TIMEOUT = 30  # seconds
    PDF_MAX_RETRIES = 3
```

### Layer 2: Client Deployment Configuration

**File:** `config/clients/{client_name}/client_config.py`

Client-specific deployment configuration that overrides 3DN Template defaults:

```python
"""
3DN Scraper Template - Client Deployment Configuration
Client: [CLIENT_NAME]
"""

from config.base_config import BaseConfig
from typing import Dict, List

class ClientConfig(BaseConfig):
    """Client-specific configuration"""
    
    # Client identification
    CLIENT_NAME = "agar"
    CLIENT_FULL_NAME = "Agar Cleaning Systems"
    
    # Website configuration
    BASE_URL = "https://agar.com.au"
    
    # URL patterns
    CATEGORY_URL_PATTERN = "/product-category/{slug}/"
    PRODUCT_URL_PATTERN = "/product/{slug}/"
    
    # Output configuration
    OUTPUT_PREFIX = "AgarScrape"
    BASE_OUTPUT_DIR = "agar_scrapes"
    
    # Known categories (fallback)
    KNOWN_CATEGORIES = [
        "toilet-bathroom-cleaners",
        "green-cleaning-products",
        # ... etc
    ]
    
    # Client-specific timeouts (if needed)
    # PAGE_TIMEOUT = 90000  # Override if needed
    
    # PDF configuration
    HAS_SDS_DOCUMENTS = True
    HAS_PDS_DOCUMENTS = True
    SDS_FIELD_NAME = "sds_url"
    PDS_FIELD_NAME = "pds_url"
    
    # Product schema mapping
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

### Layer 3: Client Extraction Strategies

**File:** `config/clients/{client_name}/extraction_strategies.py`

CSS selectors and extraction logic specific to client's website:

```python
"""
3DN Scraper Template - Extraction Strategies
Client: [CLIENT_NAME]
"""

from typing import Dict, List
from strategies.base_strategy import ExtractionStrategy

class ClientExtractionStrategy(ExtractionStrategy):
    """Client-specific CSS selectors and extraction logic"""
    
    # Category page selectors
    CATEGORY_SELECTORS = {
        "products": "ul.products li.product",
        "product_link": "a.woocommerce-LoopProduct-link",
        "product_name": "h2.woocommerce-loop-product__title"
    }
    
    # Product detail page selectors
    PRODUCT_SELECTORS = {
        "name": "h1.product_title",
        "image": "div.woocommerce-product-gallery img",
        "overview": "div.product-overview",
        "description": "div.woocommerce-Tabs-panel--description",
        "sku": "span.sku",
        "categories": "span.posted_in a"
    }
    
    # PDF link selectors
    PDF_SELECTORS = {
        "sds_link": "a[href*='SDS']",
        "pds_link": "a[href*='PDS']",
        "document_section": "div.product-documents"
    }
    
    def extract_product_data(self, html: str) -> Dict:
        """Custom extraction logic if needed"""
        # Default CSS extraction
        # Override for complex extraction needs
        pass
```

---

## Implementation Stages

### Stage 1: 3DN Template Foundation (Days 1-2)

**Objective:** Create the 3DN Scraper Template structure and refactor existing code

#### Tasks:

1. **Create 3DN Template Directory Structure**
   - Set up `config/`, `core/`, `strategies/`, `scripts/`, `docs/` directories
   - Create `__init__.py` files for Python packages
   - Add 3DN branding to README and documentation

2. **Refactor Configuration System**
   - Create `base_config.py` with 3DN Template defaults
   - Create `client_config.template.py` as deployment starter
   - Move Agar configuration to `config/clients/agar/client_config.py` (first example deployment)
   - Create configuration loader that selects active client deployment

3. **Abstract Core Modules**
   - Refactor `category_scraper.py` to use client deployment config
   - Refactor `product_scraper.py` to use client extraction strategies
   - Update all modules to be deployment-agnostic
   - Remove all client-specific hardcoded values

4. **Create Extraction Strategy System**
   - Define `BaseStrategy` interface for client deployments
   - Implement `CSSExtractionStrategy` as default
   - Move Agar selectors to `extraction_strategies.py` as example

#### Deliverables:
- [ ] Complete 3DN Template directory structure
- [ ] Client-agnostic core modules
- [ ] Agar migrated as first client deployment example
- [ ] Working 3DN Template with deployment system

---

### Stage 2: Client Deployment Automation (Days 3-4)

**Objective:** Create tools and scripts for easy client deployment of 3DN Template

#### Tasks:

1. **Create Client Deployment Script**
   - Interactive `deploy_new_client.py` script
   - Prompts for client organization information
   - Generates client deployment directory structure
   - Creates starter extraction strategy file from template
   - Sets up client-specific output directories

2. **Configuration Validation**
   - `validate_config.py` script for deployment validation
   - Checks for required deployment configuration fields
   - Validates URL patterns and client settings
   - Tests client website connectivity
   - Verifies extraction selectors work on client site

3. **Testing Utilities**
   - `test_connection.py` - test client website access
   - Test mode for quick deployment validation
   - Sample data extraction test for client site

4. **Environment Setup**
   - Update `setup_venv.sh` for 3DN Template
   - Update `requirements.txt`
   - Create `.env.template` for deployment secrets

#### Deliverables:
- [ ] Interactive client deployment script
- [ ] Deployment validation tools
- [ ] Client testing utilities
- [ ] Updated setup scripts with 3DN branding

---

### Stage 3: Documentation (Days 5-6)

**Objective:** Create comprehensive 3DN Template documentation

#### Tasks:

1. **Client Deployment Documentation**
   - `CLIENT_DEPLOYMENT_GUIDE.md` - step-by-step guide for deploying to new clients
   - `configuration-guide.md` - detailed deployment config reference
   - `extraction-strategies.md` - how to create client-specific strategies
   - `troubleshooting.md` - common deployment issues and solutions

2. **Developer Documentation**
   - `architecture.md` - 3DN Template architecture
   - `api-reference.md` - core module API reference
   - Code comments and docstrings with 3DN branding
   - Example client deployment implementations

3. **3DN Template README**
   - Overview of 3DN Scraper Template capabilities
   - Quick start guide for deploying to first client
   - Feature list
   - Client deployment examples (Agar as primary example)

#### Deliverables:
- [ ] Complete client deployment documentation
- [ ] Developer documentation with 3DN branding
- [ ] Updated README files
- [ ] Code documentation

---

### Stage 4: Testing & Validation (Days 7-8)

**Objective:** Ensure 3DN Template works for multiple client deployments

#### Tasks:

1. **Create Second Client Deployment**
   - Deploy 3DN Template for second example client
   - Use a public e-commerce site
   - Document the deployment process
   - Validate client-specific extraction strategies

2. **Test Agar Deployment**
   - Verify Agar works as first client deployment
   - Run full scrape test on Agar deployment
   - Compare output with original scraper
   - Performance testing

3. **3DN Template Testing**
   - Test deployment script with new client
   - Validate configuration system across deployments
   - Test all core modules are client-agnostic
   - Error handling validation

4. **Documentation Review**
   - Test deployment guide with fresh 3DN Template install
   - Review all documentation for 3DN branding consistency
   - Fix any issues or gaps

#### Deliverables:
- [ ] Working second client deployment (not Agar)
- [ ] Validated Agar as first deployment example
- [ ] Complete test suite for 3DN Template
- [ ] Refined documentation with 3DN branding

---

## Client Deployment Guide

### When Users Configure What

This section defines the configuration timeline for deploying the 3DN Scraper Template to a new client organization.

#### Phase 1: Initial Setup (Before Starting)

**What:** Basic client information and website details

**Configuration File:** `config/clients/{client_name}/client_config.py`

**Required Settings:**
```python
CLIENT_NAME = "clientname"           # Short identifier
CLIENT_FULL_NAME = "Client Company"  # Full name
BASE_URL = "https://client.com"      # Website URL
OUTPUT_PREFIX = "ClientScrape"       # Output directory prefix
BASE_OUTPUT_DIR = "client_scrapes"   # Base output directory
```

**How to Deploy:**
1. Run `python scripts/deploy_new_client.py`
2. Answer interactive prompts:
   - Client/organization short name (lowercase, no spaces)
   - Client/organization full name
   - Client website URL
   - Output directory preferences
3. Script creates initial deployment configuration

**Validation:**
```bash
python scripts/validate_config.py --client clientname
python scripts/test_connection.py --client clientname
```

---

#### Phase 2: URL Pattern Discovery (After Initial Setup)

**What:** Understanding the client's URL structure

**Configuration File:** `config/clients/{client_name}/client_config.py`

**Required Settings:**
```python
CATEGORY_URL_PATTERN = "/category/{slug}/"  # How categories are accessed
PRODUCT_URL_PATTERN = "/product/{slug}/"     # How products are accessed
```

**How to Configure:**
1. Manually browse the client website
2. Identify category page URL patterns
3. Identify product page URL patterns
4. Document any variations
5. Update configuration file

**Testing:**
```bash
python main.py --client clientname --test  # Test the deployment
```

---

#### Phase 3: Extraction Strategy (Iterative Process)

**What:** CSS selectors for extracting data from pages

**Configuration File:** `config/clients/{client_name}/extraction_strategies.py`

**Required Selectors:**

```python
# Category page selectors
CATEGORY_SELECTORS = {
    "products": "CSS selector for product list",
    "product_link": "CSS selector for product URLs",
    "product_name": "CSS selector for product names",
    "pagination": "CSS selector for next page (optional)"
}

# Product detail page selectors
PRODUCT_SELECTORS = {
    "name": "CSS selector for product name",
    "image": "CSS selector for main image",
    "description": "CSS selector for description",
    "sku": "CSS selector for SKU (optional)",
    "categories": "CSS selector for categories (optional)",
    "price": "CSS selector for price (optional)"
}

# PDF/Document selectors (if applicable)
PDF_SELECTORS = {
    "sds_link": "CSS selector for SDS document",
    "pds_link": "CSS selector for PDS document",
    "document_section": "CSS selector for document area"
}
```

**How to Configure for Client:**
1. Open sample category page from client website in browser
2. Use browser dev tools (F12) to inspect elements
3. Identify unique CSS selectors for each element on client site
4. Test selectors in browser console:
   ```javascript
   document.querySelector("your-selector")
   ```
5. Add selectors to client's extraction strategy file
6. Test extraction on client site:
   ```bash
   python scripts/test_extraction.py --client clientname --url "sample-url"
   ```
7. Iterate until all required fields are extracted correctly from client site

**Best Practices:**
- Use specific selectors (class names, IDs)
- Avoid overly generic selectors (div, span alone)
- Test on multiple product pages
- Handle missing fields gracefully

---

#### Phase 4: Data Schema Mapping (After Extraction Works)

**What:** Mapping extracted data to output format

**Configuration File:** `config/clients/{client_name}/client_config.py`

**Required Settings:**
```python
PRODUCT_SCHEMA = {
    "name_field": "product_name",
    "url_field": "product_url",
    "image_field": "product_image_url",
    "description_field": "product_description",
    "sku_field": "product_sku",
    "categories_field": "product_categories",
    "price_field": "product_price"  # Optional
}

# PDF/Document configuration
HAS_SDS_DOCUMENTS = True/False
HAS_PDS_DOCUMENTS = True/False
SDS_FIELD_NAME = "sds_url"
PDS_FIELD_NAME = "pds_url"
```

**How to Configure:**
1. Review sample extracted data
2. Map extracted fields to output schema
3. Decide which fields are required vs optional
4. Configure PDF/document handling if applicable
5. Test complete workflow:
   ```bash
   python main.py --client clientname --test
   ```

---

#### Phase 5: Category Discovery (Optional Enhancement)

**What:** Automatic category discovery vs manual list

**Configuration File:** `config/clients/{client_name}/client_config.py`

**Options:**

**Option A: Manual Category List (Simpler)**
```python
KNOWN_CATEGORIES = [
    "category-slug-1",
    "category-slug-2",
    "category-slug-3"
]
```

**Option B: Auto-Discovery (Advanced)**
```python
CATEGORY_DISCOVERY_ENABLED = True
CATEGORY_NAV_SELECTOR = "nav.product-categories li a"
CATEGORY_EXTRACT_SLUG_FROM_URL = True
```

**How to Configure:**
1. Start with manual list for simplicity
2. Test with known categories
3. If auto-discovery needed, add navigation selectors
4. Test discovery:
   ```bash
   python core/category_scraper.py --client clientname
   ```

---

#### Phase 6: Performance Tuning (After Basic Functionality Works)

**What:** Optimizing timeouts, delays, and limits

**Configuration File:** `config/clients/{client_name}/client_config.py`

**Optional Overrides:**
```python
# Timeout configuration (if defaults don't work)
PAGE_TIMEOUT = 90000  # Increase if pages load slowly
DETAIL_PAGE_TIMEOUT = 45000
RATE_LIMIT_DELAY = 3  # Increase if getting blocked

# Test mode limits (for faster testing)
TEST_CATEGORY_LIMIT = 3
TEST_PRODUCT_LIMIT = 10

# Retry configuration
MAX_RETRIES = 5  # Increase for unreliable connections
RETRY_DELAY = 10
```

**How to Configure:**
1. Run initial scrapes in test mode
2. Monitor for timeouts or errors
3. Adjust timeouts if needed
4. Test rate limiting if getting blocked
5. Fine-tune for optimal performance

---

### Deployment Checklist for New Client

Use this checklist when deploying 3DN Scraper Template to a new client:

- [ ] **Phase 1: Initial Deployment**
  - [ ] Run `deploy_new_client.py` script
  - [ ] Verify client deployment configuration created
  - [ ] Test client website connection
  - [ ] Validate deployment configuration

- [ ] **Phase 2: URL Patterns**
  - [ ] Document category URL pattern
  - [ ] Document product URL pattern
  - [ ] Add to configuration
  - [ ] Test URL generation

- [ ] **Phase 3: Extraction Strategy**
  - [ ] Identify category page selectors
  - [ ] Identify product page selectors
  - [ ] Test selectors in browser
  - [ ] Add to extraction strategy file
  - [ ] Test extraction with sample URLs
  - [ ] Iterate until all required fields extracted

- [ ] **Phase 4: Data Schema**
  - [ ] Map extracted fields to schema
  - [ ] Configure PDF/document handling
  - [ ] Test complete workflow in test mode
  - [ ] Verify output format

- [ ] **Phase 5: Category Discovery**
  - [ ] Create initial category list
  - [ ] Test category scraping
  - [ ] (Optional) Implement auto-discovery

- [ ] **Phase 6: Performance Tuning**
  - [ ] Run test mode scrapes
  - [ ] Monitor for errors or timeouts
  - [ ] Adjust configuration as needed
  - [ ] Run full scrape test

- [ ] **Final Validation**
  - [ ] Full scrape in test mode
  - [ ] Review output data quality
  - [ ] Check all expected fields present
  - [ ] Verify PDFs downloaded (if applicable)
  - [ ] Run full production scrape

---

## Migration Checklist

### Pre-Migration Preparation

- [ ] Backup current Agar scraper directory
- [ ] Document current Agar functionality
- [ ] Create test dataset from current Agar scraper
- [ ] Set up git repository for 3DN Template

### 3DN Template Creation

- [ ] Create 3DN Template directory structure with branding
- [ ] Create base configuration system for 3DN Template
- [ ] Create client deployment configuration template
- [ ] Implement deployment configuration loader
- [ ] Refactor core modules to be deployment-agnostic

### Code Migration

- [ ] Move Agar config to clients/agar deployment directory
- [ ] Update all client-specific hardcoded references
- [ ] Create Agar extraction strategy as first deployment example
- [ ] Test Agar as first client deployment
- [ ] Verify Agar deployment output matches original

### Deployment Tooling Development

- [ ] Create `deploy_new_client.py` script for 3DN Template deployments
- [ ] Create `validate_config.py` script for deployment validation
- [ ] Create `test_connection.py` script for client sites
- [ ] Create `test_extraction.py` script for client deployments
- [ ] Update `main.py` with client deployment selection

### Documentation

- [ ] Write CLIENT_DEPLOYMENT_GUIDE.md
- [ ] Write configuration-guide.md for deployments
- [ ] Write extraction-strategies.md for client deployments
- [ ] Write troubleshooting.md for deployment issues
- [ ] Update README.md with 3DN Template branding
- [ ] Add code documentation with 3DN branding

### Testing

- [ ] Create second example client deployment (not Agar)
- [ ] Test deployment script workflow
- [ ] Validate deployment configuration system
- [ ] Test all core modules are client-agnostic
- [ ] Performance testing across deployments
- [ ] Error handling validation

### Finalization

- [ ] Review all documentation for 3DN branding consistency
- [ ] Clean up code and add 3DN header comments
- [ ] Remove debug code
- [ ] Optimize performance across deployments
- [ ] Create 3DN Template release notes
- [ ] Tag 3DN Template version 1.0

---

## Testing Strategy

### Unit Testing

**Core Module Tests:**
- Configuration loading
- URL pattern generation
- Data extraction
- PDF handling
- Error handling

**Test Files:**
```
tests/
├── test_config_loader.py
├── test_extraction_strategies.py
├── test_core_modules.py
└── test_utilities.py
```

### Integration Testing

**Full Workflow Tests:**
- Category discovery → Product collection → Detail scraping
- PDF extraction and download
- Output generation
- Error recovery

### Client Testing

**Per-Client Validation:**
1. Test mode scrape (limited data)
2. Extraction accuracy validation
3. Output format verification
4. Performance benchmarking
5. Full scrape test

### Setup Testing

**New Client Setup:**
1. Fresh installation
2. Run setup script
3. Follow SETUP_GUIDE.md
4. Complete configuration
5. Run test scrape
6. Validate results

---

## Appendix: Example Client Deployments

### Example 1: Agar (First Deployment)

**Client:** "Agar Cleaning Systems"  
**URL:** `https://agar.com.au`  
**Products:** Industrial cleaning products with SDS/PDS documents

```python
# config/clients/agar/client_config.py
class ClientConfig(BaseConfig):
    CLIENT_NAME = "agar"
    CLIENT_FULL_NAME = "Agar Cleaning Systems"
    BASE_URL = "https://agar.com.au"
    
    CATEGORY_URL_PATTERN = "/product-category/{slug}/"
    PRODUCT_URL_PATTERN = "/product/{slug}/"
    
    OUTPUT_PREFIX = "AgarScrape"
    BASE_OUTPUT_DIR = "agar_scrapes"
    
    HAS_SDS_DOCUMENTS = True
    HAS_PDS_DOCUMENTS = True
    
    KNOWN_CATEGORIES = [
        "toilet-bathroom-cleaners",
        "green-cleaning-products",
        # ... etc
    ]
```

### Example 2: Simple E-Commerce Site

**Client:** "Example Shop"  
**URL:** `https://example-shop.com`  
**Products:** Basic product catalog with images and descriptions

```python
# client_config.py
class ClientConfig(BaseConfig):
    CLIENT_NAME = "exampleshop"
    CLIENT_FULL_NAME = "Example Shop"
    BASE_URL = "https://example-shop.com"
    
    CATEGORY_URL_PATTERN = "/category/{slug}"
    PRODUCT_URL_PATTERN = "/product/{slug}"
    
    OUTPUT_PREFIX = "ExampleShopScrape"
    BASE_OUTPUT_DIR = "exampleshop_scrapes"
    
    HAS_SDS_DOCUMENTS = False
    HAS_PDS_DOCUMENTS = False
    
    PRODUCT_SCHEMA = {
        "name_field": "product_name",
        "url_field": "product_url",
        "image_field": "product_image",
        "description_field": "description",
        "price_field": "price"
    }
```

### Example 3: Industrial Products (Similar to Agar)

**Client:** "Industrial Supplies Co"  
**URL:** `https://industrial-supplies.com`  
**Products:** Technical products with SDS/PDS documents

```python
# client_config.py
class ClientConfig(BaseConfig):
    CLIENT_NAME = "industrialsupplies"
    CLIENT_FULL_NAME = "Industrial Supplies Co"
    BASE_URL = "https://industrial-supplies.com"
    
    CATEGORY_URL_PATTERN = "/products/{slug}/"
    PRODUCT_URL_PATTERN = "/product-detail/{slug}/"
    
    OUTPUT_PREFIX = "IndustrialScrape"
    BASE_OUTPUT_DIR = "industrial_scrapes"
    
    HAS_SDS_DOCUMENTS = True
    HAS_PDS_DOCUMENTS = True
    SDS_FIELD_NAME = "safety_datasheet"
    PDS_FIELD_NAME = "product_datasheet"
    
    PRODUCT_SCHEMA = {
        "name_field": "product_name",
        "url_field": "product_url",
        "image_field": "image_url",
        "description_field": "full_description",
        "sku_field": "sku_number",
        "categories_field": "categories"
    }
    
    # Longer timeouts for document-heavy pages
    PAGE_TIMEOUT = 90000
    DETAIL_PAGE_TIMEOUT = 60000
```

---

## Success Criteria

### 3DN Template Completion

- [ ] Agar scraper fully migrated to 3DN Template as first deployment
- [ ] New client can be deployed in < 2 hours using 3DN Template
- [ ] Deployment configuration is straightforward and well-documented
- [ ] All core functionality preserved and client-agnostic
- [ ] Performance maintained or improved across deployments
- [ ] Comprehensive 3DN-branded documentation
- [ ] Working second client deployment (validates template reusability)

### Quality Metrics

- [ ] All modules have docstrings with 3DN branding
- [ ] Deployment configuration validation catches common errors
- [ ] Client deployment guide is clear and complete
- [ ] Test mode works for quick deployment validation
- [ ] Error messages are helpful and reference 3DN Template
- [ ] Code is maintainable and extensible for new client deployments

---

## Next Steps After 3DN Template Creation

1. **Deploy to Second Client:** Validate 3DN Template with real second client deployment
2. **Gather Feedback:** Improve 3DN Template based on actual deployment usage
3. **Add Features:** Consider additional 3DN Template capabilities like:
   - API integration
   - Database storage
   - Change detection
   - Scheduling
   - Notifications
4. **Optimize:** Performance improvements based on deployment patterns
5. **Expand:** Support for different types of client sites (non-e-commerce)
6. **Market:** Promote 3DN Scraper Template to potential clients

---

## Questions to Consider During Implementation

1. **Configuration Management:**
   - Should we support environment variables?
   - Do we need a configuration GUI?
   - How to handle sensitive data (API keys, credentials)?

2. **Extraction Strategies:**
   - Support for JavaScript-heavy sites?
   - Support for API-based extraction?
   - Support for authentication?

3. **Data Storage:**
   - JSON only or database option?
   - Data versioning/change tracking?
   - Data export formats?

4. **Deployment:**
   - Docker containerization?
   - Cloud deployment options?
   - Scheduling integration?

---

## Conclusion

This plan provides a comprehensive roadmap for creating the **3DN Scraper Template** from the existing Agar scraper. The staged approach ensures that each phase builds on the previous one, with clear deliverables and testing at each stage.

The 3DN Scraper Template will be a reusable product that can be deployed to different client organizations by providing client-specific configuration (URL, schema, selectors, etc.) without modifying the core template code.

The key to success is maintaining the proven Agar scraper architecture while making it deployment-agnostic and flexible enough to handle different client requirements without becoming overly complex.

**Estimated Timeline:** 8-10 days for complete 3DN Template implementation and validation

**Priority:** Focus on Stages 1-2 first (template foundation and deployment automation) before extensive documentation and testing.

**Result:** A professional 3DN-branded scraping template that can be deployed to new clients in under 2 hours.
