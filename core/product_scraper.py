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


def _classify_crawl_failure(result) -> tuple:
    """Classify a Crawl4AI failure result. Returns (category, diagnostics_dict)."""
    status_code = getattr(result, 'status_code', None)
    error_msg = getattr(result, 'error_message', '') or ''
    response_headers = getattr(result, 'response_headers', {}) or {}
    html = getattr(result, 'html', '') or ''

    notable_headers = {
        k: v for k, v in response_headers.items()
        if any(s in k.lower() for s in ('cf-', 'x-cache', 'server', 'x-powered-by', 'retry-after'))
    }

    header_keys_lower = {k.lower() for k in response_headers}
    html_lower = html.lower()
    is_cf_block = (
        bool({'cf-ray', 'cf-mitigated'} & header_keys_lower) or
        any(s in html_lower for s in ('cloudflare', 'cf-browser-verification', 'error 1020', 'just a moment'))
    )

    if is_cf_block:
        category = 'CLOUDFLARE_BLOCK'
    elif status_code == 429:
        category = 'RATE_LIMITED'
    elif status_code == 403:
        category = 'HTTP_403_FORBIDDEN'
    elif status_code and status_code >= 500:
        category = 'SERVER_ERROR'
    elif 'timeout' in error_msg.lower():
        category = 'TIMEOUT'
    elif getattr(result, 'success', False) and not getattr(result, 'extracted_content', None):
        category = 'CSS_EXTRACTION_FAILED'
    else:
        category = 'UNKNOWN_FAILURE'

    diagnostics = {
        'status_code': status_code,
        'error_message': error_msg,
        'html_length': len(html),
        'html_preview': html[:300].replace('\n', ' ') if html else '',
        'notable_headers': notable_headers,
    }
    return category, diagnostics

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
        """Scrape product details using client-specific CSS selectors.

        Retries up to MAX_RETRIES times with exponential backoff for transient
        failures (timeouts, server errors, rate limiting, CSS not found).
        Logs diagnostic detail on every failure to surface anti-bot signals.
        """
        product_detail_schema = self.extraction_strategy.get_product_detail_schema()
        extraction_strategy = JsonCssExtractionStrategy(schema=product_detail_schema)

        crawler_config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.BYPASS,
            screenshot=self.save_screenshots,
            wait_for="css:.product_title",
            page_timeout=self.config.DETAIL_PAGE_TIMEOUT,
            user_agent=self.config.USER_AGENT,
            delay_before_return_html=2.0
        )

        max_retries = max(1, getattr(self.config, 'MAX_RETRIES', 3))
        retry_delay = getattr(self.config, 'RETRY_DELAY', 5)

        for attempt in range(1, max_retries + 1):
            label = f"CSS, attempt {attempt}/{max_retries}" if attempt > 1 else "CSS"
            print(f"  → Scraping product details ({label})...")

            result = None
            try:
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(product_info["url"], config=crawler_config)
            except Exception as crawl_exc:
                exc_str = str(crawl_exc)
                category = 'TIMEOUT' if 'timeout' in exc_str.lower() else 'CRAWL_EXCEPTION'
                print(f"  ✗ [{category}] {exc_str[:300]}")
                if attempt < max_retries:
                    backoff = retry_delay * (2 ** (attempt - 1))
                    print(f"  ↻ Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                    continue
                raise

            # Crawl completed — check for success
            if result.success and result.extracted_content:
                try:
                    data = json.loads(result.extracted_content)
                    if isinstance(data, list):
                        data = data[0] if data else {}

                    if self.save_screenshots and result.screenshot:
                        product_name = clean_product_name(data.get("product_name", product_info.get("title", "Unknown")))
                        screenshot_path = self.output_dir / "screenshots" / f"{sanitize_filename(product_name)}.png"
                        screenshot_path.parent.mkdir(exist_ok=True)
                        save_screenshot(result.screenshot, screenshot_path)

                    print(f"  ✓ Extracted product details")
                    return data
                except json.JSONDecodeError as e:
                    print(f"  ✗ Error parsing product details JSON: {e}")
                    raise ValueError(f"Failed to parse product details JSON: {e}") from e
                except Exception as e:
                    print(f"  ✗ Error processing product details: {e}")
                    raise

            # Crawl failed — diagnose exactly why
            category, diag = _classify_crawl_failure(result)
            print(f"  ✗ [{category}] status={diag['status_code']} html={diag['html_length']}b")
            if diag['error_message']:
                print(f"  ✗ Crawl error: {diag['error_message'][:300]}")
            if diag['notable_headers']:
                print(f"  ✗ Notable headers: {diag['notable_headers']}")
            if diag['html_preview']:
                print(f"  ✗ HTML preview: {diag['html_preview']!r}")

            retryable = category in ('TIMEOUT', 'CSS_EXTRACTION_FAILED', 'SERVER_ERROR', 'RATE_LIMITED')
            if retryable and attempt < max_retries:
                backoff = retry_delay * (2 ** (attempt - 1))
                if category == 'RATE_LIMITED':
                    backoff = max(backoff, 30)
                print(f"  ↻ [{category}] Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                continue

            raise ValueError(f"[{category}] No content extracted from product page")
    
    async def scrape_product(self, product_info: Dict) -> Optional[Dict]:
        """Main scraper method - extracts product details only

        Raises:
            ValueError: If product details cannot be extracted
            Exception: For other scraping failures
        """

        print(f"\n  → Product: {product_info.get('title', 'Unknown Product')}")

        # Get product details with CSS extraction
        try:
            css_data = await self.scrape_product_details(product_info)
            if not css_data:
                raise ValueError("Failed to extract product details")

            # Format the product data
            product_data = self.format_product_data(css_data, product_info)

            if not product_data:
                raise ValueError("Failed to format product data")

            return product_data
        except Exception as e:
            print(f"  ✗ Failed to scrape product: {e}")
            raise
    
    def format_product_data(self, css_data: Dict, product_info: Dict) -> Dict:
        """Format scraped product data (NO PDF URLs - use product_pdf_scraper.py)

        Raises:
            ValueError: If product name cannot be extracted
        """

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
            product_name = product_info.get("title", "")
        if not product_name:
            # FAIL - don't mask broken CSS selectors with fallback values
            print(f"  ✗ Failed to extract product name - check CSS selectors")
            raise ValueError("Failed to extract product name - check CSS selectors")
        
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
