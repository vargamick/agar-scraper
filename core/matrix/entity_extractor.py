"""
Entity Extractor

Extracts and normalizes entities from matrix data.
Handles deduplication and synonym resolution.
"""

import logging
import re
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

from api.integrations.memento.schemas import Entity, EntityType
from config.matrix_config import DISCONTINUED_PRODUCTS
from .parser import MatrixRow

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    """Result of entity extraction."""
    entities: Dict[EntityType, List[Entity]]
    entity_count: int
    duplicates_removed: int


class EntityExtractor:
    """
    Extract and normalize entities from matrix data.

    Handles:
    - Name normalization (case, whitespace, punctuation)
    - Synonym resolution
    - Deduplication within and across entity types
    """

    # Default synonym mappings (normalized_name -> list of variations)
    DEFAULT_SYNONYMS = {
        # Surfaces
        "timber": ["wood", "wooden", "hardwood", "softwood", "wooden floors"],
        "vinyl": ["vinyl flooring", "vinyl floors", "vinyl tiles"],
        "ceramic": ["ceramic tiles", "ceramics"],
        "concrete": ["cement", "cementitious", "concrete floors"],
        "terrazzo": ["sealed terrazzo"],
        "marble": ["sealed marble", "marble floors"],
        "porcelain": ["porcelain tiles", "non-porous porcelain tiles"],
        "linoleum": ["lino"],

        # Locations
        "hospitals": ["hospital", "medical facilities", "healthcare facilities"],
        "kitchens": ["kitchen", "commercial kitchens"],
        "food processing": ["food processing areas", "food processing equipment",
                          "food processing surfaces", "food-processing equipment"],
        "bathrooms": ["bathroom", "washrooms", "restrooms"],
        "schools": ["school", "educational facilities"],
    }

    def __init__(
        self,
        synonyms: Optional[Dict[str, List[str]]] = None,
        case_sensitive: bool = False,
    ):
        """
        Initialize extractor.

        Args:
            synonyms: Custom synonym mappings (merged with defaults)
            case_sensitive: Whether to use case-sensitive matching
        """
        self.case_sensitive = case_sensitive

        # Build synonym lookup (variation -> canonical)
        self.synonyms = dict(self.DEFAULT_SYNONYMS)
        if synonyms:
            self.synonyms.update(synonyms)

        self._synonym_lookup: Dict[str, str] = {}
        self._build_synonym_lookup()

    def _build_synonym_lookup(self):
        """Build reverse lookup from variations to canonical names."""
        for canonical, variations in self.synonyms.items():
            canonical_normalized = self._normalize_for_lookup(canonical)
            self._synonym_lookup[canonical_normalized] = canonical
            for variation in variations:
                variation_normalized = self._normalize_for_lookup(variation)
                self._synonym_lookup[variation_normalized] = canonical

    def _normalize_for_lookup(self, name: str) -> str:
        """Normalize name for synonym lookup."""
        if not self.case_sensitive:
            name = name.lower()
        return name.strip()

    def normalize_name(self, name: str) -> str:
        """
        Normalize an entity name.

        Steps:
        1. Strip whitespace
        2. Normalize case (if not case-sensitive)
        3. Normalize multiple spaces to single space
        4. Apply synonym resolution
        5. Title case for display

        Args:
            name: Raw entity name

        Returns:
            Normalized name
        """
        if not name:
            return ""

        # Basic normalization
        normalized = name.strip()
        normalized = re.sub(r"\s+", " ", normalized)

        # Lookup key
        lookup_key = self._normalize_for_lookup(normalized)

        # Check synonyms
        if lookup_key in self._synonym_lookup:
            normalized = self._synonym_lookup[lookup_key]

        # Title case for display (but keep acronyms)
        if not self.case_sensitive:
            # Preserve words that are all caps (likely acronyms)
            words = normalized.split()
            normalized_words = []
            for word in words:
                if word.isupper() and len(word) <= 4:
                    normalized_words.append(word)
                else:
                    normalized_words.append(word.title())
            normalized = " ".join(normalized_words)

        return normalized

    def get_normalized_key(self, name: str) -> str:
        """
        Get the normalized key for deduplication.

        This is a lowercase, trimmed version for matching.
        """
        normalized = self.normalize_name(name)
        return normalized.lower().strip()

    def extract_entities(self, rows: List[MatrixRow]) -> ExtractionResult:
        """
        Extract all unique entities from matrix rows.

        Args:
            rows: List of parsed MatrixRow objects

        Returns:
            ExtractionResult with deduplicated entities
        """
        entities: Dict[EntityType, List[Entity]] = {
            EntityType.PRODUCT: [],
            EntityType.SURFACE: [],
            EntityType.SOILAGE: [],
            EntityType.LOCATION: [],
            EntityType.BENEFIT: [],
        }

        # Track seen entities for deduplication
        seen: Dict[EntityType, Set[str]] = {t: set() for t in EntityType}
        duplicates_removed = 0

        for row in rows:
            # Product
            entity, is_dup = self._create_entity_if_new(
                EntityType.PRODUCT, row.product_name, seen
            )
            if entity:
                entities[EntityType.PRODUCT].append(entity)
            if is_dup:
                duplicates_removed += 1

            # Surfaces
            for surface in row.surfaces:
                entity, is_dup = self._create_entity_if_new(
                    EntityType.SURFACE, surface, seen
                )
                if entity:
                    entities[EntityType.SURFACE].append(entity)
                if is_dup:
                    duplicates_removed += 1

            # Incompatible surfaces (same entity type, different relationship)
            for surface in row.incompatible_surfaces:
                entity, is_dup = self._create_entity_if_new(
                    EntityType.SURFACE, surface, seen
                )
                if entity:
                    entities[EntityType.SURFACE].append(entity)
                if is_dup:
                    duplicates_removed += 1

            # Soilage
            for soilage in row.soilage_types:
                entity, is_dup = self._create_entity_if_new(
                    EntityType.SOILAGE, soilage, seen
                )
                if entity:
                    entities[EntityType.SOILAGE].append(entity)
                if is_dup:
                    duplicates_removed += 1

            # Incompatible soilage
            for soilage in row.incompatible_soilage:
                entity, is_dup = self._create_entity_if_new(
                    EntityType.SOILAGE, soilage, seen
                )
                if entity:
                    entities[EntityType.SOILAGE].append(entity)
                if is_dup:
                    duplicates_removed += 1

            # Locations
            for location in row.locations:
                entity, is_dup = self._create_entity_if_new(
                    EntityType.LOCATION, location, seen
                )
                if entity:
                    entities[EntityType.LOCATION].append(entity)
                if is_dup:
                    duplicates_removed += 1

            # Benefits
            for benefit in row.benefits:
                entity, is_dup = self._create_entity_if_new(
                    EntityType.BENEFIT, benefit, seen
                )
                if entity:
                    entities[EntityType.BENEFIT].append(entity)
                if is_dup:
                    duplicates_removed += 1

        total_entities = sum(len(e) for e in entities.values())
        logger.info(
            f"Extracted {total_entities} unique entities "
            f"({duplicates_removed} duplicates removed)"
        )

        return ExtractionResult(
            entities=entities,
            entity_count=total_entities,
            duplicates_removed=duplicates_removed,
        )

    def _is_discontinued(self, product_name: str) -> bool:
        """
        Check if a product is in the discontinued products list.

        Args:
            product_name: The product name to check

        Returns:
            True if the product is discontinued
        """
        # Normalize both for comparison
        name_upper = product_name.strip().upper()
        return name_upper in [p.upper() for p in DISCONTINUED_PRODUCTS]

    def _create_entity_if_new(
        self,
        entity_type: EntityType,
        name: str,
        seen: Dict[EntityType, Set[str]],
    ) -> tuple[Optional[Entity], bool]:
        """
        Create entity if not already seen.

        Returns:
            Tuple of (entity or None, was_duplicate)
        """
        normalized_name = self.normalize_name(name)
        normalized_key = self.get_normalized_key(name)

        if normalized_key in seen[entity_type]:
            return None, True

        seen[entity_type].add(normalized_key)

        # Build properties dict
        properties = {}

        # Check if product is discontinued
        if entity_type == EntityType.PRODUCT and self._is_discontinued(name):
            properties["is_discontinued"] = True
            logger.info(f"Marked product '{normalized_name}' as discontinued")

        entity = Entity(
            entity_type=entity_type,
            name=normalized_name,
            normalized_name=normalized_key,
            properties=properties,
            source="application_matrix",
        )

        return entity, False

    def get_entity_stats(self, result: ExtractionResult) -> Dict[str, int]:
        """Get counts by entity type."""
        return {
            entity_type.value: len(entities)
            for entity_type, entities in result.entities.items()
        }
