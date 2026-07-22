"""Video content processor for RAG-Anything.

Mirrors AsrModalProcessor in structure:
  1. Extract audio → ASR transcribe → segments
  2. Hybrid keyframe extraction (ffprobe scenes + time interval)
  3. VLM per-frame description (with retry + error taxonomy)
  4. Visual condensation (OCR-first, LLM fallback)
  5. Time alignment → exclusive ownership assignment
  6. MapReduce → entity extraction
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from bisect import bisect_left
from typing import Dict, List, Any, Optional, Tuple

from raganything.modalprocessors import BaseModalProcessor

logger = logging.getLogger(__name__)

VIDEO_ENTITY_TYPE_ENUM = frozenset({
    "meeting", "lecture", "presentation", "interview",
    "tutorial", "demo", "screencast", "vlog", "movie_clip",
    "documentary", "conversation", "unknown",
})

MAX_ENTITY_TRANSCRIPT_PREVIEW = 1000
MAX_OCR_CHARS = 120


class VideoModalProcessor(BaseModalProcessor):
    """Video content processor: ASR + keyframe extraction + VLM description."""

    def __init__(
        self,
        lightrag,
        modal_caption_func,
        vlm_model_func=None,
        asr_backend=None,
        config=None,
        tokenizer=None,
        context_extractor=None,
        image_transport=None,
    ):
        super().__init__(lightrag, modal_caption_func, context_extractor)
        self.vlm_model_func = vlm_model_func
        self.asr_backend = asr_backend
        self._config = config
        self.image_transport = image_transport
        if tokenizer:
            self.tokenizer = tokenizer

    # ── entry points ─────────────────────────────────

    async def process_multimodal_content(
        self, modal_content, content_type, file_path,
        item_info=None, batch_mode=False, doc_id=None, chunk_order_index=0,
    ) -> Tuple[str, Dict[str, Any], list]:
        """Individual processing entry. Delegates to generate_description_only.
        Multi-chunk generation happens in the batch pipeline."""
        enhanced_caption, entity_info = await self.generate_description_only(
            modal_content, content_type, item_info, None
        )
        return enhanced_caption, entity_info, []

    async def generate_description_only(
        self, modal_content, content_type, item_info=None, entity_name=None,
    ) -> Tuple[str, Dict[str, Any]]:
        """Main entry: extract audio → ASR → keyframes → VLM → time alignment → MapReduce."""
        video_path = modal_content.get("video_path")
        if not video_path:
            raise ValueError(f"No video_path in modal_content: {modal_content}")

        # 0a. Compute identifiers (three-layer separation)
        video_quick_hash = self._quick_video_hash(video_path)
        semantic_video_id = self._semantic_video_fingerprint(video_path)
        modal_content["_video_quick_hash"] = video_quick_hash
        modal_content["_video_source_id"] = semantic_video_id

        # 0b. Prepare output directories
        output_dir = self._prepare_output_dir(video_path)

        # 1. Extract audio → ASR transcribe → segments
        audio_path = self._extract_audio(video_path, output_dir)
        asr_result = {}
        audio_available = False
        if audio_path:
            try:
                asr_result = await self._transcribe_audio(audio_path)
                audio_available = bool(asr_result.get("transcript", "").strip())
            except Exception as e:
                logger.warning(f"Audio transcription failed for {video_path}: {e}")
                asr_result = {"segments": [], "transcript": "", "language": "unknown",
                              "duration": 0}
            finally:
                self._safe_remove(audio_path)

        # 2. Hybrid keyframe extraction
        keyframes = self._extract_keyframes(video_path, output_dir, semantic_video_id)

        try:
            # 2b. Upload frames to public URL transport
            prep = None
            if keyframes and self.image_transport:
                prep = await self.image_transport.prepare_urls(keyframes, semantic_video_id)
                keyframes = prep.frames

            # 3. VLM per-frame description (with capability-aware fallback)
            vlm_support = getattr(self.vlm_model_func, 'vlm_support', None)
            if keyframes and self.vlm_model_func:
                if prep is None:
                    # No transport → use local mode
                    if vlm_support and vlm_support.supports_base64:
                        keyframes = await self._describe_frames(keyframes)
                    elif vlm_support and vlm_support.supports_url:
                        logger.warning(
                            "ImageTransport not configured but VLM requires URL. "
                            "Visual analysis SKIPPED. Set COS_BUCKET/COS_APPID to enable.")
                    else:
                        keyframes = await self._describe_frames(keyframes)
                elif prep.transport_available:
                    keyframes = await self._describe_frames(keyframes)
                elif prep.fatal_error:
                    if vlm_support and vlm_support.supports_base64:
                        logger.warning(
                            f"ImageTransport fatal error ({prep.fatal_error}), "
                            f"falling back to base64.")
                        keyframes = await self._describe_frames(keyframes)
                    else:
                        logger.error(
                            f"ImageTransport fatal error ({prep.fatal_error}). "
                            f"Visual analysis SKIPPED.")
                else:
                    if vlm_support and vlm_support.supports_base64:
                        logger.warning(
                            "All frame uploads failed, falling back to base64.")
                        keyframes = await self._describe_frames(keyframes)
                    else:
                        logger.warning(
                            "All frame uploads failed and VLM requires URL. "
                            "Visual analysis SKIPPED.")
            elif keyframes and not self.vlm_model_func:
                logger.warning(
                    "vlm_model_func not provided; frame descriptions will be empty. "
                    "Set vlm_model_func in RAGAnything() to enable visual analysis."
                )

            # 4. Time alignment + visual condensation
            if audio_available:
                segments = self._segment_with_overlap(asr_result)
                segments = self._align_frames_to_segments(segments, keyframes)
            else:
                # Audio-less video: merge frame descriptions as pseudo-transcript
                pseudo_text = "\n".join(
                    f"[{f['frame_time']:.1f}s] {f.get('description', '')}"
                    for f in keyframes if f.get("description")
                ) if keyframes else "(no audio track, no keyframes)"
                # Use actual video duration, not asr_result (which is 0 for audio-less)
                video_duration = self._get_duration(video_path)
                if not video_duration:
                    video_duration = max(
                        (f.get("frame_time", 0) for f in keyframes), default=0.0
                    )
                segments = [{
                    "text": pseudo_text,
                    "start_time": 0.0,
                    "end_time": video_duration,
                    "segment_index": 0,
                    "relative_position": 0.0,
                    "source_segment_indices": [],
                    "speaker_labels": [],
                    "group_summary": "",
                    "frames": keyframes,
                }]

            # 4a. Visual condensation (OCR-first, LLM fallback)
            all_frames = []
            for seg in segments:
                all_frames.extend(seg.get("frames", []))
            if all_frames:
                all_frames = await self._condense_frame_descriptions(all_frames)

            # 5. MapReduce (transcript-only, frames only in leaf chunks)
            summary, entity_info = await self._recursive_mapreduce(
                segments, entity_name, item_info, video_path, asr_result,
            )

            # 5b. Entity uniqueness
            entity_info["video_source_id"] = semantic_video_id

            # 6. Store in modal_content for downstream chunk conversion
            modal_content["_audio_segments"] = segments
            modal_content["_asr_result"] = asr_result
            modal_content["_video_keyframes"] = keyframes
            modal_content["_audio_missing"] = not audio_available
            return summary, entity_info

        finally:
            if prep is not None and self.image_transport:
                try:
                    await self.image_transport.cleanup(keyframes)
                except Exception as e:
                    logger.warning(
                        f"ImageTransport cleanup failed (non-fatal): {e}")

    # ── utilities ─────────────────────────────────

    @staticmethod
    def _safe_remove(path) -> None:
        """Remove file if exists, ignore errors."""
        try:
            if path and Path(path).exists():
                Path(path).unlink()
        except Exception:
            pass

    @staticmethod
    def _get_audio_timeout(video_path: str, min_timeout: int = 120,
                           factor: float = 3.0) -> int:
        """Dynamic ffmpeg timeout based on video duration."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of",
                 "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True, timeout=30)
            duration = float(result.stdout.strip())
            return max(min_timeout, int(duration * factor))
        except Exception:
            return 300

    def _quick_video_hash(self, video_path: str) -> str:
        """Physical file identity: xxhash64 of head+tail+mid."""
        import xxhash
        size = os.path.getsize(video_path)
        with open(video_path, "rb") as f:
            head = f.read(65536)
            f.seek(-65536, 2) if size > 131072 else f.seek(0)
            tail = f.read(65536)
            mid = None
            if size > 262144:
                f.seek(size // 2)
                mid = f.read(256)
        hasher = xxhash.xxh64()
        hasher.update(str(size).encode())
        hasher.update(head)
        hasher.update(tail)
        if mid:
            hasher.update(mid)
        return hasher.hexdigest()[:16]

    def _semantic_video_fingerprint(self, video_path: str) -> str:
        """Semantic video identity: stable across re-encodes."""
        try:
            import imagehash
            from PIL import Image
            probe = subprocess.run([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "json", video_path,
            ], capture_output=True, text=True, timeout=30)
            duration = float(json.loads(probe.stdout)
                           .get("format", {}).get("duration", 0))
            phashes = []
            for pct in [0.1, 0.5, 0.9]:
                ts = duration * pct
                with tempfile.NamedTemporaryFile(suffix=".jpg",
                                                 delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    subprocess.run([
                        "ffmpeg", "-accurate_seek", "-ss", str(ts),
                        "-i", video_path,
                        "-frames:v", "1", "-q:v", "2", "-y", tmp_path,
                    ], check=True, capture_output=True, timeout=30)
                    phashes.append(str(imagehash.phash(
                        Image.open(tmp_path))))
                finally:
                    self._safe_remove(tmp_path)
            raw = f"dur:{duration}:phash:{':'.join(phashes)}"
            return "sf-" + hashlib.sha256(raw.encode()).hexdigest()[:16]
        except ImportError:
            return self._quick_video_hash(video_path)

    def _extract_audio(self, video_path: str, output_dir) -> Optional[str]:
        """Extract audio track via FFmpeg. Returns None if no audio track."""
        audio_path = Path(output_dir) / "audio.wav"
        try:
            subprocess.run([
                "ffmpeg", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1",
                "-y", str(audio_path),
            ], check=True, capture_output=True,
               timeout=self._get_audio_timeout(video_path))
            return str(audio_path)
        except subprocess.CalledProcessError as e:
            logger.warning(f"No audio track or extraction failed: {e}")
            self._safe_remove(audio_path)
            return None
        except FileNotFoundError:
            logger.error("FFmpeg not found; audio extraction skipped")
            return None

    async def _transcribe_audio(self, audio_path: str) -> dict:
        """Transcribe via ASR backend."""
        return await asyncio.to_thread(
            self.asr_backend.transcribe, audio_path)

    def _prepare_output_dir(self, video_path: str) -> Path:
        """Content-hash-based output dir for temp artifacts.
        Directory: <parser_output_dir>/video_cache/<video_quick_hash>/
        NOTE: cache dir (evictable). Frame files go to video_frames/ (persistent)."""
        quick_hash = self._quick_video_hash(video_path)
        base = (Path(self._config.parser_output_dir) if self._config
                else Path("."))
        out = base / "video_cache" / quick_hash
        out.mkdir(parents=True, exist_ok=True)
        return out

    def _extract_keyframes(self, video_path, output_dir,
                           semantic_video_id) -> list[dict]:
        """Keyframe extraction dispatcher.

        Algorithm selection (config.video_keyframe_algorithm):
        - 'interval': uniform time-spacing (fastest, most predictable)
        - 'scene':    ffprobe scene-change detection (content-aware)
        - 'iframes':  I-frame positions from encoding metadata (natural cut points)
        - 'hybrid':   I-frames + interval gap-fill (cheap metadata + guaranteed coverage)
        """
        algorithm = getattr(self._config, "video_keyframe_algorithm", "interval")
        interval = getattr(self._config, "video_keyframe_interval", 10)
        max_frames = getattr(self._config, "video_max_frames", 50)

        base = (Path(self._config.parser_output_dir) if self._config
                else Path("."))
        frames_dir = base / "video_frames" / semantic_video_id
        frames_dir.mkdir(parents=True, exist_ok=True)

        duration = self._get_duration(video_path)
        if duration is None or duration <= 0:
            logger.warning(f"Cannot determine duration for {video_path}")
            return []

        min_frames = max(1, int(duration / interval))

        # ── Route to algorithm ──
        if algorithm == "scene":
            timestamps = self._scene_timestamps(video_path, duration)
        elif algorithm == "iframes":
            timestamps = self._iframe_timestamps(video_path)
        elif algorithm == "hybrid":
            timestamps = self._hybrid_timestamps(video_path, duration, interval)
        else:
            timestamps = []

        # Fallback: if algorithm produced too few, use interval
        if len(timestamps) < min_frames:
            timestamps = list(self._interval_timestamps(duration, interval))
            if timestamps and timestamps[0] > 0.5:
                timestamps.insert(0, 0.0)

        # Cap to max_frames via uniform sampling
        timestamps = self._cap_timestamps(timestamps, max_frames)

        # Extract actual frame images via ffmpeg
        return self._extract_frame_images(timestamps, frames_dir,
                                          semantic_video_id, video_path)

    # ── timestamp sources ────────────────────────────────

    def _scene_timestamps(self, video_path: str, duration: float) -> list[float]:
        """Scene-change detection via ffprobe select filter."""
        try:
            return self._detect_scenes(video_path, duration)
        except Exception as e:
            logger.warning(
                f"Scene detection failed for {video_path}, "
                f"falling back to interval: {e}")
            return []

    def _iframe_timestamps(self, video_path: str) -> list[float]:
        """Extract I-frame (keyframe) positions from encoding metadata.

        I-frames are natural cut-points placed by the video encoder.
        Metadata-only query — no pixel decoding, very fast.

        ffprobe output (default format, two lines per frame):
            pts_time=0.000000
            pict_type=I
            pts_time=0.033333
            pict_type=P
        """
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error",
                 "-select_streams", "v",
                 "-show_entries", "frame=pts_time,pict_type",
                 "-of", "default=noprint_wrappers=1",
                 video_path
                 ],
                capture_output=True, text=True,
                timeout=60,
            )
            timestamps = []
            current_time: float | None = None
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.startswith("pts_time="):
                    try:
                        current_time = float(line.split("=", 1)[1])
                    except ValueError:
                        current_time = None
                elif line == "pict_type=I" and current_time is not None:
                    timestamps.append(current_time)
                    current_time = None
            return timestamps
        except subprocess.TimeoutExpired:
            logger.warning("I-frame detection timed out")
            return []
        except Exception as e:
            logger.warning(f"I-frame detection failed: {e}")
            return []

    def _hybrid_timestamps(self, video_path: str, duration: float,
                           interval: int) -> list[float]:
        """I-frames + interval gap-fill.

        1. Get I-frame positions (natural cut points, metadata-only, cheap)
        2. Sort + deduplicate
        3. For gaps larger than interval*2, fill with interval-spaced frames
        4. Always include t=0 if first frame is > 0.5s away

        Results: good cut-point coverage + guaranteed density in long static scenes.
        """
        iframes = self._iframe_timestamps(video_path)
        if not iframes:
            return []

        iframes = sorted(set(round(t, 2) for t in iframes))

        # Merge nearby I-frames (< 0.5s apart = same scene)
        merged = [iframes[0]]
        for t in iframes[1:]:
            if t - merged[-1] >= 0.5:
                merged.append(t)

        # Gap fill: insert interval frames in large gaps
        filled = [merged[0]]
        for i in range(1, len(merged)):
            gap = merged[i] - merged[i - 1]
            if gap > interval * 2:
                # Insert N intermediate frames
                n_fill = int(gap / interval) - 1
                for j in range(1, n_fill + 1):
                    filled.append(round(merged[i - 1] + j * interval, 1))
            filled.append(merged[i])

        # Ensure t=0 is included
        if filled and filled[0] > 0.5:
            filled.insert(0, 0.0)

        return filled

    # ── helpers ──────────────────────────────────────────

    @staticmethod
    def _cap_timestamps(timestamps: list[float], max_frames: int) -> list[float]:
        """Limit timestamps to max_frames via uniform downsampling."""
        if not timestamps:
            return []
        if max_frames <= 1:
            return [timestamps[0]]
        if len(timestamps) > max_frames:
            indices = {
                int(i * (len(timestamps) - 1) / (max_frames - 1))
                for i in range(max_frames)
            }
            return [timestamps[i] for i in sorted(indices)]
        return timestamps

    def _extract_frame_images(self, timestamps: list[float],
                              frames_dir: Path, semantic_video_id: str,
                              video_path) -> list[dict]:
        """Extract actual .jpg frames via ffmpeg -ss. Dedup by time bucket."""
        seen = set()
        frames: list[dict] = []
        prefix_len = len("sf-")
        id_prefix = (semantic_video_id[prefix_len:prefix_len + 10]
                     if len(semantic_video_id) > prefix_len
                     else semantic_video_id)

        for idx, ts in enumerate(timestamps):
            ts_rounded = round(ts, 3)
            bucket = round(ts, 1)
            if bucket in seen:
                continue
            seen.add(bucket)

            frame_filename = f"frame_{idx:04d}.jpg"
            frame_path = frames_dir / frame_filename
            frame_id = f"{id_prefix}:{ts_rounded:.3f}"

            if frame_path.exists():
                frames.append({
                    "frame_id": frame_id,
                    "frame_path": str(frame_path),
                    "frame_time": ts_rounded,
                })
                continue

            try:
                subprocess.run([
                    "ffmpeg", "-accurate_seek", "-ss", str(ts),
                    "-i", video_path,
                    "-frames:v", "1", "-q:v", "2",
                    "-y", str(frame_path),
                ], check=True, capture_output=True, timeout=30)
                frames.append({
                    "frame_id": frame_id,
                    "frame_path": str(frame_path),
                    "frame_time": ts_rounded,
                })
            except subprocess.CalledProcessError as e:
                logger.debug(f"Frame extraction at {ts}s failed: {e}")
                continue

        algorithm = getattr(self._config, "video_keyframe_algorithm", "interval")
        duration = self._get_duration(video_path)
        logger.info(
            f"Extracted {len(frames)} keyframes for {Path(video_path).name} "
            f"(duration={duration:.0f}s, algorithm={algorithm})")
        return frames

    def _get_duration(self, video_path: str) -> float | None:
        """Get video duration in seconds via ffprobe."""
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration", "-of",
                 "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except Exception as e:
            logger.debug(f"Failed to get duration: {e}")
            return None

    def _detect_scenes(self, video_path: str, duration: float,
                       scene_threshold: float = 0.4) -> list[float]:
        """Detect scene change timestamps via ffprobe.

        Uses the 'select' filter with scene detection. Falls back to empty list
        if the filter is not available on this ffmpeg build.
        """
        try:
            result = subprocess.run(
                ["ffprobe", "-f", "lavfi",
                 "-i", f"movie={video_path},select='gt(scene,{scene_threshold})'",
                 "-show_entries", "frame=pkt_pts_time",
                 "-of", "compact=p=0", "-v", "quiet"],
                capture_output=True, text=True,
                timeout=max(30, int(duration * 0.5)),
            )
            timestamps = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    try:
                        ts = float(line)
                        if 0 <= ts <= duration:
                            timestamps.append(ts)
                    except ValueError:
                        continue
            return timestamps
        except subprocess.TimeoutExpired:
            logger.warning("Scene detection timed out")
            return []
        except subprocess.CalledProcessError:
            # Filter not available on this ffmpeg build
            return []
        except FileNotFoundError:
            logger.error("FFmpeg not found; keyframe extraction disabled")
            return []

    @staticmethod
    def _interval_timestamps(duration: float, interval: float) -> list[float]:
        """Generate evenly-spaced timestamps."""
        return [i * interval for i in range(1, int(duration / interval) + 1)]

    # ── VLM description ─────────────────────────────────

    async def _describe_frames(self, frames: list[dict]) -> list[dict]:
        """Call VLM for each frame with retry + error taxonomy."""
        if self.vlm_model_func is None:
            raise RuntimeError(
                "VideoModalProcessor requires vlm_model_func. "
                "Pass vlm_model_func to RAGAnything()."
            )
        semaphore = asyncio.Semaphore(
            getattr(self._config, "max_parallel_vlm", 2)
        )

        # Inject temporal context for enhanced prompts
        frames_sorted = sorted(frames, key=lambda f: f.get("frame_time", 0))
        for i, f in enumerate(frames_sorted):
            f["_prev_time"] = (frames_sorted[i-1]["frame_time"]
                               if i > 0 else None)
            f["_next_time"] = (frames_sorted[i+1]["frame_time"]
                               if i < len(frames_sorted) - 1 else None)

        async def describe_one(frame: dict) -> dict:
            async with semaphore:
                for attempt in range(3):
                    try:
                        prompt = self._build_frame_prompt(frame)
                        timeout = getattr(self._config, "vlm_timeout", 60)
                        vlm_support = getattr(self.vlm_model_func, 'vlm_support', None)
                        upload_info = frame.get('upload')
                        frame_path = frame.get('frame_path', '')

                        if upload_info and upload_info.get('url'):
                            image_source = upload_info['url']
                        elif (vlm_support is None or vlm_support.supports_base64):
                            image_source = frame_path
                        else:
                            logger.debug(
                                f"Skipping frame at {frame.get('frame_time', 0)}s: "
                                f"VLM requires URL but none available")
                            frame["description"] = ""
                            frame["vlm_error"] = True
                            return frame

                        description = await asyncio.wait_for(
                            self.vlm_model_func(image_source, prompt),
                            timeout=timeout,
                        )
                        frame["description"] = description
                        frame["vlm_model"] = getattr(
                            self.vlm_model_func, "__name__", "vlm")
                        frame["vlm_error"] = False

                        # Parse OCR/SCENE from structured VLM output
                        parsed = self._parse_vlm_output(description)
                        if parsed:
                            frame["ocr_text"] = parsed.get("ocr", "")
                            frame["scene_description"] = parsed.get(
                                "scene", description)
                        else:
                            frame["ocr_text"] = ""
                            frame["scene_description"] = description
                        return frame
                    except Exception as e:
                        retryable = self._is_retryable_vlm_error(e)
                        if not retryable:
                            logger.error(
                                f"VLM non-retryable error for "
                                f"{frame['frame_path']}: {e}")
                            frame["description"] = ""
                            frame["ocr_text"] = ""
                            frame["vlm_error"] = True
                            return frame
                        if attempt < 2:
                            wait = 2 ** attempt
                            logger.warning(
                                f"VLM retry {attempt+1} for "
                                f"{frame['frame_path']}: {e}")
                            await asyncio.sleep(wait)
                        else:
                            logger.error(
                                f"VLM failed after 3 retries for "
                                f"{frame['frame_path']}: {e}")
                            frame["description"] = ""
                            frame["ocr_text"] = ""
                            frame["vlm_model"] = ""
                            frame["vlm_error"] = True
                            return frame

        tasks = [describe_one(f) for f in frames]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"VLM fatal error for frame "
                    f"{frames[i].get('frame_path', '?')}: {result}")
                frames[i]["description"] = ""
                frames[i]["ocr_text"] = ""
                frames[i]["vlm_error"] = True
        return frames

    def _build_frame_prompt(self, frame: dict) -> str:
        """Build VLM prompt with OCR/scene separation."""
        if getattr(self._config, "video_vlm_contextual_prompt", False):
            prev_time = frame.get("_prev_time", None)
            next_time = frame.get("_next_time", None)
            prev_str = (f"前一个关键帧时间：{prev_time}。"
                        if prev_time else "")
            next_str = (f"后一个关键帧时间：{next_time}。"
                        if next_time else "")
            return (
                f"这是视频 {frame['frame_time']:.1f}s 处的关键帧。"
                f"{prev_str}{next_str}\n\n"
                f"请分离输出以下两部分，用 ===OCR=== 和 ===SCENE=== 分隔：\n\n"
                f"===OCR===\n"
                f"精确提取画面中所有可见文字（代码、标题、数字、标签），不遗漏、不转写。\n"
                f"如无文字则输出 [无]。\n\n"
                f"===SCENE===\n"
                f"描述画面主体：人物身份、动作、图表类型、物体。\n"
                f"如可明显观察到与相邻帧的变化，再描述变化；否则只描述当前画面。\n"
                f"禁止推断连续动作或事件因果。"
            )
        return (
            "请详细描述这张图片，分离输出以下两部分，"
            "用 ===OCR=== 和 ===SCENE=== 分隔：\n\n"
            "===OCR===\n"
            "精确提取画面中所有可见文字。如无文字则输出 [无]。\n\n"
            "===SCENE===\n"
            "描述画面主体。"
        )

    # ── VLM output parsing & retry ────────────────────────────────

    def _parse_vlm_output(self, raw: str) -> dict | None:
        """Parse OCR/SCENE from structured VLM response."""
        if not raw:
            return None

        ocr_match = re.search(
            r'===OCR===\s*\n(.*?)(?:===|$)', raw, re.DOTALL)
        scene_match = re.search(
            r'===SCENE===\s*\n(.*?)(?:===|$)', raw, re.DOTALL)

        if ocr_match or scene_match:
            return {
                "ocr": ocr_match.group(1).strip() if ocr_match else "",
                "scene": (scene_match.group(1).strip()
                          if scene_match else raw),
            }

        ocr_candidates = re.findall(
            r'[\d]{2,4}[xX×][\d]{2,4}|[\d]+%|'
            r'[A-Z][a-z]+ [A-Z][a-z]+|[\d.,]+ [A-Z]{2,}',
            raw
        )
        if ocr_candidates:
            return {"ocr": "; ".join(ocr_candidates[:10]), "scene": raw}

        return {"ocr": "", "scene": raw}

    def _is_retryable_vlm_error(self, exc: Exception) -> bool:
        """Classify VLM errors: transient (retry) vs permanent (fail)."""
        err = str(exc).lower()

        non_retryable = [
            "invalid", "bad request", "400", "401", "403", "404",
            "auth", "permission", "not found", "unsupported",
            "api key", "unauthorized",
        ]
        if any(x in err for x in non_retryable):
            return False

        retryable = [
            "timeout", "rate limit", "too many", "429",
            "500", "502", "503", "504",
            "service unavailable", "internal server",
            "connection", "reset", "temporary",
        ]
        if any(x in err for x in retryable):
            return True

        return True  # conservative: retry unknown errors

    # ── visual condensation ─────────────────────────────────

    async def _condense_frame_descriptions(
            self, frames: list[dict]) -> list[dict]:
        """OCR-first semantic condensation."""
        for frame in frames:
            raw = frame.get("description", "")
            if not raw:
                continue

            ocr = frame.get("ocr_text", "").strip()
            if ocr and len(ocr) > 5:
                ocr_lines = [l.strip() for l in ocr.split("\n")
                             if l.strip()]
                salient_lines = [
                    l for l in ocr_lines
                    if not re.match(r'^[\d{}\-:/\s]{3,}$', l)
                    and not (len(l) < 3 and l.isupper())
                    and not l.startswith(
                        ("Menu", "File", "Edit", "View"))
                ]
                condensed = "; ".join(salient_lines)[:MAX_OCR_CHARS]
                frame["condensed"] = (condensed if condensed
                                      else ocr[:MAX_OCR_CHARS])
            else:
                condensed = await self._condense_single(raw)
                frame["condensed"] = condensed

            # Extractive layer
            extractive_terms = set()
            if ocr:
                for term in re.split(r"[,\s;:。，；：、]+", ocr):
                    term = term.strip().lower()
                    if len(term) > 2 and not term.isspace():
                        extractive_terms.add(term)
            if frame.get("scene_description"):
                scene_terms = re.findall(
                    r"[A-Za-z0-9_一-鿿]+",
                    frame["scene_description"]
                )
                extractive_terms.update(
                    t for t in scene_terms if len(t) > 2)
            frame["extractive_terms"] = sorted(extractive_terms)
        return frames

    async def _condense_single(self, raw: str) -> str:
        """One-shot LLM condensation."""
        prompt = (
            "Condense this visual description into one concise line "
            "(≤30 words). Preserve key entities, numbers, and text. "
            "Omit visual details (colors, positions, clothing).\n\n"
            f"Raw: {raw}\nCondensed:"
        )
        result = await self.modal_caption_func(
            prompt, system_prompt="", max_tokens=64)
        return result.strip() or raw[:120]

    # ── segment chunking & frame alignment ─────────────────────

    def _segment_with_overlap(self, asr_result: dict) -> list[dict]:
        """Merge ASR segments into chunks with 1-segment overlap.
        Uses tokenizer for accurate sizing."""
        token_size = getattr(
            self._config, "video_chunk_token_size", 600)
        raw_segments = asr_result.get("segments", [])
        if not raw_segments:
            return []

        chunks = []
        i = 0
        while i < len(raw_segments):
            chunk_segs = []
            token_count = 0
            prev_i = i
            while i < len(raw_segments) and token_count < token_size:
                seg = raw_segments[i]
                chunk_segs.append(seg)
                text = seg.get("text", "")
                if self.tokenizer:
                    token_count += len(self.tokenizer.encode(text))
                else:
                    token_count += len(text) // 3
                i += 1
            # 1-segment overlap for next chunk
            if i < len(raw_segments):
                OVERLAP_SEGMENTS = 1
                i = max(prev_i + 1, i - OVERLAP_SEGMENTS)

            start = chunk_segs[0]["start"]
            end = chunk_segs[-1]["end"]
            duration = asr_result.get("duration", 1)
            chunks.append({
                "text": " ".join(
                    s.get("text", "") for s in chunk_segs),
                "start_time": start,
                "end_time": end,
                "segment_index": len(chunks),
                "relative_position": (
                    min(1.0, end / duration) if duration > 0 else 0),
                "source_segment_indices": [
                    s.get("segment_index", s.get("id", si))
                    for si, s in enumerate(chunk_segs)
                ],
                "speaker_labels": list({
                    s.get("speaker_label") for s in chunk_segs
                    if s.get("speaker_label")
                }),
                "group_summary": "",
            })
        return chunks

    def _align_frames_to_segments(self, segments,
                                  keyframes) -> list[dict]:
        """Exclusive ownership assignment. Each frame belongs to exactly
        one segment: the one whose midpoint is closest.
        O(log S) per frame via bisect."""
        if not keyframes:
            return segments

        midpoints = [
            (s["start_time"] + s["end_time"]) / 2 for s in segments
        ]

        # Step 1: assign each frame to its owner segment
        for f in keyframes:
            frame_time = f.get("frame_time", 0)
            insert = bisect_left(midpoints, frame_time)
            if insert == 0:
                f["owner_segment"] = 0
            elif insert >= len(segments):
                f["owner_segment"] = len(segments) - 1
            else:
                before = midpoints[insert - 1]
                after = midpoints[insert]
                f["owner_segment"] = (
                    insert - 1
                    if (frame_time - before) < (after - frame_time)
                    else insert
                )

        # Step 2: populate segments with ONLY owned frames
        for i, seg in enumerate(segments):
            seg["frames"] = [
                f for f in keyframes
                if f.get("owner_segment", 0) == i
            ]

        return segments

    # ── MapReduce ─────────────────────────────────

    async def _recursive_mapreduce(
        self, segments, entity_name, item_info, source_path, asr_result,
    ) -> Tuple[str, Dict[str, Any]]:
        """Recursive MapReduce: batch summarize → reduce → global synthesis.
        Transcript-only for group summaries. Frames only in leaf chunks."""
        from raganything.prompt import PROMPTS

        batch_size = getattr(
            self._config, "video_summarize_batch_size", 8)
        max_batches = getattr(
            self._config, "video_summarize_max_batches", 20)
        duration = asr_result.get("duration", 0)
        language = asr_result.get("language", "unknown")
        keyframe_count = len(asr_result.get("segments", []))
        file_name = Path(source_path).name

        # Batch summarize segments (transcript-only)
        limit = min(len(segments), batch_size * max_batches)
        batches = []
        for i in range(0, limit, batch_size):
            batch = segments[i:i+batch_size]
            batches.append(batch)

        summaries = []
        for bi, batch in enumerate(batches):
            text = "\n".join(
                f"[{s['start_time']:.0f}s-{s['end_time']:.0f}s] "
                f"{s.get('text', '')}"
                for s in batch
            )
            prompt = PROMPTS["video_group_summary_prompt"].format(
                file_name=file_name,
                start_time=batch[0]["start_time"],
                end_time=batch[-1]["end_time"],
                text=text,
            )
            try:
                result = await self.modal_caption_func(
                    prompt, system_prompt="", max_tokens=128)
                summaries.append(result.strip())
            except Exception as e:
                logger.warning(f"Batch summary {bi} failed: {e}")
                summaries.append("")

        # Recursive reduce
        while len(summaries) > 1:
            new_summaries = []
            for i in range(0, len(summaries), batch_size):
                batch = summaries[i:i+batch_size]
                prompt = PROMPTS["video_reduce_prompt"].format(
                    batch_index=i//batch_size + 1,
                    total_batches=((len(summaries) + batch_size - 1)
                                   // batch_size),
                    summaries="\n".join(batch),
                )
                try:
                    result = await self.modal_caption_func(
                        prompt, system_prompt="", max_tokens=128)
                    new_summaries.append(result.strip())
                except Exception as e:
                    logger.warning(f"Reduce batch failed: {e}")
                    new_summaries.append("")
            summaries = new_summaries

        reduced_summary = summaries[0] if summaries else ""

        # Global synthesis
        prompt = PROMPTS["video_global_prompt"].format(
            entity_name=entity_name or file_name,
            type_enum=", ".join(sorted(VIDEO_ENTITY_TYPE_ENUM)),
            file_name=file_name,
            duration=f"{duration:.0f}",
            language=language,
            keyframe_count=keyframe_count,
            reduced_summary=reduced_summary,
            context="",
        )

        try:
            result = await self.modal_caption_func(
                prompt, system_prompt="", max_tokens=256)
            parsed = json.loads(result.strip())
        except Exception:
            parsed = {
                "detailed_description": reduced_summary,
                "entity_info": {
                    "entity_name": entity_name or file_name,
                    "entity_type": "unknown",
                    "summary": reduced_summary[:200],
                }
            }

        desc = parsed.get("detailed_description", reduced_summary)
        entity = parsed.get("entity_info", {})

        video_sha256 = asr_result.get("audio_sha256", "") or ""
        entity["chunk_count"] = len(segments)
        entity["transcript_preview"] = asr_result.get(
            "transcript", "")[:MAX_ENTITY_TRANSCRIPT_PREVIEW]
        entity["audio_sha256"] = video_sha256
        entity["audio_source_id"] = video_sha256[:12]

        if entity.get("entity_type", "") not in VIDEO_ENTITY_TYPE_ENUM:
            entity["entity_type"] = "unknown"

        return desc, entity
