from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # CORS settings
    cors_allow_origins: Optional[str] = None

    # Rate limiting settings
    rate_limit_per_minute: int = 600

    # Cache TTLs (in seconds)
    tiles_cache_ttl: int = 604800  # 7 days
    quickfacts_cache_ttl: int = 86400  # 24 hours

    # Logging settings
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
