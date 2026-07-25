"""Tests for PipelineBuilder."""
from raganything.pipeline.base import Stage, StageResult
from raganything.pipeline.builder import PipelineBuilder, create_default_pipeline


class DummyStage(Stage):
    def __init__(self, marker=None):
        self.marker = marker

    async def execute(self, ctx, services):
        return StageResult()


class TestPipelineBuilder:
    def test_add_stage_appends(self):
        s1 = DummyStage("a")
        s2 = DummyStage("b")
        pipeline = PipelineBuilder().add_stage("a", s1).add_stage("b", s2).build()
        assert len(pipeline._stages) == 2

    def test_add_before_inserts(self):
        s1, s2, s3 = DummyStage("a"), DummyStage("b"), DummyStage("c")
        pipeline = (
            PipelineBuilder()
            .add_stage("a", s1)
            .add_stage("c", s3)
            .add_before("c", "b", s2)
            .build()
        )
        names = [s.marker for s in pipeline._stages]
        assert names == ["a", "b", "c"]

    def test_add_after_inserts(self):
        s1, s2, s3 = DummyStage("a"), DummyStage("b"), DummyStage("c")
        pipeline = (
            PipelineBuilder()
            .add_stage("a", s1)
            .add_stage("c", s3)
            .add_after("a", "b", s2)
            .build()
        )
        names = [s.marker for s in pipeline._stages]
        assert names == ["a", "b", "c"]

    def test_replace(self):
        s1, s2 = DummyStage("a"), DummyStage("b")
        pipeline = PipelineBuilder().add_stage("a", s1).replace("a", "b", s2).build()
        assert pipeline._stages[0].marker == "b"

    def test_create_default_pipeline_has_all_stages(self):
        pipeline = create_default_pipeline()
        stage_names = [type(s).__name__ for s in pipeline._stages]
        assert "FileValidateStage" in stage_names
        assert "ParseStage" in stage_names
        assert "TextInsertStage" in stage_names
        assert "MultimodalStage" in stage_names
        assert "EntityMergeStage" in stage_names
