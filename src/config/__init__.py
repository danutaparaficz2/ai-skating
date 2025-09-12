"""Configuration management for Data on Ice project."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Data on Ice"
    app_version: str = "1.0.0"
    secret_key: str = "your-secret-key-here"
    debug: bool = False
    
    # Alibaba Cloud
    alibaba_access_key_id: str = ""
    alibaba_access_key_secret: str = ""
    alibaba_region: str = "cn-hangzhou"
    
    # Qwen LLM
    qwen_api_key: str = ""
    qwen_model_name: str = "qwen-turbo"
    
    # AnalyticDB
    analyticdb_host: str = "localhost"
    analyticdb_port: int = 3306
    analyticdb_user: str = ""
    analyticdb_password: str = ""
    analyticdb_database: str = "isu_data"
    
    # OpenSearch
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_username: str = ""
    opensearch_password: str = ""
    opensearch_index: str = "isu_archive"
    
    # PAI-EAS
    pai_eas_endpoint: str = ""
    pai_eas_token: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get database connection URL."""
    return (
        f"mysql://{settings.analyticdb_user}:{settings.analyticdb_password}@"
        f"{settings.analyticdb_host}:{settings.analyticdb_port}/{settings.analyticdb_database}"
    )


def get_opensearch_config() -> dict:
    """Get OpenSearch configuration."""
    return {
        "host": settings.opensearch_host,
        "port": settings.opensearch_port,
        "http_auth": (settings.opensearch_username, settings.opensearch_password),
        "use_ssl": True,
        "verify_certs": False,
        "ssl_show_warn": False,
    }