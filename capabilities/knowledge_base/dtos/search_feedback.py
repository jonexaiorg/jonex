

from datetime import datetime
from typing import Optional

try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class SubmitSearchFeedbackRequest(BaseModel):


    session_id: str = Field(..., min_length=1, max_length=128, description="搜索会话 ID")
    query: str = Field(..., min_length=1, max_length=2000, description="搜索问题")
    answer_preview: Optional[str] = Field(default=None, description="回答摘要")
    feedback_type: str = Field(..., regex="^(like|dislike)$", description="反馈类型：like / dislike")
    knowledge_base_ids: list[str] = Field(
        ..., min_items=1, description="被引用的知识库 ID 列表，至少一个",
    )
    knowledge_base_names: Optional[dict[str, str]] = Field(
        default=None, description="知识库 ID → 名称映射",
    )
    searched_at: Optional[str] = Field(default=None, description="搜索时间（ISO 格式）")

    class Config:
        extra = "forbid"


class CancelSearchFeedbackRequest(BaseModel):


    session_id: str = Field(..., min_length=1, max_length=128, description="搜索会话 ID")
    feedback_type: str = Field(..., regex="^(like|dislike)$", description="要取消的反馈类型")
    knowledge_base_ids: list[str] = Field(
        ..., min_items=1, description="知识库 ID 列表",
    )

    class Config:
        extra = "forbid"


class ListSearchFeedbackRequest(BaseModel):


    knowledge_base_id: str = Field(..., min_length=1, max_length=128, description="知识库 ID")
    feedback_type: Optional[str] = Field(default=None, regex="^(like|dislike)?$", description="按反馈类型过滤")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=50, ge=1, le=100, description="每页条数")

    class Config:
        extra = "forbid"


class SearchFeedbackToggleAdoptRequest(BaseModel):


    feedback_id: str = Field(..., min_length=1, max_length=128, description="反馈记录 ID")

    class Config:
        extra = "forbid"


class SearchFeedbackItemResponse(BaseModel):


    id: str
    tenant_id: str
    user_id: str
    session_id: str
    query: str
    answer_preview: Optional[str] = None
    knowledge_base_id: str
    knowledge_base_name: Optional[str] = None
    feedback_type: str
    adopted: bool = False
    searched_at: Optional[datetime | str] = None
    created_at: Optional[datetime | str] = None
    updated_at: Optional[datetime | str] = None


class SearchFeedbackListResponse(BaseModel):


    items: list[SearchFeedbackItemResponse] = Field(default_factory=list)
    total: int = 0
    like_count: int = 0
    dislike_count: int = 0
    page: int = 1
    page_size: int = 50


class SearchFeedbackStatsResponse(BaseModel):


    total: int = 0
    like_count: int = 0
    dislike_count: int = 0
