"""
Relationship Builder

Builds knowledge graph relationships from matrix data.
Creates entities and relationships in Memento.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from api.integrations.memento.client import MementoClient
from api.integrations.memento.schemas import (
    Entity,
    Relationship,
    EntityType,
    RelationshipType,
)
from .parser import MatrixRow
from .entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)


@dataclass
class BuildResult:
    """Result of relationship building."""
    entities_created: int = 0
    entities_cached: int = 0
    relationships_created: int = 0
    errors: List[str] = field(default_factory=list)


class RelationshipBuilder:
    """
    Build knowledge graph relationships from matrix data.

    Handles:
    - Creating entities (with caching to avoid duplicates)
    - Creating relationships between entities
    - Batch processing for efficiency
    """

    def __init__(
        self,
        memento_client: MementoClient,
        entity_extractor: Optional[EntityExtractor] = None,
    ):
        """
        Initialize builder.

        Args:
            memento_client: Memento API client
            entity_extractor: Entity extractor for normalization
        """
        self.client = memento_client
        self.extractor = entity_extractor or EntityExtractor()

        # Entity ID cache: (entity_type, normalized_name) -> entity_id
        self._entity_id_cache: Dict[tuple, str] = {}

        # Statistics
        self._stats = {
            "entities_created": 0,
            "entities_from_cache": 0,
            "relationships_created": 0,
            "errors": 0,
        }

    async def build_from_rows(self, rows: List[MatrixRow]) -> BuildResult:
        """
        Build all entities and relationships from matrix rows.

        Args:
            rows: List of parsed MatrixRow objects

        Returns:
            BuildResult with statistics
        """
        result = BuildResult()
        relationships_to_create: List[Relationship] = []

        for row in rows:
            try:
                # Get or create product entity
                product_id = await self._get_or_create_entity(
                    EntityType.PRODUCT,
                    row.product_name,
                )

                # Build relationships for this product
                row_relationships = await self._build_product_relationships(
                    product_id, row
                )
                relationships_to_create.extend(row_relationships)

            except Exception as e:
                error_msg = f"Error processing product '{row.product_name}': {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        # Create all relationships
        for relationship in relationships_to_create:
            try:
                await self.client.create_relationship(
                    source_entity_id=relationship.source_entity_id,
                    target_entity_id=relationship.target_entity_id,
                    relationship_type=relationship.relationship_type,
                    properties=relationship.properties,
                )
                result.relationships_created += 1
            except Exception as e:
                error_msg = f"Error creating relationship: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        result.entities_created = self._stats["entities_created"]
        result.entities_cached = self._stats["entities_from_cache"]

        logger.info(
            f"Build complete: {result.entities_created} entities created, "
            f"{result.relationships_created} relationships created, "
            f"{len(result.errors)} errors"
        )

        return result

    async def _build_product_relationships(
        self,
        product_id: str,
        row: MatrixRow,
    ) -> List[Relationship]:
        """Build all relationships for a single product."""
        relationships = []

        # SUITABLE_FOR Surface
        for surface in row.surfaces:
            surface_id = await self._get_or_create_entity(EntityType.SURFACE, surface)
            relationships.append(Relationship(
                source_entity_id=product_id,
                target_entity_id=surface_id,
                relationship_type=RelationshipType.SUITABLE_FOR,
                properties={"context": "compatible surface"},
            ))

        # INCOMPATIBLE_WITH Surface
        for surface in row.incompatible_surfaces:
            surface_id = await self._get_or_create_entity(EntityType.SURFACE, surface)
            relationships.append(Relationship(
                source_entity_id=product_id,
                target_entity_id=surface_id,
                relationship_type=RelationshipType.INCOMPATIBLE_WITH,
                properties={"context": "incompatible surface"},
            ))

        # HANDLES Soilage
        for soilage in row.soilage_types:
            soilage_id = await self._get_or_create_entity(EntityType.SOILAGE, soilage)
            relationships.append(Relationship(
                source_entity_id=product_id,
                target_entity_id=soilage_id,
                relationship_type=RelationshipType.HANDLES,
                properties={"context": "handles soilage"},
            ))

        # UNSUITABLE_FOR Soilage
        for soilage in row.incompatible_soilage:
            soilage_id = await self._get_or_create_entity(EntityType.SOILAGE, soilage)
            relationships.append(Relationship(
                source_entity_id=product_id,
                target_entity_id=soilage_id,
                relationship_type=RelationshipType.UNSUITABLE_FOR,
                properties={"context": "unsuitable for soilage"},
            ))

        # USED_IN Location
        for location in row.locations:
            location_id = await self._get_or_create_entity(EntityType.LOCATION, location)
            relationships.append(Relationship(
                source_entity_id=product_id,
                target_entity_id=location_id,
                relationship_type=RelationshipType.USED_IN,
                properties={"context": "used in location"},
            ))

        # HAS_BENEFIT Benefit
        for benefit in row.benefits:
            benefit_id = await self._get_or_create_entity(EntityType.BENEFIT, benefit)
            relationships.append(Relationship(
                source_entity_id=product_id,
                target_entity_id=benefit_id,
                relationship_type=RelationshipType.HAS_BENEFIT,
                properties={"context": "product benefit"},
            ))

        return relationships

    async def _get_or_create_entity(
        self,
        entity_type: EntityType,
        name: str,
    ) -> str:
        """
        Get existing entity ID or create new entity.

        Uses caching to minimize API calls.

        Args:
            entity_type: Type of entity
            name: Display name

        Returns:
            Entity ID
        """
        normalized_name = self.extractor.get_normalized_key(name)
        display_name = self.extractor.normalize_name(name)
        cache_key = (entity_type, normalized_name)

        # Check local cache
        if cache_key in self._entity_id_cache:
            self._stats["entities_from_cache"] += 1
            return self._entity_id_cache[cache_key]

        # Use Memento's upsert (which has its own cache)
        entity_id = await self.client.upsert_entity(
            entity_type=entity_type,
            name=display_name,
            normalized_name=normalized_name,
        )

        # Store in local cache
        self._entity_id_cache[cache_key] = entity_id
        self._stats["entities_created"] += 1

        return entity_id

    def get_stats(self) -> Dict[str, Any]:
        """Get builder statistics."""
        return {
            "entities_created": self._stats["entities_created"],
            "entities_from_cache": self._stats["entities_from_cache"],
            "relationships_created": self._stats["relationships_created"],
            "errors": self._stats["errors"],
            "cache_size": len(self._entity_id_cache),
        }

    def clear_cache(self):
        """Clear the entity ID cache."""
        self._entity_id_cache.clear()
        logger.debug("Entity ID cache cleared")
