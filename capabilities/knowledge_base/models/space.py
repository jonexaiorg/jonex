
import uuid

from sqlalchemy import Column, Integer, String, Text

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class Space(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "spaces"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(String(64))
    status = Column(String(32), default="active")
    knowledge_base_count = Column(Integer, default=0)
    service_count = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, "tenant_id": self.tenant_id,
            "name": self.name, "description": self.description,
            "owner_id": self.owner_id,
            "status": self.status,
            "knowledge_base_count": self.knowledge_base_count,
            "service_count": self.service_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SpacePermission(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "space_permissions"
    __table_args__ = {"schema": "knowledge_base"}

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    space_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    role = Column(String(32), nullable=False, default="viewer")
