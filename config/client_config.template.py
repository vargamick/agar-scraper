"""
3DN Scraper Template - Client Configuration Template
Version: 1.0.0

Copy this file to config/clients/{your_client_name}/client_config.py
and customize the settings for your specific client deployment.

This template provides a starting point for configuring a new client.
"""

from config.base_config import BaseConfig
from typing import Dict, List


class ClientConfig(BaseConfig):
    """Client-specific configuration
    
    Override BaseConfig settings to customize for your client.
    Only include settings that differ from the base configuration.
    """
    
    # ============================================================================
    # REQUIRED: Client Identification
    # ============================================================================
    
    CLIENT_NAME = "yourclient"  # Short identifier (lowercase, no spaces)
    CLIENT_FULL_NAME = "Your Client Company Name"
    
    # ============================================================================
    # REQUIRED: Website Configuration
    # ============================================================================
    
    BASE_URL = "https://yourclient.com"
    
    # ============================================================================
    # REQUIRED: URL Patterns
    # ============================================================================
    
    # How category pages are accessed
    # Example: "/category/{slug}/" or "/products/{slug}/" or "/shop/{slug}/"
    CATEGORY_URL_PATTERN = "/category/{slug}/"
    
    # How product detail pages are accessed
    # Example: "/product/{slug}/" or "/item/{slug}/" or "/p/{slug}/"
    PRODUCT_URL_PATTERN = "/product/{slug}/"
    
    # ============================================================================
    # REQUIRED: Output Configuration
    # ============================================================================
    
    OUTPUT_PREFIX = "YourClientScrape"  # Prefix for output directories
    BASE_OUTPUT_DIR = "yourclient_scrapes"  # Base output directory name
    
    # ============================================================================
    # NOTE: Categories are Discovered Dynamically
    # ============================================================================
    
    # Categories are automatically discovered from the website at runtime.
    # No hardcoded category lists are needed or supported.
    # The CategoryScraper will discover all available categories from the site.
    
    # ============================================================================
    # OPTIONAL: PDF/Document Configuration
    # ============================================================================
    
    # Does your client have SDS (Safety Data Sheet) documents?
    HAS_SDS_DOCUMENTS = False
    
    # Does your client have PDS (Product Data Sheet) documents?
    HAS_PDS_DOCUMENTS = False
    
    # Field names for PDF URLs (if applicable)
    SDS_FIELD_NAME = "sds_url"
    PDS_FIELD_NAME = "pds_url"
    
    # ============================================================================
    # OPTIONAL: Product Schema Mapping
    # ============================================================================
    
    # Customize field names in output JSON if needed
    PRODUCT_SCHEMA = {
        "name_field": "product_name",
        "url_field": "product_url",
        "image_field": "product_image_url",
        "overview_field": "product_overview",
        "description_field": "product_description",
        "sku_field": "product_skus",
        "categories_field": "product_categories"
    }
    
    # ============================================================================
    # OPTIONAL: Timeout Overrides (if default timeouts don't work)
    # ============================================================================
    
    # Uncomment and adjust if pages load slowly or timeout
    # PAGE_TIMEOUT = 90000  # 90 seconds
    # DETAIL_PAGE_TIMEOUT = 45000  # 45 seconds
    
    # ============================================================================
    # OPTIONAL: Rate Limiting (if getting blocked or need slower scraping)
    # ============================================================================
    
    # Uncomment and adjust if needed
    # RATE_LIMIT_DELAY = 3  # Seconds between requests
    
    # ============================================================================
    # OPTIONAL: Test Mode Limits (for faster testing during setup)
    # ============================================================================
    
    # Uncomment and adjust if needed
    # TEST_CATEGORY_LIMIT = 3  # Number of categories to test
    # TEST_PRODUCT_LIMIT = 10  # Number of products per category to test
    
    # ============================================================================
    # OPTIONAL: Retry Configuration
    # ============================================================================
    
    # Uncomment and adjust if connection is unreliable
    # MAX_RETRIES = 5
    # RETRY_DELAY = 10  # Seconds between retries


# ============================================================================
# DEPLOYMENT CHECKLIST
# ============================================================================
"""
Before running your scraper, ensure you have:

1. [ ] Set CLIENT_NAME and CLIENT_FULL_NAME
2. [ ] Set BASE_URL to your client's website
3. [ ] Configured CATEGORY_URL_PATTERN (browse site to find pattern)
4. [ ] Configured PRODUCT_URL_PATTERN (browse site to find pattern)
5. [ ] Set OUTPUT_PREFIX and BASE_OUTPUT_DIR
6. [ ] Created extraction_strategies.py with CSS selectors
7. [ ] Tested connection: python scripts/test_connection.py --client yourclient
8. [ ] Validated config: python scripts/validate_config.py --client yourclient
9. [ ] Run test scrape: python main.py --client yourclient --test

Note: Categories are discovered dynamically from the website - no manual category
      configuration is required. The scraper will automatically find all categories.

See docs/configuration-guide.md for detailed setup instructions.
"""
