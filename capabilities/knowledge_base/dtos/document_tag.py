"""DTOs for document-tag association."""
from typing import Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:  # pragma: no cover
    from pydantic import BaseModel, Field


class SetDocumentTagsRequest(BaseModel):
    """全量替换文档标签列表。"""

    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    tag_ids: list[str] = Field(default_factory=list)


class AddDocumentTagRequest(BaseModel):
    """为文档添加单个标签。"""

    knowledge_base_id: str = Field(..., min_length=1, max_length=128)
    tag_id: str = Field(..., min_length=1, max_length=64)


class DocumentTagListResponse(BaseModel):
    """文档的标签列表响应。"""

    items: list[dict] = Field(default_factory=list)
    total: int = 0


class DocumentTagActionResponse(BaseModel):
    """文档标签操作响应。"""

    document_id: str
    tag_id: Optional[str] = None
    message: str


__all__ = [
    "AddDocumentTagRequest",
    "DocumentTagActionResponse",
    "DocumentTagListResponse",
    "SetDocumentTagsRequest",
]
