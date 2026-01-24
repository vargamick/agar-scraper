"""
Matrix Processing Module

Parses Product Application Matrix data and processes it into
entities and relationships for the knowledge graph.
"""

from .parser import MatrixParser, MatrixRow
from .entity_extractor import EntityExtractor
from .product_matcher import ProductMatcher, MatchReport
from .relationship_builder import RelationshipBuilder
from .processor import MatrixProcessor

__all__ = [
    "MatrixParser",
    "MatrixRow",
    "EntityExtractor",
    "ProductMatcher",
    "MatchReport",
    "RelationshipBuilder",
    "MatrixProcessor",
]
