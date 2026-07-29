"""
Complete document parsing + multimodal content insertion Pipeline

This script integrates:
1. Document parsing (using configurable parsers)
2. Pure text content LightRAG insertion
3. Specialized processing for multimodal content (using different processors)
"""

import base64
import os
from typing import Dict, Any, Optional, Callable
import sys
import time
import asyncio
import atexit
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

# Add project root directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file BEFORE importing LightRAG
# This is critical for TIKTOKEN_CACHE_DIR to work properly in offline environments
# The OS environment variables take precedence over the .env file
load_dotenv(dotenv_path=".env", override=False)

# ruff: noqa: E402 — imports below depend on env vars set by load_dotenv above

from lightrag import LightRAG
from lightrag.utils import logger

# Import configuration and modules
from raganything.config import RAGAnythingConfig
from raganything.query import QueryMixin
from raganything.batch import BatchMixin
from raganything.utils import get_processor_supports
from raganything.parsers import MineruParser, SUPPORTED_PARSERS, get_parser
from raganything.callbacks import CallbackManager
from raganything.asr import create_asr_backend
from raganything.asr.backends import *  # noqa: F401, F403 -- trigger registration
from raganything.video_analysis.backends import *  # noqa: F401, F403 -- trigger registration

# Import specialized processors
from raganything.modalprocessors import (
    ContextExtractor,
    ContextConfig,
)

# Pipeline and builder
from raganything.pipeline import DocumentPipeline, PipelineContext, PipelineServices
from raganything.processor import ProcessorMixin
from raganything.processor_builder import ModalProcessorBuilder
from raganything.cache import ParseCacheManager
from raganything.doc_status import DocStatusManager
from raganything.event_bus import EventBus, DocStatusListener


@dataclass
class RAGAnything(QueryMixin, BatchMixin, ProcessorMixin):
    """Multimodal Document Processing Pipeline - Complete document parsing and insertion pipeline"""

    # Core Components
    # ---
    lightrag: Optional[LightRAG] = field(default=None)
    """Optional pre-initialized LightRAG instance."""

    llm_model_func: Optional[Callable] = field(default=None)
    """LLM model function for text analysis."""

    vision_model_func: Optional[Callable] = field(default=None)
    """Vision model function for image analysis."""

    embedding_func: Optional[Callable] = field(default=None)
    """Embedding function for text vectorization."""

    asr_model_func: Optional[Callable] = field(default=None)
    """ASR model function for audio transcription. Must be synchronous.
    Processor wraps in asyncio.to_thread. Required when enable_audio_processing=True."""

    _asr_backend: Optional[Any] = field(default=None, init=False)
    """Internal ASR backend instance, auto-selected or wrapped from asr_model_func."""

    preprocess_audio_func: Optional[Callable] = field(default=None)
    """Optional audio preprocessing function (resample, normalize, VAD).
    Signature: (audio_path: str, output_dir: str) -> str (returns preprocessed path)."""

    vlm_model_func: Optional[Callable] = field(default=None)
    """VLM model function for video keyframe analysis. Used by VideoModalProcessor."""

    vlm_bound: Optional[Any] = field(default=None)
    """[jonex] BoundModel for VLM (preferred over vlm_model_func for image caption).
    Used to create base64_caption_adapter in image processor factory."""

    config: Optional[RAGAnythingConfig] = field(default=None)
    """Configuration object, if None will create with environment variables."""

    # LightRAG Configuration
    # ---
    lightrag_kwargs: Dict[str, Any] = field(default_factory=dict)
    """Additional keyword arguments for LightRAG initialization when lightrag is not provided.
    This allows passing all LightRAG configuration parameters like:
    - kv_storage, vector_storage, graph_storage, doc_status_storage
    - top_k, chunk_top_k, max_entity_tokens, max_relation_tokens, max_total_tokens
    - cosine_threshold, related_chunk_number
    - chunk_token_size, chunk_overlap_token_size, tokenizer, tiktoken_model_name
    - embedding_batch_num, embedding_func_max_async, embedding_cache_config
    - llm_model_name, llm_model_max_token_size, llm_model_max_async, llm_model_kwargs
    - rerank_model_func, vector_db_storage_cls_kwargs, enable_llm_cache
    - max_parallel_insert, max_graph_nodes, addon_params, etc.
    """

    # Internal State
    # ---
    modal_processors: Dict[str, Any] = field(default_factory=dict, init=False)
    """Dictionary of multimodal processors."""

    # Pipeline
    pipeline: Optional[DocumentPipeline] = field(default=None, init=False)
    """Document processing pipeline (replaces ProcessorMixin)."""

    event_bus: Optional[EventBus] = field(default=None, init=False)
    """Event bus for pipeline side effects (doc_status, metrics, etc.)."""

    doc_status_mgr: Optional[DocStatusManager] = field(default=None, init=False)
    """Document status manager for tracking processing state."""

    context_extractor: Optional[ContextExtractor] = field(default=None, init=False)
    """Context extractor for providing surrounding content to modal processors."""

    parse_cache: Optional[Any] = field(default=None, init=False)
    """Parse result cache storage using LightRAG KV storage."""

    multimodal_status_cache: Optional[Any] = field(default=None, init=False)
    """Compatibility KV storage for multimodal completion state."""

    callback_manager: CallbackManager = field(
        default_factory=CallbackManager, init=False, repr=False
    )
    """Processing callbacks manager (optional hooks for observability and metrics)."""

    _parser_installation_checked: bool = field(default=False, init=False)
    """Flag to track if parser installation has been checked."""

    # ── v2 HTTP mode ──
    http_client: Optional[Any] = field(default=None)
    """HttpLightRagClient for external LightRAG Server (:9621) mode.

    When set, skips embedded LightRAG init and uses create_http_pipeline()
    instead of create_default_pipeline(). Parser + VLM are still needed.
    """

    _http_mode: bool = field(default=False, init=False)
    """Internal flag: True when http_client is provided (production path)."""

    def __post_init__(self):
        """Post-initialization setup following LightRAG pattern"""
        # Initialize configuration if not provided
        if self.config is None:
            self.config = RAGAnythingConfig()

        # Set working directory
        self.working_dir = self.config.working_dir

        # Set up logger (use existing logger, don't configure it)
        self.logger = logger

        # Set up document parser
        self.doc_parser = get_parser(self.config.parser)
        # per-task parser 实例缓存（preset 链路：按 ctx.parser_type 选解析器）
        self._task_parser_cache: dict = {}

        # ── v2 HTTP mode detection ──
        if self.http_client is not None:
            self._http_mode = True
            self.logger.info("RAGAnything: HTTP mode (external :9621), "
                             "skipping embedded LightRAG init")

        # Register close method for cleanup
        atexit.register(self.close)

        # Create working directory if needed
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
            self.logger.info(f"Created working directory: {self.working_dir}")

        # Initialize pipeline
        if self._http_mode:
            from raganything.pipeline.builder import create_http_pipeline
            self.pipeline = create_http_pipeline()
            self.logger.info("DocumentPipeline initialized (HTTP mode): "
                             "validate → parse → multimodal → push_chunks")
        else:
            self.pipeline = DocumentPipeline.create_default()
            self.logger.info("DocumentPipeline initialized with 5 stages")

        # Initialize event bus (listeners registered when lightrag is ready)
        self.event_bus = EventBus()
        self._listeners_registered = False

        # Log configuration info
        self.logger.info("RAGAnything initialized with config:")
        self.logger.info(f"  Working directory: {self.config.working_dir}")
        self.logger.info(f"  Parser: {self.config.parser}")
        self.logger.info(f"  Parse method: {self.config.parse_method}")
        self.logger.info(
            f"  Multimodal processing - Image: {self.config.enable_image_processing}, "
            f"Table: {self.config.enable_table_processing}, "
            f"Equation: {self.config.enable_equation_processing}, "
            f"Audio: {self.config.enable_audio_processing}, "
            f"Video: {self.config.enable_video_processing}"
        )
        self.logger.info(f"  Max concurrent files: {self.config.max_concurrent_files}")

    def close(self):
        """Cleanup resources when object is destroyed.

        Handles three common scenarios:
        1. Inside a running async context (e.g., FastAPI shutdown) -> schedule task
        2. No event loop in thread (typical atexit) -> create one with asyncio.run()
        3. Event loop exists but is closed/closing (atexit race) -> create new loop
        """
        # Release ASR backend first (synchronous, outside event loop concerns)
        if getattr(self, '_asr_backend', None) is not None:
            try:
                self._asr_backend.close()
                self._asr_backend = None
            except Exception:
                pass  # Silently ignore during shutdown

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None and loop.is_running():
                # Case 1: We're inside a running event loop, schedule cleanup task
                loop.create_task(self.finalize_storages())
            else:
                # Case 2/3: No running loop. Clean up any stale loop reference
                # so asyncio.run() can create a fresh one (Python 3.10+ raises
                # RuntimeError if a loop is already set for the thread).
                if loop is not None:
                    try:
                        loop.close()
                    except Exception:
                        pass
                    asyncio.set_event_loop(None)
                asyncio.run(self.finalize_storages())
        except Exception:
            # Silently ignore during interpreter shutdown - the event loop and
            # resources are being torn down anyway, and printing may fail if
            # stdout/stderr are already closed. This avoids the noisy
            # "There is no current event loop in thread 'MainThread'" warning
            # that confused users (#135).
            pass

    def _create_context_config(self) -> ContextConfig:
        """Create context configuration from RAGAnything config"""
        return ContextConfig(
            context_window=self.config.context_window,
            context_mode=self.config.context_mode,
            max_context_tokens=self.config.max_context_tokens,
            include_headers=self.config.include_headers,
            include_captions=self.config.include_captions,
            filter_content_types=self.config.context_filter_content_types,
        )

    def _create_context_extractor(self) -> ContextExtractor:
        """Create context extractor with tokenizer from LightRAG"""
        if self.lightrag is None:
            raise ValueError(
                "LightRAG must be initialized before creating context extractor"
            )

        context_config = self._create_context_config()
        return ContextExtractor(
            config=context_config, tokenizer=self.lightrag.tokenizer
        )

    def _auto_create_vlm_func(self):
        """Auto-create VLM function from vision binding config when not explicitly provided.

        Reads VISION_BINDING_HOST / VISION_BINDING_API_KEY (fallback to LLM_BINDING_HOST/KEY),
        constructs an OpenAI-compatible VLM wrapper that encodes image → base64 → API call.
        Returns None if no binding host is configured.
        """
        # 连接信息优先级：config > VLM_BINDING_HOST (preset 链路) > VISION_BINDING_HOST (旧) > LLM_BINDING_HOST
        vision_host = (
            self.config.vision_binding_host
            or os.getenv("VLM_BINDING_HOST", "")
            or os.getenv("VISION_BINDING_HOST", "")
            or os.getenv("LLM_BINDING_HOST", "")
        )
        vision_key = (
            self.config.vision_binding_api_key
            or os.getenv("VLM_BINDING_API_KEY", "")
            or os.getenv("VISION_BINDING_API_KEY", "")
            or os.getenv("LLM_BINDING_API_KEY", "")
        )
        if not vision_host:
            return None

        from lightrag.llm.openai import openai_complete_if_cache

        vlm_model = self.config.vlm_model_name or "gpt-4o"

        async def _vlm_func(image_path: str, prompt: str) -> str:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return await openai_complete_if_cache(
                vlm_model,
                None,
                system_prompt=None,
                history_messages=[],
                base_url=vision_host,
                api_key=vision_key,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                            },
                        ],
                    }
                ],
            )

        _vlm_func.vlm_model = vlm_model
        from raganything.image_transport import VLMSupport

        _vlm_func.vlm_support = VLMSupport(
            supports_url=True,
            supports_base64=True,
        )
        return _vlm_func


    async def _init_processors_via_builder(self):
        """Initialize multimodal processors using ModalProcessorBuilder.

        Replaces _initialize_processors() with builder + factory pattern.
        """
        # HTTP mode: allow processor init without embedded LightRAG
        _lightrag = self.lightrag
        if _lightrag is None:
            # Create a minimal dataclass stub so BaseModalProcessor.asdict() works
            # (in HTTP mode, storage/embedding are handled by :9621 server)
            from dataclasses import dataclass as _dc, field as _f
            from typing import Any as _Any, Optional as _Opt, Callable as _Call
            @_dc
            class _LightRagStub:
                text_chunks: _Opt[_Any] = None
                chunks_vdb: _Opt[_Any] = None
                entities_vdb: _Opt[_Any] = None
                relationships_vdb: _Opt[_Any] = None
                chunk_entity_relation_graph: _Opt[_Any] = None
                embedding_func: _Opt[_Call] = None
                llm_model_func: _Opt[_Call] = None
                tokenizer: _Opt[_Any] = None
                llm_response_cache: _Opt[_Any] = None
                max_parallel_insert: int = 2
            _lightrag = _LightRagStub()
        _tokenizer = getattr(_lightrag, "tokenizer", None)

        # Auto-create VLM function for video if not explicitly provided
        if self.config.enable_video_processing and self.vlm_model_func is None:
            self.vlm_model_func = self._auto_create_vlm_func()
            if self.vlm_model_func is not None:
                self.logger.info("Auto-created vlm_model_func from vision binding config")

        # ASR backend
        asr_backend = None
        if self.config.enable_audio_processing or self.config.enable_video_processing:
            try:
                asr_backend = create_asr_backend(self.config, self.asr_model_func)
                self._asr_backend = asr_backend
            except Exception as e:
                self.logger.warning(f"ASR backend init failed (non-fatal): {e}")

        # Context extractor (tokenizer required; skip if no lightrag)
        context_extractor = None
        if _tokenizer:
            context_config = self._create_context_config()
            context_extractor = ContextExtractor(
                config=context_config, tokenizer=_tokenizer,
            )
            self.context_extractor = context_extractor

        # Build processors via builder
        vlm_func = self.vlm_model_func
        # In HTTP mode, lightrag is None — ModalProcessorBuilder handles this
        builder = ModalProcessorBuilder(
            _lightrag, self.config, self.llm_model_func,
            vlm_func=vlm_func,
        )
        # [jonex] 批次 2-C：传递 BoundModel 供 image factory 用 base64_caption_adapter
        if self.vlm_bound is not None:
            builder.with_vlm_bound(self.vlm_bound)
        builder.with_asr_backend(asr_backend)
        if context_extractor:
            builder.with_context_extractor(context_extractor)
        self.modal_processors = builder.build_all()

        # Video analysis backends (only when video processing is enabled)
        if self.config.enable_video_processing:
            self._video_analysis_backends = {}
            try:
                from raganything.video_analysis import get_video_analysis_backend
                local_cls = get_video_analysis_backend("local")
                self._video_analysis_backends["local"] = local_cls(
                    self.config, local_analyze_func=None,
                )
            except Exception as e:
                self.logger.warning(f"Failed to init local video backend: {e}")

            # Wire local backend to the video processor
            video_proc = self.modal_processors.get("video")
            local_backend = self._video_analysis_backends.get("local")
            if video_proc is not None and local_backend is not None:
                local_backend._analyze_func = video_proc._analyze_via_local

        self.logger.info(
            f"Modal processors initialized via builder: {list(self.modal_processors.keys())}"
        )
        self.logger.info(f"Context configuration: {self._create_context_config()}")

    def update_config(self, **kwargs):
        """Update configuration with new values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.debug(f"Updated config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown config parameter: {key}")

    async def _ensure_lightrag_initialized(self):
        """Ensure LightRAG instance is initialized, create if necessary"""
        try:
            # Check parser installation — warn on failure but don't block
            # (pipelines like video processing don't need a parser at all).
            if not self._parser_installation_checked:
                if not self.doc_parser.check_installation():
                    self.logger.warning(
                        f"Parser '{self.config.parser}' CLI not found on PATH. "
                        "Document parsing will fail, but pipelines that don't need "
                        "a parser (video, query-only) can still proceed."
                    )
                else:
                    self.logger.info(f"Parser '{self.config.parser}' installation verified")
                self._parser_installation_checked = True

            if self.lightrag is not None:
                # LightRAG was pre-provided, but we need to ensure it's properly initialized
                # Inherit model functions from LightRAG if not explicitly provided
                if self.llm_model_func is None and hasattr(
                    self.lightrag, "llm_model_func"
                ):
                    self.llm_model_func = self.lightrag.llm_model_func
                    self.logger.debug("Inherited llm_model_func from LightRAG instance")

                if self.embedding_func is None and hasattr(
                    self.lightrag, "embedding_func"
                ):
                    self.embedding_func = self.lightrag.embedding_func
                    self.logger.debug("Inherited embedding_func from LightRAG instance")

                try:
                    # Ensure LightRAG storages are initialized
                    if (
                        not hasattr(self.lightrag, "_storages_status")
                        or self.lightrag._storages_status.name != "INITIALIZED"
                    ):
                        self.logger.info(
                            "Initializing storages for pre-provided LightRAG instance"
                        )
                        await self.lightrag.initialize_storages()
                        from lightrag.kg.shared_storage import (
                            initialize_pipeline_status,
                        )

                        await initialize_pipeline_status()

                    # Initialize parse cache if not already done
                    if self.parse_cache is None:
                        self.logger.info(
                            "Initializing parse cache for pre-provided LightRAG instance"
                        )
                        self.parse_cache = (
                            self.lightrag.key_string_value_json_storage_cls(
                                namespace="parse_cache",
                                workspace=self.lightrag.workspace,
                                global_config=self.lightrag.__dict__,
                                embedding_func=self.embedding_func,
                            )
                        )
                        await self.parse_cache.initialize()

                    if self.multimodal_status_cache is None:
                        self.logger.info(
                            "Initializing multimodal status cache for pre-provided LightRAG instance"
                        )
                        self.multimodal_status_cache = (
                            self.lightrag.key_string_value_json_storage_cls(
                                namespace="multimodal_status",
                                workspace=self.lightrag.workspace,
                                global_config=self.lightrag.__dict__,
                                embedding_func=self.embedding_func,
                            )
                        )
                        await self.multimodal_status_cache.initialize()

                    # Initialize processors if not already done
                    if not self.modal_processors:
                        await self._init_processors_via_builder()

                    return {"success": True}

                except Exception as e:
                    error_msg = (
                        f"Failed to initialize pre-provided LightRAG instance: {str(e)}"
                    )
                    self.logger.error(error_msg, exc_info=True)
                    return {"success": False, "error": error_msg}

            # Validate required functions for creating new LightRAG instance
            if self.llm_model_func is None:
                error_msg = "llm_model_func must be provided when LightRAG is not pre-initialized"
                self.logger.error(error_msg)
                return {"success": False, "error": error_msg}

            if self.embedding_func is None:
                error_msg = "embedding_func must be provided when LightRAG is not pre-initialized"
                self.logger.error(error_msg)
                return {"success": False, "error": error_msg}

            from lightrag.kg.shared_storage import initialize_pipeline_status

            # Prepare LightRAG initialization parameters
            lightrag_params = {
                "working_dir": self.working_dir,
                "llm_model_func": self.llm_model_func,
                "embedding_func": self.embedding_func,
            }

            # Merge user-provided lightrag_kwargs, which can override defaults
            lightrag_params.update(self.lightrag_kwargs)

            # Log the parameters being used for initialization (excluding sensitive data)
            log_params = {
                k: v
                for k, v in lightrag_params.items()
                if not callable(v)
                and k not in ["llm_model_kwargs", "vector_db_storage_cls_kwargs"]
            }
            self.logger.info(f"Initializing LightRAG with parameters: {log_params}")

            try:
                # Create LightRAG instance with merged parameters
                self.lightrag = LightRAG(**lightrag_params)
                await self.lightrag.initialize_storages()
                await initialize_pipeline_status()

                # Initialize parse cache storage using LightRAG's KV storage
                self.parse_cache = self.lightrag.key_string_value_json_storage_cls(
                    namespace="parse_cache",
                    workspace=self.lightrag.workspace,
                    global_config=self.lightrag.__dict__,
                    embedding_func=self.embedding_func,
                )
                await self.parse_cache.initialize()

                self.multimodal_status_cache = (
                    self.lightrag.key_string_value_json_storage_cls(
                        namespace="multimodal_status",
                        workspace=self.lightrag.workspace,
                        global_config=self.lightrag.__dict__,
                        embedding_func=self.embedding_func,
                    )
                )
                await self.multimodal_status_cache.initialize()

                # Initialize processors after LightRAG is ready
                await self._init_processors_via_builder()

                self.logger.info(
                    "LightRAG, parse cache, multimodal status cache, and multimodal processors initialized"
                )
                return {"success": True}

            except Exception as e:
                error_msg = f"Failed to initialize LightRAG instance: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Unexpected error during LightRAG initialization: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"success": False, "error": error_msg}

    async def finalize_storages(self):
        """Finalize all storages including parse cache and LightRAG storages

        This method should be called when shutting down to properly clean up resources
        and persist any cached data. It will finalize both the parse cache and LightRAG's
        internal storages.

        Example usage:
            try:
                rag_anything = RAGAnything(...)
                await rag_anything.process_file("document.pdf")
                # ... other operations ...
            finally:
                # Always finalize storages to clean up resources
                if rag_anything:
                    await rag_anything.finalize_storages()

        Note:
            - This method is automatically called in __del__ when the object is destroyed
            - Manual calling is recommended in production environments
            - All finalization tasks run concurrently for better performance
        """
        try:
            tasks = []

            # Finalize parse cache if it exists
            if self.parse_cache is not None:
                tasks.append(self.parse_cache.finalize())
                self.logger.debug("Scheduled parse cache finalization")

            if self.multimodal_status_cache is not None:
                tasks.append(self.multimodal_status_cache.finalize())
                self.logger.debug("Scheduled multimodal status cache finalization")

            # Finalize LightRAG storages if LightRAG is initialized
            if self.lightrag is not None:
                tasks.append(self.lightrag.finalize_storages())
                self.logger.debug("Scheduled LightRAG storages finalization")

            # Run all finalization tasks concurrently
            if tasks:
                await asyncio.gather(*tasks)
                self.logger.info("Successfully finalized all RAGAnything storages")
            else:
                self.logger.debug("No storages to finalize")

        except Exception as e:
            self.logger.error(f"Error during storage finalization: {e}")
            raise

    def check_parser_installation(self) -> bool:
        """
        Check if the configured parser is properly installed

        Returns:
            bool: True if the configured parser is properly installed
        """
        return self.doc_parser.check_installation()

    def verify_parser_installation_once(self) -> bool:
        if not self._parser_installation_checked:
            if not self.doc_parser.check_installation():
                raise RuntimeError(
                    f"Parser '{self.config.parser}' is not properly installed. "
                    "Please install it using pip install or uv pip install."
                )
            self._parser_installation_checked = True
            self.logger.info(f"Parser '{self.config.parser}' installation verified")
        return True

    def get_config_info(self) -> Dict[str, Any]:
        """Get current configuration information"""
        config_info = {
            "directory": {
                "working_dir": self.config.working_dir,
                "parser_output_dir": self.config.parser_output_dir,
            },
            "parsing": {
                "parser": self.config.parser,
                "parse_method": self.config.parse_method,
                "display_content_stats": self.config.display_content_stats,
            },
            "multimodal_processing": {
                "enable_image_processing": self.config.enable_image_processing,
                "enable_table_processing": self.config.enable_table_processing,
                "enable_equation_processing": self.config.enable_equation_processing,
                "enable_audio_processing": self.config.enable_audio_processing,
                "enable_video_processing": self.config.enable_video_processing,
            },
            "audio_processing": {
                "audio_asr_timeout": self.config.audio_asr_timeout,
                "max_parallel_asr": self.config.max_parallel_asr,
                "audio_chunk_token_size": self.config.audio_chunk_token_size,
                "min_asr_confidence": self.config.min_asr_confidence,
                "audio_summarize_batch_size": self.config.audio_summarize_batch_size,
                "audio_summarize_max_batches": self.config.audio_summarize_max_batches,
            },
            "context_extraction": {
                "context_window": self.config.context_window,
                "context_mode": self.config.context_mode,
                "max_context_tokens": self.config.max_context_tokens,
                "include_headers": self.config.include_headers,
                "include_captions": self.config.include_captions,
                "filter_content_types": self.config.context_filter_content_types,
            },
            "batch_processing": {
                "max_concurrent_files": self.config.max_concurrent_files,
                "supported_file_extensions": self.config.supported_file_extensions,
                "recursive_folder_processing": self.config.recursive_folder_processing,
            },
            "logging": {
                "note": "Logging fields have been removed - configure logging externally",
            },
        }

        # Add LightRAG configuration if available
        if self.lightrag_kwargs:
            # Filter out sensitive data and callable objects for display
            safe_kwargs = {
                k: v
                for k, v in self.lightrag_kwargs.items()
                if not callable(v)
                and k not in ["llm_model_kwargs", "vector_db_storage_cls_kwargs"]
            }
            config_info["lightrag_config"] = {
                "custom_parameters": safe_kwargs,
                "note": "LightRAG will be initialized with these additional parameters",
            }
        else:
            config_info["lightrag_config"] = {
                "custom_parameters": {},
                "note": "Using default LightRAG parameters",
            }

        return config_info

    def set_content_source_for_context(
        self, content_source, content_format: str = "auto"
    ):
        """Set content source for context extraction in all modal processors

        Args:
            content_source: Source content for context extraction (e.g., MinerU content list)
            content_format: Format of content source ("minerU", "text_chunks", "auto")
        """
        if not self.modal_processors:
            self.logger.warning(
                "Modal processors not initialized. Content source will be set when processors are created."
            )
            return

        for processor_name, processor in self.modal_processors.items():
            try:
                processor.set_content_source(content_source, content_format)
                self.logger.debug(f"Set content source for {processor_name} processor")
            except Exception as e:
                self.logger.error(
                    f"Failed to set content source for {processor_name}: {e}"
                )

        self.logger.info(
            f"Content source set for context extraction (format: {content_format})"
        )

    def update_context_config(self, **context_kwargs):
        """Update context extraction configuration

        Args:
            **context_kwargs: Context configuration parameters to update
                (context_window, context_mode, max_context_tokens, etc.)
        """
        # Update the main config
        for key, value in context_kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.debug(f"Updated context config: {key} = {value}")
            else:
                self.logger.warning(f"Unknown context config parameter: {key}")

        # Recreate context extractor with new config if processors are initialized
        if self.lightrag and self.modal_processors:
            try:
                self.context_extractor = self._create_context_extractor()
                # Update all processors with new context extractor
                for processor_name, processor in self.modal_processors.items():
                    processor.context_extractor = self.context_extractor

                self.logger.info(
                    "Context configuration updated and applied to all processors"
                )
                self.logger.info(
                    f"New context configuration: {self._create_context_config()}"
                )
            except Exception as e:
                self.logger.error(f"Failed to update context configuration: {e}")

    def get_processor_info(self) -> Dict[str, Any]:
        """Get processor information"""
        base_info = {
            "mineru_installed": MineruParser.check_installation(MineruParser()),
            "parser_installation": {
                parser_name: get_parser(parser_name).check_installation()
                for parser_name in SUPPORTED_PARSERS
            },
            "config": self.get_config_info(),
            "models": {
                "llm_model": "External function"
                if self.llm_model_func
                else "Not provided",
                "vision_model": "External function"
                if self.vision_model_func
                else "Not provided",
                "embedding_model": "External function"
                if self.embedding_func
                else "Not provided",
            },
        }

        if not self.modal_processors:
            base_info["status"] = "Not initialized"
            base_info["processors"] = {}
        else:
            base_info["status"] = "Initialized"
            base_info["processors"] = {}

            for proc_type, processor in self.modal_processors.items():
                base_info["processors"][proc_type] = {
                    "class": processor.__class__.__name__,
                    "supports": get_processor_supports(proc_type),
                    "enabled": True,
                }

        return base_info

    def _resolve_task_parser(self, name):
        """按 per-task parser 名解析解析器实例（带缓存）；名空/非法回退 self.doc_parser。"""
        name = (name or "").strip().lower()
        if not name:
            return self.doc_parser
        cached = self._task_parser_cache.get(name)
        if cached is not None:
            return cached
        try:
            from raganything.parsers import get_parser
            parser = get_parser(name)
        except Exception:
            self.logger.warning("Unknown per-task parser '%s', fallback to default", name)
            return self.doc_parser
        self._task_parser_cache[name] = parser
        return parser

    async def process_document_complete(
        self,
        file_path: str,
        file_name: Optional[str] = None,
        scheme_name: Optional[str] = None,
        cancel_event: Optional["asyncio.Event"] = None,
        force_reparse: bool = False,
        *,
        tenant_id: str = "",
        kb_id: str = "",
        doc_id: str = "",
        ctx: Optional[PipelineContext] = None,
        **kwargs,
    ) -> Optional[str]:
        """Process a document through the pipeline.

        Args:
            file_path: Path to the document file.
            file_name: Display name for the document.
            scheme_name: Optional scheme name for pipeline configuration.
            cancel_event: Optional asyncio.Event for cooperative cancellation.
            force_reparse: If True, skip parse cache and force full re-parse.
            tenant_id: [HTTP mode] Tenant identifier.
            kb_id: [HTTP mode] Knowledge base identifier.
            doc_id: [HTTP mode] Client-side document_id for file_source.
            ctx: [HTTP mode] Pre-built PipelineContext (overrides auto-build).

        Returns:
            doc_id on success, or None on failure (with error logged).
        """
        # ── HTTP mode: skip LightRAG init, use external :9621 ──────
        if self._http_mode:
            if ctx is None:
                ctx = PipelineContext(
                    file_path=str(file_path),
                    file_name=file_name or os.path.basename(file_path),
                    tenant_id=tenant_id,
                    kb_id=kb_id,
                    doc_id=doc_id,
                    cancel_event=cancel_event,
                    force_reparse=force_reparse,
                )
            ctx.started_at = time.time()

            # ── per-task effective config + parser（preset 链路）──
            # 在单例 config 基础上覆盖 preset 提供的字段（保留 working_dir 等默认）；
            # 选出 per-task parser 并注入其配置（如 mineru_online 的 token）。
            import dataclasses as _dc
            from raganything.config import RAGAnythingConfig as _RAGCfg
            _snap = getattr(ctx, "config_snapshot", None) or {}
            _fields = set(_RAGCfg.__dataclass_fields__)
            _overrides = {k: v for k, v in _snap.items() if k in _fields and not k.startswith("_")}
            eff_config = _dc.replace(self.config, **_overrides) if _overrides else self.config

            _parser_name = (getattr(ctx, "parser_type", "") or getattr(eff_config, "parser", "") or "")
            task_parser = self._resolve_task_parser(_parser_name)
            if _snap and hasattr(task_parser, "configure"):
                try:
                    task_parser.configure(**_snap)   # mineru_online token 等在此注入
                except Exception:
                    self.logger.warning("parser.configure failed for '%s'", _parser_name, exc_info=True)

            services = PipelineServices(
                config=eff_config,
                lightrag=None,
                doc_parser=task_parser,
                modal_processors=getattr(self, "modal_processors", {}),
                parse_cache=ParseCacheManager(self.parse_cache, eff_config) if self.parse_cache else None,
                doc_status_mgr=None,
                callback_manager=self.callback_manager,
                event_bus=self.event_bus,
                logger=self.logger,
                http_client=self.http_client,
            )
            result = await self.pipeline.execute(ctx, services)
            # Merge final context back: pipeline runs stages on internal ctx
            # copies (merge_context → dataclasses.replace produces NEW objects),
            # so scalar fields set by stages (counters, error, rebind of
            # pending_track_ids) do NOT reflect onto the caller's ctx unless
            # copied back here. Must run on BOTH success and failure so #5/#6
            # counters, error message and pending_track_ids survive a FAILED task
            # (KB reconciliation depends on them).
            if result.final_ctx is not None:
                final: PipelineContext = result.final_ctx
                ctx.content_list = final.content_list
                ctx.doc_id = final.doc_id
                ctx.multimodal_items = final.multimodal_items
                ctx.multimodal_results = final.multimodal_results
                ctx.collected_doc_ids = final.collected_doc_ids
                ctx.pending_track_ids = final.pending_track_ids
                # [jonex] #5/#6: propagate push-outcome counters + pipeline error
                ctx.total_chunk_count = final.total_chunk_count
                ctx.failed_chunk_count = final.failed_chunk_count
                ctx.timeout_chunk_count = final.timeout_chunk_count
                ctx.duplicated_chunk_count = final.duplicated_chunk_count
                ctx.total_pushed_count = final.total_pushed_count
                ctx.error = final.error
            ctx.completed_at = time.time()
            if not result.success:
                self.logger.error(f"HTTP pipeline failed: {result.error}")
                return None
            return ctx.doc_id or doc_id

        # ── Embedded mode: full LightRAG pipeline ──────────────────
        # Ensure LightRAG is initialized (including modal processors via builder)
        init_result = await self._ensure_lightrag_initialized()
        if not init_result or not init_result.get("success"):
            self.logger.error(
                f"LightRAG initialization failed: {(init_result or {}).get('error', 'unknown error')}"
            )
            return None

        # Ensure doc_status listener is registered on the event bus
        if self.event_bus is not None and not getattr(self, "_listeners_registered", False):
            doc_status_mgr = DocStatusManager(self.lightrag, self.config) if hasattr(self, "lightrag") else None
            if doc_status_mgr is not None:
                DocStatusListener(doc_status_mgr).register(self.event_bus)
                self._listeners_registered = True

        ctx = PipelineContext(
            file_path=str(file_path),
            file_name=file_name or os.path.basename(file_path),
            cancel_event=cancel_event,
            force_reparse=force_reparse,
        )
        services = PipelineServices(
            config=self.config,
            lightrag=self.lightrag,
            doc_parser=self.doc_parser,
            modal_processors=getattr(self, "modal_processors", {}),
            parse_cache=ParseCacheManager(self.parse_cache, self.config) if self.parse_cache else None,
            doc_status_mgr=DocStatusManager(self.lightrag, self.config) if hasattr(self, "lightrag") else None,
            callback_manager=self.callback_manager,
            event_bus=self.event_bus,
            logger=self.logger,
        )
        result = await self.pipeline.execute(ctx, services)
        if not result.success:
            self.logger.error(f"Pipeline failed: {result.error}")
            return None
        return result.doc_id

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
