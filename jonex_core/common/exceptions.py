#!/usr/bin/python3



from typing import Optional, Dict, Any


class JonexException(Exception):

    code: int = 1000
    status_code: int = 500
    default_message: str = "Internal server error"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):

        self.message = message or self.default_message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:

        result = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result



class InternalError(JonexException):

    code = 1000
    status_code = 500
    default_message = "Internal server error"


class InvalidParameterError(JonexException):

    code = 1001
    status_code = 400
    default_message = "Invalid request parameters"


class ResourceNotFoundError(JonexException):

    code = 1002
    status_code = 404
    default_message = "Requested resource not found"


class ResourceConflictError(JonexException):

    code = 1003
    status_code = 409
    default_message = "Resource state conflict"


class OperationNotSupportedError(JonexException):

    code = 1004
    status_code = 405
    default_message = "Operation not supported"



class CapabilityError(JonexException):

    code = 2000
    status_code = 500
    default_message = "Capability call failed"


class CapabilityNotFoundError(CapabilityError):

    code = 2001
    status_code = 404
    default_message = "Requested capability not found"


class CapabilityInvokeError(CapabilityError):

    code = 2002
    status_code = 500
    default_message = "Capability execution failed"


class CapabilityTimeoutError(CapabilityError):

    code = 2003
    status_code = 504
    default_message = "Capability call timed out"


class CapabilityValidationError(CapabilityError):

    code = 2004
    status_code = 400
    default_message = "Invalid capability input parameters"


class CapabilityIdFormatError(CapabilityError):

    code = 2005
    status_code = 400
    default_message = "Invalid capability ID format"



class AuthError(JonexException):

    code = 3000
    status_code = 401
    default_message = "Authentication failed"


class MissingApiKeyError(AuthError):

    code = 3001
    status_code = 401
    default_message = "Missing X-API-Key header"


class InvalidApiKeyError(AuthError):

    code = 3002
    status_code = 401
    default_message = "Invalid API Key"


class TokenExpiredError(AuthError):

    code = 3003
    status_code = 401
    default_message = "Authentication Token has expired"


class InternalAuthError(AuthError):

    code = 3004
    status_code = 403
    default_message = "Internal service authentication failed"


class TenantIsolationError(AuthError):

    code = 3005
    status_code = 403
    default_message = "Access to this tenant resource is denied"


class PermissionDeniedError(AuthError):

    code = 3006
    status_code = 403
    default_message = "Insufficient permissions"


class RateLimitExceededError(AuthError):

    code = 3007
    status_code = 429
    default_message = "Too many requests. Try again later"



class DataError(JonexException):

    code = 4000
    status_code = 500
    default_message = "Data processing failed"


class DatabaseError(DataError):

    code = 4001
    status_code = 500
    default_message = "Database operation failed"


class CacheError(DataError):

    code = 4002
    status_code = 500
    default_message = "Cache operation failed"


class DataIntegrityError(DataError):

    code = 4003
    status_code = 400
    default_message = "Data integrity constraint violation"



class ServiceError(JonexException):

    code = 5000
    status_code = 503
    default_message = "Service unavailable"


class ServiceUnavailableError(ServiceError):

    code = 5001
    status_code = 503
    default_message = "Dependency service unavailable"


class ServiceDiscoveryError(ServiceError):

    code = 5002
    status_code = 503
    default_message = "Service discovery failed"


class UpstreamServiceError(ServiceError):

    code = 5003
    status_code = 502
    default_message = "Upstream service returned an error"


class ServiceTimeoutError(ServiceError):

    code = 5004
    status_code = 504
    default_message = "Service call timed out"



EXCEPTION_REGISTRY: Dict[int, type] = {

    1000: InternalError,
    1001: InvalidParameterError,
    1002: ResourceNotFoundError,
    1003: ResourceConflictError,
    1004: OperationNotSupportedError,

    2000: CapabilityError,
    2001: CapabilityNotFoundError,
    2002: CapabilityInvokeError,
    2003: CapabilityTimeoutError,
    2004: CapabilityValidationError,
    2005: CapabilityIdFormatError,

    3000: AuthError,
    3001: MissingApiKeyError,
    3002: InvalidApiKeyError,
    3003: TokenExpiredError,
    3004: InternalAuthError,
    3005: TenantIsolationError,
    3006: PermissionDeniedError,
    3007: RateLimitExceededError,

    4000: DataError,
    4001: DatabaseError,
    4002: CacheError,
    4003: DataIntegrityError,

    5000: ServiceError,
    5001: ServiceUnavailableError,
    5002: ServiceDiscoveryError,
    5003: UpstreamServiceError,
    5004: ServiceTimeoutError,
}


def get_exception_class(code: int) -> type:

    return EXCEPTION_REGISTRY.get(code, JonexException)
