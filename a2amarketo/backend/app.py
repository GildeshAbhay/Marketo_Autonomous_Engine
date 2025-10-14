from sqlalchemy import select  # Add this
from rbac import (
    validate_user_query_permission,
    ROLE_ADMIN,
    ROLE_ANALYST
)
from typing import Optional
from functools import wraps
from fastapi import Request, Depends
import sys, os, uuid, asyncio, nest_asyncio, time
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
# Add parent directory to path to import host agent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from host_agent_marketo.host.agent import HostAgent
from models import (
    QueryRequest, QueryResponse, ReportRequest, ReportTemplate, 
    ConversationHistory, UserCreate, UserResponse, Token, RefreshTokenRequest,
    AutonomousReportRequest, AutonomousReportResponse
)
from database import (
    init_db, save_conversation, get_conversation_history, 
    User, async_session_maker, log_api_usage, APIUsage,
    get_user_usage_stats
)
from config import settings
from auth import (
    get_password_hash, authenticate_user, create_access_token, 
    create_refresh_token, get_current_active_user, verify_refresh_token,
    get_user_by_username, get_user_by_email,require_analyst_or_admin,require_admin
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

async def track_api_usage(
    request: Request,
    current_user: User,
    endpoint_type: str,
    query_text: str = None,
    session_id: str = None
):
    """Helper to track API usage."""
    await log_api_usage(
        user_id=current_user.id,
        username=current_user.username,
        endpoint=request.url.path,
        endpoint_type=endpoint_type,
        method=request.method,
        session_id=session_id,
        query_text=query_text
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
    
    # 🆕 NEW: Validate role (only allow analyst by default, admin must be set manually)
    if user_data.role not in [ROLE_ADMIN, ROLE_ANALYST]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be '{ROLE_ADMIN}' or '{ROLE_ANALYST}'"
        )
    
    # Security: Don't allow users to self-register as admin
    # First user can be admin, or admins must be set via database/migration
    async with async_session_maker() as session:
        result = await session.execute(select(User))
        existing_users = result.scalars().all()
        
        # If trying to register as admin and not the first user, reject
        if user_data.role == ROLE_ADMIN and len(existing_users) > 0:
            # Check if requester is already an admin (would need auth token)
            # For now, block self-registration as admin
            user_data.role = ROLE_ANALYST  # Force to analyst

    # Create new user
    async with async_session_maker() as session:
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            role=user_data.role  # ✅ ADD THIS LINE
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
    
    # access_token = create_access_token(data={"sub": user.username})
    # refresh_token = create_refresh_token(data={"sub": user.username})
        # 🆕 UPDATED: Include role in token claims
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "role": user.role}
    )
    
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
    current_user: User = Depends(require_analyst_or_admin),
    req: Request = None  # Add Request object
):
    """
    Send a query to the Host Agent and get response.
    This DIRECTLY calls the host agent.
    **Requires authentication.**
    """
    if not host_agent_instance:
        raise HTTPException(status_code=503, detail="Host agent not initialized")

 # 🆕 NEW: Validate query permissions based on user role
    validate_user_query_permission(request.query, current_user.role)

    # 🆕 Track API usage
    await track_api_usage(
        request=req,
        current_user=current_user,
        endpoint_type="query",
        query_text=request.query,
        session_id=request.session_id
    )

    try:
        # Call host agent's stream method
        full_response = ""
        async for event in host_agent_instance.stream(
            query=request.query,
            session_id=request.session_id
            #user_role=current_user.role
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
async def get_report_templates(current_user: User = Depends(require_analyst_or_admin)):
    """
    Returns available report templates.
    These are pre-defined report structures.
    Requires authentication with analyst or admin role.
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

@app.post("/api/reports/autonomous-generate")
async def generate_autonomous_report(
    request: AutonomousReportRequest,
    current_user: User = Depends(require_analyst_or_admin),
    req: Request = None
):
    """
    Generate a fully autonomous comprehensive report.
    Combines Marketo data with web research using Gemini API.
    **Requires authentication with analyst or admin role.**
    """
    if not host_agent_instance:
        raise HTTPException(status_code=503, detail="Host agent not initialized")
    
    # Track API usage
    await track_api_usage(
        request=req,
        current_user=current_user,
        endpoint_type="autonomous_report",
        session_id=request.session_id
    )
    try:
        # Initialize report components
        from report_generator import ReportDataCollector, AutonomousReportGenerator
        
        collector = ReportDataCollector(
            host_agent=host_agent_instance,
            websearch_agent_url=settings.websearch_agent_url
        )
        generator = AutonomousReportGenerator()
        # Step 1: Collect Marketo data
        print(f"📊 Collecting Marketo data from {request.start_date} to {request.end_date}...")
        marketo_data = await collector.collect_marketo_data(
            start_date=request.start_date,
            end_date=request.end_date,
            session_id=request.session_id
        )
        # Step 2: Collect web research (if requested)
        web_research = []
        if request.include_web_research:
            print("🔍 Collecting web research...")
            web_research = await collector.collect_web_research(
                topic="marketing automation",
                session_id=request.session_id
            )
        # Step 3: Generate comprehensive report using Gemini
        print("🤖 Generating comprehensive report with Gemini...")
        report_content = await generator.generate_comprehensive_report(
            start_date=request.start_date,
            end_date=request.end_date,
            marketo_data=marketo_data,
            web_research=web_research,
            report_type=request.report_type
        )
        # Save to database
        await save_conversation(
            session_id=request.session_id,
            user_id=request.user_id,
            query=f"Autonomous Report: {request.start_date} to {request.end_date}",
            response=report_content
        )
        return AutonomousReportResponse(
            session_id=request.session_id,
            report_content=report_content,
            report_type=request.report_type,
            period={"start_date": request.start_date, "end_date": request.end_date},
            generated_at=datetime.utcnow(),
            included_web_research=request.include_web_research
        )
    except Exception as e:
        print(f"❌ Error generating autonomous report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/api/history/{session_id}")
async def get_history(
    session_id: str,
    current_user: User = Depends(require_analyst_or_admin)
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

@app.get("/api/analytics/my-usage")
async def get_my_usage_stats(
    current_user: User = Depends(get_current_active_user),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get API usage statistics for the current user."""
    stats = await get_user_usage_stats(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Count by endpoint type
    from collections import Counter
    endpoint_counts = Counter()
    for req in stats["requests"]:
        endpoint_counts[req["endpoint_type"]] += 1
    
    stats["by_endpoint_type"] = dict(endpoint_counts)
    
    return stats


@app.get("/api/analytics/all-usage")
async def get_all_usage_stats(
    current_user: User = Depends(require_admin)
):
    """Get all users' API usage statistics (Admin only)."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(APIUsage).order_by(APIUsage.timestamp.desc()).limit(1000)
        )
        usages = result.scalars().all()
        
        from collections import Counter
        user_counts = Counter()
        endpoint_counts = Counter()
        
        for u in usages:
            user_counts[u.username] += 1
            endpoint_counts[u.endpoint_type] += 1
        
        return {
            "total_requests": len(usages),
            "by_user": dict(user_counts),
            "by_endpoint_type": dict(endpoint_counts),
            "recent_requests": [
                {
                    "username": u.username,
                    "endpoint": u.endpoint,
                    "endpoint_type": u.endpoint_type,
                    "timestamp": u.timestamp
                }
                for u in usages[:50]  # Last 50 requests
            ]
        }

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


