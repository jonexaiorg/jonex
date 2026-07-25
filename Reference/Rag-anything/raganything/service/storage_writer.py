"""StorageWriter — staging directories, atomic rename, symlink, task.yaml I/O."""
from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml

from raganything.service.path_utils import validate_path_component

_STORAGE_ROOT_ENV = "STORAGE_ROOT"
_DEFAULT_STORAGE_ROOT = "./mineru_storage"


class StorageWriter:
    """Manages the lifecycle of parsed artifacts on disk.

    Lifecycle::

        1. create_staging() → {root}/{tenant}/{doc_id}.staging.{timestamp}/
        2. Write files into staging (task.yaml, mineru/, video/)
        3. commit() → mv staging → versions/{timestamp}/ + symlink latest
        4. On error: staging dir can be cleaned up; existing data untouched.
    """

    def __init__(self, root: str | Path | None = None):
        if root is None:
            root = os.getenv(_STORAGE_ROOT_ENV, _DEFAULT_STORAGE_ROOT)
        self.root = Path(root)

    # ── Public API ───────────────────────────────────────────────────

    def create_staging(
        self, tenant_id: str, doc_id: str, timestamp: str,
    ) -> Path:
        """Create a staging directory for the task output.

        Returns path: ``{root}/{tenant}/{doc_id}.staging.{timestamp}/``
        The caller writes all files here, then calls ``commit()``.
        """
        validate_path_component(tenant_id, "tenant_id")
        validate_path_component(doc_id, "doc_id")
        validate_path_component(timestamp, "timestamp")

        staging_dir = self.root / tenant_id / f"{doc_id}.staging.{timestamp}"
        # Clean up leftover from a previous failed attempt
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=False)
        return staging_dir

    def write_task_yaml_atomic(self, filepath: Path, data: dict) -> None:
        """Write task.yaml atomically using tempfile + os.replace."""
        data.setdefault("version", 1)
        data.setdefault("updated_at", datetime.now(timezone.utc).isoformat())

        dir_name = filepath.parent
        fd, tmp_path = tempfile.mkstemp(
            dir=str(dir_name), suffix=".yaml.tmp",
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
            os.replace(tmp_path, str(filepath))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def update_task_yaml_atomic(
        self, filepath: Path, updater: Callable[[dict], None],
    ) -> None:
        """Read existing task.yaml, apply updater, write back atomically."""
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        updater(data)
        self.write_task_yaml_atomic(filepath, data)

    def commit(
        self, tenant_id: str, doc_id: str, timestamp: str,
    ) -> Path:
        """Move staging → versions/{timestamp}/ + update 'latest' symlink.

        Returns the final version directory path.
        """
        validate_path_component(tenant_id, "tenant_id")
        validate_path_component(doc_id, "doc_id")
        validate_path_component(timestamp, "timestamp")

        staging_dir = self.root / tenant_id / f"{doc_id}.staging.{timestamp}"
        if not staging_dir.exists():
            raise FileNotFoundError(f"Staging dir not found: {staging_dir}")

        doc_dir = self.root / tenant_id / doc_id
        versions_dir = doc_dir / "versions"
        final_dir = versions_dir / timestamp

        versions_dir.mkdir(parents=True, exist_ok=True)
        os.replace(str(staging_dir), str(final_dir))

        # Atomic symlink update: tmp_link → os.replace
        tmp_link = doc_dir / f"latest.tmp.{timestamp}"
        target_rel = f"versions/{timestamp}"
        if os.name == "nt":
            # Windows fallback: plain text marker
            with tempfile.NamedTemporaryFile(
                mode="w", dir=str(doc_dir), suffix=".latest.tmp",
                delete=False, encoding="utf-8",
            ) as f:
                f.write(f"{target_rel}\n")
            os.replace(f.name, str(doc_dir / "latest.txt"))
        else:
            tmp_link.symlink_to(target_rel)
            os.replace(str(tmp_link), str(doc_dir / "latest"))
        # Clean up tmp_link if os.replace failed to consume it
        if tmp_link.exists():
            tmp_link.unlink()

        return final_dir

    def cleanup_staging(self, tenant_id: str, doc_id: str) -> None:
        """Remove leftover staging directories for a doc (e.g. on startup)."""
        tenant_dir = self.root / tenant_id
        if not tenant_dir.exists():
            return
        for entry in tenant_dir.iterdir():
            if entry.name.startswith(f"{doc_id}.staging."):
                shutil.rmtree(entry)

    @staticmethod
    def build_storage_info(
        root: Path,
        tenant_id: str,
        doc_id: str,
        timestamp: str,
        asset_base_url: str,
        has_mineru: bool = False,
        has_video: bool = False,
    ) -> dict:
        """Build a StorageInfo-compatible dict for API/webhook responses."""
        relative_base = f"{tenant_id}/{doc_id}/versions/{timestamp}"
        info: dict = {
            "root": str(root),
            "asset_base_url": asset_base_url,
        }
        if has_mineru:
            info["mineru_dir"] = f"{relative_base}/mineru"
            info["latest_url"] = (
                f"{asset_base_url}/{tenant_id}/{doc_id}/latest/mineru"
            )
        if has_video:
            info["video_dir"] = f"{relative_base}/video"
            info["latest_url"] = (
                f"{asset_base_url}/{tenant_id}/{doc_id}/latest/video"
            )
        info.setdefault("latest_url",
                        f"{asset_base_url}/{tenant_id}/{doc_id}/latest")
        return info
