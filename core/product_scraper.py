"""
3DN Scraper Template - Product Detail Scraper Module
Version: 1.0.0

Scrapes detailed information from individual product pages using CSS extraction.
Works with any client configuration through the config loader system.

ONLY handles CSS-based extraction (name, image, overview, description, SKU)
For PDF links, use product_pdf_scraper.py
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Optional, List, Type
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from config.config_loader import ConfigLoader
from config.base_config import BaseConfig
from core.utils import save_json, load_json, clean_product_name, save_screenshot, sanitize_filename

class ProductScraper:
    """Scrape product details (NO PDF EXTRACTION - use product_pdf_scraper.py for PDFs)
    
    This scraper is client-agnostic and uses the config loader system to work
    with any client deployment.
    """
    
    def __init__(self, config: Type[BaseConfig], extraction_strategy, 
                 output_dir: Path = None, save_screenshots: bool = True):
        """Initialize product scraper with client configuration
        
        Args:
            config: Client configuration class
            extraction_strategy: Client extraction strategy class
            output_dir: Output directory for scraped data
            save_screenshots: Whether to save page screenshots
        """
        self.config = config
        self.extraction_strategy = extraction_strategy
        self.output_dir = output_dir or Path(".")
        self.base_url = config.BASE_URL
        self.save_screenshots = save_screenshots
    
    async def scrape_product_details(self, product_info: Dict) -> Optional[Dict]:
        """Scrape product details using client-specific CSS selectors
        
        Args:
            product_info: Dictionary with product information including URL
            
        Returns:
            Dictionary with extracted product data or None if extraction failed
        """
        
        # Get extraction schema from client strategy
        product_detail_schema = self.extraction_strategy.get_product_detail_schema()
        
        # Simple CSS extraction - NO JavaScript
        extraction_strategy = JsonCssExtractionStrategy(schema=product_detail_schema)
        
        # Use client-specific configuration
        crawler_config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.BYPASS,
            screenshot=self.save_screenshots,
            wait_for="css:.product_title",
            page_timeout=self.config.DETAIL_PAGE_TIMEOUT,
            user_agent=self.config.USER_AGENT,
            delay_before_return_html=2.0
        )
        
        async with AsyncWebCrawler() as crawler:
            print(f"  → Scraping product details (CSS)...")
            
            try:
                result = await crawler.arun(product_info["url"], config=crawler_config)
                
                if result.success and result.extracted_content:
                    try:
                        data = json.loads(result.extracted_content)
                        if isinstance(data, list):
                            data = data[0] if data else {}
                        
                        # Save screenshot if available
                        if self.save_screenshots and result.screenshot:
                            product_name = clean_product_name(data.get("product_name", product_info.get("title", "Unknown")))
                            screenshot_path = self.output_dir / "screenshots" / f"{sanitize_filename(product_name)}.png"
                            screenshot_path.parent.mkdir(exist_ok=True)
                            save_screenshot(result.screenshot, screenshot_path)
                        
                        print(f"  ✓ Extracted product details")
                        return data
                    except Exception as e:
                        print(f"  ✗ Error parsing product details: {e}")
                        return None
                
                print(f"  ✗ No content extracted")
                return None
                    
            except Exception as e:
                print(f"  ✗ Error scraping product details: {e}")
                return None
    
    async def scrape_product(self, product_info: Dict) -> Optional[Dict]:
        """Main scraper method - extracts product details only"""
        
        print(f"\n  → Product: {product_info.get('title', 'Unknown Product')}")
        
        # Get product details with CSS extraction
        css_data = await self.scrape_product_details(product_info)
        if not css_data:
            print(f"  ✗ Failed to extract product details")
            return None
        
        # Format the product data
        product_data = self.format_product_data(css_data, product_info)
        
        return product_data
    
    def format_product_data(self, css_data: Dict, product_info: Dict) -> Dict:
        """Format scraped product data (NO PDF URLs - use product_pdf_scraper.py)"""
        
        # Get product image with fallbacks
        product_image = ""
        if css_data.get("main_image"):
            product_image = css_data["main_image"]
        elif css_data.get("gallery_images") and len(css_data["gallery_images"]) > 0:
            product_image = css_data["gallery_images"][0]
        elif product_info.get("image"):
            product_image = product_info["image"]
        
        # Get clean product name
        product_name = clean_product_name(css_data.get("product_name", ""))
        if not product_name:
            product_name = product_info.get("title", "Unknown")
        
        # Build product data (NO PDF URLS)
        return {
            "product_name": product_name,
            "product_url": product_info.get("url", ""),
            "product_image_url": product_image,
            "product_overview": css_data.get("product_overview", ""),
            "product_description": css_data.get("product_description", ""),
            "product_skus": css_data.get("product_sku", ""),
            "product_categories": css_data.get("product_categories", []) or [product_info.get("category", "")],
            "scraped_at": datetime.now().isoformat(),
            "category": product_info.get("category", ""),
            "category_slug": product_info.get("category_slug", "")
        }
    
    async def scrape_products(self, products: List[Dict]) -> List[Dict]:
        """Scrape multiple products"""
        successful = []
        failed = []
        
        for i, product in enumerate(products, 1):
            print(f"\n[Product {i}/{len(products)}]")
            
            product_data = await self.scrape_product(product)
            
            if product_data:
                successful.append(product_data)
                
                # Save individual product
                if self.output_dir:
                    filename = sanitize_filename(product_data["product_name"])
                    save_json(product_data, self.output_dir / "products" / f"{filename}.json")
                    print(f"  ✓ Saved product details")
            else:
                failed.append(product)
            
            # Rate limiting - use client config
            if i < len(products):
                await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
        
        return successful


async def main():
    """Standalone execution for product scraping"""
    parser = argparse.ArgumentParser(
        description="3DN Scraper Template - Product Detail Scraper (CSS-based extraction)"
    )
    
    parser.add_argument(
        '--client', '-c',
        type=str,
        required=True,
        help='Client name (e.g., agar)'
    )
    
    parser.add_argument(
        '--url',
        type=str,
        help='Single product URL to scrape'
    )
    
    parser.add_argument(
        '--products', '-p',
        type=str,
        help='Path to products JSON file'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=".",
        help='Output directory'
    )
    
    parser.add_argument(
        '--screenshots', '-s',
        action='store_true',
        default=True,
        help='Save screenshots'
    )
    
    args = parser.parse_args()
    
    # Load client configuration
    try:
        config = ConfigLoader.load_client_config(args.client)
        strategies = ConfigLoader.load_client_strategies(args.client)
        
        if strategies is None:
            print(f"❌ Error: No extraction strategies found for client '{args.client}'")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error loading client configuration: {e}")
        sys.exit(1)
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    (output_dir / "products").mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print(f" 3DN PRODUCT SCRAPER - {config.CLIENT_FULL_NAME}".center(60))
    print("="*60)
    
    scraper = ProductScraper(
        config=config,
        extraction_strategy=strategies,
        output_dir=output_dir, 
        save_screenshots=args.screenshots
    )
    
    if args.url:
        # Single product mode
        product_info = {
            "title": "Product",
            "url": args.url,
            "category": "Unknown",
            "category_slug": "unknown"
        }
        product_data = await scraper.scrape_product(product_info)
        if product_data:
            filename = sanitize_filename(product_data["product_name"])
            save_json(product_data, output_dir / f"{filename}.json")
            print(f"\n✓ Saved to {filename}.json")
    elif args.products:
        # Multiple products mode
        products = load_json(Path(args.products))
        successful = await scraper.scrape_products(products)
        
        # Save summary
        save_json(successful, output_dir / "scraped_products.json")
        print(f"\n✓ Scraped {len(successful)}/{len(products)} products")
    else:
        print("❌ Please provide --url or --products")
    
    print("="*60)


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        print(f"❌ Error: Python 3.11+ required (you have {sys.version})")
        sys.exit(1)
    
    asyncio.run(main())
