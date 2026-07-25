"""
Processor integration — apply prompt overrides when processing with a prompt_id.

This module provides the glue between:
  1. The prompt config CRUD API (prompts.py + prompt_config_manager.py)
  2. The modal processors (modalprocessors.py + video_processor.py)

Usage pattern (inside a processor's generate_description_only or similar)::

    from raganything.service.prompt_integration import resolve_prompt_overrides, PromptOverride

    # At the start of processing, load overrides once:
    overrides = resolve_prompt_overrides(
        pcm=request.app.state.prompt_config_manager,
        tenant_id=tenant_id,
        preset_name="document",
        prompt_ids=["abc123", "def456"],  # optional: specific prompt config IDs
    )

    # Then when building prompts, check for overrides:
    vision_prompt_text = overrides.get_effective_prompt(
        code="vision_prompt",
        default=PROMPTS["vision_prompt"],
    )

Design rationale:
  - Overrides are loaded once per processing task, not per prompt invocation.
  - The default from PROMPTS registry is always available as fallback.
  - Specific prompt_ids take precedence over preset-wide overrides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from raganything.service.prompt_config_manager import PromptConfigManager


@dataclass
class PromptOverride:
    """Resolved prompt overrides for a single processing task.

    ``by_code`` maps prompt_code → override content text.
    When multiple overrides match the same code (e.g. one by preset, one by id),
    the id-specific one wins (loaded last).
    """

    by_code: Dict[str, str] = field(default_factory=dict)

    def get_effective_prompt(self, code: str, default: str) -> str:
        """Return the override content for *code*, or *default* if no override exists.

        Args:
            code: PROMPTS registry key, e.g. "vision_prompt"
            default: The default prompt template text (from PROMPTS registry)

        Returns:
            The override content string, or the default.
        """
        override = self.by_code.get(code)
        if override is not None:
            return override
        return default

    def has_override(self, code: str) -> bool:
        """Check if an override exists for the given prompt code."""
        return code in self.by_code

    def to_dict(self) -> Dict[str, str]:
        return dict(self.by_code)


def resolve_prompt_overrides(
    pcm: PromptConfigManager,
    tenant_id: str,
    preset_name: str = "",
    prompt_ids: Optional[List[str]] = None,
) -> PromptOverride:
    """Load prompt overrides from the config manager.

    Resolution order (last wins):
      1. All overrides for the tenant+preset (from YAML files)
      2. Specific prompt_ids (if provided) — looked up individually

    Args:
        pcm: The PromptConfigManager instance (from app.state).
        tenant_id: Tenant scope for overrides.
        preset_name: Which preset's overrides to load.
        prompt_ids: Optional list of specific prompt config IDs to apply.
                    These take precedence over preset-wide overrides.

    Returns:
        A PromptOverride object with the resolved by_code mapping.
    """
    by_code: Dict[str, str] = {}

    # Layer 1: Preset-wide overrides (all configs for this tenant+preset)
    if preset_name:
        overrides = pcm.load_overrides(tenant_id, preset_name)
        by_code.update(overrides)

    # Layer 2: Specific prompt_id overrides (higher priority)
    if prompt_ids:
        for pid in prompt_ids:
            item = pcm.get(tenant_id, pid)
            if item is not None and item.content:
                by_code[item.prompt_code] = item.content

    return PromptOverride(by_code=by_code)
