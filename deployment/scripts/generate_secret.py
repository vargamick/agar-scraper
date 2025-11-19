#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for production deployment.

Usage:
    python3 generate_secret.py
"""

import secrets
import string

def generate_secret_key(length=64):
    """
    Generate a cryptographically secure secret key.

    Args:
        length: Length of the secret key (default: 64)

    Returns:
        Secure random string
    """
    # Use URL-safe base64 encoding for maximum compatibility
    return secrets.token_urlsafe(length)

def generate_password(length=32):
    """
    Generate a secure random password.

    Args:
        length: Length of the password (default: 32)

    Returns:
        Secure random password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

if __name__ == "__main__":
    print("=" * 70)
    print("PRODUCTION SECRET KEY GENERATION")
    print("=" * 70)
    print()

    secret_key = generate_secret_key()
    print("SECRET_KEY (copy this to your .env file):")
    print(f"SECRET_KEY={secret_key}")
    print()

    db_password = generate_password()
    print("DATABASE PASSWORD (copy this to your .env file):")
    print(f"POSTGRES_PASSWORD={db_password}")
    print()

    print("=" * 70)
    print("IMPORTANT: Store these values securely!")
    print("=" * 70)
    print()
    print("1. Copy the SECRET_KEY to your .env file")
    print("2. Copy the POSTGRES_PASSWORD to your .env file")
    print("3. Update DATABASE_URL with the new password")
    print("4. Never commit these values to version control")
    print()
