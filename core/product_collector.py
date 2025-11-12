"""
Product URL collection module for Agar scraper
Collects product URLs from category pages
Handles hierarchical category structures with subcategories
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from typing import Type

from config.base_config import BaseConfig
from core.utils import save_json, load_json, get_rate_limit_delay

# Maximum depth for recursive category scraping to prevent infinite loops
MAX_CATEGORY_DEPTH = 5

class ProductCollector:
    """Collect product URLs from category pages with support for hierarchical structures"""
    
    def __init__(self, config: Type[BaseConfig], output_dir: Path = None, test_mode: bool = False):
        self.config = config
        self.output_dir = output_dir or Path(".")
        self.base_url = config.BASE_URL
        self.test_mode = test_mode
        self.test_limit = config.TEST_PRODUCT_LIMIT
        self.processed_categories = set()  # Track processed categories to avoid duplicates
    
    async def collect_from_category(self, category: Dict, depth: int = 0, parent_slug: str = None) -> List[Dict]:
        """
        Extract all product URLs and subcategories from a category page.
        Handles hierarchical category structures recursively.
        
        Args:
            category: Category dict with 'name', 'slug', and 'url'
            depth: Current recursion depth (to prevent infinite loops)
            parent_slug: Parent category slug for maintaining hierarchy
        
        Returns:
            List of product dicts
        """
        # Check recursion depth
        if depth >= MAX_CATEGORY_DEPTH:
            print(f"  ⚠️ Maximum category depth ({MAX_CATEGORY_DEPTH}) reached, skipping subcategories")
            return []
        
        # Check if already processed
        category_key = category['url']
        if category_key in self.processed_categories:
            print(f"  ⚠️ Category already processed, skipping: {category['name']}")
            return []
        self.processed_categories.add(category_key)
        
        indent = "  " * depth
        print(f"\n{indent}📂 Collecting from: {category['name']} (depth: {depth})")
        
        # First, check if this category has subcategories or products
        subcategories, products = await self._extract_page_content(category['url'], indent)
        
        all_products = []
        
        # Handle subcategories
        if subcategories:
            print(f"{indent}  ✓ Found {len(subcategories)} subcategories")
            
            # Save parent category data with subcategory info
            category_data = {
                "name": category['name'],
                "slug": category['slug'],
                "url": category['url'],
                "has_subcategories": True,
                "subcategory_count": len(subcategories),
                "subcategories": [{"name": sc['name'], "slug": sc['slug']} for sc in subcategories]
            }
            if parent_slug:
                category_data['parent_slug'] = parent_slug
            
            category_path = self._get_category_output_path(category['slug'], parent_slug, is_product_list=False)
            save_json(category_data, category_path)
            print(f"{indent}  → Saved category data with subcategories")
            
            # Recursively scrape each subcategory
            for i, subcat in enumerate(subcategories, 1):
                print(f"{indent}  [{i}/{len(subcategories)}] Processing subcategory: {subcat['name']}")
                subcat_products = await self.collect_from_category(
                    subcat, 
                    depth=depth + 1,
                    parent_slug=category['slug']
                )
                all_products.extend(subcat_products)
                
                # Rate limiting between subcategories
                if i < len(subcategories):
                    delay = get_rate_limit_delay(self.config)
                    await asyncio.sleep(delay)
        
        # Handle products on this page
        if products:
            print(f"{indent}  ✓ Found {len(products)} products on this page")
            
            # Add category information to each product
            for product in products:
                product["category"] = category["name"]
                product["category_slug"] = category["slug"]
                if parent_slug:
                    product["parent_category_slug"] = parent_slug
            
            all_products.extend(products)
            
            # Save products for this specific category
            product_list_path = self._get_category_output_path(category['slug'], parent_slug, is_product_list=True)
            save_json(products, product_list_path)
            
            # If no subcategories, also save category metadata
            if not subcategories:
                category_data = {
                    "name": category['name'],
                    "slug": category['slug'],
                    "url": category['url'],
                    "has_subcategories": False,
                    "product_count": len(products)
                }
                if parent_slug:
                    category_data['parent_slug'] = parent_slug
                
                category_path = self._get_category_output_path(category['slug'], parent_slug, is_product_list=False)
                save_json(category_data, category_path)
        
        if not subcategories and not products:
            print(f"{indent}  ⚠️ No subcategories or products found")
        
        print(f"{indent}  ✓ Total products collected: {len(all_products)}")
        
        return all_products
    
    def _get_category_output_path(self, category_slug: str, parent_slug: str = None, 
                                  is_product_list: bool = False) -> Path:
        """
        Get output path for category data.
        
        Args:
            category_slug: Slug of the current category
            parent_slug: Slug of parent category (if subcategory)
            is_product_list: Whether this is for a product list file
        
        Returns:
            Path: Direct file path (not directory) for the category data
        """
        categories_dir = self.output_dir / "categories"
        categories_dir.mkdir(parents=True, exist_ok=True)
        
        if parent_slug:
            # Subcategory - create parent folder if needed
            parent_dir = categories_dir / parent_slug
            parent_dir.mkdir(parents=True, exist_ok=True)
            
            # File naming: parent_subcategory[_products].json
            if is_product_list:
                filename = f"{parent_slug}_{category_slug}_products.json"
            else:
                filename = f"{parent_slug}_{category_slug}.json"
            
            return parent_dir / filename
        else:
            # Top-level category - save directly in categories/
            if is_product_list:
                filename = f"{category_slug}_products.json"
            else:
                filename = f"{category_slug}.json"
            
            return categories_dir / filename
    
    async def _extract_page_content(self, category_url: str, indent: str = "  ") -> Tuple[List[Dict], List[Dict]]:
        """
        Extract both subcategories and products from a category page.
        
        Returns:
            Tuple of (subcategories, products)
        """
        subcategories = []
        products = []
        
        extraction_strategies = [
            # Strategy 1: Extract subcategories (product-category items)
            {
                "name": "Subcategories",
                "schema": {
                    "name": "Subcategory List",
                    "baseSelector": "ul.products",
                    "fields": [
                        {
                            "name": "subcategories",
                            "selector": "li.product-category",
                            "type": "nested_list",
                            "fields": [
                                {"name": "title", "selector": "h2", "type": "text"},
                                {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
                                {"name": "count", "selector": "mark.count", "type": "text"},
                                {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"}
                            ]
                        }
                    ]
                }
            },
            # Strategy 2: Extract products (type-product items)
            {
                "name": "Products",
                "schema": {
                    "name": "Product List",
                    "baseSelector": "ul.products",
                    "fields": [
                        {
                            "name": "products",
                            "selector": "li.type-product",
                            "type": "nested_list",
                            "fields": [
                                {"name": "title", "selector": "h2", "type": "text"},
                                {"name": "url", "selector": "a", "type": "attribute", "attribute": "href"},
                                {"name": "image", "selector": "img", "type": "attribute", "attribute": "src"}
                            ]
                        }
                    ]
                }
            }
        ]
        
        async with AsyncWebCrawler() as crawler:
            print(f"{indent}→ Fetching: {category_url}")
            
            # Try each extraction strategy
            for strategy_info in extraction_strategies:
                extraction_strategy = JsonCssExtractionStrategy(schema=strategy_info['schema'])
                
                crawler_config = CrawlerRunConfig(
                    extraction_strategy=extraction_strategy,
                    cache_mode=CacheMode.BYPASS,
                    wait_for="css:ul.products li",
                    page_timeout=self.config.PAGE_TIMEOUT,
                    verbose=False,
                    user_agent=self.config.USER_AGENT
                )
                
                try:
                    result = await crawler.arun(category_url, config=crawler_config)
                    
                    if result.success and result.extracted_content:
                        data = json.loads(result.extracted_content)
                        
                        if isinstance(data, list):
                            data = data[0] if data else {}
                        
                        # Extract subcategories
                        if strategy_info['name'] == "Subcategories":
                            subcats = data.get("subcategories", [])
                            if subcats:
                                print(f"{indent}  ✓ Extracted {len(subcats)} subcategories")
                                for subcat in subcats:
                                    url = subcat.get("url", "")
                                    if url and not url.startswith("http"):
                                        url = f"{self.base_url}{url}"
                                    
                                    if url and "/product-category/" in url:
                                        # Extract slug from URL
                                        slug = url.rstrip('/').split('/')[-1]
                                        title = subcat.get("title", "").strip()
                                        # Remove count from title if present
                                        if "(" in title:
                                            title = title.split("(")[0].strip()
                                        
                                        subcat_data = {
                                            "name": title,
                                            "slug": slug,
                                            "url": url,
                                            "count": subcat.get("count", "").strip("()"),
                                            "image": subcat.get("image", "")
                                        }
                                        subcategories.append(subcat_data)
                        
                        # Extract products
                        elif strategy_info['name'] == "Products":
                            prods = data.get("products", [])
                            if prods:
                                print(f"{indent}  ✓ Extracted {len(prods)} products")
                                for prod in prods:
                                    url = prod.get("url", "")
                                    if url and not url.startswith("http"):
                                        url = f"{self.base_url}{url}"
                                    
                                    if url and "/product/" in url:
                                        product_data = {
                                            "title": prod.get("title", "").strip(),
                                            "url": url,
                                            "image": prod.get("image", "")
                                        }
                                        products.append(product_data)
                        
                except Exception as e:
                    print(f"{indent}  ✗ Error with {strategy_info['name']} strategy: {e}")
        
        # Deduplicate products
        seen_urls = set()
        unique_products = []
        for product in products:
            if product["url"] not in seen_urls:
                seen_urls.add(product["url"])
                unique_products.append(product)
        
        # Apply test limit if needed
        if self.test_mode and len(unique_products) > self.test_limit:
            unique_products = unique_products[:self.test_limit]
            print(f"{indent}  ⚠️ Limited to {self.test_limit} products (test mode)")
        
        return subcategories, unique_products
    
    async def collect_all_products(self, categories: List[Dict]) -> List[Dict]:
        """Collect products from all categories.
        
        Handles hierarchical category structures automatically.
        
        Args:
            categories: List of category dictionaries (REQUIRED - must be freshly scraped)
            
        Returns:
            List of all products collected
            
        Raises:
            ValueError: If no categories provided
        """
        if not categories:
            raise ValueError(
                "No categories provided. Categories must be scraped dynamically using "
                "CategoryScraper.discover_categories() before collecting products."
            )
        
        all_products = []
        
        for i, category in enumerate(categories, 1):
            print(f"\n{'='*60}")
            print(f"[TOP-LEVEL CATEGORY {i}/{len(categories)}]")
            print(f"{'='*60}")
            
            # Start recursive collection from depth 0
            products = await self.collect_from_category(category, depth=0)
            all_products.extend(products)
            
            # Rate limiting between top-level categories
            if i < len(categories):
                delay = get_rate_limit_delay(self.config)
                await asyncio.sleep(delay)
        
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
    
    # Load config
    from config.config_loader import ConfigLoader
    config = ConfigLoader.load_client_config('agar')
    
    collector = ProductCollector(config=config, output_dir=output_dir, test_mode=args.test)
    
    if args.category:
        # Single category mode
        category = {
            "name": args.category.replace("-", " ").title(),
            "slug": args.category,
            "url": f"{config.BASE_URL}/product-category/{args.category}/"
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
