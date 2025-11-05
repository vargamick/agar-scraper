"""
3DN Scraper Template - Agar Extraction Strategies
Client: Agar Cleaning Systems
Website: https://agar.com.au

This file contains CSS selectors and extraction logic specific to Agar's website.
"""

from typing import Dict, List, Optional


class AgarExtractionStrategy:
    """CSS selectors and extraction logic for Agar Cleaning Systems website"""
    
    # ============================================================================
    # Category Page Selectors
    # ============================================================================
    
    CATEGORY_SELECTORS = {
        # Product list on category pages
        "products": "ul.products li.product",
        "product_link": "a.woocommerce-LoopProduct-link",
        "product_name": "h2.woocommerce-loop-product__title",
        "product_image": "img.attachment-woocommerce_thumbnail",
        
        # Pagination (if needed)
        "pagination": "nav.woocommerce-pagination",
        "next_page": "a.next.page-numbers",
    }
    
    # ============================================================================
    # Product Detail Page Selectors
    # ============================================================================
    
    PRODUCT_SELECTORS = {
        # Main product information
        "name": "main h1.product_title, div.product h1.product_title, h1.product_title.entry-title",
        "main_image": "img.wp-post-image, .woocommerce-product-gallery__wrapper img:first-child",
        "gallery_images": ".woocommerce-product-gallery img",
        
        # Product details
        "overview": ".woocommerce-product-details__short-description",
        "description": "#tab-description",
        "sku": "span.sku",
        "categories": "span.posted_in a",
        
        # Additional product information (if available)
        "price": "span.woocommerce-Price-amount",
        "stock_status": "p.stock",
    }
    
    # ============================================================================
    # PDF/Document Selectors
    # ============================================================================
    
    PDF_SELECTORS = {
        # SDS (Safety Data Sheet) link
        "sds_link": "a[href*='SDS'], a[href*='sds'], a:contains('SDS'), a:contains('Safety Data Sheet')",
        
        # PDS (Product Data Sheet) link
        "pds_link": "a[href*='PDS'], a[href*='pds'], a:contains('PDS'), a:contains('Product Data Sheet')",
        
        # Document section container
        "document_section": "div.product-documents, div.woocommerce-tabs, #tab-additional_information",
        
        # All document links
        "all_document_links": "a[href$='.pdf'], a[href*='.pdf']",
    }
    
    # ============================================================================
    # JSON Schema for CSS Extraction
    # ============================================================================
    
    @classmethod
    def get_product_detail_schema(cls) -> Dict:
        """Get JSON schema for product detail extraction
        
        This schema is used with JsonCssExtractionStrategy for extracting
        product details from Agar product pages.
        
        Returns:
            Dictionary with extraction schema
        """
        return {
            "name": "Product Details",
            "baseSelector": "body",
            "fields": [
                {
                    "name": "product_name",
                    "selector": cls.PRODUCT_SELECTORS["name"],
                    "type": "text"
                },
                {
                    "name": "main_image",
                    "selector": cls.PRODUCT_SELECTORS["main_image"],
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "gallery_images",
                    "selector": cls.PRODUCT_SELECTORS["gallery_images"],
                    "type": "list",
                    "attribute": "src"
                },
                {
                    "name": "product_overview",
                    "selector": cls.PRODUCT_SELECTORS["overview"],
                    "type": "text"
                },
                {
                    "name": "product_sku",
                    "selector": cls.PRODUCT_SELECTORS["sku"],
                    "type": "text"
                },
                {
                    "name": "product_categories",
                    "selector": cls.PRODUCT_SELECTORS["categories"],
                    "type": "list"
                },
                {
                    "name": "product_description",
                    "selector": cls.PRODUCT_SELECTORS["description"],
                    "type": "text"
                }
            ]
        }
    
    @classmethod
    def get_category_schema(cls) -> Dict:
        """Get JSON schema for category page extraction
        
        This schema is used with JsonCssExtractionStrategy for extracting
        product listings from Agar category pages.
        
        Returns:
            Dictionary with extraction schema
        """
        return {
            "name": "Category Products",
            "baseSelector": cls.CATEGORY_SELECTORS["products"],
            "fields": [
                {
                    "name": "product_name",
                    "selector": cls.CATEGORY_SELECTORS["product_name"],
                    "type": "text"
                },
                {
                    "name": "product_url",
                    "selector": cls.CATEGORY_SELECTORS["product_link"],
                    "type": "attribute",
                    "attribute": "href"
                },
                {
                    "name": "product_image",
                    "selector": cls.CATEGORY_SELECTORS["product_image"],
                    "type": "attribute",
                    "attribute": "src"
                }
            ]
        }
    
    # ============================================================================
    # Custom Extraction Methods (if needed)
    # ============================================================================
    
    @staticmethod
    def extract_pdf_links(html: str) -> Dict[str, Optional[str]]:
        """Extract PDF links from product page HTML
        
        This is a placeholder for custom PDF extraction logic if needed.
        The basic CSS selectors should work for most cases.
        
        Args:
            html: Product page HTML
            
        Returns:
            Dictionary with 'sds_url' and 'pds_url' keys
        """
        # Default implementation uses CSS selectors
        # Override this method if complex logic is needed
        return {
            "sds_url": None,
            "pds_url": None
        }
    
    @staticmethod
    def clean_product_data(data: Dict) -> Dict:
        """Clean and normalize extracted product data
        
        This is a placeholder for custom data cleaning logic if needed.
        
        Args:
            data: Raw extracted data
            
        Returns:
            Cleaned data dictionary
        """
        # Default implementation returns data as-is
        # Override this method if custom cleaning is needed
        return data
