from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import Field, field_validator
import os

class BaseConfig(BaseSettings):
    """
    Base configuration with common settings.
    """
    ENV: str = "development"
    SERVICE_NAME: str
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    LOG_LEVEL: str = "INFO"
    
    # MinIO Settings
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio_admin"
    MINIO_SECRET_KEY: str = "minio_password"
    MINIO_SECURE: bool = False
    
    # Database Settings - Support both direct DATABASE_URL and individual POSTGRES_ variables
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "job_tracker_prod"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "secure_password"
    DATABASE_URL: str = Field(default="")
    
    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def construct_database_url(cls, v, info):
        # If DATABASE_URL is provided and not empty, use it
        if v and v.strip():
            return v
        # Otherwise, construct from POSTGRES_ variables
        values = info.data
        return (
            f"postgresql://{values.get('POSTGRES_USER', 'admin')}:"
            f"{values.get('POSTGRES_PASSWORD', 'secure_password')}"
            f"@{values.get('POSTGRES_HOST', 'postgres')}:"
            f"{values.get('POSTGRES_PORT', 5432)}/"
            f"{values.get('POSTGRES_DB', 'job_tracker_prod')}"
        )

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_config(config_cls):
    return config_cls()
