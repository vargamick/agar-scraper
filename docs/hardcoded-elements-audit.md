# Hardcoded Elements and Fallback Code Audit

## Executive Summary

This document identifies all hardcoded values and fallback logic in the codebase that undermines dynamic scraping and testing. These elements must be removed to ensure the scraper always operates from fresh data scraped from websites.

**Critical Issue**: The presence of hardcoded categories and fallback logic makes it impossible to verify if the scraper is actually working correctly or just falling back to hardcoded values.

---

## Issues Identified

### 1. KNOWN_CATEGORIES Hardcoding

#### Location: `config/base_config.py` (Line ~70)
```python
# Known Categories (fallback) - should be overridden in client config
KNOWN_CATEGORIES = []
```

**Issue**: 
- Defines `KNOWN_CATEGORIES` as a base configuration option
- Comment explicitly calls it a "fallback"
- This encourages client configs to define hardcoded categories

**Impact**: 
- Creates expectation that categories should be hardcoded
- Used in test scripts as fallback
- Included in config summary reporting

**Remediation**:
- **REMOVE** `KNOWN_CATEGORIES` from base config entirely
- Remove from `get_config_summary()` method
- Update documentation to clarify categories are always scraped dynamically

---

#### Location: `config/clients/agar/client_config.py` (Lines 39-54)
```python
# ============================================================================
# Known Categories
# ============================================================================

KNOWN_CATEGORIES = [
    "toilet-bathroom-cleaners",
    "green-cleaning-products", 
    "vehicle-cleaning",
    "hard-floor-care",
    "specialty-cleaning",
    "disinfectants-antibacterials",
    "kitchen-cleaners",
    "carpet-upholstery",
    "laundry-products",
    "air-fresheners",
    "hand-soaps-sanitisers",
    "all-purpose-floor-cleaners",
    "chlorinated-cleaners-sanitisers",
    "floor-care"
]
```

**Issue**:
- Hardcoded list of 14 categories
- Actually has 57 categories available on website
- Missing all subcategories

**Impact**:
- Would be used as fallback if scraper fails
- Creates false sense of completeness
- Makes testing unreliable

**Remediation**:
- **REMOVE** entire `KNOWN_CATEGORIES` section from client config
- If documentation reference is needed, use comments only (not configuration)

---

#### Location: `config.py` (Root level - Lines 22-38)
```python
# Known categories (fallback if discovery fails)
KNOWN_CATEGORIES = [
    "toilet-bathroom-cleaners",
    "green-cleaning-products", 
    "vehicle-cleaning",
    "hard-floor-care",
    "specialty-cleaning",
    "disinfectants-antibacterials",
    "kitchen-cleaners",
    "carpet-upholstery",
    "laundry-products",
    "air-fresheners",
    "hand-soaps-sanitisers",
    "all-purpose-floor-cleaners",
    "chlorinated-cleaners-sanitisers",
    "floor-care"
]
```

**Issue**:
- Legacy configuration file with hardcoded categories
- Comment explicitly says "fallback if discovery fails"
- Entire `config.py` file appears to be legacy/deprecated

**Impact**:
- Duplicate configuration source
- Confusion about which config to use
- Fallback logic available for old code

**Remediation**:
- **DELETE** `config.py` file entirely if it's no longer used
- OR clearly mark as deprecated with warnings
- Remove all `KNOWN_CATEGORIES` references

---

### 2. Fallback Logic Using Hardcoded Values

#### Location: `scripts/test_connection.py` (Lines 91-96, 108-111)
```python
async def test_category_url(config):
    """Test a sample category URL."""
    from crawl4ai import AsyncWebCrawler
    
    # Get first known category if available
    if hasattr(config, 'KNOWN_CATEGORIES') and config.KNOWN_CATEGORIES:
        category_slug = config.KNOWN_CATEGORIES[0]
    else:
        print("\n⚠️  No KNOWN_CATEGORIES defined in config, skipping category URL test")
        return True, 0
```

**Issue**:
- Uses `KNOWN_CATEGORIES` to test category URL connectivity
- Falls back gracefully if not available
- This is **THE EXACT PROBLEM** - testing with hardcoded values

**Impact**:
- Tests validate hardcoded categories, not actual scraping
- If scraper breaks, tests still pass using hardcoded fallback
- False confidence in system functionality

**Remediation**:
- **REWRITE** test to first scrape categories dynamically
- Use first discovered category for testing
- If no categories can be discovered, test should FAIL (not skip)
- Alternative: Allow explicit `--test-category` parameter for testing specific URLs

---

#### Location: `config/client_config.template.py` (Lines 82-91, 149-150)
```python
# List of known category slugs for fallback if auto-discovery fails
KNOWN_CATEGORIES = [
    "category-slug-1",
    "category-slug-2",
    "category-slug-3"
]

# ... later in checklist ...
# Known categories (update after discovery)
6. [ ] Added at least one KNOWN_CATEGORIES slug
```

**Issue**:
- Template encourages adding hardcoded categories
- Explicitly says "fallback if auto-discovery fails"
- Checklist requires adding hardcoded values

**Impact**:
- All new client configs will have hardcoded categories
- Perpetuates the problem across all deployments
- Makes scraper unreliable by design

**Remediation**:
- **REMOVE** `KNOWN_CATEGORIES` from template entirely
- Update checklist to remove this requirement
- Add note that categories are always discovered dynamically
- Template should emphasize dynamic discovery only

---

#### Location: `scripts/deploy_new_client.py` (Line with `KNOWN_CATEGORIES = []`)
```python
KNOWN_CATEGORIES = []
```

**Issue**:
- Deployment script includes `KNOWN_CATEGORIES` in generated configs
- Even if empty, it creates the expectation

**Impact**:
- New deployments will have this field
- Developers might add hardcoded values later

**Remediation**:
- **REMOVE** from deployment script template generation
- Do not create this field in new client configs

---

### 3. Image Fallback Logic

#### Location: `core/product_scraper.py` (Lines 127-135)
```python
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
```

**Issue**:
- Multiple fallback layers for product images
- Last fallback uses `product_info.get("image")` which comes from product listing
- This masks extraction failures

**Impact**:
- If CSS selectors are broken, silently falls back
- No indication that scraping failed
- Tests may pass even with broken extraction

**Remediation**:
- **DECISION**: This is acceptable fallback logic (multiple extraction strategies from same scrape)
- Trying main_image → gallery → listing is valid strategy hierarchy
- This is NOT masking failures - it's using multiple data sources from successful scrape
- No action needed - this is proper extraction strategy implementation

**Rationale**: This falls under "Acceptable Fallbacks" - trying multiple extraction strategies within the same successful scrape. The data all comes from the website, just from different DOM locations.

---

## Summary of Required Changes

### Critical (Must Fix)

1. ❌ **DELETE** `KNOWN_CATEGORIES` from `config/base_config.py`
2. ❌ **DELETE** `KNOWN_CATEGORIES` from `config/clients/agar/client_config.py`
3. ❌ **DELETE** or mark deprecated `config.py` (root level)
4. ❌ **REWRITE** `scripts/test_connection.py` to scrape categories dynamically
5. ❌ **REMOVE** `KNOWN_CATEGORIES` from `config/client_config.template.py`
6. ❌ **REMOVE** `KNOWN_CATEGORIES` from `scripts/deploy_new_client.py`

### Important (Should Fix)

7. ⚠️ **ADD LOGGING** to image fallback logic in `core/product_scraper.py`
8. ⚠️ **UPDATE** all documentation referencing `KNOWN_CATEGORIES`
9. ⚠️ **REMOVE** `known_categories_count` from `get_config_summary()` in base config

### Testing Requirements

After remediation:
- ✅ Run full scraper test with no hardcoded values
- ✅ Verify test_connection.py discovers categories dynamically
- ✅ Confirm no fallback to hardcoded values occurs
- ✅ Deploy new client and verify no hardcoded category prompts

---

## Principles for Future Development

### Never Use Hardcoded Data

1. **No hardcoded lists of URLs, categories, or products**
2. **No fallback to "known" or "example" values**
3. **Tests must scrape dynamically, not use fixtures**
4. **If scraping fails, the failure must be visible, not masked**

### Acceptable Fallbacks

1. **Multiple extraction strategies** (try CSS selector A, then B, then C)
2. **Multiple data sources within same scrape** (main image → gallery → product listing)
3. **Retry logic with exponential backoff**

### Unacceptable Fallbacks

1. **Using pre-defined lists when scraping fails**
2. **Returning cached/old data silently**
3. **Skipping tests instead of failing when validation fails**
4. **Any logic that says "use hardcoded value if X fails"**

---

## Implementation Priority

### Phase 1: Remove Configuration Hardcoding
- Delete KNOWN_CATEGORIES from all configs
- Update templates to not include it
- Estimated time: 30 minutes

### Phase 2: Fix Test Scripts
- Rewrite test_connection.py to discover categories
- Remove fallback logic
- Estimated time: 1 hour

### Phase 3: Add Warnings/Logging
- Add explicit logging to remaining fallback logic
- Make fallbacks visible in output
- Estimated time: 30 minutes

### Phase 4: Documentation Update
- Update all docs to remove KNOWN_CATEGORIES references
- Add "no hardcoding" principles
- Estimated time: 30 minutes

**Total Estimated Time: 2.5 hours**

---

---

## Additional Findings: Product Collection and Scraping

### 4. Product Name Fallback Logic

#### Location: `core/product_scraper.py` (Lines 140-142)
```python
product_name = clean_product_name(css_data.get("product_name", ""))
if not product_name:
    product_name = product_info.get("title", "Unknown")
```

**Issue**:
- Falls back to "Unknown" if product name extraction fails
- Silent failure - no warning that extraction failed
- Makes it impossible to detect broken CSS selectors

**Impact**:
- Products with failed name extraction still appear successful
- Tests pass even when name extraction is broken
- Data quality issues hidden in output

**Remediation**:
- **REMOVE** "Unknown" fallback entirely
- **FAIL** the extraction if no product name found
- Force proper CSS selector configuration

```python
product_name = clean_product_name(css_data.get("product_name", ""))
if not product_name:
    product_name = product_info.get("title", "")
if not product_name:
    # FAIL - don't mask the problem
    return None  # This forces the extraction to be marked as failed
```

**Priority**: HIGH - Silent failures mask broken configurations

**Rationale**: If we can't extract a product name, the CSS selectors are wrong and need fixing. Returning "Unknown" masks this problem. Better to fail visibly so the configuration gets fixed.

---

#### Location: `core/utils.py` (Lines 14-16, 25-27)
```python
def sanitize_filename(filename: str) -> str:
    """Sanitize filename for saving"""
    if not filename:
        return "unknown"

def clean_product_name(name: str) -> str:
    """Clean up product name by removing common suffixes"""
    if not name:
        return ""
```

**Issue**:
- `sanitize_filename` returns "unknown" for empty input
- `clean_product_name` returns "" for empty input
- Silent handling of empty values masks upstream failures

**Impact**:
- Files named "unknown" may accumulate without notice
- Empty product names propagate through system
- Root cause of empty names not visible

**Remediation**:
- Keep current implementation - these are utility functions
- Empty filename fallback is acceptable for edge cases
- Caller should validate before calling these functions

**Priority**: LOW - No change needed

**Rationale**: These are low-level utility functions. The proper place to handle empty names is in the caller (product scraper), not in utilities. The `sanitize_filename()` function needs a safe fallback for file operations.

---

### 5. Category Loading Fallback

#### Location: `core/product_collector.py` (Lines 137-144)
```python
async def collect_all_products(self, categories: List[Dict] = None) -> List[Dict]:
    """Collect products from all categories."""
    if not categories:
        # Try to load from file
        categories_file = self.output_dir / "categories.json"
        if categories_file.exists():
            categories = load_json(categories_file)
        else:
            raise ValueError("No categories provided and categories.json not found")
```

**Issue**:
- Falls back to loading categories from file if not provided
- This could load old/stale category data
- Bypasses fresh category discovery

**Impact**:
- If categories aren't explicitly passed, uses file instead of scraping
- Could use outdated category list from previous run
- Defeats purpose of dynamic category discovery

**Remediation**:
- Remove file loading fallback entirely
- Always require categories to be explicitly provided
- Force caller to scrape categories fresh

```python
async def collect_all_products(self, categories: List[Dict]) -> List[Dict]:
    """Collect products from all categories.
    
    Args:
        categories: List of category dictionaries (REQUIRED - must be freshly scraped)
    """
    if not categories:
        raise ValueError(
            "No categories provided. Categories must be scraped dynamically using "
            "CategoryScraper.discover_categories() before collecting products."
        )
```

**Priority**: HIGH - This fallback can bypass dynamic discovery

---

### 6. Hardcoded Base URL in Utils

#### Location: `core/utils.py` (Line 57)
```python
def create_run_metadata(run_dir: Path, mode: str = "FULL") -> Dict:
    """Create initial run metadata"""
    metadata = {
        "run_id": run_dir.name,
        "start_time": datetime.now().isoformat(),
        "mode": mode,
        "base_url": "https://agar.com.au",  # HARDCODED!
        "status": "RUNNING",
        "run_directory": str(run_dir.absolute())
    }
```

**Issue**:
- Hardcoded Agar-specific base URL in generic utility function
- Should use config.BASE_URL instead
- Makes utils not truly generic

**Impact**:
- Function only works correctly for Agar
- Other clients would have wrong base_url in metadata
- Violates multi-client design

**Remediation**:
- Add config parameter to function
- Use config.BASE_URL

```python
def create_run_metadata(run_dir: Path, config: Type[BaseConfig], mode: str = "FULL") -> Dict:
    """Create initial run metadata"""
    metadata = {
        "run_id": run_dir.name,
        "start_time": datetime.now().isoformat(),
        "mode": mode,
        "base_url": config.BASE_URL,
        "status": "RUNNING",
        "run_directory": str(run_dir.absolute())
    }
```

**Priority**: HIGH - Breaks multi-client design

---

## Positive Findings

### Good Implementations (No Issues Found)

1. ✅ **core/product_pdf_scraper.py**: All PDF URL extraction is dynamic from pages
2. ✅ **core/pdf_downloader.py**: All downloads based on scraped metadata
3. ✅ **core/product_collector.py**: Product collection is fully dynamic (except category file fallback)

These modules correctly implement dynamic scraping with no hardcoded data or problematic fallbacks.

---

## Updated Summary of Required Changes

### Critical (Must Fix)

1. ❌ **DELETE** `KNOWN_CATEGORIES` from `config/base_config.py`
2. ❌ **DELETE** `KNOWN_CATEGORIES` from `config/clients/agar/client_config.py`
3. ❌ **DELETE** or mark deprecated `config.py` (root level)
4. ❌ **REWRITE** `scripts/test_connection.py` to scrape categories dynamically
5. ❌ **REMOVE** `KNOWN_CATEGORIES` from `config/client_config.template.py`
6. ❌ **REMOVE** `KNOWN_CATEGORIES` from `scripts/deploy_new_client.py`
7. ❌ **FIX** hardcoded base URL in `core/utils.py` `create_run_metadata()`
8. ❌ **REMOVE** category file loading fallback from `core/product_collector.py`

### Important (Should Fix)

9. ⚠️ **REMOVE** "Unknown" fallback in product name extraction (fail instead)
10. ⚠️ **UPDATE** all documentation referencing `KNOWN_CATEGORIES`
11. ⚠️ **REMOVE** `known_categories_count` from `get_config_summary()` in base config

### Testing Requirements

After remediation:
- ✅ Run full scraper test with no hardcoded values
- ✅ Verify test_connection.py discovers categories dynamically
- ✅ Confirm no fallback to hardcoded values occurs
- ✅ Verify no category file loading occurs
- ✅ Test with multiple clients to ensure no Agar-specific hardcoding
- ✅ Verify extractions fail visibly when CSS selectors are broken
- ✅ Deploy new client and verify no hardcoded category prompts

---

## Comprehensive Issue Count

### By Severity
- **Critical Issues**: 8 (must fix before production use)
- **Important Issues**: 3 (should fix for code quality)
- **Total Issues**: 11

### By Category
- **Hardcoded Categories**: 6 issues
- **Hardcoded Values**: 1 issue (base URL)
- **Silent Fallbacks**: 4 issues
- **Bypass Logic**: 2 issues

---

## Implementation Priority (Updated)

### Phase 1: Remove Configuration Hardcoding (CRITICAL)
1. Delete KNOWN_CATEGORIES from all configs
2. Remove from templates and deployment scripts
3. Fix hardcoded base URL in utils
4. Remove category file loading fallback
- **Estimated time: 45 minutes**

### Phase 2: Fix Test Scripts (CRITICAL)
1. Rewrite test_connection.py to discover categories
2. Remove all fallback logic from tests
- **Estimated time: 1 hour**

### Phase 3: Remove Silent Fallbacks (IMPORTANT)
1. Remove "Unknown" product name fallback (fail instead)
2. Verify Crawl4AI logging is properly configured
3. Test that extraction failures are visible
- **Estimated time: 30 minutes**

### Phase 4: Documentation Update (IMPORTANT)
1. Update all docs to remove KNOWN_CATEGORIES references
2. Add "no hardcoding" principles
3. Document proper multi-client usage
- **Estimated time: 30 minutes**

**Total Estimated Time: 2.5 hours**

---

## Date
November 6, 2025

## Status
✅ **IMPLEMENTATION COMPLETE** - All remediation items have been successfully implemented (June 11, 2025)

### Implementation Summary
- ✅ All 8 critical issues resolved
- ✅ All 3 important issues resolved
- ✅ Total: 11/11 issues fixed
- ✅ New architecture document created: `docs/dynamic-scraping-architecture.md`
- ✅ All code now enforces dynamic scraping with visible failures
- ✅ Testing required before marking as production-ready

**See:** `docs/dynamic-scraping-architecture.md` for the new architecture and design principles.
