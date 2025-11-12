# Change Detection Analysis for Agar Scraper

## Executive Summary

Product pages on agar.com.au include **`article:modified_time`** metadata that can be used to detect when pages have been updated. This allows for efficient incremental scraping by only re-scraping changed pages.

## Current Findings

### Available Date Metadata

From analyzing a live product page (All Fresh), the following metadata is available:

```json
{
  "modifiedTime": "2025-06-19T02:48:18+00:00",
  "article:modified_time": "2025-06-19T02:48:18+00:00"
}
```

This metadata is present in **Open Graph (og:) meta tags** which are standard for WordPress/WooCommerce sites.

### Current Scraping Behavior

The scraper currently:
1. **Does NOT capture** the `modified_time` metadata
2. Records only `scraped_at` timestamp (when we scraped it)
3. Has no mechanism to compare previous scrapes
4. Always re-scrapes all products on each run

## Proposed Solution

### 1. Add Modified Time Capture

Update `product_scraper.py` to extract and store the page's `article:modified_time`:

```python
# Add to product data schema
{
    "product_name": "...",
    "product_url": "...",
    "page_modified_at": "2025-06-19T02:48:18+00:00",  # NEW
    "scraped_at": "2025-10-31T15:25:03.497539",
    # ... rest of fields
}
```

### 2. Implement Change Detection Module

Create `change_detector.py`:

```python
"""
Change detection module for incremental scraping
Compares page modification times to determine what needs re-scraping
"""

class ChangeDetector:
    def __init__(self, previous_run_dir: Path):
        """Load data from previous scraping run"""
        self.previous_data = self.load_previous_run(previous_run_dir)
    
    def needs_update(self, product_url: str, current_modified_time: str) -> bool:
        """
        Check if product needs re-scraping based on modified time
        
        Returns:
            True if product is new or has been modified since last scrape
            False if product hasn't changed
        """
        if product_url not in self.previous_data:
            return True  # New product
        
        previous_modified = self.previous_data[product_url].get("page_modified_at")
        if not previous_modified:
            return True  # No previous modified time, re-scrape
        
        return current_modified_time > previous_modified
    
    def get_changes_summary(self, all_products: List[Dict]) -> Dict:
        """
        Analyze all products and return change statistics
        """
        new = []
        modified = []
        unchanged = []
        
        for product in all_products:
            url = product["url"]
            modified_time = product.get("page_modified_at")
            
            if url not in self.previous_data:
                new.append(url)
            elif self.needs_update(url, modified_time):
                modified.append(url)
            else:
                unchanged.append(url)
        
        return {
            "new": len(new),
            "modified": len(modified),
            "unchanged": len(unchanged),
            "total": len(all_products)
        }
```

### 3. Update Main Pipeline

Modify `main.py` to support incremental mode:

```python
class AgarScraperOrchestrator:
    def __init__(self, ..., incremental_mode: bool = False, previous_run_dir: Path = None):
        self.incremental_mode = incremental_mode
        self.change_detector = None
        
        if incremental_mode:
            if not previous_run_dir:
                raise ValueError("Previous run directory required for incremental mode")
            self.change_detector = ChangeDetector(previous_run_dir)
    
    async def run(self):
        # ... existing steps ...
        
        # NEW: Before Step 3, check for changes
        if self.incremental_mode:
            # Quick scan to get modified times only
            modified_times = await self.quick_scan_modified_times(all_products)
            
            # Filter products that need updates
            products_to_scrape = []
            for product in all_products:
                url = product["url"]
                modified_time = modified_times.get(url)
                
                if self.change_detector.needs_update(url, modified_time):
                    product["page_modified_at"] = modified_time
                    products_to_scrape.append(product)
            
            print(f"📊 Change Detection Results:")
            print(f"   - Total products: {len(all_products)}")
            print(f"   - Need updates: {len(products_to_scrape)}")
            print(f"   - Unchanged: {len(all_products) - len(products_to_scrape)}")
            
            all_products = products_to_scrape
        
        # Continue with existing scraping...
```

### 4. Quick Metadata Scan

Create lightweight scan function to only fetch metadata:

```python
async def quick_scan_modified_times(self, products: List[Dict]) -> Dict[str, str]:
    """
    Quickly scan products to get their modified times without full scraping
    Uses HEAD requests or minimal page loads
    """
    modified_times = {}
    
    async with AsyncWebCrawler() as crawler:
        for product in products:
            url = product["url"]
            
            # Lightweight fetch - only get metadata
            result = await crawler.arun(
                url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=10000,  # Shorter timeout
                    wait_for="css:meta[property='article:modified_time']"
                )
            )
            
            if result.success:
                # Extract modified time from HTML
                # Parse the meta tag: <meta property="article:modified_time" content="...">
                modified_time = extract_modified_time_from_html(result.html)
                modified_times[url] = modified_time
    
    return modified_times
```

## Implementation Strategy

### Phase 1: Data Collection (Immediate)
1. Update `product_scraper.py` to capture `page_modified_at`
2. Run full scrapes to establish baseline with modification times
3. Store this data for future comparisons

### Phase 2: Change Detection (Next Sprint)
1. Implement `change_detector.py` module
2. Add quick metadata scanning function
3. Update main orchestrator to support `--incremental` mode

### Phase 3: Optimization (Future)
1. Implement smart caching of unchanged product data
2. Add partial update capability (only update changed fields)
3. Create change history/audit log

## Usage Examples

### Initial Full Scrape (Baseline)
```bash
python main.py --full
# Creates: agar_scrapes/AgarScrape_20251101_100000/
```

### Incremental Scrape (Only Changed Pages)
```bash
python main.py --incremental \
    --previous-run agar_scrapes/AgarScrape_20251101_100000
```

### Force Full Scrape (Ignore Changes)
```bash
python main.py --full  # Always scrapes everything
```

## Benefits

### Efficiency Gains
- **Time Savings**: Skip unchanged products (potentially 80-90% reduction)
- **Resource Usage**: Fewer HTTP requests and browser instances
- **Rate Limiting**: Reduced load on target website

### Data Quality
- **Change Tracking**: Know exactly when products were updated
- **Audit Trail**: Historical record of all modifications
- **Validation**: Can verify if scraping caught all changes

### Operational
- **Faster Updates**: Run incremental scrapes more frequently
- **Cost Reduction**: Lower compute and bandwidth costs
- **Scalability**: Easier to scale to larger product catalogs

## Metadata Extraction Details

### Meta Tags Available
```html
<meta property="og:title" content="All Fresh - Bathroom Cleaner | Agar Cleaning Systems">
<meta property="og:description" content="...">
<meta property="article:modified_time" content="2025-06-19T02:48:18+00:00">
<meta property="og:image" content="https://agar.com.au/wp-content/uploads/2023/08/All-Fresh-5L.png">
```

### Extraction Methods

#### Method 1: Regex on HTML
```python
import re
from datetime import datetime

def extract_modified_time_from_html(html: str) -> str:
    """Extract article:modified_time from meta tags"""
    pattern = r'<meta\s+property=["\']article:modified_time["\']\s+content=["\'](.*?)["\']'
    match = re.search(pattern, html)
    return match.group(1) if match else None
```

#### Method 2: CSS Selector with Crawl4AI
```python
# Add to extraction schema
{
    "name": "Page Metadata",
    "baseSelector": "head",
    "fields": [
        {
            "name": "modified_time",
            "selector": "meta[property='article:modified_time']",
            "type": "attribute",
            "attribute": "content"
        }
    ]
}
```

#### Method 3: Parse HTML with BeautifulSoup
```python
from bs4 import BeautifulSoup

def extract_modified_time_from_html(html: str) -> str:
    """Extract using BeautifulSoup for reliability"""
    soup = BeautifulSoup(html, 'html.parser')
    meta_tag = soup.find('meta', property='article:modified_time')
    return meta_tag['content'] if meta_tag else None
```

## Comparison Logic

### Date Comparison
```python
from datetime import datetime

def parse_iso_datetime(dt_string: str) -> datetime:
    """Parse ISO 8601 datetime string"""
    return datetime.fromisoformat(dt_string.replace('+00:00', '+00:00'))

def is_modified(old_time: str, new_time: str) -> bool:
    """Check if new time is later than old time"""
    old_dt = parse_iso_datetime(old_time)
    new_dt = parse_iso_datetime(new_time)
    return new_dt > old_dt
```

### Edge Cases to Handle
1. **Missing metadata**: Treat as modified (re-scrape)
2. **Invalid dates**: Log warning, treat as modified
3. **Timezone differences**: All times in UTC+00:00
4. **Clock skew**: Allow small tolerance (e.g., 1 minute)

## Testing Strategy

### Unit Tests
```python
def test_needs_update_new_product():
    """New products should always need update"""
    detector = ChangeDetector({})
    assert detector.needs_update("https://new.com", "2025-01-01T00:00:00+00:00")

def test_needs_update_modified():
    """Modified products should need update"""
    previous = {"https://old.com": {"page_modified_at": "2025-01-01T00:00:00+00:00"}}
    detector = ChangeDetector(previous)
    assert detector.needs_update("https://old.com", "2025-01-02T00:00:00+00:00")

def test_needs_update_unchanged():
    """Unchanged products should not need update"""
    previous = {"https://same.com": {"page_modified_at": "2025-01-01T00:00:00+00:00"}}
    detector = ChangeDetector(previous)
    assert not detector.needs_update("https://same.com", "2025-01-01T00:00:00+00:00")
```

### Integration Tests
```python
async def test_incremental_scrape():
    """Test full incremental scraping workflow"""
    # Setup: Previous run with 100 products
    # Modify: 10 products on website
    # Run: Incremental scrape
    # Assert: Only 10 products re-scraped
```

## Monitoring & Reporting

### Change Detection Report
```json
{
  "run_id": "AgarScrape_20251101_120000",
  "mode": "INCREMENTAL",
  "previous_run": "AgarScrape_20251031_100000",
  "change_detection": {
    "total_products": 450,
    "new_products": 5,
    "modified_products": 23,
    "unchanged_products": 422,
    "products_scraped": 28,
    "time_saved_estimate": "45 minutes"
  },
  "modified_products_list": [
    {
      "name": "All Fresh",
      "url": "https://agar.com.au/product/all-fresh/",
      "previous_modified": "2025-06-19T02:48:18+00:00",
      "current_modified": "2025-10-31T10:30:00+00:00",
      "changes_detected": true
    }
  ]
}
```

## Risks & Mitigation

### Risk 1: Metadata Not Updated
**Problem**: Website doesn't update `modified_time` when page changes  
**Mitigation**: Periodic full scrapes (e.g., monthly) to catch missed changes

### Risk 2: False Negatives
**Problem**: Missing actual changes due to metadata issues  
**Mitigation**: 
- Hash comparison as backup (compare content hash)
- Alert on suspiciously long unchanged periods

### Risk 3: Clock Skew
**Problem**: Server time differences causing false positives  
**Mitigation**: Use UTC consistently, allow small time tolerance

## Recommendations

### Immediate Actions
1. ✅ Update `product_scraper.py` to capture `page_modified_at`
2. ✅ Run baseline scrapes to collect initial modification times
3. ✅ Add modified_time to product data schema

### Short Term (Next 2 Weeks)
1. Implement `change_detector.py` module
2. Add `--incremental` flag to main.py
3. Test with sample incremental runs

### Long Term (Next Month)
1. Add content hashing as backup verification
2. Implement change history/audit log
3. Create dashboard for change statistics
4. Optimize metadata scanning performance

## Conclusion

The presence of `article:modified_time` metadata on Agar product pages provides an excellent foundation for implementing efficient change detection. This will dramatically reduce scraping time and resources while ensuring we capture all product updates.

**Key Success Metrics:**
- Reduce scraping time by 70-90% on incremental runs
- Detect 100% of product changes
- Maintain data freshness with more frequent updates

**Next Steps:**
1. Implement metadata capture (1 day)
2. Build change detector module (2 days)
3. Integrate with main pipeline (1 day)
4. Test and validate (2 days)

**Total Implementation Estimate: 6 days**
