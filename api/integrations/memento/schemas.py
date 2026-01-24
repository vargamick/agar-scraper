"""
Memento Integration Schemas

Pydantic models for entities and relationships in the knowledge graph.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    """Types of entities in the Agar product knowledge graph."""
    PRODUCT = "Product"
    SURFACE = "Surface"
    SOILAGE = "Soilage"
    LOCATION = "Location"
    BENEFIT = "Benefit"
    CATEGORY = "Category"


class RelationshipType(str, Enum):
    """Types of relationships between entities."""
    # Product to Surface relationships
    SUITABLE_FOR = "SUITABLE_FOR"
    INCOMPATIBLE_WITH = "INCOMPATIBLE_WITH"

    # Product to Soilage relationships
    HANDLES = "HANDLES"
    UNSUITABLE_FOR = "UNSUITABLE_FOR"

    # Product to Location relationships
    USED_IN = "USED_IN"

    # Product to Benefit relationships
    HAS_BENEFIT = "HAS_BENEFIT"

    # Product to Category relationships
    BELONGS_TO = "BELONGS_TO"


class Entity(BaseModel):
    """
    Represents an entity in the knowledge graph.

    Entities are the nodes in the graph (Products, Surfaces, Locations, etc.)
    """
    id: Optional[str] = Field(default=None, description="Memento entity ID (assigned after creation)")
    entity_type: EntityType = Field(..., description="Type of entity")
    name: str = Field(..., description="Display name of the entity")
    normalized_name: str = Field(..., description="Normalized name for matching/deduplication")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional entity properties")
    source: str = Field(default="application_matrix", description="Data source identifier")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    class Config:
        use_enum_values = True


class Relationship(BaseModel):
    """
    Represents a relationship between two entities in the knowledge graph.

    Relationships are the edges connecting entities (e.g., Product SUITABLE_FOR Surface).
    """
    id: Optional[str] = Field(default=None, description="Memento relationship ID")
    source_entity_id: str = Field(..., description="ID of the source entity")
    target_entity_id: str = Field(..., description="ID of the target entity")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional relationship properties")
    source: str = Field(default="application_matrix", description="Data source identifier")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")

    class Config:
        use_enum_values = True


class EntityCreateRequest(BaseModel):
    """Request payload for creating an entity in Memento."""
    type: str = Field(..., description="Entity type")
    name: str = Field(..., description="Entity name")
    properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RelationshipCreateRequest(BaseModel):
    """Request payload for creating a relationship in Memento."""
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    type: str = Field(..., description="Relationship type")
    properties: Dict[str, Any] = Field(default_factory=dict)


class EntityResponse(BaseModel):
    """Response from Memento when creating/retrieving an entity."""
    id: str
    type: str
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RelationshipResponse(BaseModel):
    """Response from Memento when creating/retrieving a relationship."""
    id: str
    source_id: str
    target_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


class ProcessingResult(BaseModel):
    """Result of matrix processing operation."""
    success: bool = Field(..., description="Whether processing succeeded")
    entities_created: int = Field(default=0, description="Number of entities created")
    entities_updated: int = Field(default=0, description="Number of entities updated")
    relationships_created: int = Field(default=0, description="Number of relationships created")
    products_matched: int = Field(default=0, description="Products matched to scraped data")
    products_unmatched: int = Field(default=0, description="Products not found in scraped data")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")
    processing_time_seconds: Optional[float] = None
