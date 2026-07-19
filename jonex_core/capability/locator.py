#!/usr/bin/python3



from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Optional

from jonex_core.common import get_logger

logger = get_logger("capability.locator")





class CapabilityMode(str, Enum):


    LOCAL = "local"
    REMOTE = "remote"
    MOCK = "mock"


@dataclass
class CapabilitySpec:


    capability_id: str
    mode: CapabilityMode = CapabilityMode.LOCAL
    endpoint: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)







_DEFAULT_SPECS: Dict[str, CapabilitySpec] = {
    "atomic.llm.qwen.v1":      CapabilitySpec("atomic.llm.qwen.v1",      CapabilityMode.LOCAL),
    "atomic.vector.milvus.v1": CapabilitySpec("atomic.vector.milvus.v1", CapabilityMode.LOCAL),
    "atomic.audio.asr.v1":     CapabilitySpec("atomic.audio.asr.v1",     CapabilityMode.LOCAL),
}





class CapabilityLocator:


    def __init__(self, manifest_path: Optional[str] = None):
        self._specs: Dict[str, CapabilitySpec] = dict(_DEFAULT_SPECS)
        self._manifest_path: Optional[Path] = None
        self._load_manifest(manifest_path)


    def get_spec(self, capability_id: str) -> CapabilitySpec:

        spec = self._specs.get(capability_id)
        if spec is None:
            logger.debug(
                f"capability_runtime does not declare {capability_id}; falling back to the LOCAL default"
            )
            spec = CapabilitySpec(capability_id=capability_id, mode=CapabilityMode.LOCAL)
            self._specs[capability_id] = spec
        return spec

    def is_local(self, capability_id: str) -> bool:
        return self.get_spec(capability_id).mode == CapabilityMode.LOCAL

    def is_remote(self, capability_id: str) -> bool:
        return self.get_spec(capability_id).mode == CapabilityMode.REMOTE

    def list_specs(self) -> Dict[str, CapabilitySpec]:
        return dict(self._specs)

    def reload(self, manifest_path: Optional[str] = None) -> None:

        self._specs = dict(_DEFAULT_SPECS)
        self._load_manifest(manifest_path or (str(self._manifest_path) if self._manifest_path else None))


    def _load_manifest(self, manifest_path: Optional[str]) -> None:
        path = self._resolve_manifest_path(manifest_path)
        if path is None:
            logger.info("No capability_runtime manifest found; using built-in defaults (all LOCAL)")
            return

        try:
            import yaml
        except ImportError as e:
            logger.warning(f"PyYAML is not installed; cannot load {path}: {e}; using the default manifest")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
        except OSError as e:
            logger.warning(f"Reading {path} failed: {e}; using the default manifest")
            return

        atomic_section = raw.get("atomic") or {}
        for short_id, cfg in atomic_section.items():
            full_id = self._normalize_atomic_id(short_id)
            spec = self._build_spec(full_id, cfg or {})
            self._specs[full_id] = spec
            logger.info(
                f"Loaded capability specification: {full_id} -> mode={spec.mode.value}"
                + (f", endpoint={spec.endpoint}" if spec.endpoint else "")
            )


        for section in ("domain", "business"):
            for full_id, cfg in (raw.get(section) or {}).items():
                spec = self._build_spec(full_id, cfg or {})
                self._specs[full_id] = spec
                logger.info(
                    f"Loaded capability specification: {full_id} -> mode={spec.mode.value}"
                    + (f", endpoint={spec.endpoint}" if spec.endpoint else "")
                )

        self._manifest_path = path

    @staticmethod
    def _normalize_atomic_id(short_id: str) -> str:

        if short_id.startswith("atomic."):
            return short_id if short_id.count(".") >= 3 else f"{short_id}.v1"
        return f"atomic.{short_id}.v1" if short_id.count(".") == 1 else f"atomic.{short_id}"

    @staticmethod
    def _build_spec(full_id: str, cfg: Dict[str, Any]) -> CapabilitySpec:
        mode_str = (cfg.get("mode") or "local").lower()
        try:
            mode = CapabilityMode(mode_str)
        except ValueError:
            logger.warning(f"Unknown mode={mode_str}; {full_id} is falling back to LOCAL")
            mode = CapabilityMode.LOCAL

        endpoint = cfg.get("endpoint")
        if mode == CapabilityMode.REMOTE:

            endpoint = _expand_env(endpoint) if endpoint else os.getenv("SIDECAR_URL")

        options = cfg.get("options") or {}
        return CapabilitySpec(
            capability_id=full_id,
            mode=mode,
            endpoint=endpoint,
            options=options,
        )

    @staticmethod
    def _resolve_manifest_path(manifest_path: Optional[str]) -> Optional[Path]:
        candidates = []
        if manifest_path:
            candidates.append(Path(manifest_path))
        env_path = os.getenv("CAPABILITY_RUNTIME_FILE")
        if env_path:
            candidates.append(Path(env_path))

        candidates.append(Path.cwd() / "capability_runtime.yaml")

        for p in candidates:
            if p and p.is_file():
                return p
        return None


def _expand_env(value: str) -> str:

    import re

    def repl(match: "re.Match[str]") -> str:
        token = match.group(1)
        if ":-" in token:
            name, default = token.split(":-", 1)
            return os.getenv(name, default)
        return os.getenv(token, "")

    return re.sub(r"\$\{([^}]+)\}", repl, value)





_locator_lock = RLock()
_locator_instance: Optional[CapabilityLocator] = None


def get_locator() -> CapabilityLocator:

    global _locator_instance
    if _locator_instance is None:
        with _locator_lock:
            if _locator_instance is None:
                _locator_instance = CapabilityLocator()
    return _locator_instance


def reset_locator() -> None:

    global _locator_instance
    with _locator_lock:
        _locator_instance = None
