"""
Memento Integration Exceptions

Custom exception classes for Memento API interactions.
"""


class MementoError(Exception):
    """Base exception for Memento integration errors."""
    pass


class MementoConnectionError(MementoError):
    """Raised when connection to Memento API fails."""

    def __init__(self, message: str, url: str = None):
        self.url = url
        super().__init__(f"Connection error{f' to {url}' if url else ''}: {message}")


class MementoAPIError(MementoError):
    """Raised when Memento API returns an error response."""

    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(
            f"API error (status {status_code}): {message}"
            if status_code else f"API error: {message}"
        )


class EntityNotFoundError(MementoError):
    """Raised when an entity is not found in the knowledge graph."""

    def __init__(self, entity_type: str, identifier: str):
        self.entity_type = entity_type
        self.identifier = identifier
        super().__init__(f"Entity not found: {entity_type} with identifier '{identifier}'")


class RelationshipError(MementoError):
    """Raised when relationship creation or lookup fails."""

    def __init__(self, message: str, source_id: str = None, target_id: str = None):
        self.source_id = source_id
        self.target_id = target_id
        super().__init__(message)


class ValidationError(MementoError):
    """Raised when entity or relationship data fails validation."""
    pass
