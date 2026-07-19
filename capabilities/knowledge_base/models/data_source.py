#!/usr/bin/python3


import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class KnowledgeDataSource(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):


    __tablename__ = "knowledge_data_sources"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    access_method_id = Column(String(64), nullable=True)
    access_type = Column(String(32), nullable=False)
    name = Column(String(255), nullable=False)
    config_json = Column(JSONB, nullable=False, default=dict)
    sync_mode = Column(String(16), nullable=False, default="manual")
    cron_expr = Column(String(128), nullable=True)
    schedule_task_id = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False, default="active")
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_status = Column(String(32), nullable=True)
    last_sync_message = Column(Text, nullable=True)
    document_count = Column(Integer, nullable=False, default=0)


    _SECRET_KEYS = ("token_ref", "credential_ref", "ingest_key_hash")

    def to_dict(self, *, reveal: bool = False) -> dict:
        cfg = dict(self.config_json or {})
        if not reveal:

            for k in self._SECRET_KEYS:
                if k in cfg:
                    cfg[k] = "***"
            auth = cfg.get("auth")
            if isinstance(auth, dict) and auth.get("token_ref"):
                auth = dict(auth)
                auth["token_ref"] = "***"
                cfg["auth"] = auth
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "knowledge_base_id": self.knowledge_base_id,
            "access_method_id": self.access_method_id,
            "access_type": self.access_type,
            "name": self.name,
            "config_json": cfg,
            "sync_mode": self.sync_mode,
            "cron_expr": self.cron_expr,
            "schedule_task_id": self.schedule_task_id,
            "status": self.status,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_sync_status": self.last_sync_status,
            "last_sync_message": self.last_sync_message,
            "document_count": self.document_count or 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


__all__ = ["KnowledgeDataSource"]
