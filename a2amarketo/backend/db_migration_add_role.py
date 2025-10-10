"""
Database migration script to add 'role' column to users table.

This script:
1. Adds 'role' column to the users table with default value 'analyst'
2. Sets the first user (typically the initial user) to 'admin' role
3. Can be run idempotently (safe to run multiple times)

Usage:
    python backend/db_migration_add_role.py
"""

import asyncio
import sys
from sqlalchemy import text
from database import engine, async_session_maker


async def migrate_add_role_column():
    """Add role column to users table and set default roles."""
    
    print("🔄 Starting database migration: Adding 'role' column to users table")
    
    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(
            text("PRAGMA table_info(users)")
        )
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'role' in column_names:
            print("✓ Column 'role' already exists. Skipping column creation.")
        else:
            # Add role column with default value
            print("Adding 'role' column with default value 'analyst'...")
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'analyst' NOT NULL")
            )
            print("✓ Column 'role' added successfully")
    
    # Set first user to admin (if any users exist)
    async with async_session_maker() as session:
        # Check if any users exist
        result = await session.execute(
            text("SELECT COUNT(*) FROM users")
        )
        user_count = result.scalar()
        
        if user_count > 0:
            # Set first user to admin
            print(f"Found {user_count} existing user(s)")
            await session.execute(
                text("""
                    UPDATE users 
                    SET role = 'admin' 
                    WHERE id = (SELECT MIN(id) FROM users)
                    AND role != 'admin'
                """)
            )
            await session.commit()
            print("✓ Set first user to 'admin' role")
        else:
            print("ℹ No existing users found. Next registered user can be set to admin manually.")
    
    print("✅ Migration completed successfully!")
    print("\nNext steps:")
    print("1. Restart your backend server")
    print("2. Verify user roles in the database")
    print("3. Optionally, manually set other admin users using SQL:")
    print("   UPDATE users SET role = 'admin' WHERE username = 'your_username';")


async def verify_migration():
    """Verify the migration was successful."""
    print("\n🔍 Verifying migration...")
    
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT username, email, role FROM users")
        )
        users = result.fetchall()
        
        if users:
            print("\nCurrent users and roles:")
            print("-" * 60)
            for user in users:
                print(f"Username: {user[0]:<20} Email: {user[1]:<30} Role: {user[2]}")
            print("-" * 60)
        else:
            print("No users found in database")


if __name__ == "__main__":
    try:
        asyncio.run(migrate_add_role_column())
        asyncio.run(verify_migration())
    except Exception as e:
        print(f"❌ Migration failed: {e}", file=sys.stderr)
        sys.exit(1)