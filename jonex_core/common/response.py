#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Jonex platform - unified response format

Define standard response structure for all API interfaces, ensuring frontend-backend contract consistency
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Any, Dict
from datetime import datetime, timezone

from fastapi.responses import JSONResponse


@dataclass
class StandardResponse:
    """Standardized response format"""
    request_id: str
    success: bool
    code: int
    message: str
    data: Optional[Any] = None
    error_details: Optional[Dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict:
        """Convert to dict (None fields will be filtered out)"""
        result = asdict(self)
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def ok(
        cls,
        request_id: str = "",
        data: Any = None,
        message: str = "success",
    ) -> "StandardResponse":
        """Success response"""
        return cls(
            request_id=request_id,
            success=True,
            code=0,
            message=message,
            data=data,
        )

    @classmethod
    def error(
        cls,
        request_id: str,
        code: int,
        message: str,
        details: Optional[Dict] = None,
    ) -> "StandardResponse":
        """Error response"""
        return cls(
            request_id=request_id,
            success=False,
            code=code,
            message=message,
            error_details=details,
        )


def success_response(
    data: Any = None,
    message: str = "success",
    request_id: str = "",
    status_code: int = 200,
) -> JSONResponse:
    """
    Build success JSONResponse

    Args:
        data: Response data
        message: Success message
        request_id: Request ID
        status_code: HTTP status code

    Returns:
        JSONResponse
    """
    response = StandardResponse.ok(request_id=request_id, data=data, message=message)
    return JSONResponse(status_code=status_code, content=response.to_dict())


def error_response(
    code: int,
    message: str,
    request_id: str = "",
    status_code: int = 500,
    details: Optional[Dict] = None,
) -> JSONResponse:
    """
    Build error JSONResponse

    Args:
        code: Business error code
        message: Error information
        request_id: Request ID
        status_code: HTTP status code
        details: Error details

    Returns:
        JSONResponse
    """
    response = StandardResponse.error(
        request_id=request_id,
        code=code,
        message=message,
        details=details,
    )
    return JSONResponse(status_code=status_code, content=response.to_dict())
