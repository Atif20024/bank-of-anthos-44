"""
Configuration module for AI Backend service.
"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service configuration
    version: str = os.getenv("VERSION", "v1.0.0")
    port: int = int(os.getenv("PORT", "8080"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database configuration
    accounts_db_uri: str = os.getenv("ACCOUNTS_DB_URI", "")
    ledger_db_uri: str = os.getenv("LEDGER_DB_URI", "")
    
    # Google Cloud configuration
    project_id: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    region: str = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
    
    # Vertex AI configuration
    vertex_ai_location: str = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    vertex_ai_model: str = os.getenv("VERTEX_AI_MODEL", "gemini-1.5-pro")
    
    # JWT configuration
    pub_key_path: str = os.getenv("PUB_KEY_PATH", "/etc/secrets/jwtRS256.key.pub")
    local_routing_num: str = os.getenv("LOCAL_ROUTING_NUM", "123456789")
    
    # AI Backend specific settings
    max_retries: int = int(os.getenv("MAX_RETRIES", "1"))
    insight_expiry_days: int = int(os.getenv("INSIGHT_EXPIRY_DAYS", "7"))
    max_insights_per_user: int = int(os.getenv("MAX_INSIGHTS_PER_USER", "50"))
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()
