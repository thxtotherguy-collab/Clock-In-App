"""
Core configuration module - loads settings from environment variables.
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    mongo_url: str
    db_name: str
    
    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480  # 8 hours
    jwt_refresh_token_expire_days: int = 7
    
    # CORS
    cors_origins: str = "*"
    
    # App Settings
    app_name: str = "Workforce Management System"
    debug: bool = False
    
    # GPS Settings
    default_geofence_radius_meters: int = 150
    gps_tracking_interval_seconds: int = 300  # 5 minutes
    
    # Offline Sync
    offline_sync_retry_attempts: int = 3
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
