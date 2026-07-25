"""
Config resolver — inline/yaml/preset → resolved RAGAnythingConfig.

Three modes (Spec §7):
  - inline: use request body fields directly
  - yaml:    load from yaml_path, merge request body as overrides
  - preset:  load from config/presets/{name}.yaml, merge request body as overrides

After resolving user-facing params, loads the profile (Spec §7 step 2-5)
to produce a complete RAGAnythingConfig.
"""

from __future__ import annotations

import os
import copy
from pathlib import Path
from typing import Any, Optional

import yaml

from raganything.config import RAGAnythingConfig
from raganything.service.models import CreateTaskRequest, TaskMode


class ConfigResolveError(Exception):
    """Raised when config resolution fails."""


class ConfigResolver:
    def __init__(self, profiles_dir: str = "config/profiles", presets_dir: str = "config/presets"):
        self._profiles_dir = Path(profiles_dir)
        self._presets_dir = Path(presets_dir)

    # ── Public API ────────────────────────────────────────────────────

    def resolve(
        self, req: CreateTaskRequest,
        tenant_id: str = "", kb_id: str = "",
    ) -> dict[str, Any]:
        """Resolve a CreateTaskRequest into a config snapshot dict.

        Returns a dict suitable for:
          1. Feeding to RAGAnythingConfig(**snapshot)
          2. Storing as task.config_snapshot

        Preset lookup order: global → {tenant}/{kb}/presets/ (deep merge).
        """
        base = self._load_base_config(req, tenant_id=tenant_id, kb_id=kb_id)
        overrides = self._extract_overrides(req)
        merged = self._deep_merge(base, overrides)

        # [jonex] RAG_PARSER 环境变量作为运维级硬覆盖：优先级 > preset YAML > request overrides，
        # 确保 deploy/.env 的解析器选择不会被 preset 或前端配置意外覆盖。
        env_parser = os.getenv("RAG_PARSER", "").strip()
        if env_parser:
            merged["parser"] = env_parser

        self._validate(merged)
        return merged

    def resolve_to_rag_config(self, req: CreateTaskRequest) -> RAGAnythingConfig:
        """Resolve and return a RAGAnythingConfig instance."""
        snapshot = self.resolve(req)
        return self._snapshot_to_config(snapshot)

    # ── Mode dispatch ─────────────────────────────────────────────────

    # Field name mapping: user-facing → RAGAnythingConfig
    _FIELD_MAP: dict[str, str | None] = {
        "llm": "llm_model",
        "embedding": "embedding_model",
        "vision": "vision_model",
        "vlm": "vlm_model_name",
        "asr": None,  # handled separately: "engine:model" → asr_binding + asr_model
        "parser": "parser",
        "modalities": "modalities",
        "output_dir": "parser_output_dir",
        "profile": "profile",
        "lightrag_url": "lightrag_url",
        "webhook_url": "webhook_url",
        "video_max_frames": "video_max_frames",
        "video_keyframe_interval": "video_keyframe_interval",
        # Model connection overrides (passthrough — consumed by ModelFactory)
        "llm_host": "llm_host",
        "llm_api_key": "llm_api_key",
        "vlm_host": "vlm_host",
        "vlm_api_key": "vlm_api_key",
        "embedding_host": "embedding_host",
        "embedding_api_key": "embedding_api_key",
    }

    def _load_base_config(
        self, req: CreateTaskRequest, tenant_id: str = "", kb_id: str = "",
    ) -> dict:
        if req.mode == TaskMode.INLINE:
            return self._req_to_config_dict(req)
        elif req.mode == TaskMode.YAML:
            raw = self._load_yaml(req.yaml_path)
            return self._normalize_keys(raw)
        elif req.mode == TaskMode.PRESET:
            raw = self._load_preset(req.preset, tenant_id=tenant_id, kb_id=kb_id)
            return self._normalize_keys(raw)
        raise ConfigResolveError(f"Unknown mode: {req.mode}")

    def _req_to_config_dict(self, req: CreateTaskRequest) -> dict:
        """Convert a CreateTaskRequest into a normalized config dict."""
        base: dict[str, Any] = {}
        for req_key, config_key in self._FIELD_MAP.items():
            val = getattr(req, req_key, None)
            if val is not None:
                if config_key:
                    base[config_key] = val
                else:
                    base.update(self._parse_asr(val))

        self._apply_modalities(base, req.modalities or [])
        return base

    def _normalize_keys(self, raw: dict) -> dict:
        """Normalize user-facing keys to RAGAnythingConfig keys."""
        result: dict[str, Any] = {}
        for req_key, config_key in self._FIELD_MAP.items():
            val = raw.get(req_key)
            if val is not None:
                if config_key:
                    result[config_key] = val
                else:
                    result.update(self._parse_asr(str(val)))
        # modalities
        mods = raw.get("modalities", [])
        self._apply_modalities(result, mods)
        # passthrough unrecognized keys
        for k, v in raw.items():
            if k not in self._FIELD_MAP and k != "modalities":
                result[k] = v
        return result

    @staticmethod
    def _deep_merge(base: dict, overlay: dict) -> dict:
        """Deep merge overlay into base. Overlay values take precedence.
        Nested dicts are merged recursively; lists and scalars are replaced."""
        result = copy.deepcopy(base)
        for key, value in overlay.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = ConfigResolver._deep_merge(result[key], value)
            else:
                result[key] = copy.deepcopy(value)
        return result

    @staticmethod
    def _apply_modalities(base: dict, mods: list[str]) -> None:
        base["enable_image_processing"] = "image" in mods
        base["enable_table_processing"] = "table" in mods
        base["enable_equation_processing"] = "equation" in mods
        base["enable_audio_processing"] = "audio" in mods
        base["enable_video_processing"] = "video" in mods

    def _parse_asr(self, asr_spec: str) -> dict:
        """Parse 'engine:model' into asr_binding + asr_model."""
        if ":" in asr_spec:
            engine, model = asr_spec.split(":", 1)
            return {"asr_binding": engine.strip(), "asr_model": model.strip()}
        return {"asr_binding": asr_spec.strip(), "asr_model": ""}

    def _extract_overrides(self, req: CreateTaskRequest) -> dict:
        """For yaml/preset modes, extract request body fields as normalized overrides.

        Only includes fields explicitly set by the caller (not Pydantic defaults).
        This prevents e.g. the default ``modalities=["video","audio"]`` from
        overriding a preset's ``modalities: [audio]``.
        """
        req_dict = self._req_to_config_dict(req)  # reuse normalization
        # Drop mode/file_path/yaml_path/preset — these are routing keys, not config
        for key in ("mode", "file_path", "yaml_path", "preset"):
            req_dict.pop(key, None)
        # Also drop modality flags derived from the request's *default* modalities
        # if modalities was not explicitly set by the caller
        fields_set = getattr(req, "model_fields_set", None) or getattr(req, "__fields_set__", set())
        if "modalities" not in fields_set:
            for key in ("modalities", "enable_video_processing", "enable_audio_processing",
                        "enable_image_processing", "enable_table_processing",
                        "enable_equation_processing"):
                req_dict.pop(key, None)
        return req_dict

    # ── YAML / Preset loading ─────────────────────────────────────────

    def _load_yaml(self, yaml_path: str | None) -> dict:
        if not yaml_path:
            raise ConfigResolveError("yaml_path is required for mode=yaml")
        path = Path(yaml_path)
        if not path.exists():
            raise ConfigResolveError(f"YAML config not found: {yaml_path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ConfigResolveError(f"Invalid YAML config: {yaml_path}")
        # Support both flat and nested {config: {...}} format
        return data.get("config", data)

    def _load_preset(
        self, preset_name: str | None,
        tenant_id: str = "", kb_id: str = "",
    ) -> dict:
        if not preset_name:
            raise ConfigResolveError("preset name is required for mode=preset")

        # 1. Load global default
        yaml_path = self._presets_dir / f"{preset_name}.yaml"
        if not yaml_path.exists():
            raise ConfigResolveError(f"Preset not found: {preset_name}")
        result = self._load_yaml(str(yaml_path))

        # 2. Load tenant/kb overlay if present (deep merge)
        if tenant_id and kb_id:
            tenant_preset_dir = (
                self._presets_dir.parent / tenant_id / kb_id / "presets"
            )
            tenant_path = tenant_preset_dir / f"{preset_name}.yaml"
            if tenant_path.exists():
                tenant_overlay = self._load_yaml(str(tenant_path))
                result = self._deep_merge(result, tenant_overlay)

        return result

    # ── Profile loading ───────────────────────────────────────────────

    def _load_profile(self, profile_name: str | None) -> dict:
        """Load profile files and return merged config overrides."""
        if not profile_name:
            return {}
        profile_dir = self._profiles_dir / profile_name
        if not profile_dir.is_dir():
            return {}  # graceful degradation

        result: dict[str, Any] = {}

        # models.env → model_id → binding/host mapping
        models_env = profile_dir / "models.env"
        if models_env.exists():
            result["_models"] = self._parse_models_env(models_env)

        # secrets.env → binding → api_key
        secrets_env = profile_dir / "secrets.env"
        if secrets_env.exists():
            result["_secrets"] = self._parse_dotenv(secrets_env)

        # endpoints.toml → default hosts
        endpoints_toml = profile_dir / "endpoints.toml"
        if endpoints_toml.exists():
            result["_endpoints"] = self._load_toml_safe(endpoints_toml)

        # audio.toml / video.toml / parser.toml → advanced params
        for toml_file in ("audio.toml", "video.toml", "parser.toml"):
            path = profile_dir / toml_file
            if path.exists():
                result.update(self._load_toml_safe(path))

        return result

    @staticmethod
    def _parse_models_env(path: Path) -> dict[str, dict]:
        """Parse models.env lines: model_id = binding://host?dim=N"""
        result: dict[str, dict] = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                # Parse: binding://host?param=value
                binding = val
                host = ""
                params: dict[str, str] = {}
                if "://" in val:
                    binding, rest = val.split("://", 1)
                    if "?" in rest:
                        host, qs = rest.split("?", 1)
                        params = dict(p.split("=") for p in qs.split("&") if "=" in p)
                    else:
                        host = rest
                result[key] = {"binding": binding, "host": host, **params}
        return result

    @staticmethod
    def _parse_dotenv(path: Path) -> dict[str, str]:
        result: dict[str, str] = {}
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                result[key.strip()] = val.strip()
        return result

    @staticmethod
    def _load_toml_safe(path: Path) -> dict:
        """Load TOML if available, else fallback to empty dict."""
        try:
            import tomllib  # Python 3.11+
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return {}
        with open(path, "rb") as f:
            return tomllib.load(f)

    # ── Validation ─────────────────────────────────────────────────────

    @staticmethod
    def _validate(config: dict) -> None:
        required = ["file_path"]
        for key in required:
            if not config.get(key):
                pass  # file_path is in the request, not merged config

    # ── Conversion ─────────────────────────────────────────────────────

    @staticmethod
    def _snapshot_to_config(snapshot: dict) -> RAGAnythingConfig:
        """Convert a resolved snapshot dict to RAGAnythingConfig.

        Filters out internal keys (_models, _secrets, _endpoints) and
        maps snapshot keys to RAGAnythingConfig field names.
        """
        config_fields = {
            field.name for field in RAGAnythingConfig.__dataclass_fields__.values()
        }
        filtered = {
            k: v for k, v in snapshot.items()
            if not k.startswith("_") and k in config_fields
        }
        return RAGAnythingConfig(**filtered)

    # ── Sanitization ───────────────────────────────────────────────────

    SENSITIVE_KEYS = {"api_key", "secret", "token", "password"}

    @classmethod
    def sanitize_snapshot(cls, snapshot: dict) -> dict:
        """Mask sensitive fields in a config snapshot.

        api_key/secret/token fields → '****'.  Operates recursively.
        """
        result = copy.deepcopy(snapshot)
        cls._sanitize_recursive(result)
        return result

    @classmethod
    def _sanitize_recursive(cls, obj: Any) -> None:
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_KEYS):
                    if isinstance(obj[key], str) and obj[key]:
                        obj[key] = "****"
                else:
                    cls._sanitize_recursive(obj[key])
        elif isinstance(obj, list):
            for item in obj:
                cls._sanitize_recursive(item)
