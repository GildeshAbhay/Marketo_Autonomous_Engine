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
    role = Column(String, default="analyst", nullable=False)  # Options: "admin", "analyst"

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

class APIUsage(Base):
    """Track user API usage for analytics."""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)  # FK to User.id
    username = Column(String, nullable=False, index=True)  # Denormalized for easier queries
    endpoint = Column(String, nullable=False)  # e.g., "/api/query", "/api/reports/generate"
    endpoint_type = Column(String, nullable=False)  # "query", "report", "auth"
    method = Column(String, nullable=False)  # "GET", "POST", etc.
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(String, nullable=True)  # For tracking sessions
    query_text = Column(Text, nullable=True)  # Store query if applicable (for audit)
    status_code = Column(Integer, nullable=True)  # Response status
    response_time_ms = Column(Integer, nullable=True)  # For performance tracking


async def log_api_usage(
    user_id: int,
    username: str,
    endpoint: str,
    endpoint_type: str,
    method: str = "POST",
    session_id: str = None,
    query_text: str = None,
    status_code: int = 200,
    response_time_ms: int = None
):
    """Log API usage for analytics."""
    async with async_session_maker() as session:
        usage = APIUsage(
            user_id=user_id,
            username=username,
            endpoint=endpoint,
            endpoint_type=endpoint_type,
            method=method,
            session_id=session_id,
            query_text=query_text,
            status_code=status_code,
            response_time_ms=response_time_ms
        )
        session.add(usage)
        await session.commit()


async def get_user_usage_stats(user_id: int, start_date: datetime = None, end_date: datetime = None):
    """Get usage statistics for a user."""
    async with async_session_maker() as session:
        query = select(APIUsage).where(APIUsage.user_id == user_id)
        
        if start_date:
            query = query.where(APIUsage.timestamp >= start_date)
        if end_date:
            query = query.where(APIUsage.timestamp <= end_date)
        
        query = query.order_by(APIUsage.timestamp.desc())
        
        result = await session.execute(query)
        usages = result.scalars().all()
        
        return {
            "total_requests": len(usages),
            "by_endpoint": {},
            "requests": [
                {
                    "endpoint": u.endpoint,
                    "endpoint_type": u.endpoint_type,
                    "timestamp": u.timestamp,
                    "status_code": u.status_code
                }
                for u in usages
            ]
        }