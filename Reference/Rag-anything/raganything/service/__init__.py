"""RAGAnything Service — FastAPI + TaskManager + config resolution.

Provides:
  - TaskManager: async task queue with cooperative cancellation
  - ConfigResolver: inline/yaml/preset → RAGAnythingConfig
  - ModelFactory: builds LLM/embedding/VLM/ASR functions from profile
  - FastAPI app factory with middleware, health checks, and routes
"""

from raganything.service.app import create_app, main
from raganything.service.config_resolver import ConfigResolver, ConfigResolveError
from raganything.service.context import get_request_id, get_tenant_id, request_id_var, tenant_id_var
from raganything.service.model_factory import ModelFactory
from raganything.service.models import (
    CancelTaskResponse,
    CreateTaskRequest,
    CreateTaskResponse,
    ErrorCode,
    ErrorResponse,
    FileType,
    HealthResponse,
    PaginatedTasks,
    PresetConfig,
    PresetListItem,
    PresetMeta,
    ProgressDetail,
    ReadyResponse,
    ResultSummary,
    TaskInfo,
    TaskListItem,
    TaskListQuery,
    TaskMode,
    TaskStatus,
    TERMINAL_STATES,
    STATE_TRANSITIONS,
    infer_file_type,
    validate_transition,
)
from raganything.service.task_manager import (
    ProgressTrackingCallback,
    SlotFullError,
    TaskCancelledError,
    TaskHandle,
    TaskManager,
    TenantRAGCache,
)

__all__ = [
    # App
    "create_app",
    "main",
    # Config
    "ConfigResolver",
    "ConfigResolveError",
    # Context
    "get_request_id",
    "get_tenant_id",
    "request_id_var",
    "tenant_id_var",
    # Models
    "CancelTaskResponse",
    "CreateTaskRequest",
    "CreateTaskResponse",
    "ErrorCode",
    "ErrorResponse",
    "FileType",
    "HealthResponse",
    "PaginatedTasks",
    "PresetConfig",
    "PresetListItem",
    "PresetMeta",
    "ProgressDetail",
    "ReadyResponse",
    "ResultSummary",
    "TaskInfo",
    "TaskListItem",
    "TaskListQuery",
    "TaskMode",
    "TaskStatus",
    "TERMINAL_STATES",
    "STATE_TRANSITIONS",
    "infer_file_type",
    "validate_transition",
    # Task Manager
    "ModelFactory",
    "ProgressTrackingCallback",
    "SlotFullError",
    "TaskCancelledError",
    "TaskHandle",
    "TaskManager",
    "TenantRAGCache",
]
