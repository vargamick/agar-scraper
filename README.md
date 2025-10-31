# Agar Scraper - Modular Web Scraper for Agar Cleaning Products

A modular, production-ready web scraper for extracting product information from agar.com.au.

## Features

- **Modular Architecture**: Separate modules for different scraping tasks
- **Standalone Execution**: Each module can run independently
- **Run Management**: Timestamped directories for each scraping session
- **Test Mode**: Limited scraping for testing and development
- **Comprehensive Reporting**: Detailed statistics and download tracking
- **Screenshot Capture**: Product page screenshots for verification

## Installation

```bash
# Requires Python 3.11+
pip install crawl4ai

# Clone or download the agar_scraper directory
cd agar_scraper
```

## Usage

### Complete Workflow

Run the complete scraping workflow:

```bash
# Test mode (limited scraping)
python main.py --test

# Full mode (complete scraping)
python main.py --full

# Custom output directory
python main.py --full -o /path/to/output
```

### Individual Modules

Each module can be run independently:

#### 1. Category Discovery

```bash
# Discover all categories
python category_scraper.py -o ./output

# Test mode (limited categories)
python category_scraper.py --test -o ./output
```

#### 2. Product URL Collection

```bash
# Collect from all categories (requires categories.json)
python product_collector.py -c categories.json -o ./output

# Collect from single category
python product_collector.py --category toilet-bathroom-cleaners -o ./output

# Test mode (limited products)
python product_collector.py --test -c categories.json -o ./output
```

#### 3. Product Detail Scraping

```bash
# Scrape single product
python product_scraper.py --url https://agar.com.au/product/all-fresh/ -o ./output

# Scrape multiple products (requires products.json)
python product_scraper.py -p products.json -o ./output

# Without screenshots
python product_scraper.py -p products.json -o ./output --no-screenshots
```

## Output Structure

```
agar_scrapes/
└── AgarScrape_20251031_120000/
    ├── run_metadata.json          # Run information
    ├── categories.json             # All categories
    ├── all_products_list.json     # All product URLs
    ├── all_products_data.json     # All scraped products
    ├── categories/
    │   └── [category-slug]/
    │       ├── products_list.json # Products in category
    │       ├── [product].json     # Individual product data
    │       └── [product]_screenshot.png
    ├── products/                  # All products (duplicated)
    ├── screenshots/               # All screenshots
    ├── logs/                      # Checkpoints and logs
    └── reports/
        └── final_report.json      # Summary statistics
```

## Product Data Schema

Each product JSON contains:

```json
{
  "product_name": "Product Name",
  "product_url": "https://...",
  "product_image_url": "https://...",
  "product_overview": "Short description",
  "product_description": "Full description",
  "product_skus": "SKU123",
  "product_categories": ["Category"],
  "sds_url": "https://.../SDS.pdf",
  "pds_url": "https://.../PDS.pdf",
  "scraped_at": "2025-10-31T12:00:00",
  "category": "Category Name",
  "category_slug": "category-slug"
}
```

## Configuration

Edit `config.py` to modify:
- Base URL
- Test mode limits
- Timeouts and delays
- User agent
- Known categories

## Requirements

- Python 3.11+
- crawl4ai library
- asyncio support

## Error Handling

- Automatic retries with different extraction strategies
- Checkpoint saving for resume capability
- Detailed error reporting in logs
- Graceful interruption handling (Ctrl+C)

## Performance

- Rate limiting between requests (2 seconds default)
- Concurrent processing where applicable
- Cache bypassing for fresh data
- Timeout management for stuck pages

## Troubleshooting

1. **No products found**: Site structure may have changed, check extraction strategies
2. **Missing downloads**: SDS/PDS links may require JavaScript interaction
3. **Timeout errors**: Increase PAGE_TIMEOUT in config.py
4. **Rate limiting**: Adjust RATE_LIMIT_DELAY in config.py

## License

For internal use only. Respect website terms of service and robots.txt.
