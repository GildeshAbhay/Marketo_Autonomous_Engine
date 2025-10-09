from pydantic_settings import BaseSettings
from typing import List
import os
import sys

# Add path to shared config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.config_loader import get_config

deployment_config = get_config()

class Settings(BaseSettings):
    # Backend settings - now from deployment_config.json
    backend_host: str = deployment_config.get_service_host("backend")
    backend_port: int = deployment_config.get_service_port("backend")
    
    # Agent URLs - now from deployment_config.json
    marketo_agent_url: str = deployment_config.get_service_url("marketo_agent")
    websearch_agent_url: str = deployment_config.get_service_url("websearch_agent")
    mcp_server_url: str = deployment_config.get_service_url("mcp_server")
    
    # CORS - environment-aware
    allowed_origins: List[str] = [
        deployment_config.get_service_url("frontend"),
        "http://localhost:3000",
        "http://localhost:5173",
    ] if deployment_config.env == "local" else [deployment_config.get_service_url("frontend")]
    
    # Database - now from deployment_config.json
    database_url: str = deployment_config.get_database_url()
    
    # JWT Authentication (keep from .env for security)
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    class Config:
        env_file = ".env"

settings = Settings()