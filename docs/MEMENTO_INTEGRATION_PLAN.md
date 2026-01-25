# Product Application Matrix to Knowledge Graph - Implementation Plan

**Target Project:** 3DN Memento (NOT agar-scraper)
**Date:** 2026-01-24

## Overview

Process the Agar Product Application Matrix Excel file into the Memento knowledge graph, creating entities and relationships that link products to surfaces, soilage types, locations, and benefits.

## Data Source

- **File:** `AskAgar_ProductsData_v1.xlsx`
- **S3 Location:** `s3://agar-documentation/agar/reference-data/application-matrix/`
- **Format:** Multi-row Excel (201 products, ~2,261 rows, 7 columns)
- **Columns:** Product, Key Benefits, Surface, Incompatible Surface, Soilage, Incompatible Soilage, Location / Area

## Entity Types to Create

| Entity Type | Count | Example Values |
|------------|-------|----------------|
| Product | 201 | 3D-GLOSS, ACID WASH, ACTIVE BREAK |
| Surface | ~600 | Vinyl tiles, Sealed timber, Ceramic tiles |
| Soilage | ~369 | Grease, Oil, Food residue |
| Location | ~193 | Supermarkets, Hospitals, Kitchens |
| Benefit | ~737 | Non-slip, Stays shiny longer |

## Relationship Types

| Relationship | Count | Description |
|-------------|-------|-------------|
| SUITABLE_FOR | ~1,520 | Product → Surface (compatible) |
| INCOMPATIBLE_WITH | ~237 | Product → Surface (incompatible) |
| HANDLES | ~961 | Product → Soilage (compatible) |
| UNSUITABLE_FOR | ~10 | Product → Soilage (incompatible) |
| USED_IN | ~385 | Product → Location |
| HAS_BENEFIT | ~1,091 | Product → Benefit |
| **TOTAL** | **~4,204** | |

## Discontinued Products (13 products)

These products exist in the matrix but return 404 on the Agar website. They should be marked with `is_discontinued: true`:

| Product | Similar Active Product |
|---------|------------------------|
| AERIAL | None |
| CIP ALKALI-07 | None |
| CITRUS SPOTTER | Carpet Spotter B |
| FB-42 | None |
| HOOK ACID | Hook Clean (different) |
| HOOK OIL CONCENTRATE | Hook Clean (different) |
| LCD-11 | None |
| POWERDET ECO | None |
| SATIN FINISH SEALER | Matte Finish Sealer |
| SOAK TANK POWDER DETERGENT LF-3 | None |
| SPICE | None |
| VAPOR-Q | None |
| VIGOUR | None |

## Implementation Components

### 1. Matrix Parser (`parser.py`)

Handles the multi-row Excel format where products span multiple rows:

```python
@dataclass
class MatrixRow:
    product_name: str
    surfaces: List[str]
    incompatible_surfaces: List[str]
    soilage_types: List[str]
    incompatible_soilage: List[str]
    locations: List[str]
    benefits: List[str]

class MatrixParser:
    def parse(self) -> List[MatrixRow]:
        # Read Excel, group rows by product
        # Handle null values: "not stated", "n/a", "-", ""
        # Return consolidated list
```

### 2. Entity Extractor (`entity_extractor.py`)

Normalizes and deduplicates entities:

- Case normalization (preserve acronyms)
- Whitespace normalization
- Synonym resolution (e.g., "timber" → ["wood", "wooden"])
- Deduplication across entity types

### 3. Product Matcher (`product_matcher.py`)

Matches matrix products to scraped product data using fuzzy matching:

```python
class ProductMatcher:
    def __init__(self, scraped_products, match_threshold=0.85):
        # Uses rapidfuzz for fuzzy string matching

    def get_match_report(self, rows) -> MatchReport:
        # Returns matched/unmatched products
        # Current match rate: 93.5% (188/201)
```

### 4. Relationship Builder (`relationship_builder.py`)

Creates entities and relationships in the knowledge graph:

```python
class RelationshipBuilder:
    async def build_from_rows(self, rows):
        # 1. Create all entities (with caching)
        # 2. Create relationships in batches
        # 3. Handle discontinued products flag
```

### 5. Configuration (`matrix_config.py`)

```python
ENTITY_TYPES = ["Product", "Surface", "Soilage", "Location", "Benefit"]

SYNONYMS = {
    "timber": ["wood", "wooden", "hardwood"],
    "hospitals": ["hospital", "medical facilities"],
    # ... more synonyms
}

DISCONTINUED_PRODUCTS = [
    "AERIAL", "CIP ALKALI-07", "CITRUS SPOTTER", ...
]

MATCH_THRESHOLD = 0.85
```

## Dependencies

```
pandas>=2.0.0
openpyxl>=3.1.0  # Excel file support
rapidfuzz>=3.0.0  # Fuzzy string matching
```

## Processing Pipeline

```
1. Download matrix from S3
2. Parse Excel file → List[MatrixRow]
3. Load scraped products (optional)
4. Match products → MatchReport
5. Extract entities → ExtractionResult
6. Build relationships → Send to Memento API
7. Report statistics
```

## Expected Output

```
Products:      201
Entities:      ~2,096
Relationships: ~4,204
Match rate:    93.5%
Discontinued:  13 (flagged)
```

## Integration Points

1. **Trigger after scrape job** - Process matrix when new product data is scraped
2. **Standalone processing** - Run matrix processing independently
3. **API endpoint** - Expose `/matrix/process` endpoint for manual triggering

## Notes

- The matrix file is already uploaded to S3
- All relationships are directional (Product → Entity)
- Entity names are normalized for consistent matching
- Discontinued products are still included but flagged
