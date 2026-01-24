# Discontinued Products Report

**Generated:** 2026-01-24
**Source:** Product Application Matrix vs Agar Website Comparison

## Summary

The Product Application Matrix (`AskAgar_ProductsData_v1.xlsx`) contains **13 products** that are no longer available on the Agar website. These products return 404 errors when accessed directly.

## Discontinued Products

| Product | Status | Similar Active Product |
|---------|--------|------------------------|
| AERIAL | Discontinued | None |
| CIP ALKALI-07 | Discontinued | None |
| CITRUS SPOTTER | Discontinued | Carpet Spotter B |
| FB-42 | Discontinued | None |
| HOOK ACID | Discontinued | Hook Clean (different product) |
| HOOK OIL CONCENTRATE | Discontinued | Hook Clean (different product) |
| LCD-11 | Discontinued | None |
| POWERDET ECO | Discontinued | None |
| SATIN FINISH SEALER | Discontinued | Matte Finish Sealer |
| SOAK TANK POWDER DETERGENT LF-3 | Discontinued | None |
| SPICE | Discontinued | None |
| VAPOR-Q | Discontinued | None |
| VIGOUR | Discontinued | None |

## Statistics

- **Total products in matrix:** 201
- **Active products (matched):** 188 (93.5%)
- **Discontinued products:** 13 (6.5%)

## Handling in Knowledge Graph

Discontinued products are:
1. Still included in the knowledge graph with their application data
2. Marked with `is_discontinued: true` property
3. Relationships (surfaces, locations, etc.) are still created

This allows historical queries and helps users understand product evolution.

## Recommendations

1. **For Agar:** Consider removing discontinued products from future matrix updates
2. **For Ask Agar:** Display a note when users ask about discontinued products
3. **For maintenance:** Re-run this analysis periodically to identify newly discontinued products
