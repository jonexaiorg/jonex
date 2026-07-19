#!/usr/bin/python3


from sqlalchemy import Boolean, Column, Integer, String

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class Folder(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):


    __tablename__ = "folders"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True)
    knowledge_base_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_preset = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_by = Column(String(64), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "knowledge_base_id": self.knowledge_base_id,
            "is_preset": bool(self.is_preset),
            "sort_order": self.sort_order or 0,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


__all__ = ["Folder"]
