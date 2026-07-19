
import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class Adapter(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "adapters"
    __table_args__ = {"schema": "business_domain"}

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(255), nullable=False)
    adapter_type = Column(String(32), nullable=False)
    config_json = Column(JSONB, default=dict)
    status = Column(String(32), default="disconnected")

    def to_dict(self):
        return {
            "id": self.id, "tenant_id": self.tenant_id,
            "name": self.name, "adapter_type": self.adapter_type,
            "config_json": self.config_json or {},
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
