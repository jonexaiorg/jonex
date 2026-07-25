"""ProcessorFactoryRegistry — decorator-based modal processor registration.

Each content type's factory is registered via ``@ProcessorFactoryRegistry.register("image")``.
Builder loops over all registered factories instead of hard-coded if-blocks.
Third-party content types can register without modifying this file.
"""

from typing import Any, Callable, Dict

from raganything.modalprocessors import (
    ImageModalProcessor,
    TableModalProcessor,
    EquationModalProcessor,
    GenericModalProcessor,
)


class ProcessorFactoryRegistry:
    """Decorator-based registry for modal processor factories."""

    _factories: Dict[str, Callable] = {}

    @classmethod
    def register(cls, content_type: str):
        """Decorator: register a factory function for a content type."""
        def decorator(factory: Callable):
            cls._factories[content_type] = factory
            return factory
        return decorator

    @classmethod
    def build_all(cls, builder) -> Dict[str, Any]:
        """Call each registered factory with *builder*. Returns {type: processor}."""
        processors: Dict[str, Any] = {}
        for content_type, factory in cls._factories.items():
            if not cls._is_enabled(builder, content_type):
                continue
            try:
                processors[content_type] = factory(builder)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to create processor '{content_type}': {e}",
                    exc_info=True,
                )
        return processors

    @classmethod
    def _is_enabled(cls, builder, content_type: str) -> bool:
        config = builder._config
        enable_map = {
            "image": getattr(config, "enable_image_processing", True),
            "table": getattr(config, "enable_table_processing", True),
            "equation": getattr(config, "enable_equation_processing", True),
            "audio": getattr(config, "enable_audio_processing", False),
            "video": getattr(config, "enable_video_processing", False),
            "generic": True,
        }
        return enable_map.get(content_type, True)


# ── Factory functions (registered via decorator) ──────────────────────

@ProcessorFactoryRegistry.register("image")
def _create_image(builder):
    # [jonex] 批次 2-C：优先用 BoundModel + base64_caption_adapter，
    # 匹配 ImageModalProcessor 的 (prompt, image_data=base64, system_prompt=...) 调用约定。
    # legacy_vlm_adapter 签名 (image_path, prompt) + file:// 与此不兼容，不可直接使用。
    vlm_bound = getattr(builder, '_vlm_bound', None)
    if vlm_bound is not None:
        from raganything.models import base64_caption_adapter
        vision_func = base64_caption_adapter(vlm_bound)
    else:
        vision_func = builder._vlm_func or builder._llm_func
    return ImageModalProcessor(
        lightrag=builder._lightrag,
        modal_caption_func=vision_func,
        context_extractor=builder._context_extractor,
    )


@ProcessorFactoryRegistry.register("table")
def _create_table(builder):
    return TableModalProcessor(
        lightrag=builder._lightrag,
        modal_caption_func=builder._llm_func,
        context_extractor=builder._context_extractor,
    )


@ProcessorFactoryRegistry.register("equation")
def _create_equation(builder):
    return EquationModalProcessor(
        lightrag=builder._lightrag,
        modal_caption_func=builder._llm_func,
        context_extractor=builder._context_extractor,
    )


@ProcessorFactoryRegistry.register("audio")
def _create_audio(builder):
    if not builder._asr_backend:
        raise RuntimeError("ASR backend not configured")
    from raganything.modalprocessors import AsrModalProcessor
    return AsrModalProcessor(
        lightrag=builder._lightrag,
        modal_caption_func=builder._llm_func,
        asr_backend=builder._asr_backend,
        config=builder._config,
        context_extractor=builder._context_extractor,
    )


@ProcessorFactoryRegistry.register("video")
def _create_video(builder):
    import os
    import logging

    _logger = logging.getLogger(__name__)

    from raganything.video_processor import VideoModalProcessor

    # ── MPS backend wiring ──────────────────────────────────────
    video_analysis_backends = {}
    default_backend = "local"

    if os.getenv("MPS_ENABLED", "").strip().lower() in ("true", "1", "yes"):
        try:
            from raganything.video_analysis.backends.mps import MPSVideoBackend

            mps_backend = MPSVideoBackend(builder._config)
            video_analysis_backends["mps"] = mps_backend
            default_backend = "mps"
            _logger.info("MPS video analysis backend enabled (MPS_ENABLED=true)")
        except Exception as e:
            _logger.warning(
                f"MPS backend init failed, falling back to local: {e}"
            )

    return VideoModalProcessor(
        lightrag=builder._lightrag,
        modal_caption_func=builder._llm_func,
        vlm_model_func=builder._vlm_func,
        asr_backend=builder._asr_backend,
        config=builder._config,
        tokenizer=builder._lightrag.tokenizer,
        context_extractor=builder._context_extractor,
        # Phase 3: pass BoundModels if available (builder may not have them yet)
        llm_bound=getattr(builder, '_llm_bound', None),
        vlm_bound=getattr(builder, '_vlm_bound', None),
        # MPS backend injection
        video_analysis_backends=video_analysis_backends or None,
        default_backend=default_backend,
    )


@ProcessorFactoryRegistry.register("generic")
def _create_generic(builder):
    return GenericModalProcessor(
        lightrag=builder._lightrag,
        modal_caption_func=builder._llm_func,
        context_extractor=builder._context_extractor,
    )


# ── Builder class (thin wrapper) ──────────────────────────────────────

class ModalProcessorBuilder:
    """Thin wrapper that delegates to ProcessorFactoryRegistry.build_all()."""

    def __init__(self, lightrag, config, llm_func, vlm_func=None):
        self._lightrag = lightrag
        self._config = config
        self._llm_func = llm_func
        self._vlm_func = vlm_func
        self._asr_backend = None
        self._context_extractor = None
        # Phase 3: BoundModel refs (optional, coexists with legacy callables)
        self._llm_bound = None
        self._vlm_bound = None

    def with_asr_backend(self, backend) -> "ModalProcessorBuilder":
        self._asr_backend = backend
        return self

    def with_context_extractor(self, extractor) -> "ModalProcessorBuilder":
        self._context_extractor = extractor
        return self

    def with_llm_bound(self, bound) -> "ModalProcessorBuilder":
        """Set BoundModel for LLM (preferred over _llm_func)."""
        self._llm_bound = bound
        return self

    def with_vlm_bound(self, bound) -> "ModalProcessorBuilder":
        """Set BoundModel for VLM (preferred over _vlm_func)."""
        self._vlm_bound = bound
        return self

    def build_all(self) -> Dict[str, Any]:
        return ProcessorFactoryRegistry.build_all(self)
