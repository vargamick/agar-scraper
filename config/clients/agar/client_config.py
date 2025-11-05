"""
3DN Scraper Template - Agar Client Configuration
Client: Agar Cleaning Systems
Website: https://agar.com.au

This is the first example client deployment of the 3DN Scraper Template.
"""

from config.base_config import BaseConfig
from typing import Dict, List


class ClientConfig(BaseConfig):
    """Agar Cleaning Systems client configuration"""
    
    # ============================================================================
    # Client Identification
    # ============================================================================
    
    CLIENT_NAME = "agar"
    CLIENT_FULL_NAME = "Agar Cleaning Systems"
    
    # ============================================================================
    # Website Configuration
    # ============================================================================
    
    BASE_URL = "https://agar.com.au"
    
    # ============================================================================
    # URL Patterns
    # ============================================================================
    
    CATEGORY_URL_PATTERN = "/product-category/{slug}/"
    PRODUCT_URL_PATTERN = "/product/{slug}/"
    
    # ============================================================================
    # Output Configuration
    # ============================================================================
    
    OUTPUT_PREFIX = "AgarScrape"
    BASE_OUTPUT_DIR = "agar_scrapes"
    
    # ============================================================================
    # Known Categories
    # ============================================================================
    
    KNOWN_CATEGORIES = [
        "toilet-bathroom-cleaners",
        "green-cleaning-products", 
        "vehicle-cleaning",
        "hard-floor-care",
        "specialty-cleaning",
        "disinfectants-antibacterials",
        "kitchen-cleaners",
        "carpet-upholstery",
        "laundry-products",
        "air-fresheners",
        "hand-soaps-sanitisers",
        "all-purpose-floor-cleaners",
        "chlorinated-cleaners-sanitisers",
        "floor-care"
    ]
    
    # ============================================================================
    # PDF/Document Configuration
    # ============================================================================
    
    HAS_SDS_DOCUMENTS = True
    HAS_PDS_DOCUMENTS = True
    SDS_FIELD_NAME = "sds_url"
    PDS_FIELD_NAME = "pds_url"
    
    # ============================================================================
    # Product Schema Mapping
    # ============================================================================
    
    PRODUCT_SCHEMA = {
        "name_field": "product_name",
        "url_field": "product_url",
        "image_field": "product_image_url",
        "overview_field": "product_overview",
        "description_field": "product_description",
        "sku_field": "product_skus",
        "categories_field": "product_categories"
    }
