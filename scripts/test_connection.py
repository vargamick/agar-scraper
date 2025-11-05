#!/usr/bin/env python3
"""
3DN Scraper Template - Connection Testing Script

Tests connectivity to a client's website to ensure it's accessible
before attempting to scrape.
"""

import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_website_connection(config):
    """Test connection to client website."""
    from crawl4ai import AsyncWebCrawler
    
    base_url = config.BASE_URL
    
    print(f"\nTesting connection to: {base_url}")
    print("-" * 80)
    
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            # Test base URL
            print(f"Fetching: {base_url}")
            start_time = datetime.now()
            
            result = await crawler.arun(
                url=base_url,
                bypass_cache=True,
                page_timeout=config.PAGE_TIMEOUT if hasattr(config, 'PAGE_TIMEOUT') else 60000
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                print(f"✓ Successfully connected")
                print(f"  Response time: {duration:.2f} seconds")
                print(f"  Status code: {result.status_code if hasattr(result, 'status_code') else 'N/A'}")
                print(f"  Content length: {len(result.html) if result.html else 0} bytes")
                
                # Check if we got reasonable content
                if result.html and len(result.html) > 1000:
                    print(f"  ✓ Received substantial HTML content")
                else:
                    print(f"  ⚠️  Warning: Received minimal HTML content (may indicate issues)")
                
                return True, duration
            else:
                print(f"✗ Connection failed")
                print(f"  Error: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                return False, 0
                
    except Exception as e:
        print(f"✗ Connection failed with exception")
        print(f"  Error: {str(e)}")
        return False, 0


async def test_category_url(config):
    """Test a sample category URL."""
    from crawl4ai import AsyncWebCrawler
    
    # Get first known category if available
    if hasattr(config, 'KNOWN_CATEGORIES') and config.KNOWN_CATEGORIES:
        category_slug = config.KNOWN_CATEGORIES[0]
    else:
        print("\n⚠️  No KNOWN_CATEGORIES defined in config, skipping category URL test")
        return True, 0
    
    # Build category URL
    category_url = config.BASE_URL + config.CATEGORY_URL_PATTERN.format(slug=category_slug)
    
    print(f"\nTesting category URL: {category_url}")
    print("-" * 80)
    
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            print(f"Fetching: {category_url}")
            start_time = datetime.now()
            
            result = await crawler.arun(
                url=category_url,
                bypass_cache=True,
                page_timeout=config.PAGE_TIMEOUT if hasattr(config, 'PAGE_TIMEOUT') else 60000
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result.success:
                print(f"✓ Successfully connected")
                print(f"  Response time: {duration:.2f} seconds")
                print(f"  Content length: {len(result.html) if result.html else 0} bytes")
                return True, duration
            else:
                print(f"✗ Connection failed")
                print(f"  Error: {result.error_message if hasattr(result, 'error_message') else 'Unknown error'}")
                print(f"  Note: Check if CATEGORY_URL_PATTERN is correct")
                return False, 0
                
    except Exception as e:
        print(f"✗ Connection failed with exception")
        print(f"  Error: {str(e)}")
        return False, 0


async def test_dns_resolution(config):
    """Test DNS resolution for the domain."""
    import socket
    from urllib.parse import urlparse
    
    parsed = urlparse(config.BASE_URL)
    domain = parsed.netloc
    
    print(f"\nTesting DNS resolution for: {domain}")
    print("-" * 80)
    
    try:
        ip_address = socket.gethostbyname(domain)
        print(f"✓ DNS resolution successful")
        print(f"  Domain: {domain}")
        print(f"  IP Address: {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"✗ DNS resolution failed")
        print(f"  Error: {str(e)}")
        print(f"  Check if domain is correct and accessible")
        return False


def test_url_patterns(config):
    """Test URL pattern formatting."""
    print(f"\nTesting URL patterns")
    print("-" * 80)
    
    all_valid = True
    
    # Test category URL pattern
    if hasattr(config, 'CATEGORY_URL_PATTERN'):
        pattern = config.CATEGORY_URL_PATTERN
        try:
            test_url = config.BASE_URL + pattern.format(slug='test-category')
            print(f"✓ Category URL pattern valid")
            print(f"  Pattern: {pattern}")
            print(f"  Example: {test_url}")
        except KeyError as e:
            print(f"✗ Category URL pattern invalid")
            print(f"  Error: Missing {e} placeholder")
            all_valid = False
    else:
        print(f"✗ CATEGORY_URL_PATTERN not defined")
        all_valid = False
    
    # Test product URL pattern
    if hasattr(config, 'PRODUCT_URL_PATTERN'):
        pattern = config.PRODUCT_URL_PATTERN
        try:
            test_url = config.BASE_URL + pattern.format(slug='test-product')
            print(f"✓ Product URL pattern valid")
            print(f"  Pattern: {pattern}")
            print(f"  Example: {test_url}")
        except KeyError as e:
            print(f"✗ Product URL pattern invalid")
            print(f"  Error: Missing {e} placeholder")
            all_valid = False
    else:
        print(f"✗ PRODUCT_URL_PATTERN not defined")
        all_valid = False
    
    return all_valid


async def run_tests(config, args):
    """Run all connection tests."""
    results = {
        'dns': False,
        'url_patterns': False,
        'base_url': False,
        'category_url': False
    }
    
    timings = {}
    
    # Test DNS resolution
    results['dns'] = await asyncio.to_thread(test_dns_resolution, config)
    
    # Test URL patterns
    results['url_patterns'] = test_url_patterns(config)
    
    # Test base URL connection
    if results['dns']:
        base_success, base_time = await test_website_connection(config)
        results['base_url'] = base_success
        timings['base_url'] = base_time
    else:
        print("\n⚠️  Skipping website connection test (DNS resolution failed)")
    
    # Test category URL (if requested)
    if not args.base_only and results['base_url']:
        category_success, category_time = await test_category_url(config)
        results['category_url'] = category_success
        timings['category_url'] = category_time
    elif args.base_only:
        print("\n⚠️  Skipping category URL test (--base-only flag set)")
        results['category_url'] = None  # Not tested
    else:
        print("\n⚠️  Skipping category URL test (base URL test failed)")
    
    return results, timings


def print_summary(results, timings):
    """Print test summary."""
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    # Count results
    tested = [k for k, v in results.items() if v is not None]
    passed = [k for k, v in results.items() if v is True]
    failed = [k for k, v in results.items() if v is False]
    
    print(f"Tests run: {len(tested)}")
    print(f"Passed: \033[92m{len(passed)}\033[0m")
    print(f"Failed: \033[91m{len(failed)}\033[0m")
    
    # Print timings if available
    if timings:
        print("\nResponse Times:")
        for test, duration in timings.items():
            print(f"  {test}: {duration:.2f}s")
    
    print("=" * 80)
    
    # Overall result
    if all(v in (True, None) for v in results.values()):
        print("\n✅ All tests passed!")
        if results['category_url'] is None:
            print("   (Some tests were skipped)")
        return 0
    else:
        print("\n❌ Some tests failed. Review the output above for details.")
        return 1


def main():
    """Main testing workflow."""
    parser = argparse.ArgumentParser(
        description='Test connectivity to client website'
    )
    parser.add_argument(
        '--client',
        required=True,
        help='Client name to test'
    )
    parser.add_argument(
        '--base-only',
        action='store_true',
        help='Only test base URL (skip category URL test)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"3DN Scraper Template - Connection Testing")
    print(f"Client: {args.client}")
    print("=" * 80)
    
    # Load configuration
    try:
        from config.config_loader import load_config
        config = load_config(args.client)
        print(f"✓ Configuration loaded")
        print(f"  Website: {config.BASE_URL}")
    except Exception as e:
        print(f"\n✗ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Run tests
    try:
        results, timings = asyncio.run(run_tests(config, args))
        exit_code = print_summary(results, timings)
        
        # Next steps
        if exit_code == 0:
            print("\nNext steps:")
            print(f"  1. Configure extraction selectors in extraction_strategies.py")
            print(f"  2. python scripts/test_extraction.py --client {args.client} --url <test-url>")
            print(f"  3. python main.py --client {args.client} --test")
        else:
            print("\nTroubleshooting:")
            print("  - Verify the BASE_URL is correct")
            print("  - Check if the website is accessible in your browser")
            print("  - Verify URL patterns match the website structure")
            print("  - Check firewall/proxy settings")
        
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
