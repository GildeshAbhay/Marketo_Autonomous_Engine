from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, select
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

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
            select(Conversation).where(Conversation.session_id == session_id).order_by(Conversation.timestamp)
        )
        conversations = result.scalars().all()
        return [
            {"query": conv.query, "response": conv.response, "timestamp": conv.timestamp}
            for conv in conversations
        ]

