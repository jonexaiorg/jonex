"""
Prompt Config Manager — YAML-file persistence for tenant-level prompt overrides.

Storage layout:
    {base_dir}/prompt_configs/{tenant_id}/{prompt_id}.yaml

Each YAML file contains:
    id: str
    tenant_id: str
    preset_name: str
    prompt_code: str          # PROMPTS registry key, e.g. "vision_prompt"
    display_name: str         # human-readable name
    description: str          # what this prompt does
    category: str             # system | analysis | chunk | summary | query
    language: str             # "en" | "zh" — which language this override targets
    content: str              # the actual prompt template text

    # Audit
    created_at: str
    updated_at: str
    created_by: str
    updated_by: str
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


# ── Models ──────────────────────────────────────────────────────────────────


class PromptConfigItem(BaseModel):
    """A stored prompt configuration record."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    tenant_id: str
    preset_name: str = ""
    prompt_code: str  # PROMPTS registry key
    display_name: str = ""
    description: str = ""
    category: str = "analysis"  # system | analysis | chunk | summary | query
    language: str = "en"
    content: str = ""  # the actual prompt template text

    # Audit
    created_at: str = ""
    updated_at: str = ""
    created_by: str = "anonymous"
    updated_by: str = "anonymous"


class PromptConfigCreate(BaseModel):
    """Request body for creating a prompt config."""
    prompt_code: str
    preset_name: str = ""
    display_name: str = ""
    description: str = ""
    category: str = "analysis"
    language: str = "en"
    content: str


class PromptConfigUpdate(BaseModel):
    """Request body for updating a prompt config (all fields optional)."""
    prompt_code: Optional[str] = None
    preset_name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    language: Optional[str] = None
    content: Optional[str] = None


class PromptConfigListResult(BaseModel):
    total: int
    items: List[PromptConfigItem]


# ── Manager ─────────────────────────────────────────────────────────────────


class PromptConfigManager:
    """CRUD operations for tenant-scoped prompt configurations.

    Each tenant's prompt overrides live in their own subdirectory.
    The YAML files are atomic-write safe (write to .tmp → os.replace).
    """

    def __init__(self, base_dir: str = "./prompt_configs"):
        self._base_dir = Path(base_dir)

    # ── Path helpers ───────────────────────────────────────────────────

    def _tenant_dir(self, tenant_id: str) -> Path:
        return self._base_dir / tenant_id

    def _prompt_path(self, tenant_id: str, prompt_id: str) -> Path:
        return self._tenant_dir(tenant_id) / f"{prompt_id}.yaml"

    # ── Internal I/O ───────────────────────────────────────────────────

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data

    @staticmethod
    def _save_yaml(path: Path, data: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)
        os.replace(tmp, path)

    def _item_from_yaml(self, path: Path) -> PromptConfigItem:
        data = self._load_yaml(path)
        return PromptConfigItem(**data)

    # ── CRUD ───────────────────────────────────────────────────────────

    def list_by_tenant(
        self,
        tenant_id: str,
        preset_name: Optional[str] = None,
        prompt_code: Optional[str] = None,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> PromptConfigListResult:
        """List prompt configs for a tenant, with optional filters."""
        tenant_dir = self._tenant_dir(tenant_id)
        items: List[PromptConfigItem] = []

        if tenant_dir.is_dir():
            for f in sorted(tenant_dir.glob("*.yaml")):
                try:
                    item = self._item_from_yaml(f)
                    if preset_name and item.preset_name != preset_name:
                        continue
                    if prompt_code and item.prompt_code != prompt_code:
                        continue
                    if category and item.category != category:
                        continue
                    items.append(item)
                except Exception:
                    pass

        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        return PromptConfigListResult(total=total, items=items[start:end])

    def get(self, tenant_id: str, prompt_id: str) -> Optional[PromptConfigItem]:
        """Get a single prompt config by id."""
        path = self._prompt_path(tenant_id, prompt_id)
        if not path.exists():
            return None
        try:
            return self._item_from_yaml(path)
        except Exception:
            return None

    def get_by_code(
        self, tenant_id: str, preset_name: str, prompt_code: str
    ) -> Optional[PromptConfigItem]:
        """Find a prompt config by tenant + preset + code (used during processing)."""
        tenant_dir = self._tenant_dir(tenant_id)
        if not tenant_dir.is_dir():
            return None
        for f in sorted(tenant_dir.glob("*.yaml")):
            try:
                item = self._item_from_yaml(f)
                if item.preset_name == preset_name and item.prompt_code == prompt_code:
                    return item
            except Exception:
                pass
        return None

    def create(
        self,
        tenant_id: str,
        body: PromptConfigCreate,
        created_by: str = "anonymous",
    ) -> PromptConfigItem:
        """Create a new prompt config."""
        now = datetime.now(timezone.utc).isoformat()
        item = PromptConfigItem(
            tenant_id=tenant_id,
            preset_name=body.preset_name,
            prompt_code=body.prompt_code,
            display_name=body.display_name or body.prompt_code,
            description=body.description,
            category=body.category,
            language=body.language,
            content=body.content,
            created_at=now,
            updated_at=now,
            created_by=created_by,
            updated_by=created_by,
        )

        path = self._prompt_path(tenant_id, item.id)
        if path.exists():
            raise FileExistsError(
                f"Prompt config '{item.id}' already exists for tenant '{tenant_id}'"
            )

        self._save_yaml(path, item.model_dump(mode="json"))
        return item

    def update(
        self,
        tenant_id: str,
        prompt_id: str,
        body: PromptConfigUpdate,
        updated_by: str = "anonymous",
    ) -> Optional[PromptConfigItem]:
        """Update an existing prompt config. Returns None if not found."""
        existing = self.get(tenant_id, prompt_id)
        if existing is None:
            return None

        now = datetime.now(timezone.utc).isoformat()
        update_data = body.model_dump(exclude_unset=True)
        update_data["updated_at"] = now
        update_data["updated_by"] = updated_by

        merged = existing.model_dump(mode="json")
        merged.update(update_data)

        item = PromptConfigItem(**merged)
        self._save_yaml(self._prompt_path(tenant_id, prompt_id), merged)
        return item

    def delete(self, tenant_id: str, prompt_id: str) -> bool:
        """Delete a prompt config. Returns True if deleted, False if not found."""
        path = self._prompt_path(tenant_id, prompt_id)
        if not path.exists():
            return False
        os.remove(path)
        return True

    # ── Batch lookup for processor integration ─────────────────────────

    def load_overrides(
        self, tenant_id: str, preset_name: str
    ) -> dict[str, str]:
        """Load all prompt overrides for a tenant+preset as {code: content} dict.

        This is the method called by processors before running analysis.
        Returns a dict of prompt_code → content for all overrides found.
        """
        overrides: dict[str, str] = {}
        tenant_dir = self._tenant_dir(tenant_id)
        if not tenant_dir.is_dir():
            return overrides

        for f in sorted(tenant_dir.glob("*.yaml")):
            try:
                data = self._load_yaml(f)
                if data.get("preset_name") == preset_name and data.get("content"):
                    code = data.get("prompt_code")
                    if code:
                        overrides[code] = data["content"]
            except Exception:
                pass
        return overrides
