"""
文本 RAG 领域能力模块 (domain.rag.text.v1)

负责：
- 文本模态的 RAG 编排（解析 → 入库 → 查询）
- 调用 atomic.rag.lightrag.v1 原子能力
- 不包含文档元数据管理（下沉到业务层）

部署策略：
  阶段一（当前）：不单独起服务，业务层进程内直接实例化 DomainRAGText，
  通过 RAGClient（LOCAL/REMOTE/MOCK 三态）调用 atomic 层。

  演进：当有多个业务能力共用 domain.rag.text 或需要独立扩缩容时，
  拆为独立 domain 服务，通过 Sidecar 反代，业务层仅修改 capability_runtime
  配置为 mode: remote 即可，代码无需改动。
"""

from jonex_core.capability.domain.rag_text.rag_text import DomainRAGText

__all__ = ["DomainRAGText"]
