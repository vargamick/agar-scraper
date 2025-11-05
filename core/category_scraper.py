"""
Category discovery module for Agar scraper
Can be run standalone to discover and save product categories
"""
import asyncio
import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from crawl4ai import AsyncWebCrawler, CacheMode
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from typing import Type

from config.base_config import BaseConfig
from core.utils import save_json, load_json

class CategoryScraper:
    """Discover and scrape product categories"""
    
    def __init__(self, config: Type[BaseConfig], output_dir: Path = None, test_mode: bool = False):
        self.config = config
        self.output_dir = output_dir or Path(".")
        self.base_url = config.BASE_URL
        self.test_mode = test_mode
    
    async def discover_categories(self) -> List[Dict]:
        """Discover all product categories from the website"""
        print("\n🔍 Discovering product categories...")
        
        # For now, use known categories as discovery might have issues
        # TODO: Implement actual discovery from website navigation
        categories = []
        for category_slug in self.config.KNOWN_CATEGORIES:
            categories.append({
                "name": category_slug.replace("-", " ").title(),
                "slug": category_slug,
                "url": f"{self.base_url}/product-category/{category_slug}/"
            })
        
        total_found = len(categories)
        
        # Apply test mode limit if enabled
        if self.test_mode and len(categories) > self.config.TEST_CATEGORY_LIMIT:
            categories = categories[:self.config.TEST_CATEGORY_LIMIT]
            print(f"✓ Using {self.config.TEST_CATEGORY_LIMIT} categories for test mode (from {total_found} known)")
        else:
            print(f"✓ Using {total_found} known categories")
        
        return categories
    
    async def scrape_category_page(self, category_url: str) -> Dict:
        """Scrape a single category page for metadata"""
        # This could be extended to get category descriptions, images, etc.
        async with AsyncWebCrawler() as crawler:
            crawler_config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                page_timeout=self.config.PAGE_TIMEOUT,
                user_agent=self.config.USER_AGENT
            )
            
            try:
                result = await crawler.arun(category_url, config=crawler_config)
                if result.success:
                    # Extract any category-specific metadata
                    return {
                        "scraped": True,
                        "timestamp": datetime.now().isoformat()
                    }
            except Exception as e:
                print(f"Error scraping category page: {e}")
        
        return {"scraped": False}
    
    def save_categories(self, categories: List[Dict]) -> Path:
        """Save categories to JSON file"""
        filepath = self.output_dir / "categories.json"
        save_json(categories, filepath)
        print(f"✓ Saved {len(categories)} categories to {filepath}")
        return filepath
    
    async def run(self) -> List[Dict]:
        """Main execution for category discovery"""
        categories = await self.discover_categories()
        
        if self.output_dir:
            self.save_categories(categories)
        
        return categories


async def main():
    """Standalone execution"""
    parser = argparse.ArgumentParser(
        description="Agar Category Scraper - Discover product categories",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=".",
        help='Output directory for categories.json'
    )
    
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Test mode - limit number of categories'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print(" AGAR CATEGORY SCRAPER".center(60))
    print("="*60)
    
    scraper = CategoryScraper(output_dir=output_dir, test_mode=args.test)
    categories = await scraper.run()
    
    print(f"\n✅ Found {len(categories)} categories")
    
    if args.verbose:
        for cat in categories:
            print(f"  - {cat['name']} ({cat['slug']})")
    
    print("="*60)


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        print(f"❌ Error: Python 3.11+ required (you have {sys.version})")
        sys.exit(1)
    
    asyncio.run(main())
