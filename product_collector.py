"""
Product URL collection module for Agar scraper
Collects product URLs from category pages
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

from config import BASE_URL, USER_AGENT, PAGE_TIMEOUT, RATE_LIMIT_DELAY, TEST_PRODUCT_LIMIT
from utils import save_json, load_json

class ProductCollector:
    """Collect product URLs from category pages"""
    
    def __init__(self, output_dir: Path = None, test_mode: bool = False):
        self.output_dir = output_dir or Path(".")
        self.base_url = BASE_URL
        self.test_mode = test_mode
        self.test_limit = TEST_PRODUCT_LIMIT
    
    async def collect_from_category(self, category: Dict) -> List[Dict]:
        """Extract all product URLs from a category page"""
        print(f"\n📂 Collecting products from: {category['name']}")
        
        extraction_strategies = [
            # Strategy 1: Standard WooCommerce
            {
                "name": "WooCommerce Standard",
                "schema": {
                    "name": "Product List",
                    "baseSelector": "main",
                    "fields": [
                        {
                            "name": "products",
                            "selector": "ul.products li.product",
                            "type": "nested_list",
                            "fields": [
                                {"name": "title", "selector": "h2", "type": "text"},
                                {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
                                {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"}
                            ]
                        }
                    ]
                }
            },
            # Strategy 2: Alternative selectors
            {
                "name": "Alternative",
                "schema": {
                    "name": "Product List Alternative",
                    "baseSelector": "body",
                    "fields": [
                        {
                            "name": "products",
                            "selector": ".product",
                            "type": "nested_list",
                            "fields": [
                                {"name": "title", "selector": ".woocommerce-loop-product__title, h2, h3", "type": "text"},
                                {"name": "url", "selector": "a.woocommerce-LoopProduct-link, a:first-of-type", "type": "attribute", "attribute": "href"}
                            ]
                        }
                    ]
                }
            }
        ]
        
        all_products = []
        current_url = category["url"]
        
        async with AsyncWebCrawler() as crawler:
            print(f"  → Fetching: {current_url}")
            
            # Try different extraction strategies
            for strategy_info in extraction_strategies:
                print(f"  → Trying strategy: {strategy_info['name']}")
                
                extraction_strategy = JsonCssExtractionStrategy(schema=strategy_info['schema'])
                
                config = CrawlerRunConfig(
                    extraction_strategy=extraction_strategy,
                    cache_mode=CacheMode.BYPASS,
                    wait_for="css:ul.products li, .product",
                    page_timeout=PAGE_TIMEOUT,
                    verbose=False,
                    user_agent=USER_AGENT
                )
                
                try:
                    result = await crawler.arun(current_url, config=config)
                    
                    if result.success and result.extracted_content:
                        data = json.loads(result.extracted_content)
                        
                        if isinstance(data, list):
                            data = data[0] if data else {}
                        
                        products = data.get("products", [])
                        
                        if products:
                            print(f"    ✓ Found {len(products)} products")
                            
                            for product in products:
                                url = product.get("url", "")
                                if url and not url.startswith("http"):
                                    url = f"{self.base_url}{url}"
                                
                                if url and "/product/" in url:
                                    product_data = {
                                        "title": product.get("title", "").strip(),
                                        "url": url,
                                        "image": product.get("image", ""),
                                        "category": category["name"],
                                        "category_slug": category["slug"]
                                    }
                                    all_products.append(product_data)
                            
                            break  # Stop trying strategies if we found products
                        
                except Exception as e:
                    print(f"    ✗ Error: {e}")
        
        # Deduplicate
        seen_urls = set()
        unique_products = []
        for product in all_products:
            if product["url"] not in seen_urls:
                seen_urls.add(product["url"])
                unique_products.append(product)
        
        print(f"  ✓ Total unique products: {len(unique_products)}")
        
        # Apply test limit if needed
        if self.test_mode and len(unique_products) > self.test_limit:
            unique_products = unique_products[:self.test_limit]
            print(f"  ⚠️ Limited to {self.test_limit} products (test mode)")
        
        return unique_products
    
    async def collect_all_products(self, categories: List[Dict] = None) -> List[Dict]:
        """Collect products from all categories"""
        if not categories:
            # Try to load from file
            categories_file = self.output_dir / "categories.json"
            if categories_file.exists():
                categories = load_json(categories_file)
            else:
                raise ValueError("No categories provided and categories.json not found")
        
        all_products = []
        
        for i, category in enumerate(categories, 1):
            print(f"\n[Category {i}/{len(categories)}]")
            products = await self.collect_from_category(category)
            all_products.extend(products)
            
            # Save per-category results
            if self.output_dir:
                category_dir = self.output_dir / "categories" / category["slug"]
                category_dir.mkdir(parents=True, exist_ok=True)
                save_json(products, category_dir / "products_list.json")
            
            # Rate limiting
            if i < len(categories):
                await asyncio.sleep(RATE_LIMIT_DELAY)
        
        return all_products
    
    def save_products(self, products: List[Dict]) -> Path:
        """Save all products to JSON file"""
        filepath = self.output_dir / "all_products_list.json"
        save_json(products, filepath)
        print(f"\n✓ Saved {len(products)} products to {filepath}")
        return filepath


async def main():
    """Standalone execution"""
    parser = argparse.ArgumentParser(
        description="Agar Product URL Collector - Collect product URLs from categories",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--categories', '-c',
        type=str,
        help='Path to categories.json file'
    )
    
    parser.add_argument(
        '--category', 
        type=str,
        help='Single category slug to collect from'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=".",
        help='Output directory'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Test mode - limit products per category'
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print(" AGAR PRODUCT URL COLLECTOR".center(60))
    print("="*60)
    
    collector = ProductCollector(output_dir=output_dir, test_mode=args.test)
    
    if args.category:
        # Single category mode
        category = {
            "name": args.category.replace("-", " ").title(),
            "slug": args.category,
            "url": f"{BASE_URL}/product-category/{args.category}/"
        }
        products = await collector.collect_from_category(category)
        if products:
            save_json(products, output_dir / f"{args.category}_products.json")
    else:
        # All categories mode
        categories = None
        if args.categories:
            categories = load_json(Path(args.categories))
        
        products = await collector.collect_all_products(categories)
        collector.save_products(products)
    
    print("="*60)


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        print(f"❌ Error: Python 3.11+ required (you have {sys.version})")
        sys.exit(1)
    
    asyncio.run(main())
