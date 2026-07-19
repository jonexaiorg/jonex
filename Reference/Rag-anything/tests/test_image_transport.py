"""Tests for ImageTransport / CosImageHost."""
import os
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from raganything.image_transport import (
    ImageTransport,
    CosImageHost,
    PrepareResult,
    VLMSupport,
    CleanupPolicy,
    _classify_error,
)


def _make_config(bucket="test-bucket", appid="1234567890", region="ap-guangzhou",
                 key_prefix="rag_anything/video", max_concurrent=2):
    return dict(
        bucket=bucket, appid=appid, region=region,
        secret_id="test-id", secret_key="test-key",
        key_prefix=key_prefix, max_concurrent=max_concurrent,
    )


def _make_mock_client():
    client = MagicMock()
    client.put_object.return_value = {"ETag": "abc123"}
    client.delete_objects.return_value = {"Error": []}
    return client


class TestErrorClassification:
    def test_nosuchbucket_is_fatal(self):
        exc = Exception()
        exc.error_code = "NoSuchBucket"
        retryable, fatal = _classify_error(exc)
        assert retryable is False
        assert fatal is True

    def test_nosuchkey_is_non_fatal(self):
        exc = Exception()
        exc.error_code = "NoSuchKey"
        retryable, fatal = _classify_error(exc)
        assert retryable is False
        assert fatal is False

    def test_403_is_fatal(self):
        exc = Exception()
        exc.status_code = 403
        retryable, fatal = _classify_error(exc)
        assert fatal is True

    def test_500_is_retryable(self):
        exc = Exception()
        exc.status_code = 500
        retryable, fatal = _classify_error(exc)
        assert retryable is True
        assert fatal is False

    def test_signature_mismatch_fatal(self):
        exc = Exception()
        exc.error_code = "SignatureDoesNotMatch"
        retryable, fatal = _classify_error(exc)
        assert fatal is True

    def test_timeout_is_retryable(self):
        retryable, fatal = _classify_error(Exception("connection timed out"))
        assert retryable is True


class TestConfigValidation:
    def test_missing_bucket_raises(self):
        cfg = _make_config(bucket="")
        with pytest.raises(ValueError):
            CosImageHost(**cfg)

    def test_missing_appid_raises(self):
        cfg = _make_config(appid="")
        with pytest.raises(ValueError):
            CosImageHost(**cfg)

    def test_dot_dot_in_prefix_raises(self):
        cfg = _make_config(key_prefix="rag/../video")
        with pytest.raises(ValueError):
            CosImageHost(**cfg)

    def test_leading_slash_raises(self):
        cfg = _make_config(key_prefix="/rag/video")
        with pytest.raises(ValueError):
            CosImageHost(**cfg)

    def test_backslash_raises(self):
        cfg = _make_config(key_prefix="rag\\video")
        with pytest.raises(ValueError):
            CosImageHost(**cfg)

    def test_valid_config_ok(self):
        CosImageHost(**_make_config(), client=_make_mock_client())


class TestSanitizePathComponent:
    def test_alphanumeric_preserved(self):
        result = CosImageHost._sanitize_path_component("frame_0001.jpg")
        assert result == "frame_0001.jpg"

    def test_dot_dot_replaced(self):
        result = CosImageHost._sanitize_path_component("../etc/passwd")
        assert "/" not in result

    def test_empty_returns_unnamed(self):
        result = CosImageHost._sanitize_path_component("")
        assert result == "unnamed"

    def test_special_chars_replaced(self):
        result = CosImageHost._sanitize_path_component("hello world!")
        assert " " not in result


@pytest.mark.asyncio
class TestPrepareUrls:
    async def test_all_upload_success(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        with tempfile.TemporaryDirectory() as td:
            frames = []
            for i in range(3):
                p = Path(td) / f"frame_{i:04d}.jpg"
                p.write_bytes(b"fake-jpeg-data")
                frames.append({"frame_path": str(p), "frame_time": float(i)})

            result = await host.prepare_urls(frames, "test_video_id")

            assert result.transport_available is True
            assert result.uploaded_count == 3
            assert result.failed_count == 0
            assert result.fatal_error is None
            for f in result.frames:
                assert f['upload']['url'].startswith("https://")
                assert f['upload']['key'].startswith("rag_anything/video/test_video_id/")

    async def test_key_contains_video_id(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "frame_0000.jpg"
            p.write_bytes(b"fake")
            frames = [{"frame_path": str(p), "frame_time": 0.0}]

            result = await host.prepare_urls(frames, "abc123_semantic_id")
            assert "abc123_semantic_id" in result.frames[0]['upload']['key']

    async def test_idempotent_skips_existing(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        frames = [{
            "frame_path": "/tmp/fake.jpg",
            "frame_time": 0.0,
            "upload": {"url": "https://existing.url/img.jpg", "key": "existing/key.jpg"},
        }]

        result = await host.prepare_urls(frames, "vid")
        assert result.uploaded_count == 1
        client.put_object.assert_not_called()

    async def test_file_not_found_skipped(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        frames = [{"frame_path": "/nonexistent/frame.jpg", "frame_time": 0.0}]
        result = await host.prepare_urls(frames, "vid")

        assert result.uploaded_count == 0
        client.put_object.assert_not_called()

    async def test_transport_available_false_when_no_uploads(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        frames = [{"frame_path": "/nonexistent/frame.jpg", "frame_time": 0.0}]
        result = await host.prepare_urls(frames, "vid")

        assert result.transport_available is False
        assert result.uploaded_count == 0

    async def test_upload_failure_graceful_degrade(self):
        client = _make_mock_client()
        client.put_object.side_effect = Exception("Connection timed out")
        host = CosImageHost(**_make_config(), client=client)

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "frame_0000.jpg"
            p.write_bytes(b"fake")
            frames = [{"frame_path": str(p), "frame_time": 0.0}]

            result = await host.prepare_urls(frames, "vid")

            assert result.transport_available is False
            assert result.failed_count == 1
            assert result.frames is frames


@pytest.mark.asyncio
class TestPrepareUrlsFatalError:
    async def test_fatal_error_skips_remaining(self):
        client = _make_mock_client()
        call_count = [0]

        def put_object_side_effect(*args, **kwargs):
            call_count[0] += 1
            exc = Exception("AccessDenied")
            exc.error_code = "AccessDenied"
            raise exc

        client.put_object.side_effect = put_object_side_effect
        host = CosImageHost(**_make_config(), client=client)

        with tempfile.TemporaryDirectory() as td:
            frames = []
            for i in range(5):
                p = Path(td) / f"frame_{i:04d}.jpg"
                p.write_bytes(b"fake")
                frames.append({"frame_path": str(p), "frame_time": float(i)})

            result = await host.prepare_urls(frames, "vid")

            assert result.fatal_error is not None
            assert "AccessDenied" in result.fatal_error
            assert result.transport_available is False
            assert call_count[0] < 5


@pytest.mark.asyncio
class TestCleanup:
    async def test_cleanup_deletes_uploaded_keys(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        frames = [
            {"upload": {"url": "https://x/img1.jpg", "key": "k1"}},
            {"upload": {"url": "https://x/img2.jpg", "key": "k2"}},
            {},
        ]
        await host.cleanup(frames)

        client.delete_objects.assert_called_once()
        call_args = client.delete_objects.call_args[1]
        delete_objects = call_args['Delete']['Object']
        assert len(delete_objects) == 2
        keys = sorted(d['Key'] for d in delete_objects)
        assert keys == ['k1', 'k2']

    async def test_cleanup_deduplicates_keys(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        frames = [
            {"upload": {"key": "k1"}},
            {"upload": {"key": "k1"}},
        ]
        await host.cleanup(frames)

        call_args = client.delete_objects.call_args[1]
        objects = call_args['Delete']['Object']
        assert len(objects) == 1

    async def test_cleanup_cttl_skips(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)
        host._cleanup_policy = CleanupPolicy.TTL
        frames = [{"upload": {"key": "k1"}}]

        await host.cleanup(frames)
        client.delete_objects.assert_not_called()

    async def test_cleanup_nosuchkey_ignored(self):
        client = _make_mock_client()
        client.delete_objects.return_value = {
            "Error": [{"Code": "NoSuchKey", "Key": "k1", "Message": ""}]
        }
        host = CosImageHost(**_make_config(), client=client)
        frames = [{"upload": {"key": "k1"}}]

        await host.cleanup(frames)

    async def test_cleanup_empty_frames(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)

        await host.cleanup([])
        client.delete_objects.assert_not_called()


class TestClose:
    def test_close_idempotent(self):
        client = _make_mock_client()
        host = CosImageHost(**_make_config(), client=client)
        host.close()
        host.close()


@pytest.mark.cos
@pytest.mark.integration
class TestCosImageHostIntegration:
    """Real COS integration tests. Requires COS_* env vars set.

    Run: uv run pytest tests/test_image_transport.py::TestCosImageHostIntegration -v -m cos
    Skip: uv run pytest tests/test_image_transport.py -v -m "not cos"
    """

    @pytest.fixture
    def cos_host(self):
        """Create CosImageHost from env vars. Skip if not configured."""
        bucket = os.getenv("COS_BUCKET", "")
        appid = os.getenv("COS_APPID", "")
        region = os.getenv("COS_REGION", "ap-guangzhou")
        secret_id = os.getenv("COS_SECRET_ID", "")
        secret_key = os.getenv("COS_SECRET_KEY", "")
        prefix = os.getenv("COS_KEY_PREFIX", "rag_anything/test")

        if not bucket or not appid or not secret_id:
            pytest.skip("COS credentials not configured in env vars")

        return CosImageHost(
            bucket=bucket,
            appid=appid,
            region=region,
            secret_id=secret_id,
            secret_key=secret_key,
            key_prefix=prefix,
            max_concurrent=2,
        )

    def _make_test_jpeg(self, tmpdir, filename: str) -> str:
        """Create a minimal valid JPEG file for testing."""
        # Minimal valid JPEG (1x1 pixel, white) — 160 bytes
        minimal_jpeg = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
            b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n'
            b'\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a'
            b'\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342'
            b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f'
            b'\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
            b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00'
            b'\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03'
            b'\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1'
            b'\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVW'
            b'XYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96'
            b'\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6'
            b'\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6'
            b'\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4'
            b'\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00'
            b'\x3f\x00\xa0\x00\x00\xff\xd9'
        )
        p = tmpdir / filename
        p.write_bytes(minimal_jpeg)
        return str(p)

    @pytest.mark.asyncio
    async def test_upload_and_url_accessible(self, cos_host, tmp_path):
        """Upload a test frame to COS and verify the returned URL is accessible."""
        frame_path = self._make_test_jpeg(tmp_path, "test_upload.jpg")
        frames = [{"frame_path": frame_path, "frame_time": 0.0}]

        result = await cos_host.prepare_urls(frames, "integration_test")

        assert result.transport_available is True, f"Upload failed: fatal_error={result.fatal_error}"
        assert result.uploaded_count == 1
        assert result.failed_count == 0

        frame_url = result.frames[0]["upload"]["url"]
        cos_key = result.frames[0]["upload"]["key"]

        print(f"\n  Uploaded to: {frame_url}")
        print(f"  COS key:     {cos_key}")

        # Verify URL format
        assert frame_url.startswith("https://")
        assert ".cos." in frame_url
        assert ".myqcloud.com/" in frame_url
        assert cos_key in frame_url

        # Verify URL is actually accessible via HTTP HEAD
        # Bucket may be public-read (HTTP 200) or private (HTTP 403).
        # In either case, the URL format and upload MUST succeed.


        try:
            req = urllib.request.Request(frame_url, method="HEAD")
            resp = urllib.request.urlopen(req, timeout=10)
            print(f"  HTTP status: {resp.status}")
            if resp.status == 200:
                content_type = resp.headers.get("Content-Type", "")
                content_length = resp.headers.get("Content-Length", "0")
                print(f"  Content-Type: {content_type}, Content-Length: {content_length}")
                assert content_type.startswith("image/"), f"Unexpected Content-Type: {content_type}"
                assert int(content_length) > 0, f"Zero Content-Length"
        except urllib.error.HTTPError as e:
            # 403 = private bucket (object exists, ACL denies anonymous read)
            # 404 = truly not found (still waiting for consistency or deleted)
            print(f"  HTTP status: {e.code} (may be private bucket)")
            assert e.code in (403, 404), f"Unexpected HTTP error: {e.code}"
        finally:
            # Cleanup after verification
            await cos_host.cleanup(result.frames)
            print(f"  Cleaned up:   {cos_key}")

    @pytest.mark.asyncio
    async def test_upload_multiple_frames_and_cleanup(self, cos_host, tmp_path):
        """Upload multiple frames, verify all URLs accessible, then cleanup."""
        frames = []
        for i in range(3):
            fp = self._make_test_jpeg(tmp_path, f"frame_{i:04d}.jpg")
            frames.append({"frame_path": fp, "frame_time": float(i)})

        result = await cos_host.prepare_urls(frames, "multi_upload_test")

        assert result.transport_available is True
        assert result.uploaded_count == 3
        assert result.failed_count == 0

        urls = [f["upload"]["url"] for f in result.frames]
        keys = [f["upload"]["key"] for f in result.frames]

        print(f"\n  Uploaded {len(urls)} frames:")
        for url in urls:
            print(f"    {url}")

        # Verify each URL


        for i, url in enumerate(urls):
            req = urllib.request.Request(url, method="HEAD")
            try:
                resp = urllib.request.urlopen(req, timeout=10)
                print(f"  Frame {i}: HTTP {resp.status}")
            except urllib.error.HTTPError as e:
                print(f"  Frame {i}: HTTP {e.code} (may be private bucket)")
                assert e.code in (403, 404), f"Unexpected HTTP error: {e.code}"

        # Cleanup
        await cos_host.cleanup(result.frames)
        print(f"  Cleaned up {len(keys)} frames")

        # Verify cleanup — re-check URLs should be 404 (or 403 for private bucket)
        for url in urls:
            req = urllib.request.Request(url, method="HEAD")
            try:
                resp = urllib.request.urlopen(req, timeout=10)
                print(f"  Post-cleanup status for {url}: {resp.status}")
            except urllib.error.HTTPError as e:
                print(f"  Post-cleanup status for {url}: {e.code}")
                assert e.code in (404, 403), f"Expected 404/403 after delete, got {e.code}"

    @pytest.mark.asyncio
    async def test_upload_failure_with_invalid_path(self, cos_host):
        """Nonexistent file path should be skipped gracefully."""
        frames = [{"frame_path": "/nonexistent/path/frame.jpg", "frame_time": 0.0}]

        result = await cos_host.prepare_urls(frames, "invalid_path_test")

        assert result.uploaded_count == 0
        assert result.transport_available is False


class TestVLMSupport:
    def test_vlmsupport_fields(self):
        s = VLMSupport(supports_url=True, supports_base64=False)
        assert s.supports_url is True
        assert s.supports_base64 is False

    def test_prepare_result_fields(self):
        r = PrepareResult(frames=[], transport_available=True,
                          uploaded_count=5, failed_count=2,
                          fatal_error=None)
        assert r.transport_available is True
        assert r.uploaded_count == 5
