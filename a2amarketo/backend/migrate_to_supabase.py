import asyncio
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from database import Base, User, Conversation
from config import settings

async def migrate_sqlite_to_postgres():
    """Migrate data from SQLite to PostgreSQL (Supabase)."""
    
    # SQLite connection (old)
    sqlite_conn = sqlite3.connect('conversations.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # PostgreSQL connection (new - Supabase)
    pg_engine = create_async_engine(settings.database_url)
    async with pg_engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    pg_session = async_sessionmaker(pg_engine, class_=AsyncSession)
    
    # Migrate Users
    sqlite_cursor.execute("SELECT * FROM users")
    users = sqlite_cursor.fetchall()
    
    async with pg_session() as session:
        for user in users:
            new_user = User(
                id=user[0],
                username=user[1],
                email=user[2],
                hashed_password=user[3],
                full_name=user[4],
                is_active=user[5],
                created_at=user[6]
            )
            session.add(new_user)
        await session.commit()
    
    # Migrate Conversations
    sqlite_cursor.execute("SELECT * FROM conversations")
    conversations = sqlite_cursor.fetchall()
    
    async with pg_session() as session:
        for conv in conversations:
            new_conv = Conversation(
                id=conv[0],
                session_id=conv[1],
                user_id=conv[2],
                query=conv[3],
                response=conv[4],
                timestamp=conv[5]
            )
            session.add(new_conv)
        await session.commit()
    
    print(f"✅ Migrated {len(users)} users and {len(conversations)} conversations")
    
    sqlite_conn.close()
    await pg_engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_sqlite_to_postgres())