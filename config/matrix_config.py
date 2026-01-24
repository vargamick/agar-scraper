"""
Matrix Processing Configuration

Configuration for entity types, relationship types, and processing settings
for the Product Application Matrix.
"""

from typing import Dict, List


# Entity types in the knowledge graph
ENTITY_TYPES = [
    "Product",
    "Surface",
    "Soilage",
    "Location",
    "Benefit",
    "Category",
]

# Relationship type mappings
RELATIONSHIP_TYPES = {
    # Surface relationships
    "compatible_surface": "SUITABLE_FOR",
    "incompatible_surface": "INCOMPATIBLE_WITH",

    # Soilage relationships
    "compatible_soilage": "HANDLES",
    "incompatible_soilage": "UNSUITABLE_FOR",

    # Location relationships
    "location": "USED_IN",

    # Benefit relationships
    "benefit": "HAS_BENEFIT",

    # Category relationships
    "category": "BELONGS_TO",
}

# Normalization settings
NORMALIZATION = {
    "case_sensitive": False,
    "strip_whitespace": True,
    "collapse_spaces": True,
}

# Fuzzy matching threshold (0-1)
MATCH_THRESHOLD = 0.85

# Synonyms for entity normalization
# Format: canonical_name -> list of variations
SYNONYMS: Dict[str, List[str]] = {
    # Surfaces
    "timber": ["wood", "wooden", "hardwood", "softwood", "wooden floors"],
    "vinyl": ["vinyl flooring", "vinyl floors", "vinyl tiles"],
    "ceramic": ["ceramic tiles", "ceramics"],
    "concrete": ["cement", "cementitious", "concrete floors"],
    "terrazzo": ["sealed terrazzo"],
    "marble": ["sealed marble", "marble floors"],
    "porcelain": ["porcelain tiles", "non-porous porcelain tiles"],
    "linoleum": ["lino"],
    "stainless steel": ["stainless", "ss"],
    "glass": ["glass surfaces"],

    # Locations
    "hospitals": ["hospital", "medical facilities", "healthcare facilities"],
    "kitchens": ["kitchen", "commercial kitchens", "kitchen areas"],
    "food processing": [
        "food processing areas",
        "food processing equipment",
        "food processing surfaces",
        "food-processing equipment",
        "food preparation areas",
    ],
    "bathrooms": ["bathroom", "washrooms", "restrooms", "toilet areas"],
    "schools": ["school", "educational facilities"],
    "supermarkets": ["supermarket", "retail stores", "grocery stores"],
    "restaurants": ["restaurant", "dining areas", "food service"],
    "factories": ["factory", "manufacturing", "industrial"],
    "offices": ["office", "office buildings", "commercial buildings"],
    "nursing homes": ["nursing home", "aged care", "elderly care"],

    # Soilage types
    "grease": ["greasy", "oil", "oily", "fats"],
    "food residue": ["food waste", "food deposits", "organic matter"],
    "soap scum": ["soap residue", "detergent buildup"],
    "hard water": ["mineral deposits", "limescale", "calcium"],
}

# Discontinued products (no longer on Agar website as of 2026-01-24)
# These products return 404 errors when accessed directly
DISCONTINUED_PRODUCTS = [
    "AERIAL",
    "CIP ALKALI-07",
    "CITRUS SPOTTER",
    "FB-42",
    "HOOK ACID",
    "HOOK OIL CONCENTRATE",
    "LCD-11",
    "POWERDET ECO",
    "SATIN FINISH SEALER",
    "SOAK TANK POWDER DETERGENT LF-3",
    "SPICE",
    "VAPOR-Q",
    "VIGOUR",
]

# S3 paths for matrix data
S3_CONFIG = {
    "bucket": "agar-documentation",
    "matrix_prefix": "agar/reference-data/application-matrix/",
    "default_matrix_file": "AskAgar_ProductsData_v1.xlsx",
}

# Excel parsing configuration
EXCEL_CONFIG = {
    # Row containing column headers (0-indexed)
    # Set to None to auto-detect
    "header_row": None,

    # Column name mappings (lowercase key -> internal field name)
    "column_mapping": {
        "product": "product_name",
        "key benefits": "benefits",
        "surface": "surfaces",
        "incompatible surface": "incompatible_surfaces",
        "soilage": "soilage_types",
        "incompatible soilage": "incompatible_soilage",
        "location / area": "locations",
        "location/area": "locations",
    },

    # Values to treat as null/empty
    "null_values": ["not stated", "n/a", "na", "none", "-", ""],
}

# Processing settings
PROCESSING = {
    # Maximum products to process (0 = no limit)
    "max_products": 0,

    # Enable dry run by default in development
    "default_dry_run": False,

    # Batch size for relationship creation
    "relationship_batch_size": 100,

    # Retry settings
    "max_retries": 3,
    "retry_delay_seconds": 1.0,
}
