from sqlalchemy import Column, BigInteger

from jonex_core.common.database import Base
from jonex_core.common.entity import TenantMixin, TimestampMixin


class RolePermission(TenantMixin, TimestampMixin, Base):
    __tablename__ = "role_permissions"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(BigInteger, nullable=False)
    permission_id = Column(BigInteger, nullable=False)
