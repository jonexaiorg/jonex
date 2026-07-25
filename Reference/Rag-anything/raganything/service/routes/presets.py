"""
GET    /api/v1/presets                 — List presets (global + tenant/kb scoped)
GET    /api/v1/presets/{name}          — Get preset detail (tenant/kb overlay)
PUT    /api/v1/presets/{name}          — Create/update preset at tenant/kb scope
DELETE /api/v1/presets/{name}          — Delete preset from tenant/kb scope

Preset scoping (resolved from X-Tenant-ID header + ?kb_id= query param):

  No tenant header  → global   config/presets/{name}.yaml
  Tenant only       → tenant   config/{tenant_id}/presets/{name}.yaml
  Tenant + kb_id    → kb       config/{tenant_id}/{kb_id}/presets/{name}.yaml

Listing merges across scopes: global base → tenant overlay → kb overlay.
CRUD operates on the most specific scope.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException, Query, Request

from raganything.service.context import get_request_id, get_tenant_id
from raganything.service.models import PresetConfig
from raganything.service.prompt_definitions import get_preset_prompts

router = APIRouter(tags=["presets"])

# ── Helpers ────────────────────────────────────────────────────────────


def _yaml_safe_str(value: str) -> str:
    """Return a YAML-safe inline representation of *value*.

    Uses yaml.safe_dump for proper quoting, then strips the trailing
    document-end marker (``...``) that PyYAML appends to scalar dumps.
    """
    dumped = yaml.safe_dump(value, allow_unicode=True, default_flow_style=True)
    # Remove trailing document end marker: "...\n" or "..."
    if dumped.endswith("...\n"):
        dumped = dumped[:-4]
    elif dumped.endswith("..."):
        dumped = dumped[:-3]
    return dumped.strip()


def _prompts_summary(preset_name: str) -> list[dict]:
    """Build a prompts summary list for a given preset name."""
    defs = get_preset_prompts(preset_name)
    return [
        {
            "code": p.code,
            "display_name": p.display_name,
            "description": p.description,
            "category": p.category,
        }
        for p in defs
    ]


def _err(code: int, message: str) -> HTTPException:
    from raganything.service.models import ErrorResponse

    return HTTPException(
        status_code=code // 100,
        detail=ErrorResponse(
            code=code, request_id=get_request_id(), message=message
        ).model_dump(mode="json"),
    )


# ── Scope resolution ───────────────────────────────────────────────────


def _scope_dir(request: Request, kb_id: str = "") -> Path:
    """Return the preset directory for the current tenant/kb scope.

    Resolves from X-Tenant-ID header (set by middleware into ContextVar)
    and optional kb_id query parameter.

    Returns:
        Path to the scoped presets directory.
    """
    base = request.app.state.config_resolver._presets_dir
    tenant_id = get_tenant_id()

    if not tenant_id:
        return base  # global: config/presets/

    if kb_id:
        return base.parent / tenant_id / kb_id / "presets"

    return base.parent / tenant_id / "presets"


def _list_scoped_presets(request: Request, kb_id: str = "") -> dict[str, dict]:
    """Collect presets across scopes with proper overlay.

    Merging order: global → tenant → kb (later overrides earlier).
    Returns {name: {description, version, updated_at, scope}} dict.
    """
    base = request.app.state.config_resolver._presets_dir
    tenant_id = get_tenant_id()
    result: dict[str, dict] = {}

    # Layer 1: global presets
    _collect_yaml_presets(base, result, scope="global")

    if not tenant_id:
        return result

    # Layer 2: tenant presets
    tenant_dir = base.parent / tenant_id / "presets"
    _collect_yaml_presets(tenant_dir, result, scope="tenant")

    if not kb_id:
        return result

    # Layer 3: kb presets
    kb_dir = base.parent / tenant_id / kb_id / "presets"
    _collect_yaml_presets(kb_dir, result, scope="kb")

    return result


def _collect_yaml_presets(
    directory: Path, target: dict[str, dict], scope: str
) -> None:
    """Read *.yaml files from *directory* into *target* dict (overlay on conflict)."""
    if not directory.is_dir():
        return
    for f in sorted(directory.glob("*.yaml")):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
            name = f.stem
            target[name] = {
                "name": name,
                "description": data.get("description", ""),
                "version": data.get("version", "1.0"),
                "updated_at": data.get("updated_at"),
                "scope": scope,
            }
        except Exception:
            pass


# ── GET /api/v1/presets ────────────────────────────────────────────────


@router.get("/presets")
async def list_presets(
    request: Request,
    kb_id: str = Query(default="", description="知识库 ID（可选，需配合 X-Tenant-ID）"),
):
    """List presets merged across global → tenant → kb scopes."""
    merged = _list_scoped_presets(request, kb_id=kb_id)
    items = []
    for name, meta in sorted(merged.items()):
        item = dict(meta)
        item["prompts"] = _prompts_summary(name)
        items.append(item)
    return {"code": 0, "request_id": get_request_id(), "data": items}


# ── GET /api/v1/presets/{name} ─────────────────────────────────────────


@router.get("/presets/{name}")
async def get_preset(
    name: str,
    request: Request,
    kb_id: str = Query(default="", description="知识库 ID（可选，需配合 X-Tenant-ID）"),
):
    """Get a preset with tenant/kb overlay applied (deep merge).

    Uses the same loading strategy as ConfigResolver._load_preset:
    global base → tenant overlay → kb overlay.
    """
    base = request.app.state.config_resolver._presets_dir
    tenant_id = get_tenant_id()

    result: dict = {}
    found = False

    # Layer 1: global base
    global_path = base / f"{name}.yaml"
    if global_path.exists():
        with open(global_path, "r", encoding="utf-8") as f:
            result = yaml.safe_load(f) or {}
        found = True

    # Layer 2: tenant overlay (deep merge)
    if tenant_id:
        tenant_path = base.parent / tenant_id / "presets" / f"{name}.yaml"
        if tenant_path.exists():
            with open(tenant_path, "r", encoding="utf-8") as f:
                overlay = yaml.safe_load(f) or {}
            result = _deep_merge_dicts(result, overlay)
            found = True

    # Layer 3: kb overlay (deep merge)
    if tenant_id and kb_id:
        kb_path = base.parent / tenant_id / kb_id / "presets" / f"{name}.yaml"
        if kb_path.exists():
            with open(kb_path, "r", encoding="utf-8") as f:
                overlay = yaml.safe_load(f) or {}
            result = _deep_merge_dicts(result, overlay)
            found = True

    if not found:
        raise _err(40402, f"Preset not found: {name}")

    # Layer 2: tenant overlay
    if tenant_id:
        tenant_path = base.parent / tenant_id / "presets" / f"{name}.yaml"
        if tenant_path.exists():
            with open(tenant_path, "r", encoding="utf-8") as f:
                overlay = yaml.safe_load(f) or {}
            result = _deep_merge_dicts(result, overlay)

    # Layer 3: kb overlay
    if tenant_id and kb_id:
        kb_path = base.parent / tenant_id / kb_id / "presets" / f"{name}.yaml"
        if kb_path.exists():
            with open(kb_path, "r", encoding="utf-8") as f:
                overlay = yaml.safe_load(f) or {}
            result = _deep_merge_dicts(result, overlay)

    result["prompts"] = _prompts_summary(name)
    return {"code": 0, "request_id": get_request_id(), "data": result}


# ── PUT /api/v1/presets/{name} ─────────────────────────────────────────


@router.put("/presets/{name}", status_code=200)
async def upsert_preset(
    name: str,
    body: PresetConfig,
    request: Request,
    kb_id: str = Query(default="", description="知识库 ID（可选，需配合 X-Tenant-ID）"),
):
    """Create or update a preset at the current tenant/kb scope.

    - No X-Tenant-ID → writes to global config/presets/
    - X-Tenant-ID present → writes to config/{tenant}/presets/
    - X-Tenant-ID + kb_id → writes to config/{tenant}/{kb_id}/presets/
    """
    presets_dir = _scope_dir(request, kb_id=kb_id)
    presets_dir.mkdir(parents=True, exist_ok=True)
    path = presets_dir / f"{name}.yaml"

    # Determine effective scope
    tenant_id = get_tenant_id()
    if tenant_id and kb_id:
        scope = "kb"
    elif tenant_id:
        scope = "tenant"
    else:
        scope = "global"

    updated_by = request.headers.get("X-User-ID", "anonymous")

    # Write YAML manually to preserve key order: metadata → config last
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(f"description: {_yaml_safe_str(body.description)}\n")
        f.write(f"version: {_yaml_safe_str(body.version)}\n")
        f.write(f"updated_at: {_yaml_safe_str(datetime.now(timezone.utc).isoformat())}\n")
        f.write(f"updated_by: {_yaml_safe_str(updated_by)}\n")
        f.write(f"scope: {scope}\n")
        f.write(f"tenant_id: {_yaml_safe_str(tenant_id)}\n")
        if kb_id:
            f.write(f"kb_id: {_yaml_safe_str(kb_id)}\n")
        f.write("config:\n")
        config_yaml = yaml.safe_dump(
            body.config, allow_unicode=True, default_flow_style=False, sort_keys=False,
        )
        for line in config_yaml.split("\n"):
            f.write(f"  {line}\n" if line.strip() else "\n")
    os.replace(tmp, path)

    doc: dict = {
        "description": body.description,
        "version": body.version,
        "updated_by": updated_by,
        "scope": scope,
        "tenant_id": tenant_id,
        "config": body.config,
    }
    if kb_id:
        doc["kb_id"] = kb_id

    return {
        "code": 0,
        "request_id": get_request_id(),
        "data": {"name": name, **doc, "prompts": _prompts_summary(name)},
    }


# ── DELETE /api/v1/presets/{name} ──────────────────────────────────────


@router.delete("/presets/{name}", status_code=200)
async def delete_preset(
    name: str,
    request: Request,
    kb_id: str = Query(default="", description="知识库 ID（可选，需配合 X-Tenant-ID）"),
):
    """Delete a preset from the current tenant/kb scope.

    Does NOT fall back to broader scopes — only deletes from the exact
    scope directory.
    """
    presets_dir = _scope_dir(request, kb_id=kb_id)
    path = presets_dir / f"{name}.yaml"
    if not path.exists():
        raise _err(40402, f"Preset not found: {name} (scope={'kb' if kb_id else 'tenant' if get_tenant_id() else 'global'})")
    os.remove(path)
    return {"code": 0, "request_id": get_request_id(), "data": {"deleted": name}}


# ── Deep merge utility (mirrors ConfigResolver._deep_merge) ────────────


def _deep_merge_dicts(base: dict, overlay: dict) -> dict:
    """Recursively merge *overlay* into *base* and return a new dict."""
    result = dict(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
