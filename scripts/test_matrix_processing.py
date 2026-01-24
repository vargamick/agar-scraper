#!/usr/bin/env python3
"""
Test script for Matrix Processing.

Tests the matrix parser, entity extraction, and product matching
without actually sending data to Memento.

Usage:
    python scripts/test_matrix_processing.py [--matrix-file PATH] [--products-file PATH]
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.matrix.parser import MatrixParser
from core.matrix.entity_extractor import EntityExtractor
from core.matrix.product_matcher import ProductMatcher


def main():
    parser = argparse.ArgumentParser(description="Test Matrix Processing")
    parser.add_argument(
        "--matrix-file",
        type=Path,
        help="Path to matrix Excel/CSV file",
    )
    parser.add_argument(
        "--products-file",
        type=Path,
        help="Path to scraped all_products.json",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )
    args = parser.parse_args()

    # Find matrix file
    matrix_path = args.matrix_file
    if not matrix_path:
        # Try common locations
        candidates = [
            Path("scraper_data/reference/AskAgar_ProductsData_v1.xlsx"),
            Path("/app/scraper_data/reference/AskAgar_ProductsData_v1.xlsx"),
        ]
        for candidate in candidates:
            if candidate.exists():
                matrix_path = candidate
                break

    if not matrix_path or not matrix_path.exists():
        print("ERROR: Matrix file not found. Specify with --matrix-file")
        sys.exit(1)

    print(f"Matrix file: {matrix_path}")
    print("-" * 60)

    # Step 1: Parse matrix
    print("\n1. PARSING MATRIX")
    matrix_parser = MatrixParser(matrix_path)
    rows = matrix_parser.parse()
    summary = matrix_parser.get_summary(rows)

    print(f"   Products parsed: {summary['total_products']}")
    print(f"   Unique surfaces: {summary['unique_surfaces']}")
    print(f"   Unique locations: {summary['unique_locations']}")

    if args.verbose:
        print(f"\n   Sample products:")
        for row in rows[:5]:
            print(f"     - {row.product_name}")

    # Step 2: Extract entities
    print("\n2. EXTRACTING ENTITIES")
    extractor = EntityExtractor()
    extraction_result = extractor.extract_entities(rows)
    stats = extractor.get_entity_stats(extraction_result)

    print(f"   Entity counts:")
    for entity_type, count in stats.items():
        print(f"     {entity_type}: {count}")
    print(f"   Duplicates removed: {extraction_result.duplicates_removed}")

    # Step 3: Count relationships
    print("\n3. RELATIONSHIP COUNTS")
    rel_counts = {
        "SUITABLE_FOR (surface)": sum(len(r.surfaces) for r in rows),
        "INCOMPATIBLE_WITH (surface)": sum(len(r.incompatible_surfaces) for r in rows),
        "HANDLES (soilage)": sum(len(r.soilage_types) for r in rows),
        "UNSUITABLE_FOR (soilage)": sum(len(r.incompatible_soilage) for r in rows),
        "USED_IN (location)": sum(len(r.locations) for r in rows),
        "HAS_BENEFIT": sum(len(r.benefits) for r in rows),
    }

    total_rels = 0
    for rel_type, count in rel_counts.items():
        print(f"   {rel_type}: {count}")
        total_rels += count
    print(f"   TOTAL: {total_rels}")

    # Step 4: Product matching (if products file provided)
    products_path = args.products_file
    if not products_path:
        # Try to find scraped products
        candidates = [
            Path("scraper_data/s3-downloads/all_products.json"),
        ]
        # Also check job folders
        jobs_dir = Path("scraper_data/jobs")
        if jobs_dir.exists():
            folders = sorted([f for f in jobs_dir.iterdir() if f.is_dir()], reverse=True)
            for folder in folders[:3]:
                candidates.append(folder / "all_products.json")

        for candidate in candidates:
            if candidate.exists():
                products_path = candidate
                break

    if products_path and products_path.exists():
        print("\n4. PRODUCT MATCHING")
        with open(products_path) as f:
            scraped_products = json.load(f)

        print(f"   Scraped products loaded: {len(scraped_products)}")

        matcher = ProductMatcher(scraped_products)
        report = matcher.get_match_report(rows)

        print(f"   Matched: {len(report.matched)} ({report.match_rate:.1%})")
        print(f"   Unmatched: {len(report.unmatched)}")

        if args.verbose and report.unmatched:
            print(f"\n   Unmatched products:")
            for name in report.unmatched:
                print(f"     - {name}")
    else:
        print("\n4. PRODUCT MATCHING")
        print("   Skipped (no scraped products file found)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Products:      {summary['total_products']}")
    print(f"Entities:      {sum(stats.values())}")
    print(f"Relationships: {total_rels}")
    if products_path and products_path.exists():
        print(f"Match rate:    {report.match_rate:.1%}")
    print("\nReady to process!")


if __name__ == "__main__":
    main()
