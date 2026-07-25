"""Unit tests for HttpLightRagClient."""

import pytest
from unittest import mock
from raganything.service.http_lightrag_client import (
    HttpLightRagClient,
    TrackStatus,
    UploadResult,
    LightRAGUnavailableError,
    LightRAGTimeoutError,
    LightRAGError,
    _validate_workspace_id,
    _map_lightrag_error,
)


class TestValidateWorkspaceId:
    def test_accepts_valid_ids(self):
        assert _validate_workspace_id("tenant_jonex_demo", "tenant_id") == "tenant_jonex_demo"
        assert _validate_workspace_id("kb-123", "kb_id") == "kb-123"
        assert _validate_workspace_id("abc.def_ghi-789.xyz", "test") == "abc.def_ghi-789.xyz"

    def test_accepts_64_chars(self):
        id_64 = "a" * 64
        assert _validate_workspace_id(id_64, "test") == id_64

    def test_rejects_65_chars(self):
        with pytest.raises(ValueError, match="Invalid test"):
            _validate_workspace_id("a" * 65, "test")

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="Invalid tenant_id"):
            _validate_workspace_id("", "tenant_id")

    def test_rejects_special_chars(self):
        with pytest.raises(ValueError, match="Invalid kb_id"):
            _validate_workspace_id("kb|123", "kb_id")
        with pytest.raises(ValueError, match="Invalid kb_id"):
            _validate_workspace_id("kb/123", "kb_id")
        with pytest.raises(ValueError, match="Invalid kb_id"):
            _validate_workspace_id("kb 123", "kb_id")


class TestDatatypes:
    def test_track_status_defaults(self):
        ts = TrackStatus(state="pending")
        assert ts.state == "pending"
        assert ts.doc_ids == []
        assert ts.error is None

    def test_track_status_completed(self):
        ts = TrackStatus(state="completed", doc_ids=["doc-1", "doc-2"])
        assert ts.state == "completed"
        assert ts.doc_ids == ["doc-1", "doc-2"]

    def test_track_status_failed(self):
        ts = TrackStatus(state="failed", error="chunk too large")
        assert ts.state == "failed"
        assert ts.error == "chunk too large"

    def test_upload_result_defaults(self):
        ur = UploadResult(track_id="trk-123", status="success")
        assert ur.track_id == "trk-123"
        assert ur.status == "success"
        assert ur.doc_ids == []

    def test_upload_result_duplicated(self):
        ur = UploadResult(track_id="trk-456", status="duplicated")
        assert ur.status == "duplicated"


class TestErrorMapping:
    def test_5xx_maps_to_502(self):
        resp = mock.MagicMock()
        resp.status_code = 500
        resp.json.return_value = {}
        exc = _map_lightrag_error(type("HTTPStatusError", (), {"response": resp})())
        assert isinstance(exc, LightRAGError)
        assert exc.code == 502

    def test_429_maps_to_429(self):
        resp = mock.MagicMock()
        resp.status_code = 429
        resp.json.return_value = {}
        exc = _map_lightrag_error(type("HTTPStatusError", (), {"response": resp})())
        assert isinstance(exc, LightRAGError)
        assert exc.code == 429

    def test_404_maps_to_404(self):
        resp = mock.MagicMock()
        resp.status_code = 404
        resp.json.return_value = {}
        exc = _map_lightrag_error(type("HTTPStatusError", (), {"response": resp})())
        assert isinstance(exc, LightRAGError)
        assert exc.code == 404


class TestHttpLightRagClientInit:
    def test_init_defaults(self):
        client = HttpLightRagClient()
        assert client.base_url == "http://lightrag:9621"
        assert client.breaker_state == "closed"

    def test_init_custom_url(self, monkeypatch):
        monkeypatch.setenv("LIGHTRAG_API_URL", "http://custom:9999")
        client = HttpLightRagClient()
        assert client.base_url == "http://custom:9999"

    # [jonex] RAG_TRACK_POLL_CONCURRENCY 校验兜底

    def test_poll_concurrency_zero_fallback(self, monkeypatch):
        monkeypatch.setenv("RAG_TRACK_POLL_CONCURRENCY", "0")
        client = HttpLightRagClient()
        assert client._track_poll_concurrency == 8

    def test_poll_concurrency_invalid_string_fallback(self, monkeypatch):
        monkeypatch.setenv("RAG_TRACK_POLL_CONCURRENCY", "8x")
        client = HttpLightRagClient()
        assert client._track_poll_concurrency == 8

    def test_poll_concurrency_negative_fallback(self, monkeypatch):
        monkeypatch.setenv("RAG_TRACK_POLL_CONCURRENCY", "-1")
        client = HttpLightRagClient()
        assert client._track_poll_concurrency == 8

    def test_poll_concurrency_custom_value(self, monkeypatch):
        monkeypatch.setenv("RAG_TRACK_POLL_CONCURRENCY", "16")
        client = HttpLightRagClient()
        assert client._track_poll_concurrency == 16


class TestHeaders:
    def test_headers_with_api_key(self, monkeypatch):
        monkeypatch.setenv("LIGHTRAG_API_KEY", "secret-key")
        client = HttpLightRagClient()
        headers = client._headers("t1", "kb1")
        assert headers["X-API-Key"] == "secret-key"
        assert headers["LIGHTRAG-WORKSPACE"] == "t1__kb1"

    def test_headers_no_api_key(self):
        client = HttpLightRagClient()
        headers = client._headers("t1", "kb1")
        assert "X-API-Key" not in headers
        assert headers["LIGHTRAG-WORKSPACE"] == "t1__kb1"

    def test_headers_tenant_only(self):
        client = HttpLightRagClient()
        headers = client._headers("t1", "")
        assert headers["LIGHTRAG-WORKSPACE"] == "t1"


class TestExceptions:
    def test_lightrag_unavailable(self):
        exc = LightRAGUnavailableError("circuit open")
        assert str(exc) == "circuit open"

    def test_lightrag_timeout(self):
        exc = LightRAGTimeoutError("timeout 300s")
        assert str(exc) == "timeout 300s"

    def test_lightrag_error(self):
        exc = LightRAGError(502, "upstream error")
        assert exc.code == 502
        assert exc.message == "upstream error"
        assert str(exc) == "upstream error"


class TestBatchTrackStatusNoDirtyPending:
    """[jonex] batch_track_status pending 脏残留修复回归测试。

    验证 processing→completed/failed 转换后，终态 track 不会残留在 pending dict 中，
    避免上游 PushChunksStage 将已完成的 chunk 误判为 timed_out。
    """

    @pytest.mark.asyncio
    async def test_processing_to_completed_not_leaked_to_pending(self):
        """第1轮 processing → 第2轮 completed：终态应在 terminal，不在 pending。"""
        client = HttpLightRagClient()

        call_count: dict[str, int] = {}

        async def _poll_one(track_id, tenant_id, kb_id):
            call_count[track_id] = call_count.get(track_id, 0) + 1
            if call_count[track_id] == 1:
                return TrackStatus(state="processing")
            return TrackStatus(state="completed", doc_ids=[f"doc-{track_id}"])

        with mock.patch.object(
            client, "_poll_one_track", side_effect=_poll_one,
        ), mock.patch(
            "raganything.service.http_lightrag_client.asyncio.sleep",
            new=mock.AsyncMock(),
        ):
            terminal, pending = await client.batch_track_status(
                ["trk-0"],
                tenant_id="t1",
                kb_id="kb1",
                max_wait_seconds=30,
            )

        assert "trk-0" in terminal
        assert terminal["trk-0"].state == "completed"
        assert terminal["trk-0"].doc_ids == ["doc-trk-0"]
        assert "trk-0" not in pending, "已完成 track 不应残留在 pending"
        assert pending == {}

        await client.close()

    @pytest.mark.asyncio
    async def test_processing_to_failed_not_leaked_to_pending(self):
        """第1轮 processing → 第2轮 failed：终态应在 terminal，不在 pending。"""
        client = HttpLightRagClient()

        call_count: dict[str, int] = {}

        async def _poll_one(track_id, tenant_id, kb_id):
            call_count[track_id] = call_count.get(track_id, 0) + 1
            if call_count[track_id] == 1:
                return TrackStatus(state="processing")
            return TrackStatus(state="failed", error="parse error")

        with mock.patch.object(
            client, "_poll_one_track", side_effect=_poll_one,
        ), mock.patch(
            "raganything.service.http_lightrag_client.asyncio.sleep",
            new=mock.AsyncMock(),
        ):
            terminal, pending = await client.batch_track_status(
                ["trk-0"],
                tenant_id="t1",
                kb_id="kb1",
                max_wait_seconds=30,
            )

        assert "trk-0" in terminal
        assert terminal["trk-0"].state == "failed"
        assert "trk-0" not in pending, "failed track 不应残留在 pending"
        assert pending == {}

        await client.close()

    @pytest.mark.asyncio
    async def test_never_completes_stays_in_pending(self):
        """始终 processing 的 track 应在 pending（不出现在 terminal）。"""
        client = HttpLightRagClient()

        async def _poll_one(track_id, tenant_id, kb_id):
            return TrackStatus(state="processing")

        with mock.patch.object(
            client, "_poll_one_track", side_effect=_poll_one,
        ), mock.patch(
            "raganything.service.http_lightrag_client.asyncio.sleep",
            new=mock.AsyncMock(),
        ):
            terminal, pending = await client.batch_track_status(
                ["trk-0"],
                tenant_id="t1",
                kb_id="kb1",
                max_wait_seconds=30,
            )

        assert "trk-0" not in terminal
        assert "trk-0" in pending
        assert pending["trk-0"].state == "processing"

        await client.close()

    @pytest.mark.asyncio
    async def test_mixed_transitions_no_cross_contamination(self):
        """3 个 track 不同转换速率，验证 terminal 与 pending 完全互斥。"""
        client = HttpLightRagClient()

        call_count: dict[str, int] = {}

        async def _poll_one(track_id, tenant_id, kb_id):
            call_count[track_id] = call_count.get(track_id, 0) + 1
            cnt = call_count[track_id]
            if track_id == "fast":
                return TrackStatus(state="completed", doc_ids=["doc-fast"])
            elif track_id == "slow":
                return TrackStatus(state="completed", doc_ids=["doc-slow"]) if cnt >= 3 else TrackStatus(state="processing")
            else:  # stuck
                return TrackStatus(state="processing")

        with mock.patch.object(
            client, "_poll_one_track", side_effect=_poll_one,
        ), mock.patch(
            "raganything.service.http_lightrag_client.asyncio.sleep",
            new=mock.AsyncMock(),
        ):
            terminal, pending = await client.batch_track_status(
                ["fast", "slow", "stuck"],
                tenant_id="t1",
                kb_id="kb1",
                max_wait_seconds=30,
            )

        assert "fast" in terminal and terminal["fast"].state == "completed"
        assert "slow" in terminal and terminal["slow"].state == "completed"
        assert "stuck" not in terminal
        assert "stuck" in pending
        assert "fast" not in pending, "fast（首轮完成）不应残留在 pending"
        assert "slow" not in pending, "slow（第3轮完成）不应残留在 pending"
        # terminal 与 pending 严格互斥
        assert set(terminal.keys()).isdisjoint(set(pending.keys()))

        await client.close()

    @pytest.mark.asyncio
    async def test_empty_track_ids(self):
        """空列表输入直接返回空 dict。"""
        client = HttpLightRagClient()
        terminal, pending = await client.batch_track_status(
            [], tenant_id="t1", kb_id="kb1",
        )
        assert terminal == {}
        assert pending == {}
        await client.close()


class TestGraphRelationships:
    @pytest.mark.asyncio
    async def test_normalizes_endpoint_fields_without_mutating_response(self):
        client = HttpLightRagClient()
        upstream = {
            "items": [
                {"src_id": "实体A", "tgt_id": "实体B", "description": "A 关联 B"},
                {"source_entity": "实体C", "target_entity": "实体D"},
            ],
            "total": 2,
            "page": 1,
            "page_size": 20,
        }

        with mock.patch.object(
            client,
            "_get_json",
            new=mock.AsyncMock(return_value=upstream),
        ) as get_json:
            result = await client.get_relationships(
                "tenant_jonex_demo",
                "kb_demo",
                document_id="doc-1",
            )

        assert result["items"][0]["source_entity"] == "实体A"
        assert result["items"][0]["target_entity"] == "实体B"
        assert result["items"][0]["src_id"] == "实体A"
        assert result["items"][0]["tgt_id"] == "实体B"
        assert result["items"][1]["source_entity"] == "实体C"
        assert result["items"][1]["target_entity"] == "实体D"
        assert "source_entity" not in upstream["items"][0]
        assert get_json.await_args.kwargs["params"]["doc_id"] == "doc-1"
        await client.close()
