from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    query: str
    session_id: str
    user_id: Optional[str] = "default_user"
    file_path: Optional[str] = None  # Add this line for file attachment support

class QueryResponse(BaseModel):
    session_id: str
    response: str
    timestamp: datetime

class ReportTemplate(BaseModel):
    id: str
    name: str
    description: str
    example_query: str

class ReportRequest(BaseModel):
    template_id: str
    parameters: Dict[str, Any]
    session_id: str
    user_id: Optional[str] = "default_user"

class ConversationHistory(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]

# Authentication Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "analyst"  # Default to analyst for safety

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    role: str  # Will be "admin" or "analyst"
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class AutonomousReportRequest(BaseModel):
    """Request for autonomous report generation."""
    start_date: str  # YYYY-MM-DD format
    end_date: str    # YYYY-MM-DD format
    report_type: str = "comprehensive"  # comprehensive, campaign, lead_analysis
    session_id: str
    user_id: Optional[str] = "default_user"
    include_web_research: bool = True

class AutonomousReportResponse(BaseModel):
    """Response for autonomous report generation."""
    session_id: str
    report_content: str  # Markdown formatted report
    report_type: str
    period: Dict[str, str]  # start_date, end_date
    generated_at: datetime
    included_web_research: bool