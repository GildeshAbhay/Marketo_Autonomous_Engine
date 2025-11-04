import json
import os
from typing import Dict, Any

class DeploymentConfig:
    """Load deployment configuration based on environment."""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            # Look for config relative to this file
            config_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "deployment_config.json"
            )
        self.config_path = config_path
        self.env = os.getenv("DEPLOYMENT_ENV", "local")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        env_config = data["environments"][self.env]
        
        # Replace ${VAR} placeholders with environment variables
        return self._resolve_env_vars(env_config)
    
    def _resolve_env_vars(self, config: Dict) -> Dict:
        """Recursively resolve environment variable placeholders."""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
            var_name = config[2:-1]
            return os.getenv(var_name, config)
        return config
    
    def get_service_url(self, service_name: str) -> str:
        """Get URL for a service."""
        # Check if there's an environment variable override (for Docker)
        import os
        env_var_name = f"{service_name.upper()}_URL"
        env_url = os.getenv(env_var_name)
        if env_url:
            return env_url
        return self.config[service_name]["url"]
    
    def get_service_host(self, service_name: str) -> str:
        """Get host for a service."""
        return self.config[service_name]["host"]
    
    def get_service_port(self, service_name: str) -> int:
        """
        Get port for a service.
        
        Priority:
        1. PORT environment variable (set by Cloud Run)
        2. deployment_config.json value
        """
        # PRIORITY 1: Cloud Run sets PORT env var
        if os.getenv("PORT"):
            return int(os.getenv("PORT"))
        
        # PRIORITY 2: deployment_config.json
        return self.config[service_name]["port"]
    
    def get_database_url(self) -> str:
        """Get database connection URL."""
        return self.config["database"]["url"]

# Singleton instance
_config = None

def get_config() -> DeploymentConfig:
    """Get deployment configuration singleton."""
    global _config
    if _config is None:
        _config = DeploymentConfig()
    return _config