"""
Product detail scraper module for Agar scraper
Scrapes detailed information from individual product pages
ONLY handles CSS-based extraction (name, image, overview, description, SKU)
For PDF links, use product_pdf_scraper.py
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from config import BASE_URL, USER_AGENT, DETAIL_PAGE_TIMEOUT, RATE_LIMIT_DELAY
from utils import save_json, load_json, clean_product_name, save_screenshot, sanitize_filename

class ProductScraper:
    """Scrape product details (NO PDF EXTRACTION - use product_pdf_scraper.py for PDFs)"""
    
    def __init__(self, output_dir: Path = None, save_screenshots: bool = True):
        self.output_dir = output_dir or Path(".")
        self.base_url = BASE_URL
        self.save_screenshots = save_screenshots
    
    async def scrape_product_details(self, product_info: Dict) -> Optional[Dict]:
        """Scrape product details using CSS selectors (name, description, images, etc.)"""
        
        # Schema for product details ONLY
        product_detail_schema = {
            "name": "Product Details",
            "baseSelector": "body",
            "fields": [
                {"name": "product_name", "selector": "main h1.product_title, div.product h1.product_title, h1.product_title.entry-title", "type": "text"},
                {"name": "main_image", "selector": "img.wp-post-image, .woocommerce-product-gallery__wrapper img:first-child", "type": "attribute", "attribute": "src"},
                {"name": "gallery_images", "selector": ".woocommerce-product-gallery img", "type": "list", "attribute": "src"},
                {"name": "product_overview", "selector": ".woocommerce-product-details__short-description", "type": "text"},
                {"name": "product_sku", "selector": "span.sku", "type": "text"},
                {"name": "product_categories", "selector": "span.posted_in a", "type": "list"},
                {"name": "product_description", "selector": "#tab-description", "type": "text"}
            ]
        }
        
        # Simple CSS extraction - NO JavaScript
        extraction_strategy = JsonCssExtractionStrategy(schema=product_detail_schema)
        
        config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.BYPASS,
            screenshot=self.save_screenshots,
            wait_for="css:.product_title",
            page_timeout=DETAIL_PAGE_TIMEOUT,
            user_agent=USER_AGENT,
            delay_before_return_html=2.0
        )
        
        async with AsyncWebCrawler() as crawler:
            print(f"  → Scraping product details (CSS)...")
            
            try:
                result = await crawler.arun(product_info["url"], config=config)
                
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
            
            # Rate limiting
            if i < len(products):
                await asyncio.sleep(RATE_LIMIT_DELAY)
        
        return successful


async def main():
    """Standalone execution"""
    parser = argparse.ArgumentParser(
        description="Agar Product Detail Scraper - CSS-based extraction only"
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
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    (output_dir / "products").mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print(" AGAR PRODUCT DETAIL SCRAPER (CSS ONLY)".center(60))
    print("="*60)
    
    scraper = ProductScraper(output_dir=output_dir, save_screenshots=args.screenshots)
    
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
