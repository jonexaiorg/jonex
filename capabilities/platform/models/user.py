from sqlalchemy import Column, BigInteger, String, SmallInteger, TIMESTAMP

from jonex_core.common.database import Base
from jonex_core.common.entity import SoftDeleteMixin, TenantMixin, TimestampMixin


class User(TenantMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "platform"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(128), nullable=False)
    password_hash = Column(String(256), nullable=False)
    display_name = Column(String(255))
    email = Column(String(255))
    role = Column(String(32), nullable=False, default="user")
    status = Column(SmallInteger, default=1)
    last_login_at = Column(TIMESTAMP)
