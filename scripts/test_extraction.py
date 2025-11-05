#!/usr/bin/env python3
"""
3DN Scraper Template - Extraction Testing Script

Tests extraction selectors on actual web pages to verify they work correctly.
Helps in debugging and configuring extraction strategies.
"""

import sys
import argparse
import asyncio
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print('=' * 80)


def print_field(name, value, indent=2):
    """Print a field with value."""
    indent_str = " " * indent
    if value is None or value == "":
        print(f"{indent_str}✗ {name}: (empty)")
    elif isinstance(value, list):
        if value:
            print(f"{indent_str}✓ {name}: {len(value)} items")
            for item in value[:3]:  # Show first 3 items
                print(f"{indent_str}  - {item[:100] if isinstance(item, str) else item}")
            if len(value) > 3:
                print(f"{indent_str}  ... and {len(value) - 3} more")
        else:
            print(f"{indent_str}✗ {name}: (empty list)")
    elif isinstance(value, dict):
        if value:
            print(f"{indent_str}✓ {name}: {len(value)} keys")
            for key, val in list(value.items())[:3]:
                val_str = str(val)[:100] if val else "(empty)"
                print(f"{indent_str}  {key}: {val_str}")
        else:
            print(f"{indent_str}✗ {name}: (empty dict)")
    else:
        value_str = str(value)[:200]
        if len(str(value)) > 200:
            value_str += "..."
        print(f"{indent_str}✓ {name}: {value_str}")


async def fetch_page(url, config):
    """Fetch a page and return the HTML."""
    from crawl4ai import AsyncWebCrawler
    
    print(f"\nFetching: {url}")
    print("-" * 80)
    
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            start_time = datetime.now()
            
            result = await crawler.arun(
                url=url,
                bypass_cache=True,
                page_timeout=config.PAGE_TIMEOUT if hasattr(config, 'PAGE_TIMEOUT') else 60000
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                print(f"✓ Page fetched successfully")
                print(f"  Response time: {duration:.2f} seconds")
                print(f"  Content length: {len(result.html) if result.html else 0} bytes")
                return result.html
            else:
                print(f"✗ Failed to fetch page")
                print(f"  Error: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                return None
                
    except Exception as e:
        print(f"✗ Failed to fetch page")
        print(f"  Error: {str(e)}")
        return None


def test_category_extraction(html, strategy, config):
    """Test extraction from a category page."""
    from bs4 import BeautifulSoup
    
    print_section("Category Page Extraction Test")
    
    if not html:
        print("Cannot test extraction: No HTML content")
        return False
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get selectors from strategy
    selectors = strategy.CATEGORY_SELECTORS if hasattr(strategy, 'CATEGORY_SELECTORS') else {}
    
    print("\nTesting Category Selectors:")
    print("-" * 80)
    
    results = {}
    all_passed = True
    
    # Test each selector
    for key, selector in selectors.items():
        print(f"\n{key}: {selector}")
        try:
            if key == "products":
                # Find all products
                elements = soup.select(selector)
                results[key] = len(elements)
                if elements:
                    print(f"  ✓ Found {len(elements)} products")
                else:
                    print(f"  ✗ No products found")
                    all_passed = False
            else:
                # Find first occurrence
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)[:100]
                    print(f"  ✓ Found: {text}")
                    results[key] = text
                else:
                    print(f"  ✗ Not found")
                    all_passed = False
                    results[key] = None
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            all_passed = False
            results[key] = None
    
    # Try to extract products using the strategy
    print("\nExtracting Products:")
    print("-" * 80)
    
    try:
        products = []
        product_elements = soup.select(selectors.get('products', ''))
        
        for i, product_el in enumerate(product_elements[:5], 1):  # Test first 5
            product_data = {}
            
            # Extract link
            if 'product_link' in selectors:
                link_el = product_el.select_one(selectors['product_link'])
                if link_el:
                    product_data['url'] = link_el.get('href', '')
            
            # Extract name
            if 'product_name' in selectors:
                name_el = product_el.select_one(selectors['product_name'])
                if name_el:
                    product_data['name'] = name_el.get_text(strip=True)
            
            products.append(product_data)
            
            print(f"\nProduct {i}:")
            for key, value in product_data.items():
                print_field(key, value)
        
        if products:
            print(f"\n✓ Successfully extracted {len(products)} products (showing first 5)")
        else:
            print(f"\n✗ No products extracted")
            all_passed = False
            
    except Exception as e:
        print(f"✗ Error extracting products: {str(e)}")
        all_passed = False
    
    return all_passed


def test_product_extraction(html, strategy, config):
    """Test extraction from a product page."""
    from bs4 import BeautifulSoup
    
    print_section("Product Page Extraction Test")
    
    if not html:
        print("Cannot test extraction: No HTML content")
        return False
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get selectors from strategy
    selectors = strategy.PRODUCT_SELECTORS if hasattr(strategy, 'PRODUCT_SELECTORS') else {}
    
    print("\nTesting Product Selectors:")
    print("-" * 80)
    
    results = {}
    all_passed = True
    
    # Test each selector
    for key, selector in selectors.items():
        print(f"\n{key}: {selector}")
        try:
            element = soup.select_one(selector)
            if element:
                if key == "image":
                    # For images, get the src attribute
                    src = element.get('src', '') or element.get('data-src', '')
                    print(f"  ✓ Found: {src[:100]}")
                    results[key] = src
                else:
                    # For text elements
                    text = element.get_text(strip=True)
                    preview = text[:200] + "..." if len(text) > 200 else text
                    print(f"  ✓ Found: {preview}")
                    results[key] = text
            else:
                print(f"  ✗ Not found")
                all_passed = False
                results[key] = None
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            all_passed = False
            results[key] = None
    
    # Print extracted product data
    print("\nExtracted Product Data:")
    print("-" * 80)
    
    for key, value in results.items():
        print_field(key, value)
    
    # Test PDF extraction if applicable
    if hasattr(strategy, 'PDF_SELECTORS') and config.HAS_SDS_DOCUMENTS or config.HAS_PDS_DOCUMENTS:
        print("\n" + "-" * 80)
        print("PDF/Document Link Extraction:")
        print("-" * 80)
        
        pdf_selectors = strategy.PDF_SELECTORS
        
        for key, selector in pdf_selectors.items():
            print(f"\n{key}: {selector}")
            try:
                element = soup.select_one(selector)
                if element:
                    href = element.get('href', '')
                    print(f"  ✓ Found: {href}")
                else:
                    print(f"  ⚠️  Not found (may be optional)")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
    
    return all_passed


async def run_test(url, config, strategy, page_type):
    """Run extraction test on a URL."""
    # Fetch the page
    html = await fetch_page(url, config)
    
    if not html:
        return False
    
    # Test extraction based on page type
    if page_type == 'category':
        return test_category_extraction(html, strategy, config)
    elif page_type == 'product':
        return test_product_extraction(html, strategy, config)
    else:
        print(f"Unknown page type: {page_type}")
        return False


def save_test_results(url, html, results, output_dir):
    """Save test results to files for debugging."""
    output_dir.mkdir(exist_ok=True)
    
    # Save HTML
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = output_dir / f"test_page_{timestamp}.html"
    html_file.write_text(html)
    print(f"\n✓ Saved HTML to: {html_file}")
    
    # Save results
    results_file = output_dir / f"test_results_{timestamp}.json"
    results_file.write_text(json.dumps(results, indent=2))
    print(f"✓ Saved results to: {results_file}")


def main():
    """Main testing workflow."""
    parser = argparse.ArgumentParser(
        description='Test extraction selectors on web pages'
    )
    parser.add_argument(
        '--client',
        required=True,
        help='Client name to test'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='URL to test extraction on'
    )
    parser.add_argument(
        '--type',
        choices=['category', 'product', 'auto'],
        default='auto',
        help='Type of page (category, product, or auto-detect)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save HTML and results to files'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"3DN Scraper Template - Extraction Testing")
    print(f"Client: {args.client}")
    print(f"URL: {args.url}")
    print("=" * 80)
    
    # Load configuration
    try:
        from config.config_loader import load_config
        config = load_config(args.client)
        print(f"✓ Configuration loaded")
    except Exception as e:
        print(f"\n✗ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Load extraction strategy
    try:
        from config.config_loader import load_extraction_strategy
        strategy = load_extraction_strategy(args.client)
        print(f"✓ Extraction strategy loaded")
    except Exception as e:
        print(f"\n✗ Failed to load extraction strategy: {e}")
        sys.exit(1)
    
    # Auto-detect page type if needed
    page_type = args.type
    if page_type == 'auto':
        if '/product/' in args.url or '/item/' in args.url:
            page_type = 'product'
            print(f"✓ Auto-detected page type: product")
        elif '/category/' in args.url or '/collection/' in args.url:
            page_type = 'category'
            print(f"✓ Auto-detected page type: category")
        else:
            print(f"⚠️  Could not auto-detect page type, defaulting to product")
            page_type = 'product'
    
    # Run test
    try:
        success = asyncio.run(run_test(args.url, config, strategy, page_type))
        
        if success:
            print_section("Test Result: ✅ PASSED")
            print("\nAll selectors are working correctly!")
            print("\nNext steps:")
            print(f"  1. Test more URLs to verify consistency")
            print(f"  2. python main.py --client {args.client} --test")
            exit_code = 0
        else:
            print_section("Test Result: ❌ FAILED")
            print("\nSome selectors are not working correctly.")
            print("\nTroubleshooting:")
            print("  1. Open the URL in your browser")
            print("  2. Use browser dev tools (F12) to inspect elements")
            print("  3. Verify CSS selectors match the actual HTML structure")
            print("  4. Update extraction_strategies.py with correct selectors")
            print(f"  5. Re-run: python scripts/test_extraction.py --client {args.client} --url {args.url}")
            exit_code = 1
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
