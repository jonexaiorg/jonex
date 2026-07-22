#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - Configuration management module

Supports:
- Multi-environment configuration (dev/test/uat/prod)
- Environment variable override
- Type safety
- Hot reload (optional)
"""

import os
from functools import lru_cache
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
try:
    # pydantic v2
    from pydantic.v1 import BaseSettings, Field, validator
except ImportError:
    # pydantic v1
    from pydantic import BaseSettings, Field, validator


# ==================== Configuration base classes ====================
class DatabaseSettings(BaseSettings):
    """Database configuration"""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USERNAME: str = "jonex"
    DB_PASSWORD: str = "jonex123"
    DB_NAME: str = "jonex"

    # Connection pool configuration
    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 100
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    class Config:
        env_file = ".env"


class RedisSettings(BaseSettings):
    """Redis Configuration"""
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Connection pool configuration
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 10
    REDIS_CONNECT_TIMEOUT: int = 5
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    REDIS_DECODE_RESPONSES: bool = True

    @validator("REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_PASSWORD", pre=True)
    def parse_redis_url(cls, v, values, field):
        """Parse connection parameters from REDIS_URL (if provided)"""
        url = values.get("REDIS_URL")
        if url and url.startswith("redis://"):
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                if parsed.hostname:
                    values["REDIS_HOST"] = parsed.hostname
                if parsed.port:
                    values["REDIS_PORT"] = parsed.port
                if parsed.path and parsed.path != "/":
                    db_str = parsed.path.lstrip("/")
                    if db_str.isdigit():
                        values["REDIS_DB"] = int(db_str)
                if parsed.password:
                    values["REDIS_PASSWORD"] = parsed.password
                return values.get(field.name, v)
            except Exception:
                pass
        return v

    class Config:
        env_file = ".env"


class SecuritySettings(BaseSettings):
    """Security configuration"""
    JWT_SECRET: str = "your_jwt_secret_key_here_please_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # User authentication configuration
    USER_JWT_EXPIRE_HOURS: int = 24
    USER_JWT_REFRESH_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12

    # API Key Configuration
    API_KEY_HEADER: str = "X-API-Key"
    API_KEY_LENGTH: int = 32

    # Login ticket configuration
    LOGIN_TICKET_EXPIRE_SECONDS: int = 60
    AUTH_ALLOWED_REDIRECT_URIS: str = ""  # JSON string: {"appId": ["uri1", "uri2"]}

    class Config:
        env_file = ".env"


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/jonex.log"
    LOG_JSON_FORMAT: bool = False

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")
        return v.upper()

    class Config:
        env_file = ".env"


class TCADPSettings(BaseSettings):
    """TCADP platform configuration"""
    TCADP_API_URL: str = "https://tcadp.tencent.com/api"
    TCADP_API_KEY: Optional[str] = None
    TCADP_WEBHOOK_SECRET: Optional[str] = None
    TCADP_WEBHOOK_URL: Optional[str] = None
    TCADP_TIMEOUT: int = 30

    class Config:
        env_file = ".env"


class MilvusSettings(BaseSettings):
    """Milvus vector database configuration"""
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: Optional[str] = None
    MILVUS_PASSWORD: Optional[str] = None
    MILVUS_HTTP_PORT: int = 9091

    # Connection configuration
    MILVUS_CONNECT_TIMEOUT: int = 30
    MILVUS_KEEP_ALIVE: bool = True
    MILVUS_ALIAS: str = "default"

    # Vector configuration
    MILVUS_DEFAULT_DIM: int = 1536
    MILVUS_DEFAULT_METRIC: str = "COSINE"
    MILVUS_DEFAULT_INDEX: str = "IVF_FLAT"

    class Config:
        env_file = ".env"


class CorsSettings(BaseSettings):
    """CORS and Cookie configuration"""
    AUTH_CORS_ORIGINS: str = ""  # Comma-separated: "https://a.com,https://b.com"
    AUTH_COOKIE_DOMAIN: str = ""
    AUTH_COOKIE_SECURE: bool = True
    AUTH_COOKIE_SAMESITE: str = "Lax"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.AUTH_CORS_ORIGINS:
            return []
        return [o.strip() for o in self.AUTH_CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"


class AppSettings(BaseSettings):
    """Application configuration"""
    APP_NAME: str = "jonex-platform"
    APP_VERSION: str = "0.1.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Environment identifier
    ENV: str = Field("dev", description="Runtime environment: dev/test/uat/prod")

    # Rate limit configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100

    # Metering configuration
    METERING_ENABLED: bool = True

    # Sidecar service address
    SIDECAR_URL: str = "http://localhost:8001"

    # Capability service address
    KNOWLEDGE_BASE_URL: str = "http://localhost:8003"
    ATOMIC_RAG_URL: str = "http://localhost:8004"

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "prod"

    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "dev"

    class Config:
        env_file = ".env"


# ==================== Main configuration class ====================
class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    LoggingSettings,
    TCADPSettings,
    MilvusSettings,
    CorsSettings,
    AppSettings,
):
    """Global configuration class"""

    class Config:
        env_file = ".env"
        case_sensitive = True


# ==================== Configuration loading ====================
def _load_env_file() -> None:
    """Load environment variable file"""
    # Try to load in priority order:
    # 1. Configuration file specified by environment variable
    # 2. .env.{environment}
    # 3. .env

    env_specific_file = os.getenv("ENV_FILE")
    env_name = os.getenv("ENV", "dev").lower()

    search_paths = [
        Path(".") / f".env.{env_name}",
        Path(".") / ".env",
        Path(".") / "deploy" / ".env",
    ]

    if env_specific_file:
        search_paths.insert(0, Path(env_specific_file))

    for path in search_paths:
        if path.exists():
            load_dotenv(path, override=True)
            break


# Load environment file first
_load_env_file()


@lru_cache(maxsize=None)
def get_config() -> Settings:
    """
    Get global configuration instance (singleton)

    Returns:
        Settings: Global configuration instance
    """
    return Settings()


def reload_config() -> Settings:
    """
    Reload configuration (hot reload)

    Note: Already created objects will not be updated automatically, need to recreate manually
    """
    _load_env_file()
    get_config.cache_clear()
    return get_config()


# ==================== Configuration export ====================
# For backward compatibility, export as constants
config = get_config()

ENV = config.ENV
DEBUG = config.is_development
