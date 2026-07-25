"""RAGAnything Service API routes."""

from raganything.service.routes.health import router as health_router
from raganything.service.routes.presets import router as presets_router
from raganything.service.routes.prompts import router as prompts_router
from raganything.service.routes.tasks import router as tasks_router

__all__ = ["health_router", "presets_router", "prompts_router", "tasks_router"]
