"""ModelRegistry — load models.env + models.yaml → bind by model_id."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

from raganything.models.driver import BaseModelDriver
from raganything.models.types import (
    BoundModel,
    ModelCapability,
    ModelSpec,
    RetryPolicy,
)

logger = logging.getLogger(__name__)

# ── Binding alias table ─────────────────────────────────────────────────
# Routes models.env binding names to actual driver bindings.
# vLLM, Ollama, LM Studio are all OpenAI-protocol-compatible —
# they don't need separate Driver classes.

BINDING_ALIASES: dict[str, str] = {
    "vllm": "openai",
    "ollama": "openai",
    "lmstudio": "openai",
    "tokenhub": "anthropic",
}


# ── ModelRegistry ────────────────────────────────────────────────────────


class RegistryError(Exception):
    """Raised when model lookup or binding resolution fails."""


class ModelRegistry:
    """Process-level singleton — resolves model_id → BoundModel.

    Scope:
        Process-level singleton. All tenants share the same model config.
        Tenant-level overrides (if needed later) via per-tenant models.yaml path.

    Usage::

        registry = ModelRegistry("config/profiles")
        registry.register_driver(OpenAIDriver())
        registry.register_driver(EchoDriver())
        registry.load_profile("dev")

        llm = registry.bind("qwen3-72b")
        response = await llm.complete([{"role":"user","content":"Hello"}])
    """

    def __init__(self, profiles_dir: str = "config/profiles"):
        self._profiles_dir = Path(profiles_dir)
        self._specs: dict[str, ModelSpec] = {}       # model_id → ModelSpec
        self._drivers: dict[str, BaseModelDriver] = {}  # binding → driver
        self._model_metadata: dict[str, dict] = {}    # model_id → extra metadata from yaml

    # ── Driver registration ──────────────────────────────────────────

    def register_driver(self, driver: BaseModelDriver) -> None:
        """Register a driver for all its declared bindings."""
        for binding in driver.bindings:
            if binding in self._drivers:
                logger.warning(
                    f"Driver for binding '{binding}' is being replaced "
                    f"({type(self._drivers[binding]).__name__} → "
                    f"{type(driver).__name__})"
                )
            self._drivers[binding] = driver
        logger.info(
            f"Registered {type(driver).__name__} "
            f"for bindings: {driver.bindings}"
        )

    # ── Profile loading ──────────────────────────────────────────────

    def load_profile(self, profile: str) -> list[ModelSpec]:
        """Load models.env + models.yaml for a profile, return specs."""
        profile_dir = self._profiles_dir / profile
        if not profile_dir.is_dir():
            raise RegistryError(f"Profile directory not found: {profile_dir}")

        # 1. Load capabilities from models.yaml (optional)
        capabilities = self._load_capabilities(profile_dir / "models.yaml")

        # 2. Load connections from models.env (required)
        specs = self._load_models_env(profile_dir / "models.env", capabilities)

        # 3. Store in registry
        for spec in specs:
            self._specs[spec.model_id] = spec

        logger.info(
            f"Loaded {len(specs)} models from profile '{profile}': "
            f"{[s.model_id for s in specs]}"
        )
        return specs

    # ── Binding ──────────────────────────────────────────────────────

    def bind(self, model_id: str) -> BoundModel:
        """Resolve a model_id to a BoundModel.

        Raises:
            RegistryError: model_id not found, or binding has no registered driver.
        """
        spec = self._specs.get(model_id)
        if spec is None:
            available = list(self._specs.keys())
            raise RegistryError(
                f"Model '{model_id}' not found in registry. "
                f"Available: {available or '(none loaded)'}"
            )

        # Resolve binding → driver
        canonical = BINDING_ALIASES.get(spec.binding, spec.binding)
        driver = self._drivers.get(canonical)
        if driver is None:
            available_drivers = list(self._drivers.keys())
            raise RegistryError(
                f"No driver registered for binding '{canonical}' "
                f"(model '{model_id}' uses binding '{spec.binding}'). "
                f"Available drivers: {available_drivers or '(none)'}. "
                f"Did you call registry.register_driver()?"
            )

        return BoundModel(spec=spec, driver=driver)

    def list_models(
        self,
        *,
        supports_vision: Optional[bool] = None,
        supports_thinking: Optional[bool] = None,
    ) -> list[ModelSpec]:
        """Filter models by capability."""
        results = list(self._specs.values())
        if supports_vision is not None:
            results = [
                s for s in results
                if s.capability.supports_vision == supports_vision
            ]
        if supports_thinking is not None:
            results = [
                s for s in results
                if s.capability.supports_thinking == supports_thinking
            ]
        return results

    @property
    def model_ids(self) -> list[str]:
        return list(self._specs.keys())

    # ── Internal: models.env parsing ──────────────────────────────────

    def _load_models_env(
        self, path: Path, capabilities: dict[str, ModelCapability],
    ) -> list[ModelSpec]:
        """Parse models.env: ``model_id = binding://host``"""
        if not path.exists():
            raise RegistryError(f"models.env not found: {path}")

        specs: list[ModelSpec] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                model_id = key.strip()
                url = val.strip()

                binding, host = self._parse_binding_url(url)
                cap = capabilities.get(
                    model_id,
                    # No models.yaml entry → safe conservative default
                    ModelCapability(),
                )
                api_key = self._resolve_api_key(model_id, binding)

                # Attach extra metadata from models.yaml
                extra = getattr(self, "_model_metadata", {}).get(model_id, {})

                specs.append(ModelSpec(
                    model_id=model_id,
                    binding=binding,
                    host=host,
                    api_key=api_key,
                    capability=cap,
                    metadata=extra,
                ))

        return specs

    @staticmethod
    def _parse_binding_url(url: str) -> tuple[str, str]:
        """Parse ``binding://host`` → (binding, host)."""
        if "://" in url:
            binding, rest = url.split("://", 1)
            # Strip query params (e.g. ?dim=768) — they belong in models.yaml
            host = rest.split("?")[0].rstrip("/")
            return binding.strip(), host.strip()
        return "", url.strip()

    @staticmethod
    def _resolve_api_key(model_id: str, binding: str) -> str:
        """Resolve API key from environment variables.

        Priority:
          1. {MODEL_ID}_API_KEY (uppercase, non-alphanumeric → underscore)
          2. {BINDING}_API_KEY
          3. OPENAI_API_KEY (fallback for OpenAI-compatible bindings)
          4. GEMINI_API_KEY (fallback for Gemini)
        """
        import re

        safe_id = re.sub(r"[^A-Za-z0-9]", "_", model_id).upper()
        keys_to_try = [
            f"{safe_id}_API_KEY",
            f"{binding.upper()}_API_KEY",
            "OPENAI_API_KEY",
        ]
        for key in keys_to_try:
            val = os.getenv(key, "")
            if val:
                return val
        return ""

    # ── Internal: models.yaml parsing ─────────────────────────────────

    def _load_capabilities(
        self, path: Path,
    ) -> dict[str, ModelCapability]:
        """Load model capabilities from YAML.

        Missing file → empty dict (all defaults).
        Missing model key → ModelCapability() default.
        """
        if not path.exists():
            return {}

        try:
            import yaml
        except ImportError:
            logger.warning(f"PyYAML not installed, skipping {path}")
            return {}

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        models_raw = data.get("models", {})
        result: dict[str, ModelCapability] = {}
        extra_metadata: dict[str, dict] = {}
        for model_id, cap_dict in models_raw.items():
            if not isinstance(cap_dict, dict):
                continue
            # Separate capability fields from extra metadata
            cap_fields = {k: v for k, v in cap_dict.items()
                         if k in ModelCapability.__dataclass_fields__}
            meta = {k: v for k, v in cap_dict.items()
                    if k not in ModelCapability.__dataclass_fields__ and k != "metadata"}
            # Also include explicit metadata block
            if "metadata" in cap_dict and isinstance(cap_dict["metadata"], dict):
                meta.update(cap_dict["metadata"])
            result[model_id] = ModelCapability(**cap_fields) if cap_fields else ModelCapability()
            if meta:
                extra_metadata[model_id] = meta
        # Store extra metadata for later use by ModelFactory
        self._model_metadata = extra_metadata
        return result
