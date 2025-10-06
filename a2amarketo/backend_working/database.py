from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text, DateTime, Integer
from datetime import datetime
import json

DATABASE_URL = "sqlite+aiosqlite:///./conversations.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    user_id = Column(String, index=True)
    query = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def save_conversation(session_id: str, user_id: str, query: str, response: str):
    async with async_session_maker() as session:
        conv = Conversation(
            session_id=session_id,
            user_id=user_id,
            query=query,
            response=response
        )
        session.add(conv)
        await session.commit()

async def get_conversation_history(session_id: str):
    async with async_session_maker() as session:
        result = await session.execute(
            f"SELECT query, response, timestamp FROM conversations WHERE session_id = '{session_id}' ORDER BY timestamp"
        )
        rows = result.fetchall()
        return [
            {"query": row[0], "response": row[1], "timestamp": row[2]}
            for row in rows
        ]

