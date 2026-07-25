"""
ModelFactory — builds llm/embedding/vlm model functions from ModelRegistry.

Replaces the old hardcoded _build_llm_func / _build_vlm_func / _build_embedding_func
with registry.bind(model_id) → BoundModel → legacy adapters for backward compat.

Usage::

    from raganything.models import ModelRegistry, OpenAIDriver, legacy_llm_adapter

    registry = ModelRegistry("config/profiles")
    registry.register_driver(OpenAIDriver())
    registry.load_profile("dev")

    factory = ModelFactory(registry)
    funcs = factory.build(profile="dev", overrides={})
    rag = RAGAnything(
        config=funcs["config"],
        llm_model_func=funcs["llm_model_func"],      # legacy callable
        embedding_func=funcs["embedding_func"],        # EmbeddingFunc
        vlm_model_func=funcs.get("vlm_model_func"),   # legacy callable (or None)
        ...
    )
"""

from __future__ import annotations

import logging
import os
from functools import partial
from typing import Any, Callable, Optional

from raganything.config import RAGAnythingConfig

logger = logging.getLogger(__name__)


class ModelFactory:
    """Builds model functions from ModelRegistry + profile config.

    Profile directory layout::

        profiles/{name}/
            models.env        # model_id = binding://host
            models.yaml       # model capabilities (optional)
            secrets.env       # binding = api_key
            endpoints.toml    # [binding] default_host = "..."
            video.toml        # video keyframe settings
    """

    def __init__(self, registry=None, profiles_dir: str = "config/profiles"):
        self._profiles_dir = profiles_dir

        # Lazy init registry if not provided
        self._registry = registry
        self._profiles_loaded: set[str] = set()

    def _ensure_registry(self):
        """Lazy-init the registry on first use."""
        if self._registry is not None:
            return
        from raganything.models import ModelRegistry
        from raganything.models.drivers.openai import OpenAIDriver
        from raganything.models.drivers.anthropic import AnthropicDriver

        self._registry = ModelRegistry(self._profiles_dir)
        self._registry.register_driver(OpenAIDriver())
        self._registry.register_driver(AnthropicDriver())

    def _ensure_profile(self, profile: str):
        """Load profile into registry if not already loaded."""
        assert self._registry is not None
        if profile not in self._profiles_loaded:
            self._registry.load_profile(profile)
            self._profiles_loaded.add(profile)

    # ── Metering headers ──────────────────────────────────────────────

    @staticmethod
    def _build_metering_headers(
        tenant_id: str = "", kb_id: str = "", trace_id: str = "",
    ) -> dict[str, str]:
        """[jonex] Build X-Jonex-* metering headers for llm-gateway accounting."""
        headers: dict[str, str] = {"X-Jonex-Scene": "raganything_ingest"}
        if tenant_id:
            headers["X-Jonex-Tenant-Id"] = tenant_id
        if kb_id:
            headers["X-Jonex-Kb-Id"] = kb_id
        if trace_id:
            headers["X-Jonex-Trace-Id"] = trace_id
        return headers

    # ── Public API ────────────────────────────────────────────────────

    def build(
        self,
        profile: str = "dev",
        overrides: Optional[dict[str, Any]] = None,
        working_dir: str = "./rag_storage",
        parser_output_dir: str = "./output",
        *,
        tenant_id: str = "",
        kb_id: str = "",
    ) -> dict[str, Any]:
        """Build model functions and RAGAnythingConfig from profile.

        Returns:
            Dict with keys:
              - config: RAGAnythingConfig
              - llm_model_func: legacy callable (prompt, system_prompt, **kw) -> str
              - embedding_func: EmbeddingFunc
              - vlm_model_func: optional legacy callable (image_path, prompt) -> str
              - asr_model_func: optional (handled by RAGAnything auto-creation)
              - lightrag_kwargs: dict for LightRAG initialization
        """
        overrides = overrides or {}
        self._ensure_registry()
        self._ensure_profile(profile)

        from raganything.models import legacy_llm_adapter, legacy_vlm_adapter
        from raganything.models.transformers import get_transformer

        # Determine model IDs
        llm_model_id = overrides.get("llm_model") or self._find_llm()
        embedding_model_id = overrides.get("embedding_model") or self._find_embedding()
        vlm_model_id = overrides.get("vlm_model_name") or self._find_vlm()

        # ── LLM ──────────────────────────────────────────────────────
        llm_func: Callable | None = None
        llm_host = ""
        if llm_model_id:
            try:
                bound_llm = self._bind_with_overrides(
                    llm_model_id, overrides, prefix="llm",
                    tenant_id=tenant_id, kb_id=kb_id,
                )
                transformer = get_transformer(
                    bound_llm.spec.binding, model_id=llm_model_id,
                )
                llm_func = legacy_llm_adapter(bound_llm, transformer=transformer)
                llm_host = bound_llm.spec.host
                logger.info(
                    f"LLM: {llm_model_id} @ {llm_host} "
                    f"(driver={type(bound_llm.driver).__name__})"
                )
            except Exception as e:
                logger.warning(f"LLM bind failed for '{llm_model_id}': {e}")
                llm_func = self._metered_llm(llm_model_id, tenant_id=tenant_id, kb_id=kb_id)

        # ── Embedding ────────────────────────────────────────────────
        embedding_func = None
        emb_host = ""
        emb_model_name = embedding_model_id or llm_model_id or "bge-m3"
        if embedding_model_id:
            try:
                embedding_func = self._build_embedding_from_registry(
                    embedding_model_id, emb_model_name,
                    tenant_id=tenant_id, kb_id=kb_id,
                )
                if embedding_func and hasattr(embedding_func, 'embedding_dim'):
                    logger.info(
                        f"Embedding: {emb_model_name} (dim={embedding_func.embedding_dim})"
                    )
            except Exception as e:
                logger.warning(f"Embedding bind failed: {e}")
                embedding_func = self._metered_embedding(emb_model_name, tenant_id=tenant_id, kb_id=kb_id)

        if embedding_func is None:
            embedding_func = self._metered_embedding(emb_model_name, tenant_id=tenant_id, kb_id=kb_id)

        # ── VLM ──────────────────────────────────────────────────────
        vlm_func: Callable | None = None
        if vlm_model_id:
            try:
                bound_vlm = self._bind_with_overrides(
                    vlm_model_id, overrides, prefix="vlm",
                    tenant_id=tenant_id, kb_id=kb_id,
                )
                vlm_func = legacy_vlm_adapter(bound_vlm)
                logger.info(
                    f"VLM: {vlm_model_id} @ {bound_vlm.spec.host} "
                    f"(driver={type(bound_vlm.driver).__name__})"
                )
            except Exception as e:
                logger.warning(f"VLM bind failed for '{vlm_model_id}': {e}")

        # ── ASR ──────────────────────────────────────────────────────
        asr_func = None  # handled by RAGAnything auto-creation from config

        # ── Config ───────────────────────────────────────────────────
        config_kwargs: dict[str, Any] = {
            "working_dir": working_dir,
            "parser_output_dir": parser_output_dir,
        }
        if overrides:
            valid_fields = {
                field.name for field in RAGAnythingConfig.__dataclass_fields__.values()
            }
            config_kwargs.update({
                k: v for k, v in overrides.items() if k in valid_fields
            })

        config = RAGAnythingConfig(**config_kwargs)
        logger.info(f"RAGAnythingConfig: working_dir={working_dir}")

        # ── LightRAG kwargs ──────────────────────────────────────────
        lightrag_kwargs: dict[str, Any] = {}
        if llm_host:
            os.environ.setdefault("LLM_BINDING_HOST", llm_host)

        # Pass embedding worker timeout from env or default 300s
        embedding_timeout = int(os.getenv("EMBEDDING_WORKER_TIMEOUT", "300"))
        embedding_batch = int(overrides.get("embedding_batch_num", os.getenv("EMBEDDING_BATCH_NUM", "2")))
        lightrag_kwargs["embedding_batch_num"] = embedding_batch
        lightrag_kwargs["embedding_func_max_async"] = embedding_timeout

        return {
            "config": config,
            "llm_model_func": llm_func,
            "embedding_func": embedding_func,
            "vlm_model_func": vlm_func,
            "asr_model_func": asr_func,
            "lightrag_kwargs": lightrag_kwargs,
        }

    # ── Model discovery helpers ──────────────────────────────────────

    def _find_llm(self) -> Optional[str]:
        """Find the first non-vision, non-thinking LLM."""
        assert self._registry is not None
        # Prefer models without vision
        for spec in self._registry.list_models(supports_vision=False):
            if not spec.capability.supports_thinking:
                return spec.model_id
        # Fallback: any model
        ids = self._registry.model_ids
        return ids[0] if ids else None

    def _find_vlm(self) -> Optional[str]:
        """Find the first vision-capable model."""
        assert self._registry is not None
        vlms = self._registry.list_models(supports_vision=True)
        return vlms[0].model_id if vlms else None

    def _find_embedding(self) -> Optional[str]:
        """Find a model suitable for embedding (has dim in metadata or known names)."""
        assert self._registry is not None
        for spec in self._registry._specs.values():
            md = spec.metadata or {}
            if md.get("embedding_dim"):
                return spec.model_id
        # Fallback: search by name
        for mid in self._registry.model_ids:
            if any(kw in mid.lower() for kw in ("bge", "embed", "e5", "gemma", "stella")):
                return mid
        return None

    # ── Fallback builders (when registry not available) ──────────────

    def _metered_llm(
        self, model_name: str, tenant_id: str = "", kb_id: str = "",
    ) -> Callable:
        """[jonex] Build an LLM callable that injects X-Jonex-* metering headers.

        Uses httpx directly (not lightrag's openai_complete_if_cache) so metering
        headers reach llm-gateway for per-tenant/per-KB token accounting.
        """
        import httpx

        host = os.getenv("LLM_BINDING_HOST", "")
        key = os.getenv("LLM_BINDING_API_KEY", "")
        metering_headers = self._build_metering_headers(tenant_id, kb_id)
        timeout = float(os.getenv("LLM_HTTP_TIMEOUT", "120"))

        async def _llm(prompt: str, system_prompt: str = "", **kw) -> str:
            messages: list[dict] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            headers: dict[str, str] = {
                "Content-Type": "application/json",
                **metering_headers,
            }
            if key:
                headers["Authorization"] = f"Bearer {key}"

            payload: dict[str, Any] = {
                "model": model_name,
                "messages": messages,
            }
            for k, v in kw.items():
                if v is not None and k not in ("history_messages",):
                    payload[k] = v

            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
                resp = await client.post(
                    f"{host}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                msg = data["choices"][0]["message"]
                # deepseek-v4 等推理模型 content 可能为空，回退到 reasoning_content
                return msg.get("content") or msg.get("reasoning_content") or ""

        return _llm

    def _metered_embedding(
        self, model_name: str, tenant_id: str = "", kb_id: str = "",
    ):
        """[jonex] Build an embedding function that injects X-Jonex-* metering headers.

        Uses httpx directly (not lightrag's openai_embed) so metering headers
        reach llm-gateway for per-tenant/per-KB token accounting.
        """
        import httpx
        from lightrag.utils import EmbeddingFunc

        host = os.getenv("LLM_BINDING_HOST", "")
        key = os.getenv("LLM_BINDING_API_KEY", "")
        emb_dim = int(os.getenv("EMBEDDING_DIM", "1024"))
        metering_headers = self._build_metering_headers(tenant_id, kb_id)
        timeout = float(os.getenv("LLM_HTTP_TIMEOUT", "120"))

        async def _embed(texts: list[str]) -> list[list[float]]:
            headers: dict[str, str] = {
                "Content-Type": "application/json",
                **metering_headers,
            }
            if key:
                headers["Authorization"] = f"Bearer {key}"

            payload: dict[str, Any] = {
                "model": model_name,
                "input": texts,
            }

            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
                resp = await client.post(
                    f"{host}/embeddings",
                    headers=headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return [item["embedding"] for item in data["data"]]

        return EmbeddingFunc(embedding_dim=emb_dim, max_token_size=8192, func=_embed)

    def _build_embedding_from_registry(
        self, model_id: str, model_name: str,
        tenant_id: str = "", kb_id: str = "",
    ):
        """Build embedding function using registry for host/api_key resolution."""
        from lightrag.llm.openai import openai_embed
        from lightrag.utils import EmbeddingFunc

        spec = self._registry._specs.get(model_id)
        if spec is None:
            return self._metered_embedding(model_name, tenant_id=tenant_id, kb_id=kb_id)

        host = spec.host
        api_key = spec.api_key or os.getenv("OPENAI_API_KEY", "")
        emb_dim = int(spec.metadata.get("embedding_dim", 1024))

        # Override lightrag's hardcoded embedding_dim on the function
        openai_embed.embedding_dim = emb_dim

        embedding_timeout = int(os.getenv("EMBEDDING_HTTP_TIMEOUT", "600"))
        embed_fn = partial(openai_embed, model=model_name, base_url=host, api_key=api_key,
                          client_configs={"timeout": embedding_timeout})
        ef = EmbeddingFunc(embedding_dim=emb_dim, max_token_size=8192, func=embed_fn)
        return ef

    # ── VLM-only builder (HTTP mode) ─────────────────────────────────

    def build_vlm(self) -> dict | None:
        """Build VLM function for multimodal processing only (HTTP mode).

        HTTP mode does not need LLM or Embedding — those are handled by
        :9621 server-side.  Only VLM is needed for image/table/video
        description generation during the multimodal stage.

        [jonex] 批次 2-C：返回 dict 包含 func (legacy adapter) 与 bound (BoundModel)，
        供 processor_builder 用 base64_caption_adapter 创建兼容 image_data 的调用。
        """
        self._ensure_registry()

        vlm_model_id = self._find_vlm()
        if not vlm_model_id:
            # Fallback: check VLM_BINDING_HOST env（preset 链路约定）
            vlm_host = os.getenv("VLM_BINDING_HOST", "")
            if vlm_host:
                vlm_model_id = os.getenv("VLM_MODEL_NAME", "") or "qwen3.5-9b-vlm:latest"
                logger.info(
                    f"No VLM model in registry, creating ad-hoc VLM: "
                    f"{vlm_model_id} @ {vlm_host}"
                )
            else:
                logger.warning(
                    "No VLM model found in registry and VLM_BINDING_HOST not set "
                    "— multimodal processing disabled"
                )
                return None

        try:
            bound_vlm = self._bind_with_overrides(vlm_model_id, {}, prefix="vlm")
            from raganything.models import legacy_vlm_adapter
            logger.info(
                f"VLM (HTTP mode): {vlm_model_id} @ {bound_vlm.spec.host} "
                f"(driver={type(bound_vlm.driver).__name__})"
            )
            return {"func": legacy_vlm_adapter(bound_vlm), "bound": bound_vlm}
        except Exception as e:
            logger.warning(f"VLM bind failed for '{vlm_model_id}': {e}")
            return None

    # ── Connection overrides ─────────────────────────────────────────

    def _bind_with_overrides(
        self, model_id: str, overrides: dict, prefix: str,
        tenant_id: str = "", kb_id: str = "",
    ) -> Any:
        """Bind a model with optional host/api_key overrides.

        Supports two paths:
        1. model_id in registry → bind + apply overrides (if any)
        2. model_id NOT in registry BUT host explicitly provided →
           create an ad-hoc BoundModel using OpenAIDriver as default

        Args:
            model_id: Model identifier.
            overrides: Config overrides dict.
            prefix: Model type prefix ("llm", "vlm", "embedding").
            tenant_id: [jonex] Tenant for metering headers.
            kb_id: [jonex] Knowledge base for metering headers.

        Returns:
            BoundModel (from registry or ad-hoc).

        Raises:
            RegistryError: If model not in registry AND no host override.
        """
        from dataclasses import replace
        from raganything.models.types import BoundModel, ModelCapability, ModelSpec

        host_key = f"{prefix}_host"
        api_key_key = f"{prefix}_api_key"
        # 连接信息优先级：preset override > env(XXX_BINDING_HOST / _API_KEY) > profile spec。
        # 这样 preset 里不写 host/key 时回退到环境变量（如 VLM_BINDING_HOST / LLM_BINDING_HOST）。
        new_host = overrides.get(host_key) or os.getenv(f"{prefix.upper()}_BINDING_HOST")
        new_api_key = overrides.get(api_key_key) or os.getenv(f"{prefix.upper()}_BINDING_API_KEY")

        # [jonex] Build metering headers for this model
        extra_headers = self._build_metering_headers(tenant_id, kb_id)

        # Try registry first
        try:
            bound = self._registry.bind(model_id)
        except Exception:
            # Not in registry — need explicit host override to proceed
            if not new_host:
                raise
            # Pick driver: check registered drivers for a matching binding
            binding = self._guess_binding(new_host)
            driver = self._registry._drivers.get(binding)
            if driver is None:
                from raganything.models.drivers.openai import OpenAIDriver
                driver = OpenAIDriver()
            spec = ModelSpec(
                model_id=model_id,
                binding=binding,
                host=new_host,
                api_key=new_api_key or "",
                capability=ModelCapability(
                    supports_vision=(prefix == "vlm"),
                ),
                extra_headers=extra_headers,
            )
            logger.info(
                f"Ad-hoc binding for '{model_id}' "
                f"(not in registry, using host={new_host})"
            )
            return BoundModel(spec=spec, driver=driver)

        # In registry — apply connection overrides if present
        if new_host or new_api_key:
            spec = bound.spec
            updated_spec = replace(
                spec,
                host=new_host if new_host else spec.host,
                api_key=new_api_key if new_api_key else spec.api_key,
                extra_headers=extra_headers,
            )
            return BoundModel(spec=updated_spec, driver=bound.driver)

        # [jonex] Inject metering headers even when no other overrides
        updated_spec = replace(bound.spec, extra_headers=extra_headers)
        return BoundModel(spec=updated_spec, driver=bound.driver)

    @staticmethod
    def _guess_binding(host: str) -> str:
        """Guess the API binding from the host URL."""
        host_lower = host.lower()
        if "tokenhub" in host_lower or "anthropic" in host_lower:
            return "tokenhub"
        if "gemini" in host_lower or "generativelanguage" in host_lower:
            return "gemini"
        # Default: OpenAI-compatible
        return "openai"

    # ── Registry access ──────────────────────────────────────────────

    @property
    def registry(self):
        return self._registry
