"""
3DN Scraper Template - Base Extraction Strategy Interface
Version: 1.0.0

This module defines the interface that all client extraction strategies should follow.
Client-specific extraction strategies can inherit from or implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseExtractionStrategy(ABC):
    """Abstract base class for extraction strategies
    
    Client-specific extraction strategies should inherit from this class
    and implement the required methods.
    """
    
    # ============================================================================
    # Required: Selector Definitions
    # ============================================================================
    
    @property
    @abstractmethod
    def CATEGORY_SELECTORS(self) -> Dict[str, str]:
        """CSS selectors for category pages
        
        Should return a dictionary with keys:
        - products: Selector for product list items
        - product_link: Selector for product URLs
        - product_name: Selector for product names
        - product_image: Selector for product images (optional)
        - pagination: Selector for pagination (optional)
        - next_page: Selector for next page link (optional)
        """
        pass
    
    @property
    @abstractmethod
    def PRODUCT_SELECTORS(self) -> Dict[str, str]:
        """CSS selectors for product detail pages
        
        Should return a dictionary with keys:
        - name: Product name selector
        - main_image: Main product image selector
        - gallery_images: Gallery images selector (optional)
        - overview: Product overview/short description selector
        - description: Full product description selector
        - sku: Product SKU selector (optional)
        - categories: Product categories selector (optional)
        """
        pass
    
    @property
    def PDF_SELECTORS(self) -> Dict[str, str]:
        """CSS selectors for PDF/document links
        
        Optional. Return empty dict if client doesn't have PDFs.
        
        Can include keys:
        - sds_link: SDS document link selector
        - pds_link: PDS document link selector
        - document_section: Document container selector
        - all_document_links: All PDF links selector
        """
        return {}
    
    # ============================================================================
    # Required: Schema Generation
    # ============================================================================
    
    @abstractmethod
    def get_product_detail_schema(self) -> Dict:
        """Generate JSON extraction schema for product detail pages
        
        Returns:
            Dictionary with extraction schema compatible with JsonCssExtractionStrategy
        """
        pass
    
    @abstractmethod
    def get_category_schema(self) -> Dict:
        """Generate JSON extraction schema for category pages
        
        Returns:
            Dictionary with extraction schema compatible with JsonCssExtractionStrategy
        """
        pass
    
    # ============================================================================
    # Optional: Custom Extraction Logic
    # ============================================================================
    
    def extract_pdf_links(self, html: str) -> Dict[str, Optional[str]]:
        """Extract PDF links from HTML
        
        Override this method if custom PDF extraction logic is needed.
        
        Args:
            html: Product page HTML
            
        Returns:
            Dictionary with PDF URLs (e.g., {'sds_url': '...', 'pds_url': '...'})
        """
        return {
            "sds_url": None,
            "pds_url": None
        }
    
    def clean_product_data(self, data: Dict) -> Dict:
        """Clean and normalize extracted product data
        
        Override this method if custom data cleaning is needed.
        
        Args:
            data: Raw extracted data
            
        Returns:
            Cleaned data dictionary
        """
        return data
    
    def extract_category_data(self, html: str) -> List[Dict]:
        """Extract product listings from category page
        
        Override this method if custom category extraction is needed.
        
        Args:
            html: Category page HTML
            
        Returns:
            List of product dictionaries
        """
        return []
    
    def extract_product_details(self, html: str) -> Dict:
        """Extract product details from product page
        
        Override this method if custom product extraction is needed.
        
        Args:
            html: Product page HTML
            
        Returns:
            Product details dictionary
        """
        return {}


class SimpleCSSStrategy(BaseExtractionStrategy):
    """Simple CSS-based extraction strategy implementation
    
    This is a concrete implementation that uses basic CSS selectors.
    Client strategies can inherit from this and override as needed.
    """
    
    def __init__(self, 
                 category_selectors: Dict[str, str],
                 product_selectors: Dict[str, str],
                 pdf_selectors: Dict[str, str] = None):
        """Initialize with selector dictionaries
        
        Args:
            category_selectors: CSS selectors for category pages
            product_selectors: CSS selectors for product pages
            pdf_selectors: CSS selectors for PDF links (optional)
        """
        self._category_selectors = category_selectors
        self._product_selectors = product_selectors
        self._pdf_selectors = pdf_selectors or {}
    
    @property
    def CATEGORY_SELECTORS(self) -> Dict[str, str]:
        return self._category_selectors
    
    @property
    def PRODUCT_SELECTORS(self) -> Dict[str, str]:
        return self._product_selectors
    
    @property
    def PDF_SELECTORS(self) -> Dict[str, str]:
        return self._pdf_selectors
    
    def get_product_detail_schema(self) -> Dict:
        """Generate product detail extraction schema"""
        fields = []
        
        # Build schema from selectors
        selector_mapping = {
            "name": ("product_name", "text"),
            "main_image": ("main_image", "attribute", "src"),
            "gallery_images": ("gallery_images", "list", "src"),
            "overview": ("product_overview", "text"),
            "description": ("product_description", "text"),
            "sku": ("product_sku", "text"),
            "categories": ("product_categories", "list"),
        }
        
        for selector_key, field_config in selector_mapping.items():
            if selector_key in self._product_selectors:
                field = {
                    "name": field_config[0],
                    "selector": self._product_selectors[selector_key],
                    "type": field_config[1]
                }
                if len(field_config) > 2:
                    field["attribute"] = field_config[2]
                fields.append(field)
        
        return {
            "name": "Product Details",
            "baseSelector": "body",
            "fields": fields
        }
    
    def get_category_schema(self) -> Dict:
        """Generate category extraction schema"""
        fields = []
        
        # Build schema from selectors
        selector_mapping = {
            "product_name": ("product_name", "text"),
            "product_link": ("product_url", "attribute", "href"),
            "product_image": ("product_image", "attribute", "src"),
        }
        
        for selector_key, field_config in selector_mapping.items():
            if selector_key in self._category_selectors:
                field = {
                    "name": field_config[0],
                    "selector": self._category_selectors[selector_key],
                    "type": field_config[1]
                }
                if len(field_config) > 2:
                    field["attribute"] = field_config[2]
                fields.append(field)
        
        base_selector = self._category_selectors.get("products", "body")
        
        return {
            "name": "Category Products",
            "baseSelector": base_selector,
            "fields": fields
        }
