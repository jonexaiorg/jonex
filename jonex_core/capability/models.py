from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum
from uuid import uuid4


class CapabilityType(str, Enum):

    ATOMIC = "atomic"
    DOMAIN = "domain"
    BUSINESS = "business"


@dataclass
class CapabilityMetadata:

    capability_id: str
    capability_name: str
    capability_type: CapabilityType
    version: str = "v1"
    description: str = ""
    author: str = "jonex"
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    pricing_plan: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @property
    def full_id(self) -> str:

        return f"{self.capability_type.value}.{self.capability_id}.{self.version}"


@dataclass
class CapabilityRequest:

    tenant_id: str
    capability_id: str
    payload: Dict[str, Any]
    request_id: str = field(default_factory=lambda: str(uuid4()))
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:

        return self.payload.get(key, default)


@dataclass
class CapabilityResponse:

    request_id: str
    success: bool
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def ok(cls, request_id: str, data: Dict[str, Any] = None, message: str = "success") -> "CapabilityResponse":

        return cls(request_id=request_id, success=True, code=0, message=message, data=data)

    @classmethod
    def error(cls, request_id: str, code: int, message: str) -> "CapabilityResponse":

        return cls(request_id=request_id, success=False, code=code, message=message)


@dataclass
class CapabilityHealth:

    capability_id: str
    is_healthy: bool
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
