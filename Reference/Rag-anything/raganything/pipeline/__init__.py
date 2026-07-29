"""Document processing pipeline — orchestrates parsing, insertion, and entity merge."""

from raganything.pipeline.base import (
    EmptyStage,
    PipelineContext,
    PipelineResult,
    PipelineServices,
    Stage,
    StageResult,
    merge_context,
)
from raganything.pipeline.stages import (
    EntityExtractStage,
    EntityMergeStage,
    FileValidateStage,
    MultimodalChunkStage,
    MultimodalStage,
    ParseStage,
    TextInsertStage,
)
from raganything.pipeline_mode import PipelineMode


class DocumentPipeline:
    """Orchestrates a sequence of stages to process a document."""

    def __init__(self, stages):
        self._stages = list(stages)

    async def execute(
        self, ctx: PipelineContext, services: PipelineServices
    ) -> PipelineResult:
        """Run all stages in sequence. Error stages are skipped unless can_run_on_error."""
        import time
        pipeline_start = time.time()
        cb = services.callback_manager
        current = ctx
        for stage in self._stages:
            if current.error and not stage.can_run_on_error:
                continue
            result = await stage.execute(current, services)
            if result.error and services.event_bus:
                from raganything.event_bus import PipelineEvent
                await services.event_bus.publish(PipelineEvent(
                    type="document_failed",
                    doc_id=current.doc_id or "",
                    file_path=current.file_name,
                    data={"error": result.error},
                ))
            # ── Callback: document error ──
            if result.error and cb:
                cb.dispatch("on_document_error", file_path=ctx.file_name,
                            error=result.error, doc_id=current.doc_id,
                            duration_seconds=time.time() - pipeline_start)
            current = merge_context(current, result)

        success = current.error is None
        # ── Callback: document complete ──
        if success and cb:
            cb.dispatch("on_document_complete", file_path=ctx.file_name,
                        doc_id=current.doc_id or "",
                        duration_seconds=time.time() - pipeline_start)
        return PipelineResult(
            success=success,
            doc_id=current.doc_id,
            error=current.error,
            status="success" if not current.error else "failed",
            final_ctx=current,
        )

    @classmethod
    def create_default(cls, mode: PipelineMode = PipelineMode.STANDALONE):
        from raganything.pipeline.builder import create_default_pipeline
        return create_default_pipeline(mode)


__all__ = [
    "DocumentPipeline",
    "EmptyStage",
    "PipelineContext",
    "PipelineResult",
    "PipelineServices",
    "PipelineMode",
    "Stage",
    "StageResult",
    "merge_context",
    "FileValidateStage",
    "ParseStage",
    "TextInsertStage",
    "MultimodalStage",
    "MultimodalChunkStage",
    "EntityExtractStage",
    "EntityMergeStage",
]
