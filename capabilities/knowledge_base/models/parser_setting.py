#!/usr/bin/python3


import uuid

from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class KnowledgeParserSetting(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):


    __tablename__ = "knowledge_parser_settings"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    file_type = Column(String(64), nullable=False)
    file_type_label = Column(String(128), nullable=False)
    parser_config_id = Column(String(64), nullable=True)
    preprocessing_json = Column(JSONB, nullable=False, default=list)
    postprocessing_json = Column(JSONB, nullable=False, default=list)
    prompt_text = Column(Text, nullable=True)
    prompt_template_id = Column(String(64), nullable=True)
    prompt_template_version = Column(String(32), nullable=True)
    summary_prompt_text = Column(Text, nullable=True)
    summary_template_id = Column(String(64), nullable=True)
    summary_template_version = Column(String(32), nullable=True)
    tag_prompt_text = Column(Text, nullable=True)
    tag_template_id = Column(String(64), nullable=True)
    tag_template_version = Column(String(32), nullable=True)
    status = Column(String(32), nullable=False, default="active")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "knowledge_base_id": self.knowledge_base_id,
            "file_type": self.file_type,
            "file_type_label": self.file_type_label,
            "parser_config_id": self.parser_config_id,
            "preprocessing_json": self.preprocessing_json or [],
            "postprocessing_json": self.postprocessing_json or [],
            "prompt_text": self.prompt_text or "",
            "prompt_template_id": self.prompt_template_id,
            "prompt_template_version": self.prompt_template_version,
            "summary_prompt_text": self.summary_prompt_text or "",
            "summary_template_id": self.summary_template_id,
            "summary_template_version": self.summary_template_version,
            "tag_prompt_text": self.tag_prompt_text or "",
            "tag_template_id": self.tag_template_id,
            "tag_template_version": self.tag_template_version,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


__all__ = ["KnowledgeParserSetting"]
