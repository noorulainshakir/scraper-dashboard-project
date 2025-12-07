"""
Configuration management with environment variables
"""
import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App Configuration
    app_name: str = "Scraper Dashboard"
    app_version: str = "1.0.0"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    
    # Database Configuration (SQLite for job history)
    database_url: str = "sqlite:///./jobs.db"
    
    # Redis Configuration (for Celery)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    @property
    def redis_url(self) -> str:
        """Build Redis URL for Celery"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # Celery Configuration
    celery_broker_url: str = ""  # Will use redis_url if not set
    celery_result_backend: str = ""  # Will use redis_url if not set
    
    # NocoDB Configuration
    nocodb_api_token: str = ""
    nocodb_base_url: str = ""
    nocodb_project_name: str = ""
    nocodb_table_name: str = ""
    
    # Wink API Configuration
    wink_api_base_url: str = "https://azurefd.downloadwink.com"
    wink_account_id: int = 0
    wink_username: str = ""
    wink_password: str = ""
    wink_store_id: int = 1
    
    # Job Configuration
    job_timeout: int = 3600  # 1 hour default timeout
    max_concurrent_jobs: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            """Parse environment variables"""
            if field_name in ['wink_account_id', 'wink_store_id', 'redis_port', 'redis_db', 
                            'job_timeout', 'max_concurrent_jobs']:
                try:
                    return int(raw_val)
                except ValueError:
                    return 0
            if field_name == 'debug':
                return raw_val.lower() in ('true', '1', 'yes')
            return raw_val
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set Celery URLs from Redis if not explicitly set
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

