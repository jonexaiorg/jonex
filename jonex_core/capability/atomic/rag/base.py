

from abc import abstractmethod
from typing import Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityType, CapabilityMetadata


class BaseRAGCapability(AtomicCapability):


    @property
    def capability_type(self) -> CapabilityType:
        return CapabilityType.ATOMIC

    @abstractmethod
    async def initialize(self) -> None:

        pass

    @abstractmethod
    async def insert(
        self,
        file_path: str,
        tenant_id: str,
        knowledge_base_id: str,
        output_dir: Optional[str] = None,
        ontology_schema: Optional[dict] = None,
    ) -> dict:

        pass

    @abstractmethod
    async def query(
        self,
        query: str,
        tenant_id: str,
        mode: str = "hybrid",
        top_k: int = 5,
        *,
        knowledge_base_id: str,
    ) -> str:

        pass

    @abstractmethod
    async def delete(
        self,
        doc_id: str,
        tenant_id: str,
        *,
        knowledge_base_id: str = "",
    ) -> bool:

        pass

    @abstractmethod
    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str,
    ) -> dict:

        pass

    def _build_metadata(self) -> CapabilityMetadata:
        return CapabilityMetadata(
            capability_id="rag.base",
            capability_name="RAG 原子能力基类",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="RAG 能力通用抽象接口",
        )
