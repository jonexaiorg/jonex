from sqlalchemy import Column, String, SmallInteger, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import JSONB

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TimestampMixin


class Tenant(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "platform"}

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SmallInteger, default=1)
    plan_type = Column(String(32), default="free")
    expire_time = Column(TIMESTAMP)
    quota_config = Column(JSONB)
    extra_config = Column(JSONB)
