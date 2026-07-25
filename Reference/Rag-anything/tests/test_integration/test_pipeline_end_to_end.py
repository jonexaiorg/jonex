"""End-to-end integration tests for the refactored pipeline."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from raganything.config import RAGAnythingConfig
from raganything.pipeline import (
    DocumentPipeline,
    PipelineContext,
    PipelineServices,
)
from raganything.pipeline.stages import FileValidateStage, ParseStage


@pytest.mark.asyncio
async def test_pipeline_e2e_with_mock_lightrag(tmp_path):
    """Verify the full pipeline executes without error with mocked dependencies."""
    doc = tmp_path / "test.txt"
    doc.write_text("Hello world")

    config = MagicMock(spec=RAGAnythingConfig)
    config.parser = "mineru"
    config.parse_method = "auto"
    config.parser_output_dir = str(tmp_path)
    config.display_content_stats = False
    config.use_full_path = False

    lightrag = MagicMock()
    lightrag.max_parallel_insert = 2
    lightrag._insert_done = AsyncMock()
    lightrag.chunk_entity_relation_graph = MagicMock()
    lightrag.entities_vdb = MagicMock()
    lightrag.relationships_vdb = MagicMock()
    lightrag.full_entities = MagicMock()
    lightrag.full_relations = MagicMock()
    lightrag.llm_response_cache = MagicMock()
    lightrag.entity_chunks = MagicMock()
    lightrag.relation_chunks = MagicMock()

    doc_parser = MagicMock()
    doc_parser.parse_document = MagicMock(
        return_value=[{"type": "text", "text": "content"}]
    )

    test_pipeline = DocumentPipeline([FileValidateStage(), ParseStage()])

    ctx = PipelineContext(file_path=str(doc), file_name="test.txt")
    services = PipelineServices(
        config=config,
        lightrag=lightrag,
        doc_parser=doc_parser,
        logger=MagicMock(),
    )

    result = await test_pipeline.execute(ctx, services)
    assert result.success


@pytest.mark.asyncio
async def test_pipeline_create_default_has_all_seven_stages():
    """Verify create_default() produces a pipeline with all 7 stages."""
    pipeline = DocumentPipeline.create_default()
    assert len(pipeline._stages) == 7

    from raganything.pipeline.stages import (
        EntityExtractStage,
        EntityMergeStage,
        FileValidateStage,
        MultimodalChunkStage,
        MultimodalStage,
        ParseStage,
        TextInsertStage,
    )

    stage_types = [type(s) for s in pipeline._stages]
    assert FileValidateStage in stage_types
    assert ParseStage in stage_types
    assert TextInsertStage in stage_types
    assert MultimodalStage in stage_types
    assert MultimodalChunkStage in stage_types
    assert EntityExtractStage in stage_types
    assert EntityMergeStage in stage_types


@pytest.mark.asyncio
async def test_pipeline_handles_missing_file(tmp_path):
    """Verify pipeline reports error for non-existent file."""
    config = MagicMock(spec=RAGAnythingConfig)

    pipeline = DocumentPipeline.create_default()

    ctx = PipelineContext(file_path=str(tmp_path / "nonexistent.pdf"))
    services = PipelineServices(
        config=config,
        lightrag=MagicMock(),
        doc_parser=MagicMock(),
        logger=MagicMock(),
    )

    result = await pipeline.execute(ctx, services)
    assert not result.success
    assert result.error is not None
    assert "not found" in result.error
