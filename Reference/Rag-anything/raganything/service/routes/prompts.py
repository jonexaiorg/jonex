"""
Prompt Config CRUD API — tenant-scoped prompt customization.

Routes:
  GET    /api/v1/presets/{name}/prompts       — list prompt definitions for a preset
  GET    /api/v1/prompts                      — list prompt configs (by tenant)
  GET    /api/v1/prompts/{prompt_id}          — get a single prompt config
  POST   /api/v1/prompts                      — create a prompt config
  PUT    /api/v1/prompts/{prompt_id}          — update a prompt config
  DELETE /api/v1/prompts/{prompt_id}          — delete a prompt config

Design decisions:
  - Prompt *definitions* come from built-in code (prompt_definitions.py).
  - Prompt *configs* (tenant overrides) are stored as YAML files per tenant.
  - A prompt_id is the stored config's id; when a task references it,
    the processor loads the override content and substitutes it for the
    default PROMPTS entry.
  - All CRUD operations are tenant-scoped via X-Tenant-ID header.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from raganything.service.context import get_request_id, get_tenant_id
from raganything.service.models import ErrorResponse
from raganything.service.prompt_definitions import (
    get_preset_prompts,
    list_all_preset_names,
)
from raganything.service.prompt_config_manager import (
    PromptConfigManager,
    PromptConfigCreate,
    PromptConfigUpdate,
)

router = APIRouter(tags=["prompts"])


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_pcm(request: Request) -> PromptConfigManager:
    return request.app.state.prompt_config_manager


def _tenant(request: Request) -> str:
    tid = get_tenant_id()
    if not tid:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                code=40001,
                request_id=get_request_id(),
                message="X-Tenant-ID header is required",
            ).model_dump(mode="json"),
        )
    return tid


def _err(code: int, message: str) -> HTTPException:
    return HTTPException(
        status_code=code // 100,
        detail=ErrorResponse(
            code=code, request_id=get_request_id(), message=message
        ).model_dump(mode="json"),
    )


def _get_user(request: Request) -> str:
    return request.headers.get("X-User-ID", "anonymous")


# ── GET /api/v1/presets/{name}/prompts ──────────────────────────────────────
#   查看某个 preset 对应的所有提示词定义（内置定义，非租户配置）


@router.get("/presets/{name}/prompts")
async def list_preset_prompts(name: str, request: Request):
    """List all prompt definitions for a given preset.

    Returns the built-in prompt definitions (code, display_name, description,
    category) that are used when processing files under this preset.

    This is a **read-only catalog** — it shows what prompts exist and can be
    overridden.  Actual tenant overrides are managed via the /prompts CRUD
    endpoints.

    Path parameters:
        name: Preset name, e.g. "image", "table", "audio", "video",
              "document", "query", "document_parse", "audio_transcribe",
              "video_full_pipeline", "text_parse"
    """
    prompts = get_preset_prompts(name)
    if not prompts:
        # Return 404 with helpful message listing known presets
        known = list_all_preset_names()
        raise _err(
            40403,
            f"Unknown preset '{name}'. Known presets: {', '.join(known)}",
        )

    # Build response: each prompt def + whether current tenant has overridden it
    tenant_id = get_tenant_id() or ""
    overridden_codes: set[str] = set()
    if tenant_id:
        pcm = _get_pcm(request)
        overrides = pcm.load_overrides(tenant_id, name)
        overridden_codes = set(overrides.keys())

    items = []
    for p in prompts:
        items.append({
            "code": p.code,
            "display_name": p.display_name,
            "description": p.description,
            "category": p.category,
            "has_override": p.code in overridden_codes,
        })

    return {
        "code": 0,
        "request_id": get_request_id(),
        "data": {
            "preset_name": name,
            "total": len(items),
            "prompts": items,
        },
    }


# ── GET /api/v1/prompts ─────────────────────────────────────────────────────
#   列出当前租户的所有提示词配置


@router.get("/prompts")
async def list_prompt_configs(
    request: Request,
    preset_name: str = Query(default="", description="Filter by preset name"),
    prompt_code: str = Query(default="", description="Filter by prompt code"),
    category: str = Query(default="", description="Filter by category"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
):
    """List prompt configs for the current tenant.

    Results are scoped to the tenant identified by X-Tenant-ID header.
    Supports optional filtering by preset_name, prompt_code, and category.
    """
    tenant_id = _tenant(request)
    pcm = _get_pcm(request)

    result = pcm.list_by_tenant(
        tenant_id=tenant_id,
        preset_name=preset_name or None,
        prompt_code=prompt_code or None,
        category=category or None,
        page=page,
        page_size=page_size,
    )

    return {
        "code": 0,
        "request_id": get_request_id(),
        "data": {
            "total": result.total,
            "page": page,
            "page_size": page_size,
            "items": [item.model_dump(mode="json") for item in result.items],
        },
    }


# ── GET /api/v1/prompts/{prompt_id} ─────────────────────────────────────────


@router.get("/prompts/{prompt_id}")
async def get_prompt_config(prompt_id: str, request: Request):
    """Get a single prompt config by ID.

    Returns 404 if the prompt_id doesn't exist or belongs to another tenant.
    """
    tenant_id = _tenant(request)
    pcm = _get_pcm(request)

    item = pcm.get(tenant_id, prompt_id)
    if item is None:
        raise _err(40404, f"Prompt config not found: {prompt_id}")

    return {
        "code": 0,
        "request_id": get_request_id(),
        "data": item.model_dump(mode="json"),
    }


# ── POST /api/v1/prompts ────────────────────────────────────────────────────


@router.post("/prompts", status_code=201)
async def create_prompt_config(body: PromptConfigCreate, request: Request):
    """Create a new prompt config for the current tenant.

    Body fields:
        prompt_code:  (required) PROMPTS key to override, e.g. "vision_prompt"
        preset_name:  which preset this applies to
        display_name: human-readable name
        description:  what this prompt does
        category:     system | analysis | chunk | summary | query
        language:     "en" | "zh"
        content:      (required) the actual prompt template text

    Returns the created config with auto-generated id and audit fields.
    """
    tenant_id = _tenant(request)
    created_by = _get_user(request)
    pcm = _get_pcm(request)

    try:
        item = pcm.create(tenant_id, body, created_by=created_by)
    except FileExistsError as e:
        raise _err(40901, str(e))

    return {
        "code": 0,
        "request_id": get_request_id(),
        "data": item.model_dump(mode="json"),
    }


# ── PUT /api/v1/prompts/{prompt_id} ─────────────────────────────────────────


@router.put("/prompts/{prompt_id}", status_code=200)
async def update_prompt_config(
    prompt_id: str, body: PromptConfigUpdate, request: Request
):
    """Update an existing prompt config. Only send fields you want to change.

    All fields are optional — omitted fields keep their current values.

    Returns 404 if the prompt_id doesn't exist or belongs to another tenant.
    """
    tenant_id = _tenant(request)
    updated_by = _get_user(request)
    pcm = _get_pcm(request)

    item = pcm.update(tenant_id, prompt_id, body, updated_by=updated_by)
    if item is None:
        # Check if it exists at all (possibly wrong tenant)
        raise _err(40404, f"Prompt config not found: {prompt_id}")

    return {
        "code": 0,
        "request_id": get_request_id(),
        "data": item.model_dump(mode="json"),
    }


# ── DELETE /api/v1/prompts/{prompt_id} ──────────────────────────────────────


@router.delete("/prompts/{prompt_id}", status_code=200)
async def delete_prompt_config(prompt_id: str, request: Request):
    """Delete a prompt config.

    Returns 404 if the prompt_id doesn't exist or belongs to another tenant.
    """
    tenant_id = _tenant(request)
    pcm = _get_pcm(request)

    deleted = pcm.delete(tenant_id, prompt_id)
    if not deleted:
        raise _err(40404, f"Prompt config not found: {prompt_id}")

    return {
        "code": 0,
        "request_id": get_request_id(),
        "data": {"deleted": prompt_id},
    }
