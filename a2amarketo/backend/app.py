import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
import nest_asyncio

# Add parent directory to path to import host agent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from host_agent_marketo.host.agent import HostAgent
from models import (
    QueryRequest, QueryResponse, ReportRequest, ReportTemplate, 
    ConversationHistory, UserCreate, UserResponse, Token, RefreshTokenRequest
)
from database import init_db, save_conversation, get_conversation_history, User, async_session_maker
from config import settings
from auth import (
    get_password_hash, authenticate_user, create_access_token, 
    create_refresh_token, get_current_active_user, verify_refresh_token,
    get_user_by_username, get_user_by_email
)

nest_asyncio.apply()

# Initialize FastAPI app
app = FastAPI(title="Marketo A2A Backend", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global host agent instance
host_agent_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize database and host agent on startup."""
    global host_agent_instance
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Initialize host agent
    # marketo_agent_urls = [
    #     "http://localhost:10002",  # Marketo Agent
    #     "http://localhost:10003",  # Web Search Agent
    # ]
    from config import settings

    marketo_agent_urls = [
        settings.marketo_agent_url,  # From deployment_config.json
        settings.websearch_agent_url,  # From deployment_config.json
    ]
    
    print("🔄 Initializing Host Agent...")
    host_agent_instance = await HostAgent.create(remote_agent_addresses=marketo_agent_urls)
    print("✅ Host Agent initialized and connected to remote agents")

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user.
    """
    # Check if username exists
    existing_user = await get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email exists
    existing_email = await get_user_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    async with async_session_maker() as session:
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            is_active=True
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible login endpoint.
    Returns access token and refresh token.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    """
    payload = verify_refresh_token(refresh_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    username = payload.get("sub")
    user = await get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.
    """
    return current_user

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "message": "Marketo A2A Backend API",
        "version": "1.0.0",
        "endpoints": [
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/refresh",
            "/api/auth/me",
            "/api/query",
            "/api/reports/templates",
            "/api/reports/generate",
            "/api/history/{session_id}"
        ]
    }

@app.post("/api/query", response_model=QueryResponse)
async def query_agent(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a query to the Host Agent and get response.
    This DIRECTLY calls the host agent.
    **Requires authentication.**
    """
    if not host_agent_instance:
        raise HTTPException(status_code=503, detail="Host agent not initialized")
    
    try:
        # Call host agent's stream method
        full_response = ""
        async for event in host_agent_instance.stream(
            query=request.query,
            session_id=request.session_id
        ):
            if event.get("is_task_complete"):
                full_response = event.get("content", "")
            else:
                # You can log intermediate updates here
                print(f"Agent update: {event.get('updates')}")
        
        # Save to database
        await save_conversation(
            session_id=request.session_id,
            user_id=request.user_id,
            query=request.query,
            response=full_response
        )
        
        return QueryResponse(
            session_id=request.session_id,
            response=full_response,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/reports/templates")
async def get_report_templates(current_user: User = Depends(get_current_active_user)):
    """
    Returns available report templates.
    These are pre-defined report structures.
    **Requires authentication.**
    """
    templates = [
        ReportTemplate(
            id="campaign_performance",
            name="Campaign Performance Report",
            description="Shows opens, clicks, and conversions for a campaign",
            example_query="Generate performance report for campaign {campaign_id}"
        ),
        ReportTemplate(
            id="lead_distribution",
            name="Lead Score Distribution",
            description="Analyze lead score distribution by segments",
            example_query="Show me lead score distribution for smart list {smart_list_id}"
        ),
        ReportTemplate(
            id="recent_campaigns",
            name="Recent Campaigns Summary",
            description="List all recent campaigns with key metrics",
            example_query="Get summary of all campaigns from last 30 days"
        )
    ]
    return {"templates": templates}

@app.post("/api/reports/generate")
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a structured report using a template.
    Constructs a detailed prompt and sends to Host Agent.
    **Requires authentication.**
    """
    if not host_agent_instance:
        raise HTTPException(status_code=503, detail="Host agent not initialized")
    
    # Construct structured prompt based on template
    template_prompts = {
        "campaign_performance": (
            f"Generate a detailed performance report for Marketo campaign ID {request.parameters.get('campaign_id')}. "
            "Include: campaign name, status, start/end dates, total opens, total clicks, click-through rate, "
            "and any available conversion metrics. Format the data in a clear, structured way."
        ),
        "lead_distribution": (
            f"Analyze the lead score distribution for smart list ID {request.parameters.get('smart_list_id')}. "
            "Show: total leads, average score, score ranges (0-25, 26-50, 51-75, 76-100), "
            "and identify any notable patterns or outliers."
        ),
        "recent_campaigns": (
            "Get a summary of all Marketo campaigns from the last 30 days. "
            "For each campaign show: name, ID, status, start date, and key performance indicators."
        )
    }
    
    prompt = template_prompts.get(
        request.template_id,
        f"Generate a report with parameters: {request.parameters}"
    )
    
    try:
        full_response = ""
        async for event in host_agent_instance.stream(
            query=prompt,
            session_id=request.session_id
        ):
            if event.get("is_task_complete"):
                full_response = event.get("content", "")
        
        # Save to database
        await save_conversation(
            session_id=request.session_id,
            user_id=request.user_id,
            query=f"Report: {request.template_id}",
            response=full_response
        )
        
        return {
            "session_id": request.session_id,
            "report_type": request.template_id,
            "response": full_response,
            "timestamp": datetime.utcnow()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/api/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve conversation history for a session.
    **Requires authentication.**
    """
    try:
        history = await get_conversation_history(session_id)
        return ConversationHistory(
            session_id=session_id,
            messages=history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

# Health check for agents
@app.get("/api/health")
async def health_check():
    """Check if all agents are responsive."""
    import httpx
    
    agent_status = {}
    async with httpx.AsyncClient(timeout=5) as client:
        # Check Marketo Agent
        try:
            resp = await client.get("http://localhost:10002/.well-known/agent-card.json")
            agent_status["marketo_agent"] = "healthy" if resp.status_code == 200 else "unhealthy"
        except:
            agent_status["marketo_agent"] = "down"
        
        # Check WebSearch Agent
        try:
            resp = await client.get("http://localhost:10003/.well-known/agent-card.json")
            agent_status["websearch_agent"] = "healthy" if resp.status_code == 200 else "unhealthy"
        except:
            agent_status["websearch_agent"] = "down"
    
    return {
        "backend": "healthy",
        "agents": agent_status,
        "host_agent": "healthy" if host_agent_instance else "not_initialized"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.backend_host, port=settings.backend_port)


