#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - unified exception system

Defines the hierarchy and error code specification for all platform business exceptions
Error code specification:
  1xxx - Common error
  2xxx - Capability-related errors
  3xxx - Authentication/authorization errors
  4xxx - Data-related errors
  5xxx - Service dependency errors
"""

from typing import Optional, Dict, Any


class JonexException(Exception):
    """
    Jonex platform base exception class

    All custom exceptions must inherit from this class for unified handling
    """
    code: int = 1000
    status_code: int = 500
    default_message: str = "Internal server error"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Args:
            message: User-friendly error message
            details: Additional error details (no sensitive info)
            cause: Original exception (for chain tracing)
        """
        self.message = message or self.default_message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict (for response serialization)"""
        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# ==================== 1xxx Common error ====================
class InternalError(JonexException):
    """Internal error"""
    code = 1000
    status_code = 500
    default_message = "Internal server error"


class InvalidParameterError(JonexException):
    """Invalid parameter"""
    code = 1001
    status_code = 400
    default_message = "Invalid request parameter"


class ResourceNotFoundError(JonexException):
    """Resource not found"""
    code = 1002
    status_code = 404
    default_message = "Requested resource not found"


class ResourceConflictError(JonexException):
    """Resource conflict"""
    code = 1003
    status_code = 409
    default_message = "Resource state conflict"


class OperationNotSupportedError(JonexException):
    """Operation not supported"""
    code = 1004
    status_code = 405
    default_message = "Operation not supported"


# ==================== 2xxx Capability-related errors ====================
class CapabilityError(JonexException):
    """Capability error base class"""
    code = 2000
    status_code = 500
    default_message = "Capability invocation failed"


class CapabilityNotFoundError(CapabilityError):
    """Capability not found"""
    code = 2001
    status_code = 404
    default_message = "Requested capability not found"


class CapabilityInvokeError(CapabilityError):
    """Capability invocation failed"""
    code = 2002
    status_code = 500
    default_message = "Capability execution failed"


class CapabilityTimeoutError(CapabilityError):
    """Capability invocation timed out"""
    code = 2003
    status_code = 504
    default_message = "Capability invocation timed out"


class CapabilityValidationError(CapabilityError):
    """Capability input validation failed"""
    code = 2004
    status_code = 400
    default_message = "Invalid capability input parameter"


class CapabilityIdFormatError(CapabilityError):
    """Invalid capability ID format"""
    code = 2005
    status_code = 400
    default_message = "Invalid capability ID format"


# ==================== 3xxx Authentication/authorization errors ====================
class AuthError(JonexException):
    """Authentication error base class"""
    code = 3000
    status_code = 401
    default_message = "Authentication failed"


class MissingApiKeyError(AuthError):
    """Missing API Key"""
    code = 3001
    status_code = 401
    default_message = "Missing X-API-Key header"


class InvalidApiKeyError(AuthError):
    """Invalid API Key"""
    code = 3002
    status_code = 401
    default_message = "Invalid API Key"


class TokenExpiredError(AuthError):
    """Token Expired"""
    code = 3003
    status_code = 401
    default_message = "Authentication token expired"


class InternalAuthError(AuthError):
    """Internal service authentication failed"""
    code = 3004
    status_code = 403
    default_message = "Internal service authentication failed"


class TenantIsolationError(AuthError):
    """Tenant isolation violation"""
    code = 3005
    status_code = 403
    default_message = "No access to tenant resources"


class PermissionDeniedError(AuthError):
    """Permission denied"""
    code = 3006
    status_code = 403
    default_message = "Permission denied"


class RateLimitExceededError(AuthError):
    """Rate limit exceeded"""
    code = 3007
    status_code = 429
    default_message = "Too many requests, please retry later"


# ==================== 4xxx Data-related errors ====================
class DataError(JonexException):
    """Data error base class"""
    code = 4000
    status_code = 500
    default_message = "Data processing failed"


class DatabaseError(DataError):
    """Database error"""
    code = 4001
    status_code = 500
    default_message = "Database operation failed"


class CacheError(DataError):
    """Cache error"""
    code = 4002
    status_code = 500
    default_message = "Cache operation failed"


class DataIntegrityError(DataError):
    """Data integrity error"""
    code = 4003
    status_code = 400
    default_message = "Data integrity constraint violation"


# ==================== 5xxx Service dependency errors ====================
class ServiceError(JonexException):
    """Service error base class"""
    code = 5000
    status_code = 503
    default_message = "Service unavailable"


class ServiceUnavailableError(ServiceError):
    """Service unavailable"""
    code = 5001
    status_code = 503
    default_message = "Dependency service unavailable"


class ServiceDiscoveryError(ServiceError):
    """Service discovery error"""
    code = 5002
    status_code = 503
    default_message = "Service discovery failed"


class UpstreamServiceError(ServiceError):
    """Upstream service error"""
    code = 5003
    status_code = 502
    default_message = "Upstream service returned error"


class ServiceTimeoutError(ServiceError):
    """Service invocation timed out"""
    code = 5004
    status_code = 504
    default_message = "Service invocation timed out"


# ==================== Exception mapping utility ====================
EXCEPTION_REGISTRY: Dict[int, type] = {
    # Common error
    1000: InternalError,
    1001: InvalidParameterError,
    1002: ResourceNotFoundError,
    1003: ResourceConflictError,
    1004: OperationNotSupportedError,
    # Capability-related
    2000: CapabilityError,
    2001: CapabilityNotFoundError,
    2002: CapabilityInvokeError,
    2003: CapabilityTimeoutError,
    2004: CapabilityValidationError,
    2005: CapabilityIdFormatError,
    # Authentication/authorization
    3000: AuthError,
    3001: MissingApiKeyError,
    3002: InvalidApiKeyError,
    3003: TokenExpiredError,
    3004: InternalAuthError,
    3005: TenantIsolationError,
    3006: PermissionDeniedError,
    3007: RateLimitExceededError,
    # Data-related
    4000: DataError,
    4001: DatabaseError,
    4002: CacheError,
    4003: DataIntegrityError,
    # Service dependency
    5000: ServiceError,
    5001: ServiceUnavailableError,
    5002: ServiceDiscoveryError,
    5003: UpstreamServiceError,
    5004: ServiceTimeoutError,
}


def get_exception_class(code: int) -> type:
    """
    Get the corresponding exception class by error code

    Args:
        code: Error code

    Returns:
        Exception class
    """
    return EXCEPTION_REGISTRY.get(code, JonexException)
