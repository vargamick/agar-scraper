# 3DN Scraper Template - Architecture Guide

**Version:** 1.0  
**Last Updated:** 2025-01-11  
**Template Version:** 1.0.0

---

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [System Architecture](#system-architecture)
4. [Core Components](#core-components)
5. [Configuration System](#configuration-system)
6. [Extraction Strategy Pattern](#extraction-strategy-pattern)
7. [Data Flow](#data-flow)
8. [Directory Structure](#directory-structure)
9. [Extensibility](#extensibility)

---

## Overview

The 3DN Scraper Template is a professional web scraping framework designed for rapid deployment across multiple client organizations. It follows a modular, client-agnostic architecture that separates core scraping logic from client-specific configuration.

### Key Characteristics

- **Client-Agnostic Core:** Core modules work across all client deployments
- **Configuration-Driven:** Client specifics defined in configuration, not code
- **Strategy Pattern:** Extraction logic isolated in pluggable strategies
- **Modular Design:** Independent, testable components
- **Extensible:** Easy to add new features and capabilities

### Architecture Goals

1. **Reusability:** Deploy to new clients in < 1 hour
2. **Maintainability:** Clear separation of concerns
3. **Testability:** Each component independently testable
4. **Scalability:** Handle sites from 100 to 10,000+ products
5. **Reliability:** Robust error handling and retry logic

---

## Design Principles

### 1. Separation of Concerns

```
Template Core (unchanging)
    ↓
Client Configuration (per-client)
    ↓
Extraction Strategy (per-client)
```

**Benefits:**
- Changes to core don't affect clients
- Client updates don't affect core
- Clear boundaries between components

### 2. Convention over Configuration

**Default behavior works out of the box:**
- Standard timeouts and retry logic
- Common URL patterns
- Typical directory structures

**Override only what's needed:**
- Client-specific timeouts
- Unique URL patterns
- Custom extraction logic

### 3. Strategy Pattern

**Extraction strategies are pluggable:**
```python
BaseStrategy (interface)
    ↓
ClientStrategy (implementation)
    ↓
Scraper Modules (use strategy)
```

**Benefits:**
- Easy to add new extraction methods
- Can swap strategies without code changes
- Testable in isolation

### 4. Configuration Layers

**Layered configuration system:**
```
Environment Variables (highest priority)
    ↓
Client Configuration
    ↓
Base Configuration (lowest priority)
```

**Benefits:**
- Environment-specific overrides
- Client-specific customization
- Sensible defaults

### 5. Fail-Safe Design

**Built-in reliability:**
- Automatic retries on failure
- Graceful degradation
- Detailed error logging
- Transaction-like run management

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     3DN Scraper Template                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Scripts    │  │     Core     │  │  Strategies  │      │
│  │              │  │              │  │              │      │
│  │ - Deploy     │  │ - Category   │  │ - Base       │      │
│  │ - Validate   │  │ - Product    │  │ - Client     │      │
│  │ - Test       │  │ - PDF        │  │   Specific   │      │
│  │   Tools      │  │ - Utils      │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Configuration System                      │    │
│  │                                                       │    │
│  │  Base Config ← Client Config ← Environment Vars     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Client Deployments                      │    │
│  │                                                       │    │
│  │  agar/  cleaningco/  chemco/  [new clients...]      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
main.py
  ↓
ConfigLoader → Loads client configuration
  ↓
CategoryScraper → Discovers product categories
  ↓                Uses ExtractionStrategy
ProductCollector → Collects product URLs
  ↓                Uses ExtractionStrategy
ProductScraper → Scrapes product details
  ↓              Uses ExtractionStrategy
PDFScraper → Extracts PDF links (optional)
  ↓          Uses ExtractionStrategy
PDFDownloader → Downloads PDFs
  ↓
Output Generator → Saves JSON, generates reports
```

---

## Core Components

### 1. Configuration Loader (`config/config_loader.py`)

**Purpose:** Dynamically load and merge configurations

**Key Functions:**
- `load_client_config(client_name)` - Load client configuration
- `validate_config(config)` - Validate configuration completeness
- `merge_configs(base, client, env)` - Merge configuration layers

**Example:**
```python
from config.config_loader import load_client_config

# Load configuration for client
config = load_client_config("agar")

# Access settings
print(config.BASE_URL)
print(config.CATEGORY_URL_PATTERN)
```

### 2. Category Scraper (`core/category_scraper.py`)

**Purpose:** Discover and scrape product category pages

**Responsibilities:**
- Build category URLs from configuration
- Fetch category pages
- Extract product URLs using extraction strategy
- Handle pagination (if needed)

**Key Methods:**
- `scrape_category(category_slug)` - Scrape single category
- `scrape_all_categories()` - Scrape all configured categories
- `extract_products(html)` - Extract product list from HTML

**Example:**
```python
from core.category_scraper import CategoryScraper

scraper = CategoryScraper(config, strategy)
products = scraper.scrape_category("cleaners")
# Returns: [{"url": "...", "name": "..."}, ...]
```

### 3. Product Collector (`core/product_collector.py`)

**Purpose:** Collect all product URLs across categories

**Responsibilities:**
- Coordinate category scraping
- Deduplicate product URLs
- Track progress
- Handle errors

**Key Methods:**
- `collect_all_products()` - Collect from all categories
- `deduplicate_urls(products)` - Remove duplicate products

### 4. Product Scraper (`core/product_scraper.py`)

**Purpose:** Scrape detailed product information

**Responsibilities:**
- Fetch product pages
- Extract product data using strategy
- Map to output schema
- Handle missing fields

**Key Methods:**
- `scrape_product(url)` - Scrape single product
- `scrape_products(urls)` - Scrape multiple products
- `extract_data(html)` - Extract product data

**Example:**
```python
from core.product_scraper import ProductScraper

scraper = ProductScraper(config, strategy)
product = scraper.scrape_product("https://site.com/product/abc")
# Returns: {"name": "...", "description": "...", ...}
```

### 5. PDF Scraper (`core/product_pdf_scraper.py`)

**Purpose:** Extract PDF document links from product pages

**Responsibilities:**
- Find SDS/PDS document links
- Validate PDF URLs
- Track found documents

**Key Methods:**
- `extract_pdf_links(html)` - Extract PDF URLs
- `validate_pdf_url(url)` - Check if URL is valid

### 6. PDF Downloader (`core/pdf_downloader.py`)

**Purpose:** Download PDF documents

**Responsibilities:**
- Download PDFs with retry logic
- Validate downloads
- Track download success/failure

**Key Methods:**
- `download_pdf(url, output_path)` - Download single PDF
- `download_batch(pdf_list)` - Download multiple PDFs

### 7. Utils (`core/utils.py`)

**Purpose:** Shared utility functions

**Provides:**
- Run directory management
- File I/O helpers
- JSON serialization
- Logging setup
- Error handling utilities

---

## Configuration System

### Configuration Hierarchy

```
┌──────────────────────────────────────┐
│   Environment Variables (.env)       │  Priority: 1 (Highest)
│   - Secrets (API keys)               │
│   - Deployment settings              │
└──────────────────────────────────────┘
              ↓ overrides
┌──────────────────────────────────────┐
│   Client Configuration               │  Priority: 2
│   - CLIENT_NAME, BASE_URL            │
│   - URL patterns                     │
│   - Client-specific overrides        │
└──────────────────────────────────────┘
              ↓ inherits from
┌──────────────────────────────────────┐
│   Base Configuration                 │  Priority: 3 (Lowest)
│   - Template defaults                │
│   - Common settings                  │
│   - Standard behaviors               │
└──────────────────────────────────────┘
```

### Configuration Loading Process

```python
# 1. Load base configuration
base_config = BaseConfig()

# 2. Load client configuration (inherits from base)
client_config = ClientConfig()  # Inherits BaseConfig

# 3. Apply environment overrides
for key, value in os.environ.items():
    if hasattr(client_config, key):
        setattr(client_config, key, value)

# 4. Validate configuration
validate_config(client_config)

# 5. Return merged configuration
return client_config
```

### Configuration Files

```
config/
├── base_config.py              # BaseConfig class
├── config_loader.py            # Loading logic
├── client_config.template.py   # Template for new clients
└── clients/
    └── {client_name}/
        ├── client_config.py    # ClientConfig class
        └── extraction_strategies.py  # Strategy implementation
```

---

## Extraction Strategy Pattern

### Strategy Interface

```python
# strategies/base_strategy.py
class ExtractionStrategy(ABC):
    """Base extraction strategy interface"""
    
    # Selector dictionaries (to be overridden)
    CATEGORY_SELECTORS = {}
    PRODUCT_SELECTORS = {}
    PDF_SELECTORS = {}
    
    @abstractmethod
    def extract_category_products(self, html: str) -> List[Dict]:
        """Extract products from category page"""
        pass
    
    @abstractmethod
    def extract_product_data(self, html: str) -> Dict:
        """Extract data from product page"""
        pass
    
    @abstractmethod
    def extract_pdf_links(self, html: str) -> Dict:
        """Extract PDF document links"""
        pass
```

### Client Strategy Implementation

```python
# config/clients/agar/extraction_strategies.py
class AgarExtractionStrategy(ExtractionStrategy):
    """Agar-specific extraction strategy"""
    
    CATEGORY_SELECTORS = {
        "products": "ul.products li.product",
        "product_link": "a.woocommerce-LoopProduct-link",
        "product_name": "h2.woocommerce-loop-product__title"
    }
    
    PRODUCT_SELECTORS = {
        "name": "h1.product_title",
        "image": "div.woocommerce-product-gallery img",
        "description": "div.woocommerce-Tabs-panel--description",
        # ... more selectors
    }
    
    # Can override methods for custom extraction
    def extract_product_data(self, html: str) -> Dict:
        # Custom extraction logic if needed
        pass
```

### Strategy Usage in Core Modules

```python
# core/product_scraper.py
class ProductScraper:
    def __init__(self, config, strategy):
        self.config = config
        self.strategy = strategy  # Injection
    
    def extract_data(self, html):
        # Use injected strategy
        return self.strategy.extract_product_data(html)
```

**Benefits:**
- Core modules don't know about specific selectors
- Easy to swap strategies
- Can test with mock strategies
- Strategies reusable across clients

---

## Data Flow

### Complete Scraping Workflow

```
1. Initialize
   ↓
   - Load configuration
   - Load extraction strategy
   - Create run directory
   - Setup logging

2. Category Discovery
   ↓
   - Build category URLs
   - Fetch category pages
   - Extract product URLs
   - Save category data

3. Product Collection
   ↓
   - Deduplicate URLs
   - Apply test limits (if test mode)
   - Queue products for scraping

4. Product Scraping
   ↓
   - Fetch product page
   - Extract product data
   - Map to schema
   - Save product JSON

5. PDF Processing (if enabled)
   ↓
   - Extract PDF links
   - Download PDFs
   - Save to pdfs/ directory

6. Finalization
   ↓
   - Generate reports
   - Save summary statistics
   - Close logging
```

### Data Transformation Pipeline

```
Raw HTML
  ↓ (ExtractionStrategy)
Extracted Data (raw structure)
  ↓ (SchemaMapper)
Mapped Data (output schema)
  ↓ (Serializer)
JSON Output
```

---

## Directory Structure

### Template Structure

```
3dn-scraper-template/
├── config/                    # Configuration system
│   ├── base_config.py         # Template defaults
│   ├── config_loader.py       # Config loading logic
│   ├── client_config.template.py  # Deployment template
│   └── clients/               # Client deployments
│       ├── agar/              # Example client
│       │   ├── client_config.py
│       │   └── extraction_strategies.py
│       └── [new_clients]/     # Additional clients
│
├── core/                      # Core modules (client-agnostic)
│   ├── category_scraper.py    # Category scraping
│   ├── product_collector.py   # Product collection
│   ├── product_scraper.py     # Product scraping
│   ├── product_pdf_scraper.py # PDF extraction
│   ├── pdf_downloader.py      # PDF downloading
│   └── utils.py               # Shared utilities
│
├── strategies/                # Strategy pattern
│   ├── base_strategy.py       # Strategy interface
│   └── [custom_strategies]/   # Custom implementations
│
├── scripts/                   # Automation tools
│   ├── deploy_new_client.py   # Client deployment
│   ├── validate_config.py     # Configuration validation
│   ├── test_connection.py     # Connection testing
│   └── test_extraction.py     # Extraction testing
│
├── docs/                      # Documentation
│   ├── CLIENT_DEPLOYMENT_GUIDE.md
│   ├── configuration-guide.md
│   ├── extraction-strategies.md
│   ├── troubleshooting.md
│   ├── architecture.md (this file)
│   └── api-reference.md
│
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── .env.template              # Environment template
└── README.md                  # Project overview
```

### Output Structure

```
{client}_scrapes/
└── run_YYYYMMDD_HHMMSS/       # Timestamped run
    ├── categories/            # Category page data
    │   └── {category}.json
    ├── products/              # Product detail data
    │   └── {product}.json
    ├── pdfs/                  # Downloaded PDFs
    │   ├── {product}_SDS.pdf
    │   └── {product}_PDS.pdf
    ├── screenshots/           # Page screenshots
    ├── logs/                  # Scraping logs
    │   ├── scraper.log
    │   ├── errors.log
    │   └── debug.log
    └── reports/               # Summary reports
        └── summary.json
```

---

## Extensibility

### Adding New Features

#### 1. Add New Field to Products

**Configuration:**
```python
# client_config.py
PRODUCT_SCHEMA = {
    # Existing fields
    "name_field": "product_name",
    "price_field": "product_price",  # New field
}
```

**Extraction Strategy:**
```python
# extraction_strategies.py
PRODUCT_SELECTORS = {
    # Existing selectors
    "name": "h1.title",
    "price": "span.price",  # New selector
}
```

#### 2. Add Custom Extraction Logic

**Override strategy method:**
```python
class ClientStrategy(ExtractionStrategy):
    def extract_product_data(self, html: str) -> Dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Custom extraction
        data = {
            "custom_field": self._extract_custom(soup)
        }
        
        return data
```

#### 3. Add New Scraper Module

**Create new module:**
```python
# core/reviews_scraper.py
class ReviewsScraper:
    def __init__(self, config, strategy):
        self.config = config
        self.strategy = strategy
    
    def scrape_reviews(self, product_url):
        # Implementation
        pass
```

**Integrate into workflow:**
```python
# main.py
# After product scraping
if config.SCRAPE_REVIEWS:
    reviews_scraper = ReviewsScraper(config, strategy)
    reviews = reviews_scraper.scrape_reviews(product_url)
```

#### 4. Add New Output Format

**Create exporter:**
```python
# core/exporters.py
class CSVExporter:
    def export(self, products, output_path):
        # Convert products to CSV
        pass
```

### Extension Points

1. **Custom Strategies:** Create strategy subclasses
2. **Custom Scrapers:** Add new scraper modules
3. **Custom Processors:** Add data transformation pipelines
4. **Custom Exporters:** Add output format handlers
5. **Custom Validators:** Add validation rules

---

## Best Practices

### 1. Keep Core Client-Agnostic

**Do:**
```python
# Core module using configuration
def build_url(self, slug):
    return f"{self.config.BASE_URL}{self.config.CATEGORY_URL_PATTERN.format(slug=slug)}"
```

**Don't:**
```python
# Hardcoded client-specific logic
def build_url(self, slug):
    if self.client == "agar":
        return f"https://agar.com.au/product-category/{slug}/"
```

### 2. Use Strategy Pattern

**Do:**
```python
# Use injected strategy
data = self.strategy.extract_product_data(html)
```

**Don't:**
```python
# Import client-specific code
from config.clients.agar.extraction import extract_data
data = extract_data(html)
```

### 3. Configuration Over Code

**Do:**
```python
# Configuration-driven
timeout = self.config.PAGE_TIMEOUT
```

**Don't:**
```python
# Hardcoded values
timeout = 60000
```

### 4. Fail Gracefully

**Do:**
```python
try:
    data = extract_field(html)
except ExtractionError:
    logger.warning("Field extraction failed")
    data = None  # Continue with partial data
```

**Don't:**
```python
# Let exceptions propagate
data = extract_field(html)  # Crashes entire scrape
```

---

## Performance Considerations

### Scalability

**Current:**
- Handles 100-10,000 products per client
- Sequential processing (one product at a time)
- Memory-efficient (processes one item at a time)

**Future Enhancements:**
- Parallel processing (multiple products simultaneously)
- Distributed scraping (multiple workers)
- Database storage (vs JSON files)

### Optimization Opportunities

1. **Caching:** Cache commonly accessed pages
2. **Batch Processing:** Process products in batches
3. **Async I/O:** Use async for network requests
4. **Connection Pooling:** Reuse HTTP connections
5. **Selective Scraping:** Only scrape changed products

---

## Security Considerations

### Current Implementation

- **No authentication:** Scrapes public websites only
- **Rate limiting:** Respects server load
- **User agent:** Uses standard browser UA
- **robots.txt:** Should be checked manually

### Best Practices

1. **Respect robots.txt**
2. **Use appropriate rate limiting**
3. **Don't overwhelm servers**
4. **Handle personal data appropriately**
5. **Store credentials securely (if needed)**

---

## Future Architecture

### Planned Enhancements

1. **Database Integration**
   - PostgreSQL/MongoDB for storage
   - Better querying and analysis
   - Change tracking

2. **API Layer**
   - REST API for accessing data
   - GraphQL for flexible queries
   - WebSocket for real-time updates

3. **Web Interface**
   - Dashboard for monitoring
   - Visual selector builder
   - Configuration UI

4. **Cloud Deployment**
   - Docker containerization
   - Kubernetes orchestration
   - AWS/GCP/Azure deployment

5. **Advanced Features**
   - Change detection and alerts
   - Scheduled automatic scraping
   - Data enrichment pipelines
   - AI-powered extraction

---

## Summary

The 3DN Scraper Template architecture is designed for:

- **Rapid Deployment:** New clients in < 1 hour
- **Maintainability:** Clear separation of concerns
- **Extensibility:** Easy to add features
- **Reliability:** Robust error handling
- **Scalability:** Handles sites of all sizes

The modular, configuration-driven design allows the same core codebase to work across diverse client websites with minimal per-client customization.

---

**Related Documentation:**
- [CLIENT_DEPLOYMENT_GUIDE.md](CLIENT_DEPLOYMENT_GUIDE.md) - Deployment workflow
- [configuration-guide.md](configuration-guide.md) - Configuration reference
- [extraction-strategies.md](extraction-strategies.md) - Strategy patterns
- [api-reference.md](api-reference.md) - API documentation

---

*3DN Scraper Template v1.0.0 - Professional Web Scraping Framework*
