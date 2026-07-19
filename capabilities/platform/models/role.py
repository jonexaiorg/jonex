from sqlalchemy import Column, BigInteger, String, SmallInteger

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class Role(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(String(512))
    is_system = Column(SmallInteger, default=0)
