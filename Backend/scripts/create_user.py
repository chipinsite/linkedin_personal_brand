#!/usr/bin/env python3
"""Script to create a user in the database.

Usage:
    python scripts/create_user.py --email admin@example.com --username admin --password secret123 --full-name "Admin User" --superuser
    python scripts/create_user.py -e admin@example.com -u admin -p secret123

Environment:
    Set DATABASE_URL if using a non-default database.
"""

import argparse
import getpass
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base
from app.models import User
from app.services.password import hash_password
from app.services.user_service import UserAlreadyExistsError, create_user, get_user_by_email, get_user_by_username


def main():
    parser = argparse.ArgumentParser(description="Create a user in the database")
    parser.add_argument("-e", "--email", required=True, help="User email address")
    parser.add_argument("-u", "--username", required=True, help="Username")
    parser.add_argument("-p", "--password", help="Password (will prompt if not provided)")
    parser.add_argument("-n", "--full-name", help="Full name (optional)")
    parser.add_argument("-s", "--superuser", action="store_true", help="Make user a superuser")
    parser.add_argument("--db-url", help="Database URL (defaults to settings.database_url)")

    args = parser.parse_args()

    # Get password securely if not provided
    password = args.password
    if not password:
        password = getpass.getpass("Enter password: ")
        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("Error: Passwords do not match", file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters", file=sys.stderr)
        sys.exit(1)

    # Connect to database
    db_url = args.db_url or settings.database_url
    print(f"Connecting to database...")

    engine = create_engine(db_url)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        try:
            user = create_user(
                db=db,
                email=args.email,
                username=args.username,
                password=password,
                full_name=args.full_name,
                is_superuser=args.superuser,
            )
            print(f"\nUser created successfully!")
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Username: {user.username}")
            print(f"  Full Name: {user.full_name or '(not set)'}")
            print(f"  Superuser: {user.is_superuser}")
            print(f"  Active: {user.is_active}")
        except UserAlreadyExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
