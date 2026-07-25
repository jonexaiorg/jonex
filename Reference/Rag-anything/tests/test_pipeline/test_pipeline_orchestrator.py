"""Tests for DocumentPipeline orchestrator."""

from unittest.mock import MagicMock

import pytest

from raganything.pipeline import (
    DocumentPipeline,
    PipelineContext,
    PipelineServices,
    Stage,
    StageResult,
)


class _PassStage(Stage):
    async def execute(self, ctx, services):
        return StageResult(content_list=[{"type": "text", "text": "hello"}])


class _FailStage(Stage):
    async def execute(self, ctx, services):
        return StageResult(error="stage failed")


class _CleanupStage(Stage):
    can_run_on_error = True

    async def execute(self, ctx, services):
        return StageResult()


@pytest.fixture
def ctx():
    return PipelineContext(file_path="/test/file.pdf")


@pytest.fixture
def services():
    return PipelineServices(
        config=MagicMock(),
        lightrag=MagicMock(),
        doc_parser=MagicMock(),
        logger=MagicMock(),
    )


@pytest.mark.asyncio
async def test_pipeline_all_pass(ctx, services):
    pipeline = DocumentPipeline([_PassStage(), _PassStage()])
    result = await pipeline.execute(ctx, services)
    assert result.success
    assert result.status == "success"


@pytest.mark.asyncio
async def test_pipeline_stops_on_error(ctx, services):
    pipeline = DocumentPipeline([_PassStage(), _FailStage(), _PassStage()])
    result = await pipeline.execute(ctx, services)
    assert not result.success
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_pipeline_cleanup_stage_runs_on_error(ctx, services):
    pipeline = DocumentPipeline([_FailStage(), _CleanupStage()])
    result = await pipeline.execute(ctx, services)
    assert not result.success


def test_create_default_pipeline():
    pipeline = DocumentPipeline.create_default()
    assert isinstance(pipeline, DocumentPipeline)
    assert len(pipeline._stages) == 7
