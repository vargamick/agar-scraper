# 3DN Scraper Template - Extraction Strategies Guide

**Version:** 1.0  
**Last Updated:** 2025-01-11  
**Template Version:** 1.0.0

---

## Table of Contents

1. [Introduction](#introduction)
2. [CSS Selector Fundamentals](#css-selector-fundamentals)
3. [Strategy Pattern Overview](#strategy-pattern-overview)
4. [Category Page Extraction](#category-page-extraction)
5. [Product Page Extraction](#product-page-extraction)
6. [PDF/Document Extraction](#pdfdocument-extraction)
7. [Testing Selectors](#testing-selectors)
8. [Advanced Extraction Techniques](#advanced-extraction-techniques)
9. [Common Patterns & Examples](#common-patterns--examples)
10. [Troubleshooting Extraction Issues](#troubleshooting-extraction-issues)

---

## Introduction

Extraction strategies define how the 3DN Scraper Template extracts data from web pages. The extraction process relies on **CSS selectors** to identify and extract specific elements from HTML.

### What is an Extraction Strategy?

An extraction strategy consists of:

1. **Category selectors** - Extract product lists from category pages
2. **Product selectors** - Extract details from product pages
3. **PDF selectors** - Extract document links (optional)
4. **Custom logic** - Advanced extraction for complex cases (optional)

### Why CSS Selectors?

CSS selectors are:
- **Powerful** - Can target specific elements precisely
- **Flexible** - Work across different HTML structures
- **Standard** - Widely used and well-documented
- **Testable** - Easy to test in browser developer tools

---

## CSS Selector Fundamentals

### Basic Selector Types

| Type | Syntax | Description | Example |
|------|--------|-------------|---------|
| **Element** | `tag` | Select by HTML tag | `div`, `h1`, `a` |
| **Class** | `.classname` | Select by class | `.product`, `.title` |
| **ID** | `#idname` | Select by ID | `#main`, `#product-123` |
| **Attribute** | `[attr]` | Select by attribute | `[href]`, `[data-id]` |
| **Attribute Value** | `[attr='value']` | Select by exact value | `[type='submit']` |
| **Attribute Contains** | `[attr*='value']` | Select if contains | `[href*='SDS']` |

### Combining Selectors

| Type | Syntax | Description | Example |
|------|--------|-------------|---------|
| **Descendant** | `A B` | B inside A (any level) | `div.product a` |
| **Child** | `A > B` | B direct child of A | `ul > li` |
| **Multiple** | `A, B` | Select A or B | `.title, h1` |
| **Chaining** | `AB` | Element with both | `div.product` |
| **Pseudo** | `A:pseudo` | Pseudo-selector | `a:first-child` |

### Examples

```css
/* Simple selectors */
h1                          /* All h1 elements */
.product                    /* Elements with class="product" */
#main-content              /* Element with id="main-content" */

/* Combined selectors */
ul.products li             /* li inside ul with class="products" */
div.product > a            /* a that is direct child of div.product */
a[href*='pdf']             /* Links containing 'pdf' in href */

/* Specific selectors */
h1.product-title           /* h1 with class="product-title" */
div.product a.link         /* a.link inside div.product */
[data-product-id]          /* Elements with data-product-id attribute */
```

### Testing Selectors in Browser

Open browser developer tools (F12):

```javascript
// Test single element
document.querySelector("h1.product-title")

// Test multiple elements
document.querySelectorAll("ul.products li.product")

// Get text content
document.querySelector("h1.product-title").textContent

// Get attribute
document.querySelector("a.product-link").getAttribute("href")

// Get all matching elements
Array.from(document.querySelectorAll("ul.products li.product"))
    .map(el => el.textContent)
```

---

## Strategy Pattern Overview

### Extraction Strategy Structure

**File:** `config/clients/{client_name}/extraction_strategies.py`

```python
from typing import Dict, List
from strategies.base_strategy import ExtractionStrategy

class ClientExtractionStrategy(ExtractionStrategy):
    """Client-specific CSS selectors and extraction logic"""
    
    # Category page selectors
    CATEGORY_SELECTORS = {
        "products": "CSS selector here",
        "product_link": "CSS selector here",
        "product_name": "CSS selector here"
    }
    
    # Product page selectors
    PRODUCT_SELECTORS = {
        "name": "CSS selector here",
        "image": "CSS selector here",
        "description": "CSS selector here",
        # ... more fields
    }
    
    # PDF/Document selectors (optional)
    PDF_SELECTORS = {
        "sds_link": "CSS selector here",
        "pds_link": "CSS selector here"
    }
```

### Inheritance Hierarchy

```
BaseStrategy (base class)
    ↓
ClientExtractionStrategy (your implementation)
    ↓
CategoryScraper, ProductScraper (use selectors)
```

---

## Category Page Extraction

Category pages list multiple products. We need to identify:
1. Individual product containers
2. Product URLs
3. Product names (optional)

### Required Selectors

```python
CATEGORY_SELECTORS = {
    "products": "selector for product containers",
    "product_link": "selector for product URL",
    "product_name": "selector for product name (optional)"
}
```

### Strategy

1. **Find the container** that holds all products
2. **Identify repeating pattern** for each product
3. **Extract the link** to product detail page
4. **Optionally extract name** for logging

### Example: WooCommerce

```html
<!-- HTML Structure -->
<ul class="products">
    <li class="product">
        <a href="/product/cleaning-solution/" class="woocommerce-LoopProduct-link">
            <h2 class="woocommerce-loop-product__title">Cleaning Solution</h2>
            <img src="image.jpg">
        </a>
    </li>
    <li class="product">
        <a href="/product/disinfectant/" class="woocommerce-LoopProduct-link">
            <h2 class="woocommerce-loop-product__title">Disinfectant</h2>
            <img src="image.jpg">
        </a>
    </li>
</ul>
```

**Selectors:**
```python
CATEGORY_SELECTORS = {
    "products": "ul.products li.product",
    "product_link": "a.woocommerce-LoopProduct-link",
    "product_name": "h2.woocommerce-loop-product__title"
}
```

### Example: Shopify

```html
<!-- HTML Structure -->
<div class="product-grid">
    <div class="product-card">
        <a href="/products/product-1" class="product-link">
            <div class="product-info">
                <h3 class="product-title">Product 1</h3>
            </div>
        </a>
    </div>
    <div class="product-card">
        <a href="/products/product-2" class="product-link">
            <div class="product-info">
                <h3 class="product-title">Product 2</h3>
            </div>
        </a>
    </div>
</div>
```

**Selectors:**
```python
CATEGORY_SELECTORS = {
    "products": "div.product-card",
    "product_link": "a.product-link",
    "product_name": "h3.product-title"
}
```

### Example: Custom Structure

```html
<!-- HTML Structure -->
<section id="products">
    <article data-product-id="123">
        <a href="/item/product-a">
            <span class="name">Product A</span>
        </a>
    </article>
    <article data-product-id="124">
        <a href="/item/product-b">
            <span class="name">Product B</span>
        </a>
    </article>
</section>
```

**Selectors:**
```python
CATEGORY_SELECTORS = {
    "products": "article[data-product-id]",
    "product_link": "a",
    "product_name": "span.name"
}
```

### Finding Category Selectors: Step-by-Step

1. **Open category page in browser**
2. **Press F12** to open developer tools
3. **Click Inspector/Elements tab**
4. **Find the product list:**
   - Look for repeating structures
   - Common containers: `<ul>`, `<div class="products">`, `<section>`

5. **Identify individual product:**
   ```javascript
   // Test in console
   document.querySelectorAll("YOUR_SELECTOR")
   // Should return multiple elements (one per product)
   ```

6. **Find the link within each product:**
   ```javascript
   // Test relative to product
   let product = document.querySelector("YOUR_PRODUCT_SELECTOR")
   product.querySelector("a")  // Should find product link
   ```

7. **Find the name within each product:**
   ```javascript
   let product = document.querySelector("YOUR_PRODUCT_SELECTOR")
   product.querySelector("h2, h3, .title")  // Find name
   ```

### Validation Checklist

- [ ] `products` selector returns multiple elements (one per product)
- [ ] `product_link` selector finds link within each product
- [ ] `product_name` selector finds name within each product (if used)
- [ ] Links are valid URLs (absolute or relative)
- [ ] Selectors work on multiple category pages

---

## Product Page Extraction

Product pages contain detailed information about a single product.

### Required Selectors

```python
PRODUCT_SELECTORS = {
    "name": "selector for product name",        # Required
    "image": "selector for main image",          # Recommended
    "description": "selector for description",   # Recommended
    "overview": "selector for summary",          # Optional
    "sku": "selector for product code",          # Optional
    "categories": "selector for categories"      # Optional
}
```

### Strategy

1. **Identify main content area** (often has class like `.product`, `.detail`)
2. **Find unique identifiers** for each field
3. **Test selectors** return correct content
4. **Handle missing fields** gracefully

### Example: WooCommerce Product Page

```html
<!-- HTML Structure -->
<div class="product">
    <h1 class="product_title">All-Purpose Cleaner</h1>
    
    <div class="woocommerce-product-gallery">
        <img src="product-image.jpg" alt="Product">
    </div>
    
    <div class="product-overview">
        <p>Fast-acting cleaner for all surfaces...</p>
    </div>
    
    <div class="woocommerce-Tabs-panel woocommerce-Tabs-panel--description">
        <h2>Description</h2>
        <p>Detailed product description...</p>
    </div>
    
    <div class="product_meta">
        <span class="sku">SKU: APC-1000</span>
        <span class="posted_in">Categories: 
            <a href="/category/cleaners">Cleaners</a>,
            <a href="/category/all-purpose">All-Purpose</a>
        </span>
    </div>
</div>
```

**Selectors:**
```python
PRODUCT_SELECTORS = {
    "name": "h1.product_title",
    "image": "div.woocommerce-product-gallery img",
    "overview": "div.product-overview",
    "description": "div.woocommerce-Tabs-panel--description",
    "sku": "span.sku",
    "categories": "span.posted_in a"
}
```

### Example: Simple Product Page

```html
<!-- HTML Structure -->
<div class="product-detail">
    <h1 class="title">Product Name</h1>
    <img class="main-image" src="image.jpg">
    <div class="summary">Short description...</div>
    <div class="full-description">Long description...</div>
    <div class="meta">
        <span class="code">Code: PROD123</span>
    </div>
</div>
```

**Selectors:**
```python
PRODUCT_SELECTORS = {
    "name": "h1.title",
    "image": "img.main-image",
    "overview": "div.summary",
    "description": "div.full-description",
    "sku": "span.code"
}
```

### Example: Complex Product Page

```html
<!-- HTML Structure -->
<article class="product-container">
    <header>
        <h1 itemprop="name">Product Name</h1>
    </header>
    
    <section class="images">
        <figure class="primary">
            <img data-src="main.jpg" src="thumb.jpg">
        </figure>
    </section>
    
    <section class="details">
        <div class="brief">Short text...</div>
        <div class="extended">Long text...</div>
    </section>
    
    <aside class="info">
        <dl>
            <dt>SKU:</dt>
            <dd>12345</dd>
            <dt>Category:</dt>
            <dd><a href="/cat">Category</a></dd>
        </dl>
    </aside>
</article>
```

**Selectors:**
```python
PRODUCT_SELECTORS = {
    "name": "h1[itemprop='name']",
    "image": "section.images img[data-src]",
    "overview": "div.brief",
    "description": "div.extended",
    "sku": "aside.info dd",  # First dd element
    "categories": "aside.info a"
}
```

### Field-Specific Extraction Tips

#### Product Name
- Usually in `<h1>` tag
- May have specific class: `.product-title`, `.product_title`, `.title`
- Sometimes has schema.org markup: `[itemprop="name"]`

```python
# Common patterns
"name": "h1.product-title"
"name": "h1.product_title"
"name": "h1[itemprop='name']"
"name": "div.product h1"
```

#### Product Image
- Main image usually in `<img>` tag
- May be in gallery/slider container
- Check for lazy loading: `data-src` vs `src`
- May need to target specific image in carousel

```python
# Common patterns
"image": "img.product-image"
"image": "div.gallery img.main"
"image": "img[itemprop='image']"
"image": "div.product-images img:first-child"
```

#### Description
- Often in `<div>` with class containing "description"
- May be in tabs/accordion
- Separate brief (overview) vs full description

```python
# Common patterns
"description": "div.description"
"description": "div.product-description"
"description": "div[id*='description']"
"description": "div.tab-content.description"
```

#### SKU/Product Code
- Often in `<span>` in product meta
- May be in data attribute
- Label may be included in text: "SKU: ABC123"

```python
# Common patterns
"sku": "span.sku"
"sku": "span.product-code"
"sku": "[data-sku]"
"sku": "div.meta .sku"
```

#### Categories
- Usually links (`<a>`) in meta section
- May be breadcrumbs
- Multiple categories possible

```python
# Common patterns
"categories": "span.posted_in a"
"categories": "div.categories a"
"categories": "div.product-meta a.category"
"categories": "nav.breadcrumb a"
```

### Finding Product Selectors: Step-by-Step

1. **Open product page in browser**
2. **Press F12** to open developer tools
3. **Right-click element** → **Inspect**
4. **Note the HTML structure**
5. **Test in console:**
   ```javascript
   // Product name
   document.querySelector("h1.product-title").textContent
   
   // Product image
   document.querySelector("img.main").src
   
   // Description
   document.querySelector(".description").textContent
   ```

6. **Verify on multiple products** to ensure consistency

### Validation Checklist

- [ ] All required fields have selectors
- [ ] Selectors return expected content
- [ ] Selectors work on multiple product pages
- [ ] Handle missing optional fields gracefully
- [ ] Image URLs are absolute (or can be made absolute)
- [ ] Text content is clean (no extra whitespace/HTML)

---

## PDF/Document Extraction

For products with downloadable documents (SDS, PDS, datasheets).

### Required Configuration

In `client_config.py`:
```python
HAS_SDS_DOCUMENTS = True
HAS_PDS_DOCUMENTS = True
```

In `extraction_strategies.py`:
```python
PDF_SELECTORS = {
    "sds_link": "selector for SDS document link",
    "pds_link": "selector for PDS document link",
    "document_section": "optional container selector"
}
```

### Finding Document Links

#### Strategy 1: Link Text Contains Keyword

```html
<a href="/docs/product-sds.pdf">Safety Data Sheet (SDS)</a>
<a href="/docs/product-pds.pdf">Product Data Sheet (PDS)</a>
```

**Selectors:**
```python
PDF_SELECTORS = {
    "sds_link": "a[href*='sds']",      # href contains 'sds'
    "pds_link": "a[href*='pds']"       # href contains 'pds'
}
```

#### Strategy 2: Link in Specific Container

```html
<div class="product-documents">
    <a href="/docs/safety.pdf" class="doc-sds">SDS</a>
    <a href="/docs/datasheet.pdf" class="doc-pds">PDS</a>
</div>
```

**Selectors:**
```python
PDF_SELECTORS = {
    "sds_link": "div.product-documents a.doc-sds",
    "pds_link": "div.product-documents a.doc-pds",
    "document_section": "div.product-documents"
}
```

#### Strategy 3: Data Attributes

```html
<a href="/docs/product1.pdf" data-type="sds">Download SDS</a>
<a href="/docs/product2.pdf" data-type="pds">Download PDS</a>
```

**Selectors:**
```python
PDF_SELECTORS = {
    "sds_link": "a[data-type='sds']",
    "pds_link": "a[data-type='pds']"
}
```

#### Strategy 4: Icon/Image Based

```html
<div class="downloads">
    <a href="/sds.pdf">
        <img src="/icons/sds.png" alt="SDS">
    </a>
    <a href="/pds.pdf">
        <img src="/icons/pds.png" alt="PDS">
    </a>
</div>
```

**Selectors:**
```python
PDF_SELECTORS = {
    "sds_link": "a img[alt='SDS']",  # Then get parent <a>
    "pds_link": "a img[alt='PDS']",  # Then get parent <a>
    "document_section": "div.downloads"
}
```

### Testing PDF Selectors

```javascript
// Find SDS link
let sdsLink = document.querySelector("a[href*='sds']")
console.log(sdsLink.href)  // Should be full URL to PDF

// Find PDS link
let pdsLink = document.querySelector("a[href*='pds']")
console.log(pdsLink.href)  // Should be full URL to PDF

// Test both exist
if (sdsLink && pdsLink) {
    console.log("✓ Both documents found")
}
```

### Common Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| `[href*='SDS']` | href contains 'SDS' (case-sensitive) | Works for `/docs/ProductSDS.pdf` |
| `[href*='sds' i]` | href contains 'sds' (case-insensitive) | Works for `/docs/product_SDS.pdf` |
| `.download-sds` | Specific class | Works if consistent class names |
| `a:contains('SDS')` | NOT SUPPORTED in CSS | Use attribute selectors instead |

### Validation Checklist

- [ ] SDS selector finds SDS document link (if HAS_SDS_DOCUMENTS=True)
- [ ] PDS selector finds PDS document link (if HAS_PDS_DOCUMENTS=True)
- [ ] Links point to actual PDF files
- [ ] URLs are absolute or can be made absolute
- [ ] Selectors work on multiple product pages
- [ ] Handle products without documents gracefully

---

## Testing Selectors

### Browser Console Testing

**Step 1: Open Developer Tools**
```
1. Navigate to target page
2. Press F12 (Windows/Linux) or Cmd+Option+I (Mac)
3. Click Console tab
```

**Step 2: Test Selectors**
```javascript
// Test single element
document.querySelector("h1.product-title")

// Test multiple elements
document.querySelectorAll("ul.products li")

// Count elements
document.querySelectorAll("ul.products li").length

// Get text content
document.querySelector("h1.product-title").textContent

// Get attribute
document.querySelector("a.product-link").getAttribute("href")

// Test if element exists
document.querySelector("div.description") !== null
```

**Step 3: Iterate Through Multiple Elements**
```javascript
// Get all products
let products = document.querySelectorAll("li.product")

// Loop through
products.forEach((product, index) => {
    let link = product.querySelector("a").href
    let name = product.querySelector("h2").textContent
    console.log(`${index + 1}. ${name} -> ${link}`)
})
```

### Using test_extraction.py Script

```bash
# Test category page
python scripts/test_extraction.py \
    --client clientname \
    --url "https://site.com/category/products/" \
    --type category

# Test product page
python scripts/test_extraction.py \
    --client clientname \
    --url "https://site.com/product/example/"

# Save results for debugging
python scripts/test_extraction.py \
    --client clientname \
    --url "https://site.com/product/example/" \
    --save
```

### Validation Workflow

1. **Test in browser first**
   ```javascript
   document.querySelectorAll("your-selector")
   ```

2. **Add to extraction_strategies.py**
   ```python
   PRODUCT_SELECTORS = {
       "name": "your-selector"
   }
   ```

3. **Test with script**
   ```bash
   python scripts/test_extraction.py --client clientname --url "url"
   ```

4. **Iterate until working**
   - Review error messages
   - Adjust selectors
   - Re-test

5. **Test on multiple pages**
   - Different categories
   - Different products
   - Edge cases

---

## Advanced Extraction Techniques

### Custom Extraction Methods

For complex cases, override extraction methods:

```python
from typing import Dict, List
from strategies.base_strategy import ExtractionStrategy
from bs4 import BeautifulSoup
import re

class ClientExtractionStrategy(ExtractionStrategy):
    """Advanced extraction for complex scenarios"""
    
    # Standard selectors
    PRODUCT_SELECTORS = {
        "name": "h1.title",
        # ... other selectors
    }
    
    def extract_product_data(self, html: str) -> Dict:
        """
        Override for custom extraction logic
        
        Args:
            html: Raw HTML content
            
        Returns:
            Dictionary with extracted data
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Custom extraction
        product_data = {
            "name": self._extract_name(soup),
            "price": self._extract_price(soup),
            "availability": self._extract_availability(soup),
            "specifications": self._extract_specifications(soup)
        }
        
        return product_data
    
    def _extract_name(self, soup: BeautifulSoup) -> str:
        """Extract product name with cleaning"""
        name_elem = soup.select_one("h1.title")
        if name_elem:
            # Clean up name
            name = name_elem.get_text(strip=True)
            # Remove SKU from name if present
            name = re.sub(r'\s*\(SKU:.*?\)', '', name)
            return name
        return ""
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Extract and parse price"""
        price_elem = soup.select_one("span.price")
        if price_elem:
            # Extract numeric value
            price_text = price_elem.get_text(strip=True)
            # Remove currency symbol and parse
            price = re.sub(r'[^\d.]', '', price_text)
            return float(price) if price else 0.0
        return 0.0
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Determine product availability"""
        stock_elem = soup.select_one("div.stock-status")
        if stock_elem:
            status = stock_elem.get_text(strip=True).lower()
            if 'in stock' in status:
                return "available"
            elif 'out of stock' in status:
                return "unavailable"
        return "unknown"
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict:
        """Extract product specifications from table"""
        specs = {}
        spec_table = soup.select_one("table.specifications")
        if spec_table:
            rows = spec_table.select("tr")
            for row in rows:
                label = row.select_one("th")
                value = row.select_one("td")
                if label and value:
                    specs[label.get_text(strip=True)] = value.get_text(strip=True)
        return specs
```

### Handling Dynamic Content

For JavaScript-rendered content:

```python
def extract_product_data(self, html: str) -> Dict:
    """Handle JavaScript-rendered content"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for data in script tags
    script_data = soup.find('script', {'type': 'application/ld+json'})
    if script_data:
        import json
        try:
            data = json.loads(script_data.string)
            return {
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "image": data.get("image", ""),
                "sku": data.get("sku", "")
            }
        except json.JSONDecodeError:
            pass
    
    # Fallback to regular extraction
    return self._extract_with_selectors(soup)
```

### Multiple Images Extraction

Extract all product images:

```python
def extract_images(self, soup: BeautifulSoup) -> List[str]:
    """Extract all product images"""
    images = []
    
    # Main image
    main_img = soup.select_one("img.main-image")
    if main_img:
        images.append(main_img.get('src', ''))
    
    # Gallery images
    gallery_imgs = soup.select("div.gallery img")
    for img in gallery_imgs:
        src = img.get('src', '') or img.get('data-src', '')
        if src and src not in images:
            images.append(src)
    
    return images
```

### Variants/Options Extraction

Extract product variants:

```python
def extract_variants(self, soup: BeautifulSoup) -> List[Dict]:
    """Extract product variants/options"""
    variants = []
    
    variant_section = soup.select_one("div.product-variants")
    if variant_section:
        options = variant_section.select("div.variant-option")
        for option in options:
            variant = {
                "size": option.get('data-size', ''),
                "color": option.get('data-color', ''),
                "sku": option.get('data-sku', ''),
                "price": self._parse_price(option.select_one("span.price"))
            }
            variants.append(variant)
    
    return variants
```

---

## Common Patterns & Examples

### Pattern 1: Simple E-Commerce

```python
CATEGORY_SELECTORS = {
    "products": "div.product-card",
    "product_link": "a.product-url",
    "product_name": "h3.product-name"
}

PRODUCT_SELECTORS = {
    "name": "h1.product-title",
    "image": "img.product-image",
    "description": "div.product-description",
    "sku": "span.product-sku"
}
```

### Pattern 2: WooCommerce

```python
CATEGORY_SELECTORS = {
    "products": "ul.products li.product",
    "product_link": "a.woocommerce-LoopProduct-link",
    "product_name": "h2.woocommerce-loop-product__title"
}

PRODUCT_SELECTORS = {
    "name": "h1.product_title",
    "image": "div.woocommerce-product-gallery img",
    "overview": "div.woocommerce-product-details__short-description",
    "description": "div.woocommerce-Tabs-panel--description",
    "sku": "span.sku",
    "categories": "span.posted_in a"
}

PDF_SELECTORS = {
    "sds_link": "a[href*='SDS']",
    "pds_link": "a[href*='PDS']"
}
```

### Pattern 3: Shopify

```python
CATEGORY_SELECTORS = {
    "products": "div.product-item",
    "product_link": "a.product-link",
    "product_name": "h3.product-title"
}

PRODUCT_SELECTORS = {
    "name": "h1.product-single__title",
    "image": "img.product-single__photo",
    "description": "div.product-single__description"
}
```

### Pattern 4: Industrial/Chemical Products

```python
CATEGORY_SELECTORS = {
    "products": "div.chemical-product",
    "product_link": "a.product-details-link",
    "product_name": "h4.chemical-name"
}

PRODUCT_SELECTORS = {
    "name": "h1.chemical-title",
    "image": "img.chemical-image",
    "overview": "div.chemical-overview",
    "description": "div.chemical-description",
    "sku": "span.chemical-code",
    "categories": "div.chemical-categories a"
}

PDF_SELECTORS = {
    "sds_link": "a.download-sds",
    "pds_link": "a.download-tds",
    "document_section": "div.safety-documents"
}
```

---

## Troubleshooting Extraction Issues

### Issue 1: Selector Returns No Elements

**Symptom:** `Found 0 elements` or extraction returns empty

**Common Causes:**
1. Selector too specific
2. HTML structure different than expected
3. Content loaded via JavaScript
4. Typo in selector

**Solutions:**
```javascript
// Test in browser console
document.querySelectorAll("your-selector")

// Try more generic selector
document.querySelectorAll("div.product")  // Instead of div.specific-product-class

// Check if element exists at all
document.body.innerHTML.includes("expected-class")
```

### Issue 2: Selector Returns Wrong Elements

**Symptom:** Extracting unrelated content

**Solutions:**
- Add more context to selector
- Use parent-child relationships
- Add specific classes

```python
# Too generic
"products": "li"

# More specific
"products": "ul.product-list li.product"

# Even more specific
"products": "main div.products-container ul.product-list li.product-item"
```

### Issue 3: Selector Works on One Page But Not Others

**Symptom:** Inconsistent extraction across pages

**Solutions:**
- Test on multiple pages during development
- Use more stable selectors (data attributes, IDs)
- Avoid selectors dependent on position (`:nth-child`)

```python
# Brittle - depends on position
"name": "div > div > div:nth-child(2) h1"

# Better - uses semantic selectors
"name": "div.product-info h1.product-name"
```

### Issue 4: Extracting Extra Whitespace or HTML

**Symptom:** Text contains newlines, tabs, or HTML tags

**Solutions:**
```python
# The scraper automatically strips whitespace and cleans HTML
# But for custom extraction:

import re

def clean_text(text: str) -> str:
    """Clean extracted text"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing
    text = text.strip()
    # Remove HTML entities
    text = text.replace('&nbsp;', ' ')
    return text
```

### Issue 5: Missing Optional Fields

**Symptom:** Some fields not present on all products

**Solution:** This is expected behavior. Ensure optional fields are marked as such:

```python
PRODUCT_SELECTORS = {
    "name": "h1.title",          # Required
    "image": "img.main",          # Required  
    "price": "span.price",       # Optional - may be missing
    "rating": "div.rating"       # Optional - may be missing
}
```

### Issue 6: PDF Links Not Found

**Symptom:** PDFs not downloading

**Troubleshooting:**
```javascript
// Test in console
document.querySelector("a[href*='SDS']")
document.querySelector("a[href*='pdf']")

// Check link attributes
let link = document.querySelector("a.download-sds")
console.log(link.href)           // Full URL
console.log(link.getAttribute('href'))  // Relative or absolute
```

**Solutions:**
- Verify `HAS_SDS_DOCUMENTS` and `HAS_PDS_DOCUMENTS` set correctly
- Check if links require JavaScript interaction
- Verify links point to actual PDFs
- Check if authentication required

### Debugging Tools

**1. Save HTML for Inspection:**
```bash
python scripts/test_extraction.py \
    --client clientname \
    --url "URL" \
    --save
```

**2. Use Browser Network Tab:**
- See actual requests made
- Check response content
- Verify URLs are accessible

**3. Test Incrementally:**
```python
# Start with simplest selector
"name": "h1"

# Add specificity
"name": "h1.title"

# Add context
"name": "div.product h1.title"
```

### Best Practices for Robust Selectors

1. **Prefer classes over complex hierarchies**
   ```python
   # Good
   "name": "h1.product-title"
   
   # Avoid
   "name": "div > div > section > div > h1"
   ```

2. **Use data attributes when available**
   ```python
   # Very stable
   "products": "[data-product]"
   "name": "[data-product-name]"
   ```

3. **Test on multiple pages**
   - Different categories
   - Products with/without images
   - Products with/without PDFs

4. **Document special cases**
   ```python
   PRODUCT_SELECTORS = {
       # Note: Some products use h2 instead of h1
       "name": "h1.title, h2.title"
   }
   ```

5. **Handle lazy-loaded images**
   ```python
   # Check both src and data-src
   "image": "img[src], img[data-src]"
   ```

### Getting Help

If extraction issues persist:

1. **Check existing examples:** Review Agar client configuration
2. **Test in isolation:** Use browser console first
3. **Use test scripts:** Run `test_extraction.py` with `--save` flag
4. **Review documentation:** See [configuration-guide.md](configuration-guide.md)
5. **Contact support:** Provide HTML samples and error logs

---

## Summary

Extraction strategies are the core of the 3DN Scraper Template's data collection capability. Success depends on:

- **Understanding CSS selectors** and how to test them
- **Analyzing HTML structure** to find stable patterns
- **Testing incrementally** on multiple pages
- **Handling edge cases** gracefully
- **Documenting assumptions** and special cases

With well-crafted selectors, the 3DN Scraper Template can reliably extract data from virtually any website structure.

---

**Related Documentation:**
- [CLIENT_DEPLOYMENT_GUIDE.md](CLIENT_DEPLOYMENT_GUIDE.md) - Complete deployment workflow
- [configuration-guide.md](configuration-guide.md) - Configuration reference
- [troubleshooting.md](troubleshooting.md) - Comprehensive troubleshooting
- [architecture.md](architecture.md) - System architecture

---

*3DN Scraper Template v1.0.0 - Professional Web Scraping Framework*
