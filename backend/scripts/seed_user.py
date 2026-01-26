"""Seed script to create a test admin user."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from uuid import uuid4

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings


async def seed_test_user():
    """Create a test user in the database."""
    # Windows-compatible event loop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    engine = create_async_engine(str(settings.database_url), echo=True)

    async with engine.begin() as conn:
        # Check if user already exists
        result = await conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": "admin@test.com"},
        )
        existing = result.fetchone()

        if existing:
            print("Test user already exists!")
            print("\nLogin credentials:")
            print("  Email: admin@test.com")
            print("  Password: admin123")
            return

        # Create test user
        user_id = str(uuid4())
        hashed_password = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")

        await conn.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, name, is_active, created_at, updated_at)
                VALUES (:id, :email, :password, :name, true, NOW(), NOW())
            """),
            {
                "id": user_id,
                "email": "admin@test.com",
                "password": hashed_password,
                "name": "Test Admin",
            },
        )

        print("Test user created successfully!")
        print("\nLogin credentials:")
        print("  Email: admin@test.com")
        print("  Password: admin123")

    await engine.dispose()


if __name__ == "__main__":
    # Set event loop policy before running
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_test_user())
