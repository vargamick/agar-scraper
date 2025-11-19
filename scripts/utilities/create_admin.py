#!/usr/bin/env python3
"""
Create default admin user for the Scraper API
"""

import sys
import os

# Add api directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from api.database.connection import init_database, db_manager
from api.database.models import User
from api.auth import hash_password
from datetime import datetime
from api.config import settings

def create_admin_user():
    """Create or update admin user."""

    # Initialize database
    init_database(settings.DATABASE_URL)

    # Get session
    session: Session = db_manager.get_session()

    try:
        # Check if admin user already exists
        existing = session.query(User).filter_by(username='admin').first()

        if existing:
            print("Admin user already exists!")
            print("=" * 50)
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@scraper.local")
            print("=" * 50)

            # Update to ensure it's a superuser
            if not existing.is_superuser:
                existing.is_superuser = True
                existing.password_hash = hash_password('admin123')
                session.commit()
                print("Updated existing user to superuser with new password")
        else:
            # Create admin user
            admin = User(
                username='admin',
                email='admin@scraper.local',
                password_hash=hash_password('admin123'),
                full_name='Admin User',
                is_active=True,
                is_superuser=True,
                last_login=datetime.utcnow()
            )
            session.add(admin)
            session.commit()

            print("Admin user created successfully!")
            print("=" * 50)
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@scraper.local")
            print("=" * 50)

    except Exception as e:
        print(f"Error creating admin user: {e}")
        session.rollback()
        return False
    finally:
        session.close()

    return True

if __name__ == '__main__':
    success = create_admin_user()
    sys.exit(0 if success else 1)
