from sqlalchemy import Column, BigInteger

from jonex_core.common.database import Base
from jonex_core.common.entity import TenantMixin, TimestampMixin


class UserRole(TenantMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    role_id = Column(BigInteger, nullable=False)
