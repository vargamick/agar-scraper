"""
Authentication module for the API.

Handles user authentication, JWT tokens, and password hashing.
"""

from api.auth.password import hash_password, verify_password
from api.auth.jwt import create_access_token, create_refresh_token, decode_access_token

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_access_token",
]
