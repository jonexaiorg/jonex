#!/usr/bin/python3



import os
from functools import lru_cache
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv
try:

    from pydantic.v1 import BaseSettings, Field, validator
except ImportError:

    from pydantic import BaseSettings, Field, validator



class DatabaseSettings(BaseSettings):

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USERNAME: str = "jonex"
    DB_PASSWORD: str = ""
    DB_NAME: str = "jonex"


    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 100
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False

    class Config:
        env_file = ".env"


class RedisSettings(BaseSettings):

    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None


    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 10
    REDIS_CONNECT_TIMEOUT: int = 5
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    REDIS_DECODE_RESPONSES: bool = True

    @validator("REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_PASSWORD", pre=True)
    def parse_redis_url(cls, v, values, field):

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

    JWT_SECRET: str = "your_jwt_secret_key_here_please_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7


    USER_JWT_EXPIRE_HOURS: int = 24
    USER_JWT_REFRESH_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12


    API_KEY_HEADER: str = "X-API-Key"
    API_KEY_LENGTH: int = 32


    LOGIN_TICKET_EXPIRE_SECONDS: int = 60
    AUTH_ALLOWED_REDIRECT_URIS: str = ""

    class Config:
        env_file = ".env"


class LoggingSettings(BaseSettings):

    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/jonex.log"
    LOG_JSON_FORMAT: bool = False

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL 必须是以下之一: {valid_levels}")
        return v.upper()

    class Config:
        env_file = ".env"


class TCADPSettings(BaseSettings):

    TCADP_API_URL: str = "https://tcadp.tencent.com/api"
    TCADP_API_KEY: Optional[str] = None
    TCADP_WEBHOOK_SECRET: Optional[str] = None
    TCADP_WEBHOOK_URL: Optional[str] = None
    TCADP_TIMEOUT: int = 30

    class Config:
        env_file = ".env"


class MilvusSettings(BaseSettings):

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: Optional[str] = None
    MILVUS_PASSWORD: Optional[str] = None
    MILVUS_HTTP_PORT: int = 9091


    MILVUS_CONNECT_TIMEOUT: int = 30
    MILVUS_KEEP_ALIVE: bool = True
    MILVUS_ALIAS: str = "default"


    MILVUS_DEFAULT_DIM: int = 1536
    MILVUS_DEFAULT_METRIC: str = "COSINE"
    MILVUS_DEFAULT_INDEX: str = "IVF_FLAT"

    class Config:
        env_file = ".env"


class CorsSettings(BaseSettings):

    AUTH_CORS_ORIGINS: str = ""
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

    APP_NAME: str = "jonex-platform"
    APP_VERSION: str = "0.1.0"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000


    ENV: str = Field("dev", description="运行环境: dev/test/uat/prod")


    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100


    METERING_ENABLED: bool = True


    CIRCUIT_BREAKER_ENABLED: bool = False
    CIRCUIT_BREAKER_THRESHOLD: int = 5


    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_ASYNC: bool = True
    AUDIT_QUEUE_MAX_SIZE: int = 10000
    AUDIT_FLUSH_BATCH_SIZE: int = 100
    AUDIT_FLUSH_INTERVAL_MS: int = 200
    AUDIT_HTTP_METHODS: str = "POST,PUT,PATCH,DELETE"
    AUDIT_RETENTION_DAYS: int = 90
    AUDIT_INGEST_URL: str = ""


    AUDIT_KEY_ACTION_KEYWORDS: str = (
        "create,update,delete,remove,save,publish,modify,edit,import,"
        "review,retry,cancel,approve,reject,bind,unbind,enable,disable,reset,upload"
    )


    SIDECAR_URL: str = "http://localhost:8001"
    SIDECAR_API_KEY: str = ""


    KNOWLEDGE_BASE_URL: str = "http://localhost:8003"
    BUSINESS_DOMAIN_URL: str = "http://localhost:8005"
    ATOMIC_RAG_URL: str = "http://localhost:8004"
    PLATFORM_URL: str = "http://localhost:8006"

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "prod"

    @property
    def is_development(self) -> bool:
        return self.ENV.lower() == "dev"

    class Config:
        env_file = ".env"


class LLMGatewaySettings(BaseSettings):


    LLMGW_UPSTREAM_LLM_HOST: str = "https://tokenhub.tencentmaas.com/v1"
    LLMGW_UPSTREAM_LLM_API_KEY: str = ""
    LLMGW_UPSTREAM_EMBED_HOST: str = "http://host.docker.internal:11434/v1"
    LLMGW_UPSTREAM_EMBED_API_KEY: str = "ollama"



    LLMGW_RERANK_BINDING: str = "ollama-generate"
    LLMGW_RERANK_MODEL: str = "awenleven/Qwen3-Reranker-4B:Q4_K_M"
    LLMGW_UPSTREAM_RERANK_HOST: str = "http://host.docker.internal:11434"
    LLMGW_UPSTREAM_RERANK_API_KEY: str = "ollama"
    LLMGW_RERANK_PROMPT_PROFILE: str = "qwen3"
    LLMGW_RERANK_MAX_DOCS: int = 12
    LLMGW_RERANK_CONCURRENCY: int = 4
    LLMGW_RERANK_TIMEOUT: int = 30

    LLMGW_PORT: int = 8787
    LLMGW_INTERNAL_TOKENS: str = ""
    LLMGW_REQUEST_TIMEOUT: int = 600

    LLMGW_METERING_ENABLED: bool = True
    LLMGW_QUOTA_ENABLED: bool = False




    LLMGW_DISABLE_THINKING_ENABLED: bool = True
    LLMGW_DISABLE_THINKING_MODELS: str = "deepseek-v4-flash-202605"
    LLMGW_DISABLE_THINKING_SCENES: str = "lightrag_extract,ontology_extract"

    LLMGW_PG_FLUSH_MAX_ROWS: int = 20
    LLMGW_PG_FLUSH_MAX_SECONDS: float = 5.0



    LLMGW_EMBED_AGGREGATE_ENABLED: bool = False
    LLMGW_EMBED_AGGREGATE_SCENES: str = "lightrag_embed,ontology_embed"

    LLMGW_EMBED_AVG_CHARS_PER_TOKEN: int = 4

    class Config:
        env_file = ".env"



class Settings(
    DatabaseSettings,
    RedisSettings,
    SecuritySettings,
    LoggingSettings,
    TCADPSettings,
    MilvusSettings,
    CorsSettings,
    AppSettings,
    LLMGatewaySettings,
):


    class Config:
        env_file = ".env"
        case_sensitive = True



def _load_env_file() -> None:






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
            load_dotenv(path, override=False)
            break



_load_env_file()


@lru_cache(maxsize=None)
def get_config() -> Settings:

    return Settings()


def reload_config() -> Settings:

    _load_env_file()
    get_config.cache_clear()
    return get_config()




config = get_config()

ENV = config.ENV
DEBUG = config.is_development
