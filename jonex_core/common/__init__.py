#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - Common utilities module

Provides database connection, cache, logging, configuration and other basic functionality
"""

from .config import Settings, get_config, reload_config
from .database import (
    Base,
    get_db,
    get_db_session,
    init_database,
    close_database,
    check_db_health,
    TenantContext,
    AsyncSessionLocal,
)
from .cache import (
    CacheUtil,
    RedisUtil,
    TenantCache,
    get_redis_client,
    RedisPoolManager,
    check_redis_health,
)
from .vector import (
    MilvusClient,
    get_milvus_client,
    check_milvus_health,
    milvus_context,
    MILVUS_AVAILABLE,
)
from .logger import (
    get_logger,
    setup_logging,
    set_request_id,
    LogContext,
    log_execution_time,
)
from .exceptions import (
    JonexException,
    InternalError,
    InvalidParameterError,
    ResourceNotFoundError,
    ResourceConflictError,
    OperationNotSupportedError,
    CapabilityError,
    CapabilityNotFoundError,
    CapabilityInvokeError,
    CapabilityTimeoutError,
    CapabilityValidationError,
    CapabilityIdFormatError,
    AuthError,
    MissingApiKeyError,
    InvalidApiKeyError,
    TokenExpiredError,
    InternalAuthError,
    TenantIsolationError,
    PermissionDeniedError,
    RateLimitExceededError,
    DataError,
    DatabaseError,
    CacheError,
    DataIntegrityError,
    ServiceError,
    ServiceUnavailableError,
    ServiceDiscoveryError,
    UpstreamServiceError,
    ServiceTimeoutError,
    get_exception_class,
)
from .response import (
    StandardResponse,
    success_response,
    error_response,
)
from .exception_handler import register_exception_handlers
from .neo4j_client import (
    get_neo4j_driver,
    close_neo4j_driver,
    ensure_ontology_schema,
)

__all__ = [
    # Configuration
    "Settings",
    "get_config",
    "reload_config",
    # Database
    "Base",
    "get_db",
    "get_db_session",
    "init_database",
    "close_database",
    "check_db_health",
    "TenantContext",
    "AsyncSessionLocal",
    # Cache
    "CacheUtil",
    "RedisUtil",
    "TenantCache",
    "get_redis_client",
    "RedisPoolManager",
    "check_redis_health",
    # Vector database
    "MilvusClient",
    "get_milvus_client",
    "check_milvus_health",
    "milvus_context",
    "MILVUS_AVAILABLE",
    # Logging
    "get_logger",
    "setup_logging",
    "set_request_id",
    "LogContext",
    "log_execution_time",
    # Exception classes
    "JonexException",
    "InternalError",
    "InvalidParameterError",
    "ResourceNotFoundError",
    "ResourceConflictError",
    "OperationNotSupportedError",
    "CapabilityError",
    "CapabilityNotFoundError",
    "CapabilityInvokeError",
    "CapabilityTimeoutError",
    "CapabilityValidationError",
    "CapabilityIdFormatError",
    "AuthError",
    "MissingApiKeyError",
    "InvalidApiKeyError",
    "TokenExpiredError",
    "InternalAuthError",
    "TenantIsolationError",
    "PermissionDeniedError",
    "RateLimitExceededError",
    "DataError",
    "DatabaseError",
    "CacheError",
    "DataIntegrityError",
    "ServiceError",
    "ServiceUnavailableError",
    "ServiceDiscoveryError",
    "UpstreamServiceError",
    "ServiceTimeoutError",
    "get_exception_class",
    # Response format
    "StandardResponse",
    "success_response",
    "error_response",
    # Exception handlers
    "register_exception_handlers",
]
