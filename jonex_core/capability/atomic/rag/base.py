"""
RAG atomic capability abstract base class

All RAG adapters (LightRAG, Milvus + FAISS, etc.) must inherit from this class,
to ensure a unified invocation contract.
"""

from abc import abstractmethod
from typing import Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityType, CapabilityMetadata


class BaseRAGCapability(AtomicCapability):
    """RAG atomic capability abstract base class

    Unified RAG capability interface: insert / query / delete / get_status
    All concrete implementations (LightRAG, Pure Vector DB, etc.) must inherit from this class.
    """

    @property
    def capability_type(self) -> CapabilityType:
        return CapabilityType.ATOMIC

    @abstractmethod
    async def initialize(self) -> None:
        """Lifecycle hook: invoked on service start, completes RAG instance initialization

        Includes:
        - Initialize LightRAG storage
        - Load model
        - Warm up parser
        """
        pass

    @abstractmethod
    async def insert(
        self,
        file_path: str,
        tenant_id: str = "default",
        output_dir: Optional[str] = None,
    ) -> dict:
        """Insert document into RAG index

        Args:
            file_path: Document local path
            tenant_id: Tenant ID, for isolation
            output_dir: Parse result output directory (optional)

        Returns:
            {
                "task_id": str,   # Async task ID
                "status": "pending",
                "file_path": str
            }
        """
        pass

    @abstractmethod
    async def query(
        self,
        query: str,
        tenant_id: str = "default",
        mode: str = "hybrid",
        top_k: int = 5,
    ) -> str:
        """RAG Query

        Args:
            query: Query
            tenant_id: Tenant ID, for isolation
            mode: Query mode (naive / local / global / hybrid)
            top_k: Result count

        Returns:
            LLM-generated answer string
        """
        pass

    @abstractmethod
    async def delete(
        self,
        doc_id: str,
        tenant_id: str = "default",
    ) -> bool:
        """Delete document

        Args:
            doc_id: Document ID
            tenant_id: Tenant ID

        Returns:
            Whether deleted successfully
        """
        pass

    @abstractmethod
    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str = "default",
    ) -> dict:
        """Query async task status

        Args:
            task_id: Task ID
            tenant_id: Tenant ID

        Returns:
            {
                "task_id": str,
                "status": "pending" | "processing" | "completed" | "failed",
                "progress": float,
                "error": str | None
            }
        """
        pass

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="rag.base",
            capability_name="RAG atomic capability base class",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="RAG capability general abstract interface",
        )
