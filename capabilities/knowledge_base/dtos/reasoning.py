"""编排推理链 DTO（本体优先检索）"""
from typing import Any, Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field

# ── 阶段标识 ──
STAGE_ONTOLOGY_MATCH = "ontology_match"
STAGE_ROUTE_DECISION = "route_decision"
STAGE_FACT_LOOKUP = "fact_lookup"
STAGE_LLM_ANSWER = "llm_answer"
STAGE_RAG_FALLBACK = "rag_fallback"
STAGE_FUSION = "fusion"
STAGE_RETRIEVAL_RERANK = "retrieval_rerank"   # LightRAG 检索期重排（召回后、送 LLM 前）
STAGE_RERANK = "rerank"                        # 平台引用期重排（LLM 答完后，多 KB fallback 引用）

# ── 状态标识 ──
STATUS_RUNNING = "running"
STATUS_DONE = "done"
STATUS_SKIPPED = "skipped"
STATUS_FAILED = "failed"


class ReasoningStep(BaseModel):
    """推理链的单个步骤"""
    stage: str
    title: str                                            # 前端展示的中文标题
    status: str = STATUS_DONE
    summary: Optional[str] = None
    detail: Optional[dict[str, Any]] = None               # 结构化明细（已脱敏）
    duration_ms: Optional[int] = None


class ReasoningTrace(BaseModel):
    """完整的推理链轨迹"""
    steps: list[ReasoningStep] = Field(default_factory=list)
    final_source: str = "rag"                             # ontology | rag | none
    total_ms: Optional[int] = None
