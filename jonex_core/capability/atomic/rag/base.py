"""
RAG 原子能力抽象基类

所有 RAG 适配器（LightRAG、Milvus + FAISS 等）必须继承此类，
保证统一的调用契约。
"""

from abc import abstractmethod
from typing import Optional

from jonex_core.capability.atomic.base import AtomicCapability
from jonex_core.capability.models import CapabilityType, CapabilityMetadata


class BaseRAGCapability(AtomicCapability):
    """RAG 原子能力抽象基类

    统一 RAG 能力接口：insert / query / delete / get_status
    所有具体实现（LightRAG、Pure Vector DB 等）必须继承此类。
    """

    @property
    def capability_type(self) -> CapabilityType:
        return CapabilityType.ATOMIC

    @abstractmethod
    async def initialize(self) -> None:
        """生命周期钩子：服务启动时调用，完成 RAG 实例初始化

        包括：
        - 初始化 LightRAG 存储
        - 加载模型
        - 预热 parser
        """
        pass

    @abstractmethod
    async def insert(
        self,
        file_path: str,
        tenant_id: str,
        knowledge_base_id: str,
        output_dir: Optional[str] = None,
        ontology_schema: Optional[dict] = None,
        preset: Optional[str] = None,
    ) -> dict:
        """插入文档到 RAG 索引

        Args:
            file_path: 文档本地路径
            tenant_id: 租户 ID，用于隔离
            knowledge_base_id: 知识库 ID，用于知识库级作用域
            output_dir: 解析结果输出目录（可选）
            ontology_schema: per-KB compiled schema（可选，push 模式）
            preset: raganything preset name（可选，KB 按文件类型解析出的解析器配置）

        Returns:
            {
                "task_id": str,   # 异步任务 ID
                "status": "pending",
                "file_path": str
            }
        """
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
        """RAG 查询

        Args:
            query: 查询问题
            tenant_id: 租户 ID，用于隔离
            mode: 查询模式（naive / local / global / hybrid）
            top_k: 返回结果数量
            knowledge_base_id: 知识库 ID，用于知识库级作用域

        Returns:
            LLM 生成的回答字符串
        """
        pass

    @abstractmethod
    async def delete(
        self,
        doc_id: str,
        tenant_id: str,
        *,
        knowledge_base_id: str = "",
    ) -> bool:
        """删除文档

        Args:
            doc_id: 文档 ID
            tenant_id: 租户 ID
            knowledge_base_id: 知识库 ID，用于定位 LightRAG workspace（与入库一致）

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    async def get_task_status(
        self,
        task_id: str,
        tenant_id: str,
    ) -> dict:
        """查询异步任务状态

        Args:
            task_id: 任务 ID
            tenant_id: 租户 ID

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
            capability_name="RAG 原子能力基类",
            capability_type=CapabilityType.ATOMIC,
            version="v1",
            description="RAG 能力通用抽象接口",
        )
