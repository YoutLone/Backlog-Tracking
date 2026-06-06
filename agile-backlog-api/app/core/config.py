from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: SecretStr
    
    # JWT
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    
    # App
    app_env: str = "development"
    debug: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# Global settings instance
settings = Settings()

# Validate critical config on startup
if settings.app_env == "production":
    assert settings.jwt_secret_key.get_secret_value() != "your-super-secret-jwt-key-change-this-in-production", \
        "Must change JWT secret in production"