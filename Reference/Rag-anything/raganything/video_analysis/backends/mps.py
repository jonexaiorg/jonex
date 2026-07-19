"""
Tencent Cloud MPS (Media Processing Service) video analysis backend.

Submits a ``VideoComprehension`` task via the MPS API, polls for
completion, and returns structured ``scenes`` + ``tags`` results.

Reference implementation: ``docs/old/material_views.py``
  - Task submission:      lines 2549–2583
  - Polling loop:         lines 2602–2712
  - JSON result parsing:  lines 2732–2756
  - Scenes & tags split:  lines 2911–2956
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from raganything.video_analysis import (
    VideoAnalysisBackend,
    VideoAnalysisResult,
    ValidationIssue,
    register_video_analysis_backend,
)

logger = logging.getLogger(__name__)


# ── Exceptions ──────────────────────────────────────────────────────────


class MPSBackendError(Exception):
    """Base exception for MPS backend errors."""


class MPSTaskError(MPSBackendError):
    """MPS task finished with a FAIL status or missing result."""


class MPSTimeoutError(MPSBackendError):
    """MPS task did not finish within the configured timeout."""


class MPSConfigError(MPSBackendError):
    """Missing or invalid MPS configuration."""


# ── Backend ─────────────────────────────────────────────────────────────


@register_video_analysis_backend()
class MPSVideoBackend(VideoAnalysisBackend):
    """Tencent Cloud MPS VideoComprehension backend.

    Required config fields (when ``video_analysis_binding="mps"``):
      - ``mps_secret_id``
      - ``mps_secret_key``
      - ``mps_cos_bucket``
      - ``mps_cos_region``

    Optional config fields with defaults:
      - ``mps_region`` (default ``"ap-guangzhou"``)
      - ``mps_definition`` (default ``33``)
      - ``mps_timeout`` (default ``600`` seconds)
      - ``mps_poll_interval`` (default ``3`` seconds)
      - ``mps_max_retries`` (default ``3``)
    """

    binding = "mps"

    def __init__(self, config):
        super().__init__(config)
        self._client = None
        self._default_prompt = self._load_default_prompt()

    # ── Default prompt loader ──────────────────────────────────────────

    def _load_default_prompt(self) -> str:
        """Load the prompt template JSON file and return the composed prompt.

        Falls back to a simple instruction if the file cannot be read.
        """
        category = getattr(self.config, "mps_prompt_category", "mps_video_understanding")
        json_path = (
            Path(__file__).parent.parent
            / "prompts"
            / f"{category}.json"
        )
        if not json_path.exists():
            logger.warning(
                "MPS prompt file not found: %s, using fallback prompt",
                json_path,
            )
            return (
                "Analyze this video and return a JSON object with 'scenes' "
                "(each with 'description', 'start_time', 'end_time') and "
                "'tags' (each with 'name', 'confidence', 'category'). "
                "Return ONLY valid JSON."
            )

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load MPS prompt %s: %s", json_path, exc)
            return "Analyze this video and return JSON with scenes and tags."

        system_prompt = data.get("system_prompt", "")
        user_prompt = data.get("user_prompt", "")
        # Replace {tag_library} placeholder with empty list if not configured
        tag_library = getattr(self.config, "mps_tag_library", "{}")
        composed = system_prompt.replace("{tag_library}", tag_library)
        if user_prompt:
            composed += "\n\n" + user_prompt.replace("{tag_library}", tag_library)
        logger.info("Loaded MPS prompt template: %s (v%s)", category, data.get("version", 1))
        return composed

    # ── Config validation ─────────────────────────────────────────────

    @classmethod
    def validate_config(cls, config) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        if not getattr(config, "mps_secret_id", None):
            issues.append(ValidationIssue(
                "error", "mps_secret_id",
                "Tencent Cloud SecretId is required for MPS backend",
            ))
        if not getattr(config, "mps_secret_key", None):
            issues.append(ValidationIssue(
                "error", "mps_secret_key",
                "Tencent Cloud SecretKey is required for MPS backend",
            ))
        if not getattr(config, "mps_cos_bucket", None):
            issues.append(ValidationIssue(
                "error", "mps_cos_bucket",
                "COS bucket name is required for MPS backend",
            ))
        if not getattr(config, "mps_cos_region", None):
            issues.append(ValidationIssue(
                "error", "mps_cos_region",
                "COS region is required for MPS backend",
            ))
        return issues

    # ── Client lazy init ──────────────────────────────────────────────

    def _ensure_client(self):
        if self._client is not None:
            return
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
                TencentCloudSDKException,
            )
            from tencentcloud.mps.v20190612 import mps_client
        except ImportError:
            raise MPSConfigError(
                "tencentcloud-sdk-python is not installed. "
                "Run: pip install tencentcloud-sdk-python"
            )

        secret_id = self.config.mps_secret_id
        secret_key = self.config.mps_secret_key
        region = getattr(self.config, "mps_region", "ap-guangzhou")

        cred = credential.Credential(secret_id, secret_key)
        self._client = mps_client.MpsClient(cred, region=region)

    # ── Main entry ───────────────────────────────────────────────────

    async def analyze_video(
        self,
        video_path: str,
        prompt: Optional[str] = None,
    ) -> VideoAnalysisResult:
        """Submit an MPS VideoComprehension task and wait for completion.

        Args:
            video_path: COS URL of the video file (e.g.
                ``https://{bucket}.cos.{region}.myqcloud.com/{key}``).
            prompt: Analysis prompt passed to MPS ``mvc.prompt``.
                Falls back to the default prompt from the JSON template
                when ``None``.

        Returns:
            Parsed :class:`VideoAnalysisResult` with scenes and tags.
        """
        self._ensure_client()

        # 1. Load prompt (use default if not provided)
        analysis_prompt = prompt if prompt is not None else self._default_prompt

        # 2. Extract COS object key from URL
        object_key = self._extract_cos_key(video_path)

        # 3. Submit task
        task_id = self._submit_task(object_key, analysis_prompt)

        # 4. Poll for result (async)
        raw_result = await self._poll_result(task_id)

        # 5. Parse JSON result
        return self._parse_result(raw_result)

    # ── COS key extraction ───────────────────────────────────────────

    @staticmethod
    def _extract_cos_key(video_url: str) -> str:
        """Extract the COS object key from a COS URL.

        Handles formats like:
          ``https://bucket.cos.region.myqcloud.com/path/to/video.mp4``
        """
        # Strip query string
        url = video_url.split("?")[0]
        # Find ".myqcloud.com/" and take everything after it
        marker = ".myqcloud.com/"
        idx = url.find(marker)
        if idx == -1:
            raise MPSBackendError(
                f"Cannot extract COS key from URL: {video_url} "
                f"(expected '.myqcloud.com/' in host)"
            )
        return url[idx + len(marker):]

    # ── Task submission ───────────────────────────────────────────────

    def _submit_task(self, object_key: str, prompt: str) -> str:
        """Build and submit ``ProcessMedia`` request.

        Reference: ``material_views.py`` lines 2554–2583.
        """
        from tencentcloud.mps.v20190612 import models

        bucket = self.config.mps_cos_bucket
        cos_region = self.config.mps_cos_region
        definition = getattr(self.config, "mps_definition", 33)

        request = models.ProcessMediaRequest()

        # Input: COS
        request.InputInfo = {
            "Type": "COS",
            "CosInputInfo": {
                "Bucket": bucket,
                "Region": cos_region,
                "Object": object_key,
            },
        }

        # Output: COS (same bucket)
        request.OutputStorage = {
            "Type": "COS",
            "CosOutputStorage": {
                "Bucket": bucket,
                "Region": cos_region,
            },
        }

        # AI Analysis Task: VideoComprehension (Definition=33)
        extended = json.dumps(
            {"mvc": {"mode": "video", "prompt": prompt}},
            ensure_ascii=False,
            separators=(",", ":"),
        )
        request.AiAnalysisTask = {
            "Definition": definition,
            "ExtendedParameter": extended,
        }
        request.TaskType = "Online"

        logger.info(
            "Submitting MPS ProcessMedia: bucket=%s key=%s definition=%d",
            bucket, object_key, definition,
        )
        response = self._client.ProcessMedia(request)
        task_id = response.TaskId
        logger.info("MPS task submitted: %s", task_id)
        return task_id

    # ── Polling ───────────────────────────────────────────────────────

    async def _poll_result(self, task_id: str) -> str:
        """Poll ``DescribeTaskDetail`` until completion or timeout.

        Reference: ``material_views.py`` lines 2602–2712.

        Returns:
            The raw ``VideoComprehensionAnalysisResult`` string.

        Raises:
            MPSTimeoutError: If the task does not finish in time.
            MPSTaskError: If the task fails or returns unexpected data.
        """
        from tencentcloud.mps.v20190612 import models

        timeout = getattr(self.config, "mps_timeout", 600)
        poll_interval = getattr(self.config, "mps_poll_interval", 3)
        max_retries = getattr(self.config, "mps_max_retries", 3)

        deadline = asyncio.get_event_loop().time() + timeout
        retry_count = 0

        while True:
            if asyncio.get_event_loop().time() > deadline:
                raise MPSTimeoutError(
                    f"MPS task {task_id} did not finish within {timeout}s"
                )

            try:
                detail_request = models.DescribeTaskDetailRequest()
                detail_request.TaskId = task_id
                response = self._client.DescribeTaskDetail(detail_request)
            except Exception as exc:
                retry_count += 1
                if retry_count > max_retries:
                    raise MPSBackendError(
                        f"MPS DescribeTaskDetail failed after "
                        f"{max_retries} retries: {exc}"
                    ) from exc
                logger.warning(
                    "DescribeTaskDetail error (retry %d/%d): %s",
                    retry_count, max_retries, exc,
                )
                await asyncio.sleep(poll_interval)
                continue

            # Reset retry counter on successful call
            retry_count = 0

            # Check task type
            if response.TaskType != "WorkflowTask":
                raise MPSTaskError(
                    f"Unexpected MPS task type: {response.TaskType} "
                    f"(expected 'WorkflowTask')"
                )

            status = response.Status

            # Extract VideoComprehension result set
            workflow_task = response.WorkflowTask
            ai_results = workflow_task.AiAnalysisResultSet or []
            filtered = [r for r in ai_results if r.Type == "VideoComprehension"]

            if not filtered:
                if status == "FINISH":
                    raise MPSTaskError(
                        f"MPS task finished but no VideoComprehension result: "
                        f"{workflow_task.Message}"
                    )
                # Still in progress
                await asyncio.sleep(poll_interval)
                continue

            vc_task = filtered[0].VideoComprehensionTask

            if vc_task.Status == "FAIL":
                raise MPSTaskError(
                    f"MPS VideoComprehension failed: {vc_task.Message}"
                )

            # Got the result
            if vc_task.Status == "SUCCESS" and vc_task.Output:
                raw = vc_task.Output.VideoComprehensionAnalysisResult
                if raw:
                    logger.info("MPS task %s completed successfully", task_id)
                    return raw

            # Still running
            logger.debug(
                "MPS task %s progress: %s", task_id, vc_task.Progress
            )
            await asyncio.sleep(poll_interval)

    # ── Result parsing ───────────────────────────────────────────────

    @staticmethod
    def _parse_result(raw: str) -> VideoAnalysisResult:
        """Parse the raw MPS JSON result string.

        Reference: ``material_views.py`` lines 2732–2756.

        The MPS response may wrap JSON in markdown code blocks.
        Tries, in order:
          1. `````json ... `````
          2. ````` ... `````
          3. ``{ ... }`` (first braced group)
          4. Whole string as JSON
        """
        cleaned = raw.strip()

        # 1. ```json ... ```
        m = re.search(r"```json\s*\n(.*?)\n```", cleaned, re.DOTALL)
        if m:
            cleaned = m.group(1).strip()
            logger.debug("MPS result: extracted ```json block")

        # 2. ``` ... ```
        if not _looks_like_json(cleaned):
            m = re.search(r"```\s*\n(.*?)\n```", cleaned, re.DOTALL)
            if m:
                cleaned = m.group(1).strip()
                logger.debug("MPS result: extracted ``` block")

        # 3. { ... }
        if not _looks_like_json(cleaned):
            m = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if m:
                cleaned = m.group(1).strip()
                logger.debug("MPS result: extracted braced JSON")

        # 4. Whole string
        if not _looks_like_json(cleaned):
            logger.warning(
                "MPS result does not look like JSON, using raw string"
            )

        try:
            obj = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise MPSBackendError(f"Failed to parse MPS result JSON: {exc}") from exc

        raw_scenes = obj.get("scenes")
        tags = obj.get("tags")

        # Normalise scenes: parse MPS time_range ("MM:SS-MM:SS")
        # into start_time / end_time (float seconds) for downstream.
        scenes = []
        if raw_scenes:
            for s in raw_scenes:
                scene = dict(s)
                time_range = scene.pop("time_range", None)
                if time_range:
                    parts = time_range.split("-")
                    if len(parts) == 2:
                        scene["start_time"] = _parse_mps_timestamp(parts[0])
                        scene["end_time"] = _parse_mps_timestamp(parts[1])
                    else:
                        scene["start_time"] = 0.0
                        scene["end_time"] = 0.0
                else:
                    scene["start_time"] = 0.0
                    scene["end_time"] = 0.0
                scenes.append(scene)

        # Use MPS-level summary if present, otherwise build from scenes/tags
        summary = obj.get("summary") or ""
        if not summary:
            summary_parts = []
            if scenes:
                summary_parts.append(f"{len(scenes)} scenes detected")
            if tags:
                tag_names = [
                    t.get("name") or t.get("tag") or str(t)
                    for t in (tags if isinstance(tags, list) else [tags])
                ]
                summary_parts.append(f"Tags: {', '.join(tag_names[:10])}")
            summary = "; ".join(summary_parts) if summary_parts else cleaned[:500]

        return VideoAnalysisResult(
            summary=summary,
            scenes=scenes,
            tags=tags,
            raw_json=raw,
            analysis_method="mps",
            metadata={
                "scenes_count": len(scenes) if scenes else 0,
                "tags_count": len(tags) if tags else 0,
            },
        )

    # ── Lifecycle ────────────────────────────────────────────────────

    def close(self) -> None:
        self._client = None


# ── Helper ──────────────────────────────────────────────────────────────


def _looks_like_json(text: str) -> bool:
    """Quick check whether *text* looks like a JSON object."""
    t = text.strip()
    return t.startswith("{") and t.endswith("}")


def _parse_mps_timestamp(ts: str) -> float:
    """Parse an MPS ``MM:SS`` or ``HH:MM:SS`` timestamp into seconds.

    Examples:
        "00:14"    -> 14.0
        "01:05"    -> 65.0
        "01:30:45" -> 5445.0
    """
    parts = list(reversed(ts.strip().split(":")))
    if not parts:
        return 0.0
    total = float(parts[0])  # seconds
    if len(parts) > 1:
        total += int(parts[1]) * 60  # minutes
    if len(parts) > 2:
        total += int(parts[2]) * 3600  # hours
    return total
