"""
Database migration to add API usage tracking table.

Usage:
    python backend/db_migration_add_usage_tracking.py
"""

import asyncio
import sys
from sqlalchemy import text
from database import engine, Base, APIUsage


async def migrate_add_usage_tracking():
    """Add api_usage table for tracking user activity."""
    
    print("🔄 Starting migration: Adding api_usage table")
    
    async with engine.begin() as conn:
        # Check if table exists
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='api_usage'")
        )
        exists = result.fetchone()
        
        if exists:
            print("✓ Table 'api_usage' already exists. Skipping creation.")
        else:
            print("Creating 'api_usage' table...")
            await conn.run_sync(Base.metadata.create_all)
            print("✓ Table 'api_usage' created successfully")
    
    print("✅ Migration completed!")


if __name__ == "__main__":
    try:
        asyncio.run(migrate_add_usage_tracking())
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)