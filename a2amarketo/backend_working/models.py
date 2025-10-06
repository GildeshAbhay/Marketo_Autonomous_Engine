from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    query: str
    session_id: str
    user_id: Optional[str] = "default_user"

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

