"""
Product PDF scraper module for Agar scraper
Scrapes PDF download links (SDS and PDS) from product pages using JavaScript
ONLY handles PDF extraction - use product_scraper.py for product details
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

from config import BASE_URL, USER_AGENT, DETAIL_PAGE_TIMEOUT, RATE_LIMIT_DELAY
from utils import save_json, load_json, sanitize_filename

class ProductPDFScraper:
    """Scrape PDF download links using JavaScript (ONLY PDFs - use product_scraper.py for product details)"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path(".")
        self.base_url = BASE_URL
    
    async def scrape_pdf_links(self, product_url: str, product_name: str = "Product") -> Optional[Dict]:
        """Extract PDF download links using 2-step process:
        1. Find SDS/PDS page link on product page
        2. Extract PDF URLs from SDS/PDS page
        """
        
        async with AsyncWebCrawler() as crawler:
            try:
                # STEP 1: Get product page and find SDS/PDS link
                print(f"  → Step 1: Finding SDS/PDS page link...")
                
                config = CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    wait_for="css:body",
                    page_timeout=DETAIL_PAGE_TIMEOUT,
                    user_agent=USER_AGENT
                )
                
                result = await crawler.arun(product_url, config)
                
                if not result.success or not result.html:
                    print(f"  ✗ Failed to fetch product page")
                    return None
                
                # Find SDS/PDS page URL in HTML
                # Pattern: <a href="https://agar.com.au/product-name-pds-sds">
                import re
                sds_page_match = re.search(r'href="([^"]*pds-sds[^"]*)"', result.html)
                
                if not sds_page_match:
                    print(f"  ✗ No SDS/PDS page link found")
                    return None
                
                sds_page_url = sds_page_match.group(1)
                # Ensure trailing slash for redirect
                if not sds_page_url.endswith('/'):
                    sds_page_url += '/'
                    
                print(f"  ✓ Found SDS/PDS page: {sds_page_url}")
                
                # STEP 2: Fetch SDS/PDS page and extract PDF URLs
                print(f"  → Step 2: Extracting PDF URLs from SDS/PDS page...")
                
                result2 = await crawler.arun(sds_page_url, config)
                
                if not result.success:
                    print(f"  ✗ Crawler failed")
                    return None
                
                if not result2.success or not result2.html:
                    print(f"  ✗ Failed to fetch SDS/PDS page")
                    return None
                
                # Extract all PDF URLs from the page
                pdf_urls = re.findall(r'href="(https://[^"]*\.pdf)"', result2.html)
                
                if not pdf_urls:
                    print(f"  ✗ No PDF URLs found on SDS/PDS page")
                    return None
                
                print(f"  ✓ Found {len(pdf_urls)} PDF URLs")
                
                # Create download objects
                downloads = []
                for url in pdf_urls:
                    downloads.append({
                        "url": url,
                        "source": "sds_pds_page"
                    })
                
                js_data = {"downloads": downloads}
                return self.format_pdf_data(js_data, product_url, product_name)
                    
            except Exception as e:
                print(f"  ✗ Error extracting PDFs: {e}")
                import traceback
                traceback.print_exc()
                return None
    
    def format_pdf_data(self, js_data: Dict, product_url: str, product_name: str) -> Dict:
        """Format extracted PDF data and identify SDS/PDS"""
        
        sds_url = None
        pds_url = None
        processed_urls = set()
        
        for download in js_data.get("downloads", []):
            url = download.get("url", "")
            if not url or url in processed_urls:
                continue
                
            processed_urls.add(url)
            
            # Normalize URL
            if not url.startswith("http"):
                if url.startswith("//"):
                    url = "https:" + url
                elif url.startswith("/"):
                    url = f"{self.base_url}{url}"
                else:
                    url = f"{self.base_url}/{url}"
            
            text = (download.get("text") or "").lower()
            url_lower = url.lower()
            
            # Identify SDS
            if not sds_url:
                if ("sds" in text or "safety" in text or 
                    "sds" in url_lower or "sds-" in url_lower or "-sds" in url_lower):
                    sds_url = url
                    continue
            
            # Identify PDS
            if not pds_url:
                if ("pds" in text or "product data" in text or 
                    "pds" in url_lower or "pds-" in url_lower or "-pds" in url_lower):
                    pds_url = url
                    continue
            
            # If we have both, we're done
            if sds_url and pds_url:
                break
        
        return {
            "product_name": product_name,
            "product_url": product_url,
            "sds_url": sds_url,
            "pds_url": pds_url,
            "scraped_at": datetime.now().isoformat(),
            "extraction_method": js_data.get("found_method", "unknown"),
            "total_pdfs_found": len(js_data.get("downloads", []))
        }
    
    async def scrape_products(self, products: List[Dict]) -> List[Dict]:
        """Scrape PDF links for multiple products"""
        successful = []
        failed = []
        
        for i, product in enumerate(products, 1):
            product_name = product.get("product_name") or product.get("title", "Unknown")
            product_url = product.get("product_url") or product.get("url", "")
            
            print(f"\n[PDF Extract {i}/{len(products)}] {product_name}")
            
            if not product_url:
                print(f"  ✗ No URL provided")
                failed.append(product)
                continue
            
            pdf_data = await self.scrape_pdf_links(product_url, product_name)
            
            if pdf_data:
                successful.append(pdf_data)
                
                # Save individual PDF data
                if self.output_dir:
                    filename = sanitize_filename(product_name)
                    pdf_dir = self.output_dir / "pdfs"
                    pdf_dir.mkdir(exist_ok=True, parents=True)
                    save_json(pdf_data, pdf_dir / f"{filename}_pdfs.json")
                    
                    # Report what was found
                    downloads = []
                    if pdf_data.get("sds_url"):
                        downloads.append("SDS")
                    if pdf_data.get("pds_url"):
                        downloads.append("PDS")
                    if downloads:
                        print(f"  ✓ PDFs: {', '.join(downloads)}")
                    else:
                        print(f"  ⚠ No SDS/PDS identified")
            else:
                failed.append(product)
            
            # Rate limiting
            if i < len(products):
                await asyncio.sleep(RATE_LIMIT_DELAY)
        
        return successful


async def main():
    """Standalone execution"""
    parser = argparse.ArgumentParser(
        description="Agar PDF Scraper - Extract PDF download links only"
    )
    
    parser.add_argument(
        '--url',
        type=str,
        help='Single product URL to scrape PDFs from'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        default="Product",
        help='Product name (for single URL mode)'
    )
    
    parser.add_argument(
        '--products', '-p',
        type=str,
        help='Path to products JSON file (with product_name and product_url fields)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=".",
        help='Output directory'
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    (output_dir / "pdfs").mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print(" AGAR PDF SCRAPER (PDF EXTRACTION ONLY)".center(60))
    print("="*60)
    
    scraper = ProductPDFScraper(output_dir=output_dir)
    
    if args.url:
        # Single product mode
        pdf_data = await scraper.scrape_pdf_links(args.url, args.name)
        if pdf_data:
            filename = sanitize_filename(args.name)
            save_json(pdf_data, output_dir / f"{filename}_pdfs.json")
            print(f"\n✓ Saved to {filename}_pdfs.json")
    elif args.products:
        # Multiple products mode
        products = load_json(Path(args.products))
        successful = await scraper.scrape_products(products)
        
        # Save summary
        save_json(successful, output_dir / "all_pdfs.json")
        print(f"\n✓ Extracted PDFs from {len(successful)}/{len(products)} products")
    else:
        print("❌ Please provide --url or --products")
    
    print("="*60)


if __name__ == "__main__":
    if sys.version_info < (3, 11):
        print(f"❌ Error: Python 3.11+ required (you have {sys.version})")
        sys.exit(1)
    
    asyncio.run(main())
