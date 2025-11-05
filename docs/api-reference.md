# 3DN Scraper Template - API Reference

**Version:** 1.0.0  
**Last Updated:** 2025-11-05

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Module](#configuration-module)
   - [ConfigLoader](#configloader)
   - [BaseConfig](#baseconfig)
3. [Core Scraping Modules](#core-scraping-modules)
   - [CategoryScraper](#categoryscraper)
   - [ProductCollector](#productcollector)
   - [ProductScraper](#productscraper)
   - [ProductPDFScraper](#productpdfscraper)
   - [PDFDownloader](#pdfdownloader)
4. [Utility Functions](#utility-functions)
5. [Strategy Interface](#strategy-interface)
   - [BaseExtractionStrategy](#baseextractionstrategy)
   - [SimpleCSSStrategy](#simplecssstrategy)
6. [Data Structures](#data-structures)
7. [Examples](#examples)

---

## Overview

This API reference provides detailed documentation for all modules, classes, and functions in the 3DN Scraper Template. The framework is designed to be client-agnostic, using configuration-driven architecture.

### Import Conventions

```python
# Configuration
from config.config_loader import ConfigLoader
from config.base_config import BaseConfig

# Core Scrapers
from core.category_scraper import CategoryScraper
from core.product_collector import ProductCollector
from core.product_scraper import ProductScraper
from core.product_pdf_scraper import ProductPDFScraper
from core.pdf_downloader import PDFDownloader

# Utilities
from core.utils import (
    save_json, load_json, sanitize_filename,
    clean_product_name, save_screenshot, get_rate_limit_delay
)

# Strategies
from strategies.base_strategy import BaseExtractionStrategy, SimpleCSSStrategy
```

---

## Configuration Module

### ConfigLoader

**Location:** `config/config_loader.py`

Central configuration management system for loading and managing client deployments.

#### Class: ConfigLoader

##### Methods

###### `load_client_config(client_name: str) -> Type[BaseConfig]`

Load configuration for a specific client deployment.

**Parameters:**
- `client_name` (str): Client identifier (e.g., 'agar', 'exampleclient')

**Returns:**
- `Type[BaseConfig]`: ClientConfig class for the specified client

**Raises:**
- `ValueError`: If client name is empty
- `ImportError`: If client configuration cannot be loaded
- `TypeError`: If ClientConfig doesn't inherit from BaseConfig

**Example:**
```python
from config.config_loader import ConfigLoader

# Load client configuration
config = ConfigLoader.load_client_config('agar')

# Access configuration
print(config.CLIENT_FULL_NAME)
print(config.BASE_URL)
print(config.CATEGORY_URL_PATTERN)
```

**Output:**
```
✓ Loaded configuration for client: Agar Cleaning Supplies
```

---

###### `load_client_strategies(client_name: str) -> module`

Load extraction strategies for a specific client.

**Parameters:**
- `client_name` (str): Client identifier

**Returns:**
- Strategy module or class containing extraction methods

**Example:**
```python
# Load strategies
strategies = ConfigLoader.load_client_strategies('agar')

# Get extraction schema
product_schema = strategies.get_product_detail_schema()
```

---

###### `get_active_config() -> Type[BaseConfig]`

Get the currently active client configuration.

**Returns:**
- `Type[BaseConfig]`: Active ClientConfig class

**Raises:**
- `RuntimeError`: If no configuration has been loaded

**Example:**
```python
# Load a config first
ConfigLoader.load_client_config('agar')

# Get active config later
active_config = ConfigLoader.get_active_config()
```

---

###### `get_active_client_name() -> str`

Get the name of the currently active client.

**Returns:**
- `str`: Active client name

**Raises:**
- `RuntimeError`: If no configuration has been loaded

---

###### `list_available_clients() -> list`

List all available client deployments.

**Returns:**
- `list`: List of available client names

**Example:**
```python
clients = ConfigLoader.list_available_clients()
print(f"Available clients: {', '.join(clients)}")
# Output: Available clients: agar, example_client
```

---

###### `print_available_clients()`

Print formatted list of available clients with full names.

**Example:**
```python
ConfigLoader.print_available_clients()
```

**Output:**
```
Available Client Deployments:
==================================================
  • agar                 - Agar Cleaning Supplies
  • example_client       - Example Client
==================================================
```

---

###### `validate_client_config(client_name: str) -> tuple[bool, list]`

Validate a client configuration.

**Parameters:**
- `client_name` (str): Client identifier

**Returns:**
- `tuple[bool, list]`: (is_valid, list_of_issues)

**Example:**
```python
is_valid, issues = ConfigLoader.validate_client_config('agar')

if is_valid:
    print("✓ Configuration is valid")
else:
    print("✗ Configuration has issues:")
    for issue in issues:
        print(f"  - {issue}")
```

---

### BaseConfig

**Location:** `config/base_config.py`

Base configuration class that all client configurations inherit from.

#### Configuration Properties

##### Basic Settings

- `CLIENT_NAME` (str): Short client identifier (e.g., 'agar')
- `CLIENT_FULL_NAME` (str): Full client name for display
- `BASE_URL` (str): Base URL of the website (e.g., 'https://agar.com.au')

##### URL Patterns

- `CATEGORY_URL_PATTERN` (str): Template for category URLs with `{slug}` placeholder
- `PRODUCT_URL_PATTERN` (str): Template for product URLs with `{slug}` placeholder

##### Output Settings

- `OUTPUT_PREFIX` (str): Prefix for output directories
- `BASE_OUTPUT_DIR` (str): Base directory for all outputs

##### Scraping Configuration

- `PAGE_TIMEOUT` (int): Page load timeout in milliseconds (default: 60000)
- `DETAIL_PAGE_TIMEOUT` (int): Product detail page timeout (default: 90000)
- `USER_AGENT` (str): User agent string for requests

##### Rate Limiting

- `RATE_LIMIT_MIN` (float): Minimum delay between requests (seconds)
- `RATE_LIMIT_MAX` (float): Maximum delay between requests (seconds)
- `RATE_LIMIT_DELAY` (float): Fixed delay (backward compatibility)

##### Test Mode

- `TEST_MODE` (bool): Enable test mode with limits
- `TEST_CATEGORY_LIMIT` (int): Maximum categories in test mode
- `TEST_PRODUCT_LIMIT` (int): Maximum products per category in test mode

##### Client-Specific

- `KNOWN_CATEGORIES` (list): List of known category slugs

**Example:**
```python
from config.base_config import BaseConfig

class MyClientConfig(BaseConfig):
    CLIENT_NAME = "myclient"
    CLIENT_FULL_NAME = "My Client Company"
    BASE_URL = "https://myclient.com"
    
    CATEGORY_URL_PATTERN = f"{BASE_URL}/category/{{slug}}/"
    PRODUCT_URL_PATTERN = f"{BASE_URL}/product/{{slug}}/"
    
    OUTPUT_PREFIX = "myclient"
    
    KNOWN_CATEGORIES = [
        "category-1",
        "category-2",
        "category-3"
    ]
```

---

## Core Scraping Modules

### CategoryScraper

**Location:** `core/category_scraper.py`

Discovers and manages product categories from the website.

#### Class: CategoryScraper

##### Constructor

```python
CategoryScraper(config: Type[BaseConfig], output_dir: Path = None, test_mode: bool = False)
```

**Parameters:**
- `config` (Type[BaseConfig]): Client configuration class
- `output_dir` (Path, optional): Output directory for results
- `test_mode` (bool): Enable test mode with limited categories

**Example:**
```python
from pathlib import Path
from config.config_loader import ConfigLoader
from core.category_scraper import CategoryScraper

# Load configuration
config = ConfigLoader.load_client_config('agar')

# Create scraper
scraper = CategoryScraper(
    config=config,
    output_dir=Path("./output"),
    test_mode=False
)
```

---

##### Methods

###### `discover_categories() -> List[Dict]`

Discover all product categories from the website.

**Returns:**
- `List[Dict]`: List of category dictionaries with keys:
  - `name` (str): Category display name
  - `slug` (str): Category URL slug
  - `url` (str): Full category URL

**Example:**
```python
categories = await scraper.discover_categories()

for cat in categories:
    print(f"{cat['name']}: {cat['url']}")
```

**Output:**
```
Cleaning Products: https://agar.com.au/product-category/cleaning-products/
Kitchen Supplies: https://agar.com.au/product-category/kitchen-supplies/
```

---

###### `scrape_category_page(category_url: str) -> Dict`

Scrape metadata from a single category page.

**Parameters:**
- `category_url` (str): URL of category page

**Returns:**
- `Dict`: Metadata dictionary with keys:
  - `scraped` (bool): Success status
  - `timestamp` (str): ISO format timestamp

---

###### `save_categories(categories: List[Dict]) -> Path`

Save categories to JSON file.

**Parameters:**
- `categories` (List[Dict]): List of category dictionaries

**Returns:**
- `Path`: Path to saved file

---

###### `run() -> List[Dict]`

Main execution method - discovers categories and optionally saves them.

**Returns:**
- `List[Dict]`: List of discovered categories

**Example:**
```python
# Run complete category discovery
categories = await scraper.run()
print(f"Found {len(categories)} categories")
```

---

### ProductCollector

**Location:** `core/product_collector.py`

Collects product URLs from category pages, handling hierarchical category structures.

#### Class: ProductCollector

##### Constructor

```python
ProductCollector(config: Type[BaseConfig], output_dir: Path = None, test_mode: bool = False)
```

**Parameters:**
- `config` (Type[BaseConfig]): Client configuration class
- `output_dir` (Path, optional): Output directory for results
- `test_mode` (bool): Enable test mode with product limits

---

##### Methods

###### `collect_from_category(category: Dict, depth: int = 0, parent_slug: str = None) -> List[Dict]`

Extract all product URLs and subcategories from a category page recursively.

**Parameters:**
- `category` (Dict): Category dictionary with 'name', 'slug', 'url'
- `depth` (int): Current recursion depth (to prevent infinite loops)
- `parent_slug` (str, optional): Parent category slug for hierarchy

**Returns:**
- `List[Dict]`: List of product dictionaries with keys:
  - `title` (str): Product title
  - `url` (str): Product URL
  - `image` (str): Product image URL
  - `category` (str): Category name
  - `category_slug` (str): Category slug
  - `parent_category_slug` (str, optional): Parent category slug

**Example:**
```python
from config.config_loader import ConfigLoader
from core.product_collector import ProductCollector

config = ConfigLoader.load_client_config('agar')
collector = ProductCollector(config=config)

category = {
    "name": "Cleaning Products",
    "slug": "cleaning-products",
    "url": "https://agar.com.au/product-category/cleaning-products/"
}

products = await collector.collect_from_category(category)
print(f"Found {len(products)} products")
```

**Features:**
- Handles hierarchical categories automatically
- Detects and processes subcategories recursively
- Maintains category hierarchy in output
- Prevents infinite loops with `MAX_CATEGORY_DEPTH` (5 levels)
- Tracks processed categories to avoid duplicates

---

###### `collect_all_products(categories: List[Dict] = None) -> List[Dict]`

Collect products from all categories.

**Parameters:**
- `categories` (List[Dict], optional): List of categories. If None, loads from categories.json

**Returns:**
- `List[Dict]`: List of all collected products

**Example:**
```python
# Collect from all categories
all_products = await collector.collect_all_products()
print(f"Total products: {len(all_products)}")
```

---

###### `save_products(products: List[Dict]) -> Path`

Save all products to JSON file.

**Parameters:**
- `products` (List[Dict]): List of product dictionaries

**Returns:**
- `Path`: Path to saved file (all_products_list.json)

---

### ProductScraper

**Location:** `core/product_scraper.py`

Scrapes detailed product information using CSS extraction. Does NOT handle PDF extraction.

#### Class: ProductScraper

##### Constructor

```python
ProductScraper(
    config: Type[BaseConfig],
    extraction_strategy,
    output_dir: Path = None,
    save_screenshots: bool = True
)
```

**Parameters:**
- `config` (Type[BaseConfig]): Client configuration class
- `extraction_strategy`: Client extraction strategy class/module
- `output_dir` (Path, optional): Output directory for results
- `save_screenshots` (bool): Whether to save page screenshots

**Example:**
```python
from config.config_loader import ConfigLoader
from core.product_scraper import ProductScraper

# Load configuration and strategies
config = ConfigLoader.load_client_config('agar')
strategies = ConfigLoader.load_client_strategies('agar')

# Create scraper
scraper = ProductScraper(
    config=config,
    extraction_strategy=strategies,
    output_dir=Path("./output"),
    save_screenshots=True
)
```

---

##### Methods

###### `scrape_product_details(product_info: Dict) -> Optional[Dict]`

Scrape product details using client-specific CSS selectors.

**Parameters:**
- `product_info` (Dict): Product information with 'url' key

**Returns:**
- `Optional[Dict]`: Extracted product data or None if failed

**Extracted Fields:**
- `product_name` (str): Product name
- `main_image` (str): Main product image URL
- `gallery_images` (list): Additional image URLs
- `product_overview` (str): Short product description
- `product_description` (str): Full product description
- `product_sku` (str): Product SKU/code
- `product_categories` (list): Product categories

---

###### `scrape_product(product_info: Dict) -> Optional[Dict]`

Main scraper method - extracts complete product details.

**Parameters:**
- `product_info` (Dict): Product information

**Returns:**
- `Optional[Dict]`: Complete product data dictionary with keys:
  - `product_name` (str): Product name
  - `product_url` (str): Product page URL
  - `product_image_url` (str): Main image URL
  - `product_overview` (str): Overview text
  - `product_description` (str): Full description
  - `product_skus` (str): Product SKU
  - `product_categories` (list): Categories
  - `scraped_at` (str): ISO timestamp
  - `category` (str): Primary category
  - `category_slug` (str): Category slug

**Example:**
```python
product_info = {
    "title": "Grease Gone",
    "url": "https://agar.com.au/product/grease-gone/",
    "category": "Cleaning Products",
    "category_slug": "cleaning-products"
}

product_data = await scraper.scrape_product(product_info)

if product_data:
    print(f"Product: {product_data['product_name']}")
    print(f"SKU: {product_data['product_skus']}")
    print(f"Overview: {product_data['product_overview'][:100]}...")
```

---

###### `scrape_products(products: List[Dict]) -> List[Dict]`

Scrape multiple products with rate limiting.

**Parameters:**
- `products` (List[Dict]): List of product information dictionaries

**Returns:**
- `List[Dict]`: List of successfully scraped products

**Example:**
```python
products = [
    {"title": "Product 1", "url": "https://...", "category": "Cat1"},
    {"title": "Product 2", "url": "https://...", "category": "Cat2"},
]

successful = await scraper.scrape_products(products)
print(f"Scraped {len(successful)}/{len(products)} products")
```

---

### ProductPDFScraper

**Location:** `core/product_pdf_scraper.py`

Extracts PDF download links from product pages. ONLY handles PDF extraction.

#### Class: ProductPDFScraper

##### Constructor

```python
ProductPDFScraper(config: Type[BaseConfig], output_dir: Path = None)
```

**Parameters:**
- `config` (Type[BaseConfig]): Client configuration class
- `output_dir` (Path, optional): Output directory for results

---

##### Methods

###### `scrape_pdf_links(product_url: str, product_name: str = "Product") -> Optional[Dict]`

Extract PDF download links using 2-step process:
1. Find SDS/PDS page link on product page
2. Extract PDF URLs from SDS/PDS page

**Parameters:**
- `product_url` (str): Product page URL
- `product_name` (str): Product name for identification

**Returns:**
- `Optional[Dict]`: PDF data dictionary with keys:
  - `product_name` (str): Product name
  - `product_url` (str): Product page URL
  - `sds_url` (str): SDS PDF URL (or None)
  - `pds_url` (str): PDS PDF URL (or None)
  - `scraped_at` (str): ISO timestamp
  - `extraction_method` (str): Method used
  - `total_pdfs_found` (int): Total PDFs found

**Example:**
```python
from config.config_loader import ConfigLoader
from core.product_pdf_scraper import ProductPDFScraper

config = ConfigLoader.load_client_config('agar')
pdf_scraper = ProductPDFScraper(config=config)

pdf_data = await pdf_scraper.scrape_pdf_links(
    product_url="https://agar.com.au/product/grease-gone/",
    product_name="Grease Gone"
)

if pdf_data:
    print(f"SDS: {pdf_data['sds_url']}")
    print(f"PDS: {pdf_data['pds_url']}")
```

---

###### `scrape_products(products: List[Dict]) -> List[Dict]`

Scrape PDF links for multiple products.

**Parameters:**
- `products` (List[Dict]): List of products with 'product_name' and 'product_url' or 'url'

**Returns:**
- `List[Dict]`: List of successfully extracted PDF data

**Example:**
```python
products = [
    {"product_name": "Product 1", "product_url": "https://..."},
    {"product_name": "Product 2", "product_url": "https://..."},
]

pdf_results = await pdf_scraper.scrape_products(products)
print(f"Extracted PDFs from {len(pdf_results)} products")
```

---

### PDFDownloader

**Location:** `core/pdf_downloader.py`

Downloads actual PDF files from extracted URLs with retry logic.

#### Class: PDFDownloader

##### Constructor

```python
PDFDownloader(
    config: Type[BaseConfig],
    run_dir: Path,
    max_retries: int = 3,
    timeout: int = 30
)
```

**Parameters:**
- `config` (Type[BaseConfig]): Client configuration class
- `run_dir` (Path): Run directory path
- `max_retries` (int): Maximum retry attempts per file
- `timeout` (int): Timeout in seconds per download

**Example:**
```python
from pathlib import Path
from config.config_loader import ConfigLoader
from core.pdf_downloader import PDFDownloader

config = ConfigLoader.load_client_config('agar')
run_dir = Path("./agar_scrapes/AgarScrape_20251105_100000")

downloader = PDFDownloader(
    config=config,
    run_dir=run_dir,
    max_retries=3,
    timeout=30
)
```

---

##### Methods

###### `download_all_pdfs(products: Optional[List[Dict]] = None) -> Dict`

Download all PDFs for scraped products.

**Parameters:**
- `products` (Optional[List[Dict]]): Product data with PDF URLs. If None, reads from PDF metadata files

**Returns:**
- `Dict`: Download statistics with keys:
  - `total_pdfs` (int): Total PDFs attempted
  - `successful_downloads` (int): Successfully downloaded
  - `failed_downloads` (int): Failed downloads
  - `skipped` (int): Already existing files
  - `total_size_bytes` (int): Total download size

**Example:**
```python
# Download from PDF metadata files
stats = await downloader.download_all_pdfs()

print(f"Downloaded: {stats['successful_downloads']}")
print(f"Failed: {stats['failed_downloads']}")
print(f"Total size: {stats['total_size_bytes'] / 1024 / 1024:.1f} MB")
```

**Output Structure:**
```
run_dir/
├── PDFs/
│   ├── Product_Name_1/
│   │   ├── Product_Name_1_SDS.pdf
│   │   └── Product_Name_1_PDS.pdf
│   ├── Product_Name_2/
│   │   ├── Product_Name_2_SDS.pdf
│   │   └── Product_Name_2_PDS.pdf
└── reports/
    └── pdf_download_report.json
```

**Features:**
- Automatic retry with exponential backoff
- Skips already downloaded files
- Validates PDF file format
- SSL verification disabled for problematic sites
- Organizes PDFs by product name
- Generates download report

---

## Utility Functions

**Location:** `core/utils.py`

### sanitize_filename

```python
sanitize_filename(filename: str) -> str
```

Sanitize filename for safe file system operations.

**Parameters:**
- `filename` (str): Original filename

**Returns:**
- `str`: Sanitized filename (max 100 chars, alphanumeric and -_ only)

**Example:**
```python
from core.utils import sanitize_filename

safe_name = sanitize_filename("Product: Name (2023) #1!")
print(safe_name)
# Output: Product Name 2023 1
```

---

### save_json

```python
save_json(data: Any, filepath: Path) -> None
```

Save data as formatted JSON file.

**Parameters:**
- `data` (Any): Data to save (must be JSON serializable)
- `filepath` (Path): Target file path

**Example:**
```python
from pathlib import Path
from core.utils import save_json

data = {"name": "Product", "price": 29.99}
save_json(data, Path("./output/product.json"))
```

---

### load_json

```python
load_json(filepath: Path) -> Any
```

Load data from JSON file.

**Parameters:**
- `filepath` (Path): JSON file path

**Returns:**
- `Any`: Loaded data structure

**Example:**
```python
from pathlib import Path
from core.utils import load_json

data = load_json(Path("./output/product.json"))
print(data['name'])
```

---

### clean_product_name

```python
clean_product_name(name: str) -> str
```

Clean product name by removing common suffixes and patterns.

**Parameters:**
- `name` (str): Raw product name

**Returns:**
- `str`: Cleaned product name

**Removes:**
- " Data Sheets"
- " Downloads"
- " - Agar"
- " | Agar"
- Trailing "SDS" or "PDS"

**Example:**
```python
from core.utils import clean_product_name

raw_name = "Grease Gone Data Sheets - Agar SDS"
clean_name = clean_product_name(raw_name)
print(clean_name)
# Output: Grease Gone
```

---

### save_screenshot

```python
save_screenshot(screenshot_data: Any, filepath: Path) -> bool
```

Save screenshot data to file.

**Parameters:**
- `screenshot_data` (Any): Screenshot data (base64, bytes, or data URL)
- `filepath` (Path): Target file path

**Returns:**
- `bool`: True if successful

**Example:**
```python
from pathlib import Path
from core.utils import save_screenshot

# screenshot_data from crawler result
success = save_screenshot(
    screenshot_data=result.screenshot,
    filepath=Path("./screenshots/product.png")
)
```

---

### get_rate_limit_delay

```python
get_rate_limit_delay(config: Type[BaseConfig]) -> float
```

Get random rate limit delay based on config settings.

**Parameters:**
- `config` (Type[BaseConfig]): Client configuration

**Returns:**
- `float`: Random delay in seconds between RATE_LIMIT_MIN and RATE_LIMIT_MAX

**Example:**
```python
import asyncio
from config.config_loader import ConfigLoader
from core.utils import get_rate_limit_delay

config = ConfigLoader.load_client_config('agar')

# Rate limit between requests
for product in products:
    await scrape_product(product)
    delay = get_rate_limit_delay(config)
    await asyncio.sleep(delay)
```

---

### create_run_metadata

```python
create_run_metadata(run_dir: Path, mode: str = "FULL") -> Dict
```

Create initial run metadata file.

**Parameters:**
- `run_dir` (Path): Run directory path
- `mode` (str): Run mode ("FULL" or "TEST")

**Returns:**
- `Dict`: Created metadata

---

### update_run_metadata

```python
update_run_metadata(run_dir: Path, updates: Dict) -> None
```

Update run metadata with new information.

**Parameters:**
- `run_dir` (Path): Run directory path
- `updates` (Dict): Fields to update

**Example:**
```python
from pathlib import Path
from core.utils import create_run_metadata, update_run_metadata

run_dir = Path("./agar_scrapes/run_001")
run_dir.mkdir(parents=True, exist_ok=True)

# Create metadata
metadata = create_run_metadata(run_dir, mode="TEST")

# Update later
update_run_metadata(run_dir, {
    "status": "COMPLETED",
    "products_scraped": 150,
    "end_time": "2025-11-05T10:30:00"
})
```

---

## Strategy Interface

### BaseExtractionStrategy

**Location:** `strategies/base_strategy.py`

Abstract base class for client extraction strategies.

#### Properties (Abstract)

##### `CATEGORY_SELECTORS` → Dict[str, str]

CSS selectors for category pages.

**Required Keys:**
- `products`: Selector for product list items
- `product_link`: Selector for product URLs
- `product_name`: Selector for product names
- `product_image`: Selector for images (optional)
- `pagination`: Pagination selector (optional)
- `next_page`: Next page link selector (optional)

---

##### `PRODUCT_SELECTORS` → Dict[str, str]

CSS selectors for product detail pages.

**Required Keys:**
- `name`: Product name selector
- `main_image`: Main product image selector
- `gallery_images`: Gallery images selector (optional)
- `overview`: Product overview selector
- `description`: Full description selector
- `sku`: Product SKU selector (optional)
- `categories`: Categories selector (optional)

---

##### `PDF_SELECTORS` → Dict[str, str]

CSS selectors for PDF/document links (optional).

**Optional Keys:**
- `sds_link`: SDS document link selector
- `pds_link`: PDS document link selector
- `document_section`: Document container selector
- `all_document_links`: All PDF links selector

---

#### Methods (Abstract)

##### `get_product_detail_schema() -> Dict`

Generate JSON extraction schema for product detail pages.

**Returns:**
- `Dict`: Schema compatible with JsonCssExtractionStrategy

---

##### `get_category_schema() -> Dict`

Generate JSON extraction schema for category pages.

**Returns:**
- `Dict`: Schema compatible with JsonCssExtractionStrategy

---

#### Optional Methods

##### `extract_pdf_links(html: str) -> Dict[str, Optional[str]]`

Extract PDF links from HTML (override for custom logic).

**Parameters:**
- `html` (str): Product page HTML

**Returns:**
- `Dict`: PDF URLs dict with 'sds_url' and 'pds_url' keys

---

##### `clean_product_data(data: Dict) -> Dict`

Clean and normalize extracted product data.

**Parameters:**
- `data` (Dict): Raw extracted data

**Returns:**
- `Dict`: Cleaned data

---

### SimpleCSSStrategy

**Location:** `strategies/base_strategy.py`

Concrete implementation of BaseExtractionStrategy using simple CSS selectors.

#### Constructor

```python
SimpleCSSStrategy(
    category_selectors: Dict[str, str],
    product_selectors: Dict[str, str],
    pdf_selectors: Dict[str, str] = None
)
```

**Example:**
```python
from strategies.base_strategy import SimpleCSSStrategy

strategy = SimpleCSSStrategy(
    category_selectors={
        "products": "ul.products li.product",
        "product_link": "a.product-link",
        "product_name": "h2.product-name",
        "product_image": "img.product-image"
    },
    product_selectors={
        "name": "h1.product-title",
        "main_image": "img.main-image",
        "overview": "div.short-description",
        "description": "div.full-description",
        "sku": "span.sku"
    },
    pdf_selectors={
        "sds_link": "a[href*='sds']",
        "pds_link": "a[href*='pds']"
    }
)

# Use in scraper
from core.product_scraper import ProductScraper

scraper = ProductScraper(
    config=config,
    extraction_strategy=strategy
)
```

---

## Data Structures

### Category Dictionary

```python
{
    "name": str,              # Display name
    "slug": str,              # URL slug
    "url": str,               # Full URL
    "count": str,             # Product count (optional)
    "image": str              # Category image (optional)
}
```

### Product List Item

```python
{
    "title": str,             # Product title
    "url": str,               # Product URL
    "image": str,             # Product image URL
    "category": str,          # Category name
    "category_slug": str      # Category slug
}
```

### Product Details

```python
{
    "product_name": str,           # Product name
    "product_url": str,            # Product page URL
    "product_image_url": str,      # Main image URL
    "product_overview": str,       # Short description
    "product_description": str,    # Full description
    "product_skus": str,           # Product SKU
    "product_categories": list,    # Categories list
    "scraped_at": str,             # ISO timestamp
    "category": str,               # Primary category
    "category_slug": str           # Category slug
}
```

### PDF Data

```python
{
    "product_name": str,           # Product name
    "product_url": str,            # Product page URL
    "sds_url": str,                # SDS PDF URL (or None)
    "pds_url": str,                # PDS PDF URL (or None)
    "scraped_at": str,             # ISO timestamp
    "extraction_method": str,      # Extraction method used
    "total_pdfs_found": int        # Total PDFs found
}
```

### Run Metadata

```python
{
    "run_id": str,                 # Run directory name
    "start_time": str,             # ISO start timestamp
    "end_time": str,               # ISO end timestamp (optional)
    "mode": str,                   # "FULL" or "TEST"
    "base_url": str,               # Client base URL
    "status": str,                 # "RUNNING", "COMPLETED", "FAILED"
    "run_directory": str,          # Absolute path to run directory
    "categories_count": int,       # Total categories (optional)
    "products_count": int,         # Total products (optional)
    "products_scraped": int,       # Successfully scraped (optional)
    "pdfs_downloaded": int         # PDFs downloaded (optional)
}
```

### Download Statistics

```python
{
    "total_pdfs": int,             # Total PDFs attempted
    "successful_downloads": int,   # Successfully downloaded
    "failed_downloads": int,       # Failed downloads
    "skipped": int,                # Already existing
    "total_size_bytes": int        # Total download size
}
```

---

## Examples

### Complete Scraping Workflow

```python
import asyncio
from pathlib import Path
from config.config_loader import ConfigLoader
from core.category_scraper import CategoryScraper
from core.product_collector import ProductCollector
from core.product_scraper import ProductScraper
from core.product_pdf_scraper import ProductPDFScraper
from core.pdf_downloader import PDFDownloader

async def full_scraping_workflow():
    """Complete scraping workflow example"""
    
    # 1. Load client configuration
    print("Loading configuration...")
    config = ConfigLoader.load_client_config('agar')
    strategies = ConfigLoader.load_client_strategies('agar')
    
    # Setup output directory
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    # 2. Discover categories
    print("\n1. Discovering categories...")
    category_scraper = CategoryScraper(
        config=config,
        output_dir=output_dir
    )
    categories = await category_scraper.run()
    print(f"Found {len(categories)} categories")
    
    # 3. Collect product URLs
    print("\n2. Collecting product URLs...")
    product_collector = ProductCollector(
        config=config,
        output_dir=output_dir
    )
    products = await product_collector.collect_all_products(categories)
    product_collector.save_products(products)
    print(f"Collected {len(products)} products")
    
    # 4. Scrape product details
    print("\n3. Scraping product details...")
    product_scraper = ProductScraper(
        config=config,
        extraction_strategy=strategies,
        output_dir=output_dir
    )
    scraped_products = await product_scraper.scrape_products(products)
    print(f"Scraped {len(scraped_products)} products")
    
    # 5. Extract PDF links
    print("\n4. Extracting PDF links...")
    pdf_scraper = ProductPDFScraper(
        config=config,
        output_dir=output_dir
    )
    pdf_data = await pdf_scraper.scrape_products(scraped_products)
    print(f"Extracted PDFs from {len(pdf_data)} products")
    
    # 6. Download PDFs
    print("\n5. Downloading PDFs...")
    downloader = PDFDownloader(
        config=config,
        run_dir=output_dir
    )
    stats = await downloader.download_all_pdfs(pdf_data)
    print(f"Downloaded {stats['successful_downloads']} PDFs")
    
    print("\n✓ Scraping complete!")

# Run the workflow
if __name__ == "__main__":
    asyncio.run(full_scraping_workflow())
```

---

### Custom Client Deployment

```python
"""Example of creating a custom client configuration"""

# 1. Create client configuration
# File: config/clients/myclient/client_config.py

from config.base_config import BaseConfig

class ClientConfig(BaseConfig):
    # Basic identification
    CLIENT_NAME = "myclient"
    CLIENT_FULL_NAME = "My Client Company"
    BASE_URL = "https://myclient.com"
    
    # URL patterns
    CATEGORY_URL_PATTERN = f"{BASE_URL}/shop/{{slug}}/"
    PRODUCT_URL_PATTERN = f"{BASE_URL}/products/{{slug}}/"
    
    # Output configuration
    OUTPUT_PREFIX = "myclient"
    BASE_OUTPUT_DIR = "myclient_scrapes"
    
    # Scraping configuration
    PAGE_TIMEOUT = 60000
    DETAIL_PAGE_TIMEOUT = 90000
    
    # Rate limiting
    RATE_LIMIT_MIN = 2.0
    RATE_LIMIT_MAX = 5.0
    
    # Known categories
    KNOWN_CATEGORIES = [
        "category-1",
        "category-2",
        "category-3"
    ]

# 2. Create extraction strategies
# File: config/clients/myclient/extraction_strategies.py

class MyclientExtractionStrategy:
    """Extraction strategies for My Client Company"""
    
    @staticmethod
    def get_product_detail_schema():
        return {
            "name": "Product Details",
            "baseSelector": "body",
            "fields": [
                {
                    "name": "product_name",
                    "selector": "h1.product-title",
                    "type": "text"
                },
                {
                    "name": "main_image",
                    "selector": "img.main-product-image",
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "product_overview",
                    "selector": "div.product-summary",
                    "type": "text"
                },
                {
                    "name": "product_description",
                    "selector": "div.product-details",
                    "type": "text"
                },
                {
                    "name": "product_sku",
                    "selector": "span.sku",
                    "type": "text"
                }
            ]
        }
    
    @staticmethod
    def get_category_schema():
        return {
            "name": "Category Products",
            "baseSelector": "ul.product-grid",
            "fields": [
                {
                    "name": "products",
                    "selector": "li.product-item",
                    "type": "nested_list",
                    "fields": [
                        {
                            "name": "title",
                            "selector": "h2.product-name",
                            "type": "text"
                        },
                        {
                            "name": "url",
                            "selector": "a.product-link",
                            "type": "attribute",
                            "attribute": "href"
                        }
                    ]
                }
            ]
        }

# 3. Use the new client
from config.config_loader import ConfigLoader

config = ConfigLoader.load_client_config('myclient')
strategies = ConfigLoader.load_client_strategies('myclient')

# Now use in scrapers as normal
```

---

### Single Product Scraping

```python
"""Example of scraping a single product"""

import asyncio
from pathlib import Path
from config.config_loader import ConfigLoader
from core.product_scraper import ProductScraper

async def scrape_single_product(product_url: str):
    """Scrape a single product page"""
    
    # Load configuration
    config = ConfigLoader.load_client_config('agar')
    strategies = ConfigLoader.load_client_strategies('agar')
    
    # Create scraper
    scraper = ProductScraper(
        config=config,
        extraction_strategy=strategies,
        output_dir=Path("./output")
    )
    
    # Prepare product info
    product_info = {
        "title": "Product",
        "url": product_url,
        "category": "Unknown",
        "category_slug": "unknown"
    }
    
    # Scrape product
    product_data = await scraper.scrape_product(product_info)
    
    if product_data:
        print("\n✓ Product scraped successfully!")
        print(f"Name: {product_data['product_name']}")
        print(f"SKU: {product_data['product_skus']}")
        print(f"Overview: {product_data['product_overview'][:100]}...")
        return product_data
    else:
        print("\n✗ Failed to scrape product")
        return None

# Run
if __name__ == "__main__":
    url = "https://agar.com.au/product/grease-gone/"
    asyncio.run(scrape_single_product(url))
```

---

### Batch PDF Download

```python
"""Example of downloading PDFs for specific products"""

import asyncio
from pathlib import Path
from config.config_loader import ConfigLoader
from core.pdf_downloader import PDFDownloader
from core.utils import save_json

async def download_pdfs_for_products(pdf_metadata: list):
    """Download PDFs for a list of products"""
    
    # Load configuration
    config = ConfigLoader.load_client_config('agar')
    
    # Setup run directory
    run_dir = Path("./pdf_downloads")
    run_dir.mkdir(exist_ok=True)
    
    # Save PDF metadata
    (run_dir / "pdfs").mkdir(exist_ok=True)
    for i, metadata in enumerate(pdf_metadata):
        filename = f"product_{i+1}_pdfs.json"
        save_json(metadata, run_dir / "pdfs" / filename)
    
    # Create downloader
    downloader = PDFDownloader(
        config=config,
        run_dir=run_dir,
        max_retries=5,
        timeout=60
    )
    
    # Download all PDFs
    stats = await downloader.download_all_pdfs()
    
    print(f"\n✓ Download complete!")
    print(f"  Successfully downloaded: {stats['successful_downloads']}")
    print(f"  Failed: {stats['failed_downloads']}")
    print(f"  Total size: {stats['total_size_bytes'] / 1024 / 1024:.1f} MB")

# Example PDF metadata
pdf_data = [
    {
        "product_name": "Product 1",
        "product_url": "https://example.com/product1",
        "sds_url": "https://example.com/pdfs/product1-sds.pdf",
        "pds_url": "https://example.com/pdfs/product1-pds.pdf"
    },
    {
        "product_name": "Product 2",
        "product_url": "https://example.com/product2",
        "sds_url": "https://example.com/pdfs/product2-sds.pdf",
        "pds_url": None
    }
]

# Run
if __name__ == "__main__":
    asyncio.run(download_pdfs_for_products(pdf_data))
```

---

### Error Handling Example

```python
"""Example with proper error handling"""

import asyncio
from pathlib import Path
from config.config_loader import ConfigLoader
from core.product_scraper import ProductScraper
from core.utils import save_json

async def robust_product_scraping(products: list):
    """Scrape products with error handling"""
    
    try:
        # Load configuration
        config = ConfigLoader.load_client_config('agar')
        strategies = ConfigLoader.load_client_strategies('agar')
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return
    
    # Setup output
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    # Create scraper
    scraper = ProductScraper(
        config=config,
        extraction_strategy=strategies,
        output_dir=output_dir
    )
    
    successful = []
    failed = []
    
    for i, product in enumerate(products, 1):
        try:
            print(f"\n[{i}/{len(products)}] Scraping: {product.get('title', 'Unknown')}")
            
            product_data = await scraper.scrape_product(product)
            
            if product_data:
                successful.append(product_data)
                print(f"  ✓ Success")
            else:
                failed.append(product)
                print(f"  ✗ No data extracted")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed.append(product)
            continue
    
    # Save results
    save_json(successful, output_dir / "successful_scrapes.json")
    save_json(failed, output_dir / "failed_scrapes.json")
    
    print(f"\n✓ Scraping complete!")
    print(f"  Successful: {len(successful)}")
    print(f"  Failed: {len(failed)}")

# Run
if __name__ == "__main__":
    products = [
        {"title": "Product 1", "url": "https://example.com/p1"},
        {"title": "Product 2", "url": "https://example.com/p2"}
    ]
    asyncio.run(robust_product_scraping(products))
```

---

## Best Practices

### Configuration Management

```python
# Always validate configuration after loading
from config.config_loader import ConfigLoader

client_name = "myclient"

# Validate before use
is_valid, issues = ConfigLoader.validate_client_config(client_name)

if not is_valid:
    print("Configuration issues:")
    for issue in issues:
        print(f"  - {issue}")
    exit(1)

# Load if valid
config = ConfigLoader.load_client_config(client_name)
```

### Rate Limiting

```python
# Always use configurable rate limiting
from core.utils import get_rate_limit_delay
import asyncio

for item in items:
    await process_item(item)
    
    # Use config-based delay
    delay = get_rate_limit_delay(config)
    await asyncio.sleep(delay)
```

### Error Recovery

```python
# Implement retry logic for critical operations
async def scrape_with_retry(scraper, product, max_retries=3):
    """Scrape with automatic retry"""
    
    for attempt in range(1, max_retries + 1):
        try:
            data = await scraper.scrape_product(product)
            if data:
                return data
        except Exception as e:
            if attempt < max_retries:
                print(f"  Retry {attempt}/{max_retries}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"  Failed after {max_retries} attempts")
                return None
```

### Resource Management

```python
# Always use context managers for file operations
from pathlib import Path
from core.utils import save_json, load_json

# Prefer utility functions that handle context properly
data = load_json(Path("input.json"))
save_json(data, Path("output.json"))

# When using files directly
with open("file.txt", "r") as f:
    content = f.read()
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-05 | Initial API reference documentation |

---

## Related Documentation

- [Client Deployment Guide](CLIENT_DEPLOYMENT_GUIDE.md) - Step-by-step deployment guide
- [Configuration Guide](configuration-guide.md) - Complete configuration reference
- [Extraction Strategies](extraction-strategies.md) - CSS selector guide
- [Architecture Guide](architecture.md) - System architecture overview
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

---

**For questions or issues, please refer to the troubleshooting guide or create an issue in the repository.**
