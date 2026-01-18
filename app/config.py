"""Application configuration."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://jlegal:jlegal@db:5432/jlegal"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Storage
    storage_path: str = "/app/storage"
    max_upload_size: int = 104857600  # 100MB

    # Workers
    workers_per_container: int = 4

    # OCR
    ocr_languages: str = "eng"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    # Security
    secret_key: str = "change-this-in-production"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
