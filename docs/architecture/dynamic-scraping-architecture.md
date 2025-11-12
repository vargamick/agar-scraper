# Dynamic Scraping Architecture

**Document Version:** 1.0  
**Date:** 2025-06-11  
**Status:** Implementation Complete

## Overview

The 3DN Scraper Template uses **fully dynamic scraping** with **zero hardcoded values**. All data is discovered from websites at runtime.

## Core Principle

> **No Hardcoded Data Sources**
> 
> The scraper discovers ALL information dynamically from the website:
> - Categories are scraped from the homepage/navigation
> - Products are extracted from category pages
> - Product details are scraped from product pages
>
> **No manual lists. No fallbacks. No hardcoded defaults.**

## Architecture Changes (June 2025)

### What Was Removed

1. **KNOWN_CATEGORIES Configuration**
   - Removed from `BaseConfig`
   - Removed from all client configs
   - Removed from templates
   - Removed from deployment scripts

2. **Category File Fallbacks**
   - Removed category file loading from `ProductCollector`
   - Categories must now be provided fresh from scraper

3. **Silent Fallback Values**
   - Removed "Unknown" fallback for product names
   - Extraction failures now visible and explicit

### Why These Changes Matter

#### Before (Problematic)
```python
# BAD: Hardcoded category list
KNOWN_CATEGORIES = [
    "toilet-bathroom-cleaners",
    "green-cleaning-products",
    ...  # Only 14 categories
]

# BAD: Silent fallback
if not product_name:
    product_name = "Unknown"  # Masks broken selectors!
```

**Problems:**
- Missed 43 categories (only found 14 of 57)
- Silent failures masked selector issues
- Required manual maintenance for new categories

#### After (Correct)
```python
# GOOD: Dynamic discovery
categories = await scraper.discover_categories()
# Returns ALL 57 categories from website

# GOOD: Fail visibly
if not product_name:
    print("✗ Failed to extract product name - check CSS selectors")
    return None  # Force fixing the real issue
```

**Benefits:**
- Discovers all categories automatically
- Failures are visible and must be fixed
- No manual maintenance required
- Adaptable to website changes

## How It Works Now

### 1. Category Discovery
```python
from core.category_scraper import CategoryScraper

# Scrape categories dynamically
scraper = CategoryScraper(config, output_dir, test_mode=False)
categories = await scraper.discover_categories()
# Returns: ALL categories found on the website
```

### 2. Product Collection
```python
from core.product_collector import ProductCollector

# Collect products from discovered categories
collector = ProductCollector(config, output_dir, test_mode=False)
products = await collector.collect_all_products(categories)
# Note: categories parameter is REQUIRED (no file loading fallback)
```

### 3. Product Scraping
```python
from core.product_scraper import ProductScraper

# Scrape product details
scraper = ProductScraper(config, strategies, output_dir)
product_data = await scraper.scrape_product(product_info)
# Returns: Product data OR None (no "Unknown" fallbacks)
```

## Configuration Guidelines

### What TO Configure
✅ **Website Structure:**
- `BASE_URL` - The website's base URL
- `CATEGORY_URL_PATTERN` - How category URLs are formed
- `PRODUCT_URL_PATTERN` - How product URLs are formed

✅ **CSS Selectors:**
- Category navigation selectors
- Product list selectors  
- Product detail selectors

✅ **Behavior:**
- Timeouts and rate limiting
- Test mode limits
- Output preferences

### What NOT TO Configure
❌ **Never Hardcode:**
- Category lists
- Product lists
- URLs (except patterns)
- Fallback values
- Default data

## Testing Dynamic Scraping

### Test Category Discovery
```bash
python scripts/test_connection.py --client agar
```
This now:
1. Discovers categories dynamically
2. Tests first discovered category
3. Fails if no categories found

### Test Full Scrape
```bash
python main.py --client agar --test
```
This now:
1. Discovers all categories from website
2. Collects products from discovered categories
3. Fails visibly if extraction breaks

## Failure Modes (By Design)

The scraper is designed to **fail visibly** when things break:

### Category Discovery Fails
```
✗ Discovered 0 unique categories from website
```
**Action:** Check category CSS selectors in extraction strategies

### Product Name Extraction Fails  
```
✗ Failed to extract product name - check CSS selectors
```
**Action:** Fix product name selector - don't mask with "Unknown"

### No Categories Provided
```
ValueError: No categories provided. Categories must be scraped 
dynamically using CategoryScraper.discover_categories()
```
**Action:** Ensure CategoryScraper runs before ProductCollector

## Migration Notes

### For Existing Deployments

If you have existing client configs with `KNOWN_CATEGORIES`:

1. **Remove** the `KNOWN_CATEGORIES` field entirely
2. **Test** category discovery with your CSS selectors
3. **Verify** all categories are discovered correctly
4. **Update** any scripts that referenced KNOWN_CATEGORIES

### For New Deployments

1. No need to manually discover categories
2. Configure CSS selectors only
3. Run test mode first
4. Scraper will discover everything automatically

## Best Practices

### ✅ DO
- Let the scraper discover data dynamically
- Configure CSS selectors accurately
- Test in test mode first
- Monitor for extraction failures
- Fix selector issues immediately

### ❌ DON'T
- Hardcode category lists
- Use fallback values like "Unknown"
- Load data from previous scrape files
- Assume things still work (test regularly)
- Mask failures with defaults

## Benefits of Dynamic Scraping

1. **Completeness:** Discovers ALL categories, not just known ones
2. **Adaptability:** Automatically handles website changes
3. **Visibility:** Failures are explicit and must be fixed
4. **Maintainability:** No manual list updates required
5. **Reliability:** No stale data from previous runs

## Related Documentation

- `docs/category-scraper-fix.md` - Original problem identification
- `docs/hardcoded-elements-audit.md` - Complete audit of issues
- `docs/configuration-guide.md` - Configuration reference
- `docs/extraction-strategies.md` - CSS selector guide

## Questions?

**Q: What if category discovery fails?**  
A: Fix your CSS selectors. The scraper must work with the actual website structure.

**Q: Can I still limit categories in test mode?**  
A: Yes, use `TEST_CATEGORY_LIMIT` in config. The scraper discovers all, then limits for testing.

**Q: What if I need to skip certain categories?**  
A: Add filtering logic in the scraper, but still discover dynamically first.

**Q: What about websites that add/remove categories?**  
A: Perfect - dynamic scraping adapts automatically. No config changes needed.
