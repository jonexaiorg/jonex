"""
Text RAG domain capability module (domain.rag.text.v1)

Responsible for:
- Text modality RAG orchestration (Parsing -> Ingestion -> Query)
- Invokes atomic.rag.lightrag.v1 atomic capability
- Does not include document Metadata management (sunk to business layer)

Deployment strategy:
  Phase 1 (current): No separate service, business layer directly instantiates DomainRAGText in-process,
  Invokes atomic layer via RAGClient (LOCAL/REMOTE/MOCK tri-state).

  Evolution: When multiple business capabilities share domain.rag.text or need independent scaling,
  Split into independent domain service, via Sidecar reverse proxy, business layer only modifies capability_runtime
  Configure as mode: remote, no code changes needed.
"""

from jonex_core.capability.domain.rag_text.rag_text import DomainRAGText

__all__ = ["DomainRAGText"]
