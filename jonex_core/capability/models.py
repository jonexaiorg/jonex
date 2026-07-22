from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from enum import Enum
from uuid import uuid4


class CapabilityType(str, Enum):
    """Capability type"""
    ATOMIC = "atomic"        # Atomic capability
    DOMAIN = "domain"        # Domain capability
    BUSINESS = "business"    # Business capability


@dataclass
class CapabilityMetadata:
    """Capability metadata"""
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
        """Full capability ID: type.id.version"""
        return f"{self.capability_type.value}.{self.capability_id}.{self.version}"


@dataclass
class CapabilityRequest:
    """Capability invocation request"""
    tenant_id: str
    capability_id: str
    payload: Dict[str, Any]
    request_id: str = field(default_factory=lambda: str(uuid4()))
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

    def get(self, key: str, default: Any = None) -> Any:
        """Get field from payload"""
        return self.payload.get(key, default)


@dataclass
class CapabilityResponse:
    """Capability invocation response"""
    request_id: str
    success: bool
    code: int
    message: str
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def ok(cls, request_id: str, data: Dict[str, Any] = None, message: str = "success") -> "CapabilityResponse":
        """Success response"""
        return cls(request_id=request_id, success=True, code=0, message=message, data=data)

    @classmethod
    def error(cls, request_id: str, code: int, message: str) -> "CapabilityResponse":
        """Error response"""
        return cls(request_id=request_id, success=False, code=code, message=message)


@dataclass
class CapabilityHealth:
    """Capability health status"""
    capability_id: str
    is_healthy: bool
    message: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
