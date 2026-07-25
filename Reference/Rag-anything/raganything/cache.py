"""Parse cache management for document parsing results."""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from raganything.utils import filter_parser_kwargs

logger = logging.getLogger(__name__)


class ParseCacheManager:
    """Cache manager for document parsing results.

    Wraps a KV-store (``parse_cache``) with file-mtime and config-version
    invalidation logic so that re-parsing an unchanged file returns the
    cached result.
    """

    def __init__(self, parse_cache: Any, config: Any) -> None:
        self._parse_cache = parse_cache
        self._config = config

    # ── public api ─────────────────────────────────────────────────────

    @staticmethod
    def generate_cache_key(
        file_path: Path,
        parse_method: Optional[str] = None,
        config: Optional[Any] = None,
        parser_name: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a deterministic cache key from file path, mtime and parsing config."""
        mtime = file_path.stat().st_mtime
        parser_name = parser_name or (getattr(config, "parser", None) if config else None)
        method = parse_method or (getattr(config, "parse_method", None) if config else None)

        config_dict: Dict[str, Any] = {
            "file_path": str(file_path.absolute()),
            "mtime": mtime,
            "parser": parser_name,
            "parse_method": method,
        }
        relevant = filter_parser_kwargs(kwargs)
        config_dict.update(relevant)

        config_str = json.dumps(config_dict, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()

    async def get_cached_result(
        self,
        cache_key: str,
        file_path: Path,
        parse_method: Optional[str] = None,
        parser_name: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[Tuple[List[Dict[str, Any]], str]]:
        """Return ``(content_list, doc_id)`` from cache, or *None* on miss/stale."""
        if self._parse_cache is None:
            return None

        try:
            cached_data = await self._parse_cache.get_by_id(cache_key)
            if not cached_data:
                return None

            current_mtime = file_path.stat().st_mtime
            if current_mtime != cached_data.get("mtime", 0):
                logger.debug(f"Cache invalid — file modified: {cache_key}")
                return None

            cached_config = cached_data.get("parse_config", {})
            current_config: Dict[str, Any] = {
                "parser": parser_name or getattr(self._config, "parser", None),
                "parse_method": parse_method or getattr(self._config, "parse_method", None),
            }
            relevant = filter_parser_kwargs(kwargs)
            current_config.update(relevant)

            if cached_config != current_config:
                logger.debug(f"Cache invalid — config changed: {cache_key}")
                return None

            content_list = cached_data.get("content_list", [])
            doc_id = cached_data.get("doc_id")
            if content_list and doc_id:
                logger.debug(f"Valid cache hit: {cache_key}")
                return content_list, doc_id

            logger.debug(f"Cache incomplete: {cache_key}")
            return None

        except Exception as e:
            logger.warning(f"Error reading parse cache: {e}")
            return None

    async def store_cached_result(
        self,
        cache_key: str,
        content_list: List[Dict[str, Any]],
        doc_id: str,
        file_path: Path,
        parse_method: Optional[str] = None,
        parser_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Persist a parsing result to the cache."""
        if self._parse_cache is None:
            return

        try:
            file_mtime = file_path.stat().st_mtime
            parse_config: Dict[str, Any] = {
                "parser": parser_name or getattr(self._config, "parser", None),
                "parse_method": parse_method or getattr(self._config, "parse_method", None),
            }
            relevant = filter_parser_kwargs(kwargs)
            parse_config.update(relevant)

            cache_data = {
                cache_key: {
                    "content_list": content_list,
                    "doc_id": doc_id,
                    "mtime": file_mtime,
                    "parse_config": parse_config,
                    "cached_at": time.time(),
                    "cache_version": "1.0",
                }
            }
            await self._parse_cache.upsert(cache_data)
            await self._parse_cache.index_done_callback()
            logger.info(f"Cached parsing result: {cache_key}")
        except Exception as e:
            logger.warning(f"Error writing parse cache: {e}")
