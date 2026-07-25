"""Unit tests for PushChunksStage."""

import asyncio
import pytest
from unittest import mock

from raganything.pipeline.base import PipelineContext, PipelineServices, StageResult
from raganything.pipeline.stages import PushChunksStage, _build_file_source


class TestBuildFileSource:
    def test_basic_text_chunk(self):
        fs = _build_file_source("t1", "kb1", "doc-123", "report.pdf", chunk_index=0,
                                page=1, line_start=10, line_end=20)
        assert fs == "kb=kb1|doc=doc-123|tenant=t1|file=report.pdf|chunk=0|cstart=10|cend=20|page=1|trace="

    def test_table_chunk(self):
        fs = _build_file_source("t1", "kb1", "doc-123", "data.xlsx", chunk_index=5,
                                page=2, table_idx=1)
        assert "table_idx=1" in fs
        assert "chunk=5" in fs
        assert "tenant=t1" in fs
        assert fs.endswith("|trace=")

    def test_image_chunk(self):
        fs = _build_file_source("t1", "kb1", "doc-123", "slides.pdf", chunk_index=2,
                                page=3, image_idx=0)
        assert "image_idx=0" in fs
        assert "page=3" in fs
        assert "tenant=t1" in fs

    def test_audio_chunk(self):
        fs = _build_file_source("t1", "kb1", "doc-123", "recording.mp3", chunk_index=1,
                                start_time=10.5, end_time=25.3)
        assert "tstart=10.500" in fs
        assert "tend=25.300" in fs

    def test_no_optional_fields(self):
        fs = _build_file_source("t1", "kb1", "doc-123", "file.txt", chunk_index=0)
        assert fs == "kb=kb1|doc=doc-123|tenant=t1|file=file.txt|chunk=0|trace="


class TestPushChunksStage:
    @pytest.fixture
    def mock_http_client(self):
        client = mock.AsyncMock()
        # Default: upload_text succeeds synchronously
        client.upload_text.return_value = mock.MagicMock(
            track_id="trk-0", status="success", doc_ids=[]
        )
        # Default: batch_track_status returns all completed
        async def _batch(ids, **kw):
            terminal = {
                tid: mock.MagicMock(state="completed", doc_ids=[f"chunk-{i}"])
                for i, tid in enumerate(ids)
            }
            return terminal, {}
        client.batch_track_status.side_effect = _batch
        return client

    @pytest.fixture
    def ctx(self):
        return PipelineContext(
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            tenant_id="t1",
            kb_id="kb1",
            doc_id="doc-123",
            content_list=[
                {"type": "text", "text": "Hello world", "page_idx": 1, "line_start": 0, "line_end": 1},
                {"type": "text", "text": "Second paragraph", "page_idx": 1, "line_start": 2, "line_end": 3},
            ],
        )

    @pytest.fixture
    def services(self, mock_http_client):
        return PipelineServices(
            config=mock.MagicMock(),
            lightrag=None,
            doc_parser=mock.MagicMock(),
            http_client=mock_http_client,
            logger=mock.MagicMock(),
        )

    @pytest.mark.asyncio
    async def test_pushes_text_chunks(self, ctx, services):
        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is None
        assert services.http_client.upload_text.call_count == 2

    @pytest.mark.asyncio
    async def test_collects_doc_ids(self, ctx, services):
        # Setup: each upload returns a unique track_id
        track_counter = [0]

        async def _upload(text, file_source, *, tenant_id, kb_id):
            tid = f"trk-{track_counter[0]}"
            track_counter[0] += 1
            return mock.MagicMock(track_id=tid, status="success", doc_ids=[])

        services.http_client.upload_text.side_effect = _upload

        async def _batch(ids, **kw):
            terminal = {
                tid: mock.MagicMock(state="completed", doc_ids=[f"chunk-{i}"])
                for i, tid in enumerate(ids)
            }
            return terminal, {}
        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert len(ctx.collected_doc_ids) == 2

    @pytest.mark.asyncio
    async def test_empty_content_returns_early(self, services):
        ctx = PipelineContext(
            file_path="/tmp/empty.pdf",
            file_name="empty.pdf",
            tenant_id="t1",
            kb_id="kb1",
            content_list=[],
        )
        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is None
        services.http_client.upload_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_requires_http_client(self, ctx):
        services = PipelineServices(
            config=mock.MagicMock(),
            lightrag=None,
            doc_parser=mock.MagicMock(),
            http_client=None,
            logger=mock.MagicMock(),
        )
        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is not None
        assert "requires http_client" in result.error

    @pytest.mark.asyncio
    async def test_cancellation_stops_push(self, ctx, services):
        cancel_event = asyncio.Event()
        cancel_event.set()  # already cancelled
        ctx.cancel_event = cancel_event

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        # No chunks should be pushed since cancel was already set
        services.http_client.upload_text.assert_not_called()
        assert "cancelled" in (result.error or "").lower() or result.error is not None

    @pytest.mark.asyncio
    async def test_upload_failure_single_chunk(self, ctx, services):
        # Make upload fail for the second chunk
        call_count = [0]

        async def _upload(text, file_source, *, tenant_id, kb_id):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Connection refused")
            return mock.MagicMock(track_id=f"trk-{call_count[0]}", status="success", doc_ids=[])

        services.http_client.upload_text.side_effect = _upload

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        # Should still succeed (1/2 succeeded)
        assert result.error is None

    @pytest.mark.asyncio
    async def test_all_uploads_fail(self, ctx, services):
        services.http_client.upload_text.side_effect = Exception("All failed")

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        # All failed — should report error
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_track_status_timeout(self, ctx, services):
        # All tracks stay pending after timeout
        async def _batch(ids, **kw):
            return {}, {tid: mock.MagicMock(state="processing") for tid in ids}
        services.http_client.batch_track_status.side_effect = _batch

        # Short timeout for test
        stage = PushChunksStage()
        stage._track_timeout = 0.1

        result = await stage.execute(ctx, services)
        # All timed out, no doc_ids collected — should fail
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_collects_multimodal_chunks(self, ctx, services):
        ctx.multimodal_results = [
            {
                "description": "A chart showing revenue growth",
                "content_type": "image",
                "item_info": {"page_idx": 1},
                "index": 0,
            }
        ]

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        # Text (2) + multimodal (1) = 3 chunks
        assert services.http_client.upload_text.call_count == 3


# ── [jonex] #6: strict doc_id/track_id confirmation ────────────────


class TestPushChunksStrictConfirmation:
    """[jonex] #6: RAG_REQUIRE_DOC_IDS strict mode tests."""

    @pytest.fixture
    def ctx(self):
        return PipelineContext(
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            tenant_id="t1",
            kb_id="kb1",
            document_id="doc-123",
            content_list=[
                {"type": "text", "text": "Chunk A", "page_idx": 1},
                {"type": "text", "text": "Chunk B", "page_idx": 2},
                {"type": "text", "text": "Chunk C", "page_idx": 3},
            ],
        )

    @pytest.fixture
    def services(self):
        client = mock.AsyncMock()
        client.upload_text.return_value = mock.MagicMock(
            track_id="trk-0", status="success", doc_ids=[]
        )
        return PipelineServices(
            config=mock.MagicMock(),
            lightrag=None,
            doc_parser=mock.MagicMock(),
            http_client=client,
            logger=mock.MagicMock(),
        )

    def _setup_upload_with_track_ids(self, services):
        """Each chunk gets a unique track_id."""
        counter = [0]

        async def _upload(text, file_source, *, tenant_id, kb_id):
            tid = f"trk-{counter[0]}"
            counter[0] += 1
            return mock.MagicMock(track_id=tid, status="success", doc_ids=[])

        services.http_client.upload_text.side_effect = _upload

    @pytest.mark.asyncio
    async def test_all_completed_success(self, ctx, services):
        """#6: all track_status completed → SUCCESS."""
        self._setup_upload_with_track_ids(services)

        async def _batch(ids, **kw):
            terminal = {
                tid: mock.MagicMock(state="completed", doc_ids=[f"doc-{i}"])
                for i, tid in enumerate(ids)
            }
            return terminal, {}

        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is None
        assert ctx.total_chunk_count == 3
        assert ctx.failed_chunk_count == 0
        assert ctx.timeout_chunk_count == 0
        assert len(ctx.collected_doc_ids) == 3

    @pytest.mark.asyncio
    async def test_partial_hard_failure_strict_mode(self, ctx, services):
        """#6: RAG_REQUIRE_DOC_IDS=true, 1 terminal failed → hard failure error."""
        self._setup_upload_with_track_ids(services)

        async def _batch(ids, **kw):
            terminal = {}
            for i, tid in enumerate(ids):
                if i == 1:  # second chunk failed
                    terminal[tid] = mock.MagicMock(
                        state="failed", doc_ids=[], error="parse error"
                    )
                else:
                    terminal[tid] = mock.MagicMock(
                        state="completed", doc_ids=[f"doc-{i}"]
                    )
            return terminal, {}

        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        # default: _require_doc_ids=True
        result = await stage.execute(ctx, services)

        assert result.error is not None
        assert "入库部分失败" in result.error
        assert "1/3" in result.error
        assert ctx.failed_chunk_count == 1
        # collected_doc_ids still has the successful ones
        assert len(ctx.collected_doc_ids) == 2

    @pytest.mark.asyncio
    async def test_timed_out_strict_mode(self, ctx, services):
        """#6: RAG_REQUIRE_DOC_IDS=true, chunk pending after timeout → TIMEOUT error."""
        self._setup_upload_with_track_ids(services)

        async def _batch(ids, **kw):
            # 2 completed, 1 still pending
            terminal = {
                ids[0]: mock.MagicMock(state="completed", doc_ids=["doc-0"]),
                ids[1]: mock.MagicMock(state="completed", doc_ids=["doc-1"]),
            }
            still_pending = {ids[2]: mock.MagicMock(state="processing")}
            return terminal, still_pending

        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is not None
        assert "RAG_PUSH_TIMEOUT" in result.error
        assert "1/3" in result.error
        assert ctx.timeout_chunk_count == 1
        assert ctx.failed_chunk_count == 0
        assert len(ctx.collected_doc_ids) == 2
        assert len(ctx.pending_track_ids) == 1

    @pytest.mark.asyncio
    async def test_relaxed_mode_partial_failure_succeeds(self, ctx, services):
        """#6: RAG_REQUIRE_DOC_IDS=false, partial failure → preserved宽松semantics."""
        self._setup_upload_with_track_ids(services)

        async def _batch(ids, **kw):
            terminal = {
                ids[0]: mock.MagicMock(state="completed", doc_ids=["doc-0"]),
                ids[1]: mock.MagicMock(state="failed", doc_ids=[], error="err"),
                ids[2]: mock.MagicMock(state="completed", doc_ids=["doc-2"]),
            }
            return terminal, {}

        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        stage._require_doc_ids = False  # relaxed mode
        result = await stage.execute(ctx, services)

        # Relaxed mode: 2/3 succeeded → SUCCESS
        assert result.error is None
        assert ctx.failed_chunk_count == 1

    @pytest.mark.asyncio
    async def test_relaxed_mode_all_timed_out_no_doc_ids(self, ctx, services):
        """#6: even in relaxed mode, all timed out with no doc_ids → failure."""
        self._setup_upload_with_track_ids(services)

        async def _batch(ids, **kw):
            still_pending = {tid: mock.MagicMock(state="processing") for tid in ids}
            return {}, still_pending

        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        stage._require_doc_ids = False
        result = await stage.execute(ctx, services)

        # All timed out, no doc_ids
        assert result.error is not None
        assert "All 3 chunks failed" in result.error

    @pytest.mark.asyncio
    async def test_push_failure_in_failed_chunk_count(self, ctx, services):
        """#6: push-level exception counts as hard_failed."""
        failed_chunk_idx = 2  # the 3rd chunk

        async def _upload(text, file_source, *, tenant_id, kb_id):
            # Use the chunk index embedded in file_source
            fs = file_source
            # chunk=N in file_source tells us which chunk
            import re
            m = re.search(r"chunk=(\d+)", fs)
            idx = int(m.group(1)) if m else -1
            if idx == failed_chunk_idx:
                raise Exception("Connection refused")
            return mock.MagicMock(
                track_id=f"trk-{idx}", status="success", doc_ids=[]
            )

        services.http_client.upload_text.side_effect = _upload

        async def _batch(ids, **kw):
            terminal = {
                tid: mock.MagicMock(state="completed", doc_ids=[f"doc-{i}"])
                for i, tid in enumerate(ids)
            }
            return terminal, {}

        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        # Strict mode: 1 push failure → hard failure
        assert result.error is not None
        assert "入库部分失败" in result.error
        assert ctx.failed_chunk_count == 1
        assert ctx.total_pushed_count == 2  # only 2 got track_ids

    @pytest.mark.asyncio
    async def test_context_counters_persisted(self, ctx, services):
        """#6: ctx counters are set correctly for all outcomes."""
        self._setup_upload_with_track_ids(services)

        async def _batch(ids, **kw):
            terminal = {
                ids[0]: mock.MagicMock(state="completed", doc_ids=["doc-0"]),
                ids[1]: mock.MagicMock(state="completed", doc_ids=["doc-1"]),
            }
            still_pending = {ids[2]: mock.MagicMock(state="processing")}
            return terminal, still_pending

        services.http_client.batch_track_status.side_effect = _batch

        stage = PushChunksStage()
        await stage.execute(ctx, services)

        assert ctx.total_chunk_count == 3
        assert ctx.failed_chunk_count == 0  # no hard failures
        assert ctx.timeout_chunk_count == 1  # one timed out
        assert ctx.total_pushed_count == 3  # all 3 got track_ids


# ── [jonex] #5: duplicated chunk tracking ───────────────────────────


class TestPushChunksDuplicatedTracking:
    """[jonex] #5: all-duplicated guard for ontology skip."""

    @pytest.fixture
    def ctx(self):
        return PipelineContext(
            file_path="/tmp/test.pdf",
            file_name="test.pdf",
            tenant_id="t1",
            kb_id="kb1",
            document_id="doc-123",
            content_list=[
                {"type": "text", "text": "Chunk A", "page_idx": 1},
                {"type": "text", "text": "Chunk B", "page_idx": 2},
            ],
        )

    @pytest.fixture
    def services(self):
        client = mock.AsyncMock()
        return PipelineServices(
            config=mock.MagicMock(),
            lightrag=None,
            doc_parser=mock.MagicMock(),
            http_client=client,
            logger=mock.MagicMock(),
        )

    def _setup_uploads(self, services, statuses):
        """Setup upload_text to return given statuses in order."""
        counter = [0]

        async def _upload(text, file_source, *, tenant_id, kb_id):
            s = statuses[counter[0]]
            counter[0] += 1
            return mock.MagicMock(track_id=f"trk-{counter[0]}", status=s, doc_ids=[])

        services.http_client.upload_text.side_effect = _upload

        async def _batch(ids, **kw):
            terminal = {
                tid: mock.MagicMock(state="completed", doc_ids=[f"doc-{i}"])
                for i, tid in enumerate(ids)
            }
            return terminal, {}

        services.http_client.batch_track_status.side_effect = _batch

    @pytest.mark.asyncio
    async def test_all_duplicated_tracking(self, ctx, services):
        """#5: all chunks duplicated → duplicated_chunk_count == total_pushed_count."""
        self._setup_uploads(services, ["duplicated", "duplicated"])

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is None
        assert ctx.duplicated_chunk_count == 2
        assert ctx.total_pushed_count == 2

    @pytest.mark.asyncio
    async def test_partial_duplicated_tracking(self, ctx, services):
        """#5: 1 duplicated, 1 new → duplicated_chunk_count=1."""
        self._setup_uploads(services, ["duplicated", "success"])

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is None
        assert ctx.duplicated_chunk_count == 1
        assert ctx.total_pushed_count == 2

    @pytest.mark.asyncio
    async def test_none_duplicated_tracking(self, ctx, services):
        """#5: all new → duplicated_chunk_count=0."""
        self._setup_uploads(services, ["success", "success"])

        stage = PushChunksStage()
        result = await stage.execute(ctx, services)

        assert result.error is None
        assert ctx.duplicated_chunk_count == 0
        assert ctx.total_pushed_count == 2
