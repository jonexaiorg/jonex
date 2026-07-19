
from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


STAGE_ONTOLOGY_MATCH = "ontology_match"
STAGE_ROUTE_DECISION = "route_decision"
STAGE_FACT_LOOKUP = "fact_lookup"
STAGE_LLM_ANSWER = "llm_answer"
STAGE_RAG_FALLBACK = "rag_fallback"
STAGE_FUSION = "fusion"
STAGE_RETRIEVAL_RERANK = "retrieval_rerank"
STAGE_RERANK = "rerank"


STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"


class ReasoningStep(BaseModel):

    stage: str
    title: str
    status: str = STATUS_DONE
    summary: Optional[str] = None
    detail: Optional[dict[str, Any]] = None
    duration_ms: Optional[int] = None


class ReasoningTrace(BaseModel):

    steps: list[ReasoningStep] = Field(default_factory=list)
    final_source: str = "rag"
    total_ms: Optional[int] = None
