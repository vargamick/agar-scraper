"""
Product Matcher

Matches products from the application matrix to scraped product data.
Uses fuzzy matching to handle slight variations in product names.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from .parser import MatrixRow

logger = logging.getLogger(__name__)


@dataclass
class ProductMatch:
    """Represents a match between matrix and scraped product."""
    matrix_name: str
    scraped_name: str
    scraped_url: Optional[str] = None
    scraped_data: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    match_type: str = "exact"  # exact, fuzzy, partial


@dataclass
class MatchReport:
    """Report of product matching results."""
    matched: List[ProductMatch] = field(default_factory=list)
    unmatched: List[str] = field(default_factory=list)
    match_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "matched_count": len(self.matched),
            "unmatched_count": len(self.unmatched),
            "match_rate": self.match_rate,
            "matched_products": [
                {
                    "matrix_name": m.matrix_name,
                    "scraped_name": m.scraped_name,
                    "confidence": m.confidence,
                    "match_type": m.match_type,
                }
                for m in self.matched
            ],
            "unmatched_products": self.unmatched,
        }


class ProductMatcher:
    """
    Match matrix products to scraped product data.

    Uses multiple matching strategies:
    1. Exact match (after normalization)
    2. Fuzzy match (using similarity ratio)
    3. Partial match (one name contains the other)
    """

    def __init__(
        self,
        scraped_products: List[Dict[str, Any]],
        match_threshold: float = 0.85,
    ):
        """
        Initialize matcher with scraped products.

        Args:
            scraped_products: List of product dicts from all_products.json
            match_threshold: Minimum similarity score for fuzzy match (0-1)
        """
        self.scraped_products = scraped_products
        self.match_threshold = match_threshold

        # Build lookup index
        self._name_lookup: Dict[str, Dict[str, Any]] = {}
        self._normalized_lookup: Dict[str, Dict[str, Any]] = {}
        self._build_lookup()

        logger.info(f"ProductMatcher initialized with {len(scraped_products)} scraped products")

    def _build_lookup(self):
        """Build lookup indices for fast matching."""
        for product in self.scraped_products:
            name = product.get("product_name", "")
            if not name:
                continue

            # Original name lookup
            self._name_lookup[name] = product

            # Normalized lookup
            normalized = self._normalize(name)
            self._normalized_lookup[normalized] = product

    def _normalize(self, name: str) -> str:
        """
        Normalize product name for matching.

        Removes:
        - Leading/trailing whitespace
        - Multiple spaces
        - Special characters (keeps alphanumeric and spaces)
        - Converts to lowercase
        """
        if not name:
            return ""

        normalized = name.lower().strip()
        # Replace special chars with space
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        # Collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def match(self, matrix_product_name: str) -> Optional[ProductMatch]:
        """
        Find the best matching scraped product.

        Args:
            matrix_product_name: Product name from the matrix

        Returns:
            ProductMatch if found, None otherwise
        """
        if not matrix_product_name:
            return None

        normalized_matrix = self._normalize(matrix_product_name)

        # Strategy 1: Exact match on original name
        if matrix_product_name in self._name_lookup:
            product = self._name_lookup[matrix_product_name]
            return ProductMatch(
                matrix_name=matrix_product_name,
                scraped_name=product.get("product_name", ""),
                scraped_url=product.get("product_url"),
                scraped_data=product,
                confidence=1.0,
                match_type="exact",
            )

        # Strategy 2: Exact match on normalized name
        if normalized_matrix in self._normalized_lookup:
            product = self._normalized_lookup[normalized_matrix]
            return ProductMatch(
                matrix_name=matrix_product_name,
                scraped_name=product.get("product_name", ""),
                scraped_url=product.get("product_url"),
                scraped_data=product,
                confidence=1.0,
                match_type="exact_normalized",
            )

        # Strategy 3: Fuzzy match
        best_match = None
        best_score = 0.0

        for scraped_normalized, product in self._normalized_lookup.items():
            score = self._similarity(normalized_matrix, scraped_normalized)
            if score > best_score and score >= self.match_threshold:
                best_score = score
                best_match = product

        if best_match:
            return ProductMatch(
                matrix_name=matrix_product_name,
                scraped_name=best_match.get("product_name", ""),
                scraped_url=best_match.get("product_url"),
                scraped_data=best_match,
                confidence=best_score,
                match_type="fuzzy",
            )

        # Strategy 4: Partial match (one contains the other)
        for scraped_normalized, product in self._normalized_lookup.items():
            if normalized_matrix in scraped_normalized or scraped_normalized in normalized_matrix:
                # Calculate confidence based on length ratio
                len_ratio = min(len(normalized_matrix), len(scraped_normalized)) / \
                           max(len(normalized_matrix), len(scraped_normalized))
                if len_ratio >= 0.5:  # At least 50% overlap
                    return ProductMatch(
                        matrix_name=matrix_product_name,
                        scraped_name=product.get("product_name", ""),
                        scraped_url=product.get("product_url"),
                        scraped_data=product,
                        confidence=len_ratio,
                        match_type="partial",
                    )

        return None

    def _similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity ratio between two strings.

        Uses a simple character-based approach that works without
        external dependencies. For better results, rapidfuzz can be used.
        """
        if not s1 or not s2:
            return 0.0

        if s1 == s2:
            return 1.0

        # Try to import rapidfuzz for better matching
        try:
            from rapidfuzz import fuzz
            return fuzz.ratio(s1, s2) / 100.0
        except ImportError:
            pass

        # Fallback: Simple character-based similarity
        # (Jaccard similarity on character bigrams)
        def get_bigrams(s):
            return set(s[i : i + 2] for i in range(len(s) - 1))

        bigrams1 = get_bigrams(s1)
        bigrams2 = get_bigrams(s2)

        if not bigrams1 or not bigrams2:
            return 0.0

        intersection = len(bigrams1 & bigrams2)
        union = len(bigrams1 | bigrams2)

        return intersection / union if union > 0 else 0.0

    def get_match_report(self, matrix_rows: List[MatrixRow]) -> MatchReport:
        """
        Generate a comprehensive match report.

        Args:
            matrix_rows: List of parsed MatrixRow objects

        Returns:
            MatchReport with matched and unmatched products
        """
        matched = []
        unmatched = []

        for row in matrix_rows:
            match = self.match(row.product_name)
            if match:
                matched.append(match)
            else:
                unmatched.append(row.product_name)

        total = len(matrix_rows)
        match_rate = len(matched) / total if total > 0 else 0.0

        report = MatchReport(
            matched=matched,
            unmatched=unmatched,
            match_rate=match_rate,
        )

        logger.info(
            f"Product matching complete: {len(matched)}/{total} matched "
            f"({match_rate:.1%}), {len(unmatched)} unmatched"
        )

        if unmatched:
            logger.warning(f"Unmatched products: {unmatched[:10]}...")

        return report

    def get_product_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get scraped product by exact or normalized name.

        Args:
            name: Product name to look up

        Returns:
            Product dict if found, None otherwise
        """
        if name in self._name_lookup:
            return self._name_lookup[name]

        normalized = self._normalize(name)
        return self._normalized_lookup.get(normalized)
