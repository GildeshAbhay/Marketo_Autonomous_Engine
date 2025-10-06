from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Backend settings
    backend_host: str = "localhost"
    backend_port: int = 5000
    
    # Agent URLs
    host_agent_url: str = "http://localhost:8000"
    marketo_agent_url: str = "http://localhost:10002"
    websearch_agent_url: str = "http://localhost:10003"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./conversations.db"
    
    # JWT Authentication
    secret_key: str = "813ade66f503ab91188bf1ed95e6c6fd4e6410c90097186960c28cdd285d20fe"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    class Config:
        env_file = ".env"

settings = Settings()

