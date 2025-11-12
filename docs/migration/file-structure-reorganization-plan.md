# File Structure Reorganization - Execution Plan

## Overview
This document outlines the plan to simplify output file locations for easier downstream processing, focusing on PDF organization, category structure, and file naming conventions.

---

## Current Structure Analysis

### Current PDF Organization
```
pdfs/
├── Product-Name_pdfs.json (metadata files)
└── Product-Name/              (subfolder per product)
    ├── Product-Name_SDS.pdf
    └── Product-Name_PDS.pdf
```

### Current Category Organization
```
categories/
├── category-name/
│   ├── subcategories.json
│   ├── products_list.json
│   └── subcategory-name/
│       └── products_list.json
```

### Current Product Organization
```
products/
├── Product-Name-1.json
├── Product-Name-2.json
└── ...
```

---

## Required Changes

### 1. PDF Folder Restructuring

**Current Problem:**
- PDFs are organized in product-specific subfolders
- Makes batch processing more complex
- Difficult to get all SDS or all PDS files at once

**New Structure:**
```
pdfs/
├── PDS/
│   ├── Product-Name-1_PDS.pdf
│   ├── Product-Name-2_PDS.pdf
│   └── ...
└── SDS/
    ├── Product-Name-1_SDS.pdf
    ├── Product-Name-2_SDS.pdf
    └── ...
```

**Benefits:**
- All PDS documents in one flat folder
- All SDS documents in one flat folder
- Easy to process all documents of one type
- Simpler file path construction

---

### 2. Category Folder Restructuring

**Current Problem:**
- Every category gets a subfolder, even if it has no subcategories
- Category data files are always nested one level deep
- Inconsistent structure between categories with/without subcategories

**New Structure for Categories WITHOUT Subcategories:**
```
categories/
├── air-fresheners.json           (category data directly at root)
├── glass-cleaners.json
├── stainless-steel-care.json
└── ...
```

**New Structure for Categories WITH Subcategories:**
```
categories/
├── floor-care.json                          (parent category data)
├── floor-care/                              (subfolder only for subcategories)
│   ├── floor-care_cutting-back.json
│   ├── floor-care_daily-floor-cleaning-detergents.json
│   ├── floor-care_floor-maintainers.json
│   └── floor-care_spray-buff.json
├── laundry-products.json
└── laundry-products/
    ├── laundry-products_detergents.json
    └── laundry-products_fabric-care.json
```

**Benefits:**
- Flatter structure for simple categories
- Clear distinction between parent and subcategories
- File names include parent context
- Easier to identify category hierarchy

---

### 3. File Naming Updates

**Current Naming:**
- `products_list.json` - no context about which category
- `subcategories.json` - no context about which parent

**New Naming Convention:**

| File Type | Current Name | New Name | Example |
|-----------|-------------|----------|---------|
| Top-level category data | N/A (in subfolder) | `{category-slug}.json` | `floor-care.json` |
| Subcategory data | `products_list.json` | `{parent}_{subcategory}.json` | `floor-care_cutting-back.json` |
| Product list for category | `products_list.json` | `{category-slug}_products.json` | `floor-care_products.json` |
| Product list for subcategory | `products_list.json` | `{parent}_{subcategory}_products.json` | `floor-care_cutting-back_products.json` |

**Benefits:**
- File names are self-documenting
- Easy to identify which category a file belongs to
- No ambiguity when files are extracted from folders
- Better for automated processing

---

## Implementation Plan

### Phase 1: Code Analysis & Preparation
- [x] Review `main.py` orchestrator structure
- [x] Review `category_scraper.py` for category file creation
- [x] Review `product_collector.py` for category/product list files
- [x] Review `pdf_downloader.py` for PDF organization
- [x] Analyze existing output structure
- [x] Document current vs. required structure

### Phase 2: PDF Downloader Modifications

**File: `core/pdf_downloader.py`**

**Changes Required:**

1. **Update directory creation** (in `__init__` method):
   ```python
   # OLD:
   self.pdf_output_dir = self.run_dir / "PDFs"
   
   # NEW:
   self.pdf_output_dir = self.run_dir / "pdfs"
   self.pds_dir = self.pdf_output_dir / "PDS"
   self.sds_dir = self.pdf_output_dir / "SDS"
   self.pds_dir.mkdir(parents=True, exist_ok=True)
   self.sds_dir.mkdir(parents=True, exist_ok=True)
   ```

2. **Update download logic** (in `_download_product_pdfs` method):
   ```python
   # OLD:
   product_pdf_dir = self.pdf_output_dir / safe_product_name
   product_pdf_dir.mkdir(parents=True, exist_ok=True)
   
   # Download to product subfolder
   product_pdf_dir / f"{safe_product_name}_SDS.pdf"
   product_pdf_dir / f"{safe_product_name}_PDS.pdf"
   
   # NEW:
   # Download directly to type-specific folders
   self.sds_dir / f"{safe_product_name}_SDS.pdf"
   self.pds_dir / f"{safe_product_name}_PDS.pdf"
   ```

3. **Update validation and error handling:**
   - Ensure unique filenames (handle duplicate product names)
   - Update statistics tracking
   - Update report generation

**Impact:**
- Simpler directory structure
- No nested product folders
- All PDFs of same type in one location

---

### Phase 3: Category Scraper Modifications

**File: `core/category_scraper.py`**

**Changes Required:**

1. **Update `save_categories` method:**
   ```python
   # OLD:
   filepath = self.output_dir / "categories.json"
   
   # NEW:
   # Create categories directory
   categories_dir = self.output_dir / "categories"
   categories_dir.mkdir(parents=True, exist_ok=True)
   
   # Save main category list at root
   filepath = self.output_dir / "categories.json"
   ```

2. **Add method to save individual category files:**
   ```python
   def save_individual_categories(self, categories: List[Dict]):
       """Save each category as individual JSON file"""
       categories_dir = self.output_dir / "categories"
       
       for category in categories:
           slug = category['slug']
           filename = f"{slug}.json"
           save_json(category, categories_dir / filename)
   ```

**Impact:**
- Creates category structure foundation
- Prepares for product collector to determine folder vs. file placement

---

### Phase 4: Product Collector Modifications

**File: `core/product_collector.py`**

**Changes Required:**

1. **Update `_get_category_output_dir` method:**
   ```python
   # OLD:
   def _get_category_output_dir(self, category_slug: str, parent_slug: str = None):
       if parent_slug:
           category_dir = self.output_dir / "categories" / parent_slug / category_slug
       else:
           category_dir = self.output_dir / "categories" / category_slug
       category_dir.mkdir(parents=True, exist_ok=True)
       return category_dir
   
   # NEW:
   def _get_category_output_path(self, category_slug: str, parent_slug: str = None, 
                                  is_product_list: bool = False):
       """
       Get output path for category data.
       
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
   ```

2. **Update `collect_from_category` method to save with new naming:**
   ```python
   # When saving subcategories:
   if subcategories:
       # Save subcategory list with parent context
       subcat_list_path = self._get_category_output_path(
           category['slug'], 
           parent_slug=parent_slug,
           is_product_list=False
       )
       # Transform subcategories to include parent info in saved file
       subcategories_data = {
           "parent_category": category['name'],
           "parent_slug": category['slug'],
           "subcategories": subcategories
       }
       save_json(subcategories_data, subcat_list_path)
   
   # When saving products:
   if products:
       product_list_path = self._get_category_output_path(
           category['slug'],
           parent_slug=parent_slug,
           is_product_list=True
       )
       save_json(products, product_list_path)
   ```

3. **Remove `subcategories.json` saving:**
   - Old logic saved a separate `subcategories.json`
   - New logic incorporates this into parent category file

**Impact:**
- Dynamic folder creation only when subcategories exist
- Self-documenting file names
- Flatter structure for simple categories

---

### Phase 5: Main Orchestrator Updates

**File: `main.py`**

**Changes Required:**

1. **Update directory creation** (in `__init__` method):
   ```python
   # Current creates all directories upfront
   # Update to be more minimal:
   (self.run_dir / "categories").mkdir(exist_ok=True)  # Base only
   (self.run_dir / "products").mkdir(exist_ok=True)
   (self.run_dir / "pdfs").mkdir(exist_ok=True)        # Base only
   (self.run_dir / "reports").mkdir(exist_ok=True)
   (self.run_dir / "logs").mkdir(exist_ok=True)
   (self.run_dir / "screenshots").mkdir(exist_ok=True)
   
   # PDS/SDS subdirectories created by PDFDownloader
   ```

2. **Update report generation** to reflect new structure

**Impact:**
- Cleaner initialization
- Specialized modules handle their own structure

---

### Phase 6: Utility Updates

**File: `core/utils.py`**

**Review Required:**
- Check if `sanitize_filename` function needs updates
- Ensure consistent filename sanitization
- Add helper functions if needed for path construction

---

## Testing Strategy

### Test Case 1: Simple Category (No Subcategories)
**Input:** Category with direct products (e.g., "glass-cleaners")

**Expected Output:**
```
categories/
├── glass-cleaners.json
└── glass-cleaners_products.json
```

### Test Case 2: Category with Subcategories
**Input:** Category with subcategories (e.g., "floor-care")

**Expected Output:**
```
categories/
├── floor-care.json
└── floor-care/
    ├── floor-care_cutting-back.json
    ├── floor-care_cutting-back_products.json
    ├── floor-care_spray-buff.json
    └── floor-care_spray-buff_products.json
```

### Test Case 3: PDF Downloads
**Input:** Products with SDS and PDS URLs

**Expected Output:**
```
pdfs/
├── PDS/
│   ├── Product-A_PDS.pdf
│   └── Product-B_PDS.pdf
└── SDS/
    ├── Product-A_SDS.pdf
    └── Product-B_SDS.pdf
```

### Test Case 4: Mixed Hierarchy
**Input:** Multiple categories, some with subcategories, some without

**Expected Output:**
- Simple categories as direct JSON files
- Complex categories with subfolders
- All naming conventions followed

---

## Migration Guide

### For Existing Scrape Results

**Option A: Leave existing results unchanged**
- Only new scrapes use new structure
- Document structure version in run metadata

**Option B: Convert existing results**
- Create migration script to reorganize old runs
- Provide backward compatibility

**Recommendation:** Option A - Clean break, simpler implementation

---

## Rollout Plan

### Step 1: Development (Estimated: 2-3 hours)
1. Implement PDFDownloader changes
2. Implement ProductCollector changes
3. Update CategoryScraper
4. Update main orchestrator
5. Update utility functions

### Step 2: Testing (Estimated: 1-2 hours)
1. Run test mode scrape
2. Verify PDF structure
3. Verify category structure
4. Verify file naming
5. Check edge cases

### Step 3: Validation (Estimated: 30 minutes)
1. Run full scrape
2. Compare output structure against plan
3. Verify all files accessible
4. Test downstream processing

### Step 4: Documentation (Estimated: 30 minutes)
1. Update README
2. Update configuration guide
3. Add structure diagram
4. Document any breaking changes

---

## Risk Assessment

### Low Risk
- PDF reorganization (simple path change)
- File naming updates (no logic change)

### Medium Risk
- Category folder logic (needs careful testing)
- Backward compatibility with existing code

### Mitigation
- Comprehensive testing with test mode
- Keep backup of current code
- Incremental implementation
- Rollback plan ready

---

## Success Criteria

✅ All PDFs organized in PDS/ and SDS/ folders
✅ Category folders only created when subcategories exist
✅ Top-level category JSON files at categories/ root
✅ Subcategory JSON files in parent folders
✅ File names include parent context
✅ Product JSON files remain at products/ root
✅ All existing functionality preserved
✅ Test scrape completes successfully
✅ Full scrape produces correct structure

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review and approve this plan
- [ ] Create feature branch
- [ ] Backup current codebase

### Implementation
- [ ] Modify `core/pdf_downloader.py`
- [ ] Modify `core/product_collector.py`
- [ ] Modify `core/category_scraper.py`
- [ ] Update `main.py`
- [ ] Review `core/utils.py`
- [ ] Update any related documentation

### Testing
- [ ] Run test mode scrape
- [ ] Verify PDF structure matches plan
- [ ] Verify category structure matches plan
- [ ] Verify file naming conventions
- [ ] Test with categories with no subcategories
- [ ] Test with categories with subcategories
- [ ] Test with nested subcategories (if applicable)

### Validation
- [ ] Run full production scrape
- [ ] Verify complete output structure
- [ ] Test downstream processing compatibility
- [ ] Performance check (no regression)

### Documentation
- [ ] Update README.md
- [ ] Update architecture documentation
- [ ] Add migration notes if needed
- [ ] Document structure changes

### Deployment
- [ ] Merge to main branch
- [ ] Tag release version
- [ ] Communicate changes to stakeholders
- [ ] Archive old structure documentation

---

## Questions for Clarification

1. **Product JSON files:** You mentioned "the JSON file generated for each product should be at the folder root." Should this be:
   - At the run directory root? (e.g., `run_dir/Product-Name.json`)
   - At the products folder root? (e.g., `run_dir/products/Product-Name.json` - CURRENT)

2. **Category data:** Should the parent category JSON file contain:
   - Just category metadata?
   - List of subcategories?
   - List of direct products (if any)?

3. **Subcategory files:** Should subcategory JSON files be:
   - Just the subcategory metadata?
   - Include the products list?
   - Separate files for metadata vs. product list?

---

## Conclusion

This reorganization will significantly simplify the output structure, making it easier to:
- Process all PDFs of a specific type
- Navigate category hierarchies
- Identify file relationships from names alone
- Integrate with downstream systems

The implementation is straightforward with low risk, primarily involving path and naming changes rather than logic modifications.
