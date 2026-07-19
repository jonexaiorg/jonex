
import uuid

from sqlalchemy import Column, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TimestampMixin


class PromptTemplate(TimestampMixin, SoftDeleteMixin, Base):


    __tablename__ = "prompt_templates"
    __table_args__ = {"schema": "business_domain"}

    id = Column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)

    tenant_id = Column(String(64), nullable=True)
    name = Column(String(255), nullable=False)
    category = Column(String(64), nullable=False)
    scope = Column(String(16), nullable=False, default="domain")
    description = Column(Text)
    status = Column(String(16), nullable=False, default="启用")
    current_version = Column(String(32), nullable=False, default="1.0")

    versions_json = Column(JSONB, nullable=False, default=list)
    created_by = Column(String(128))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "category": self.category,
            "scope": self.scope,
            "description": self.description,
            "status": self.status,
            "current_version": self.current_version,
            "versions_json": self.versions_json or [],
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
