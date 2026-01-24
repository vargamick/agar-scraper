"""
Memento API Client

Async HTTP client for interacting with the Memento Knowledge Graph API.
Handles entity and relationship CRUD operations with caching and retry logic.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

import aiohttp
from aiohttp import ClientError, ClientResponseError

from api.config import settings
from .schemas import (
    Entity,
    Relationship,
    EntityType,
    RelationshipType,
    EntityCreateRequest,
    RelationshipCreateRequest,
    EntityResponse,
    RelationshipResponse,
)
from .exceptions import (
    MementoAPIError,
    MementoConnectionError,
    EntityNotFoundError,
)


logger = logging.getLogger(__name__)


class MementoClient:
    """
    Async client for Memento Knowledge Graph API.

    Provides methods for creating, updating, and querying entities
    and relationships in the knowledge graph.

    Uses caching to minimize duplicate API calls and supports
    idempotent upsert operations.
    """

    def __init__(
        self,
        instance_id: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Memento client.

        Args:
            instance_id: Memento instance ID (defaults to settings.MEMENTO_DEFAULT_INSTANCE)
            api_url: Memento API base URL (defaults to settings.MEMENTO_API_URL)
            api_key: Memento API key (defaults to settings.MEMENTO_API_KEY)
            config: Optional configuration overrides
        """
        self.config = config or {}

        # API configuration
        self.api_url = api_url or self.config.get('api_url') or settings.MEMENTO_API_URL
        self.api_key = api_key or self.config.get('api_key') or settings.MEMENTO_API_KEY
        self.instance_id = instance_id or self.config.get('instanceId') or settings.MEMENTO_DEFAULT_INSTANCE

        # Validate configuration
        if not self.api_url:
            raise ValueError("Memento API URL is required (set MEMENTO_API_URL)")
        if not self.api_key:
            raise ValueError("Memento API key is required (set MEMENTO_API_KEY)")

        # Ensure API URL doesn't end with /
        self.api_url = self.api_url.rstrip('/')

        # Caching for entity lookups (normalized_name -> entity_id)
        self._entity_cache: Dict[str, str] = {}

        # Request configuration
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.max_retries = 3
        self.retry_delay = 1.0

        # Session (created on first use)
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(f"MementoClient initialized for instance '{self.instance_id}' at {self.api_url}")

    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers,
            )
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Memento API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (will be appended to base URL)
            data: Request body (for POST/PUT)
            params: Query parameters

        Returns:
            Response JSON data

        Raises:
            MementoAPIError: If API returns an error
            MementoConnectionError: If connection fails
        """
        url = f"{self.api_url}{endpoint}"
        session = await self._get_session()

        last_error = None
        for attempt in range(self.max_retries):
            try:
                async with session.request(
                    method,
                    url,
                    json=data,
                    params=params,
                ) as response:
                    response_text = await response.text()

                    if response.status >= 400:
                        raise MementoAPIError(
                            message=response_text,
                            status_code=response.status,
                            response_body=response_text,
                        )

                    if response_text:
                        return await response.json()
                    return {}

            except ClientResponseError as e:
                last_error = MementoAPIError(
                    message=str(e),
                    status_code=e.status,
                )
                logger.warning(f"API error (attempt {attempt + 1}/{self.max_retries}): {e}")

            except ClientError as e:
                last_error = MementoConnectionError(message=str(e), url=url)
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.max_retries}): {e}")

            except Exception as e:
                last_error = MementoAPIError(message=str(e))
                logger.warning(f"Unexpected error (attempt {attempt + 1}/{self.max_retries}): {e}")

            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise last_error

    # ==================== Entity Operations ====================

    async def create_entity(
        self,
        entity_type: EntityType,
        name: str,
        normalized_name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new entity in the knowledge graph.

        Args:
            entity_type: Type of entity (Product, Surface, etc.)
            name: Display name
            normalized_name: Normalized name for matching
            properties: Additional entity properties

        Returns:
            Entity ID
        """
        endpoint = f"/instances/{self.instance_id}/entities"

        payload = {
            "type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
            "name": name,
            "properties": {
                "normalized_name": normalized_name,
                "source": "application_matrix",
                "created_at": datetime.utcnow().isoformat(),
                **(properties or {}),
            },
        }

        response = await self._request("POST", endpoint, data=payload)
        entity_id = response.get("id") or response.get("entity_id")

        if entity_id:
            # Cache the entity
            cache_key = self._get_cache_key(entity_type, normalized_name)
            self._entity_cache[cache_key] = entity_id
            logger.debug(f"Created entity: {entity_type} '{name}' -> {entity_id}")

        return entity_id

    async def get_entity_by_name(
        self,
        entity_type: EntityType,
        normalized_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Find an entity by its normalized name.

        Args:
            entity_type: Type of entity to search for
            normalized_name: Normalized name to match

        Returns:
            Entity data if found, None otherwise
        """
        # Check cache first
        cache_key = self._get_cache_key(entity_type, normalized_name)
        if cache_key in self._entity_cache:
            entity_id = self._entity_cache[cache_key]
            return {"id": entity_id}

        endpoint = f"/instances/{self.instance_id}/entities/search"
        params = {
            "type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
            "property": "normalized_name",
            "value": normalized_name,
        }

        try:
            response = await self._request("GET", endpoint, params=params)
            entities = response.get("entities", response.get("results", []))

            if entities:
                entity = entities[0]
                entity_id = entity.get("id")
                if entity_id:
                    self._entity_cache[cache_key] = entity_id
                return entity

        except MementoAPIError as e:
            if e.status_code == 404:
                return None
            raise

        return None

    async def upsert_entity(
        self,
        entity_type: EntityType,
        name: str,
        normalized_name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create entity if it doesn't exist, or return existing entity ID.

        This is an idempotent operation - safe to call multiple times.

        Args:
            entity_type: Type of entity
            name: Display name
            normalized_name: Normalized name for matching
            properties: Additional properties

        Returns:
            Entity ID (existing or newly created)
        """
        # Check cache first
        cache_key = self._get_cache_key(entity_type, normalized_name)
        if cache_key in self._entity_cache:
            return self._entity_cache[cache_key]

        # Try to find existing
        existing = await self.get_entity_by_name(entity_type, normalized_name)
        if existing and existing.get("id"):
            return existing["id"]

        # Create new
        return await self.create_entity(entity_type, name, normalized_name, properties)

    async def get_or_create_entity(
        self,
        entity_type: EntityType,
        name: str,
        normalized_name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Alias for upsert_entity for clarity."""
        return await self.upsert_entity(entity_type, name, normalized_name, properties)

    # ==================== Relationship Operations ====================

    async def create_relationship(
        self,
        source_entity_id: str,
        target_entity_id: str,
        relationship_type: RelationshipType,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a relationship between two entities.

        Args:
            source_entity_id: ID of source entity
            target_entity_id: ID of target entity
            relationship_type: Type of relationship
            properties: Additional relationship properties

        Returns:
            Relationship ID
        """
        endpoint = f"/instances/{self.instance_id}/relationships"

        payload = {
            "source_id": source_entity_id,
            "target_id": target_entity_id,
            "type": relationship_type.value if isinstance(relationship_type, RelationshipType) else relationship_type,
            "properties": {
                "source": "application_matrix",
                "created_at": datetime.utcnow().isoformat(),
                **(properties or {}),
            },
        }

        response = await self._request("POST", endpoint, data=payload)
        relationship_id = response.get("id") or response.get("relationship_id")

        logger.debug(
            f"Created relationship: {source_entity_id} -{relationship_type}-> {target_entity_id}"
        )

        return relationship_id

    async def create_relationships_batch(
        self,
        relationships: List[Relationship],
    ) -> List[str]:
        """
        Create multiple relationships in a batch.

        Args:
            relationships: List of Relationship objects

        Returns:
            List of relationship IDs
        """
        endpoint = f"/instances/{self.instance_id}/relationships/batch"

        payload = {
            "relationships": [
                {
                    "source_id": r.source_entity_id,
                    "target_id": r.target_entity_id,
                    "type": r.relationship_type,
                    "properties": {
                        "source": r.source,
                        **(r.properties or {}),
                    },
                }
                for r in relationships
            ]
        }

        try:
            response = await self._request("POST", endpoint, data=payload)
            return response.get("ids", response.get("relationship_ids", []))
        except MementoAPIError:
            # Fallback to individual creation if batch not supported
            logger.info("Batch creation not supported, falling back to individual creation")
            ids = []
            for r in relationships:
                rel_id = await self.create_relationship(
                    r.source_entity_id,
                    r.target_entity_id,
                    r.relationship_type,
                    r.properties,
                )
                ids.append(rel_id)
            return ids

    # ==================== Utility Methods ====================

    def _get_cache_key(self, entity_type: EntityType, normalized_name: str) -> str:
        """Generate cache key for entity lookup."""
        type_value = entity_type.value if isinstance(entity_type, EntityType) else entity_type
        return f"{type_value}:{normalized_name}"

    def clear_cache(self):
        """Clear the entity cache."""
        self._entity_cache.clear()
        logger.debug("Entity cache cleared")

    async def health_check(self) -> bool:
        """
        Check if Memento API is accessible.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            endpoint = f"/instances/{self.instance_id}/health"
            await self._request("GET", endpoint)
            return True
        except Exception as e:
            logger.warning(f"Memento health check failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            "instance_id": self.instance_id,
            "api_url": self.api_url,
            "cached_entities": len(self._entity_cache),
        }
